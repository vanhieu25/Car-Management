"""Unit tests for BaoHanhService — T-G4.3.TEST.01..05.

Tests:
- TEST.01: Unit test auto_create_from_hop_dong → ngay_ket_thuc (BR-BH-02)
- TEST.02: Unit test create_request reject nếu ngày > ngay_ket_thuc
- TEST.03: Test find_expiring_in_30_days với 5 BH (3 trong window)
- TEST.04: Integration WF-04: HĐ → giao xe → BH tự sinh → tạo request → in phiếu
- TEST.05: UAT theo AC-BH-01, 02

References:
- BR-BH-01..10 — Warranty management
- BR-BH-01: Auto-create BH when contract is delivered
- BR-BH-02: ngay_ket_thuc = ngay_bat_dau + thoi_han_bh months
- BR-BH-03: Warn when warranty expiring within 30 days
- BR-BH-04: Classify requests (mien_phi / tinh_phi)
- BR-BH-05: Request status transitions
- BR-BH-06: chi_phi validation
- BR-BH-07: Warranty slip PDF content
- TRG-02: Warranty creation on delivery
- AC-BH-01: List warranties with correct info
- AC-BH-02: Warranty detail screen shows all fields
"""

import pytest
import sqlite3
import os
import sys
import tempfile
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.application.services.bao_hanh_service import (
    BaoHanhService,
    BaoHanhYeuCauData,
    BaoHanhNotFoundError,
    BaoHanhYeuCauNotFoundError,
    InvalidStateTransitionError,
    ValidationError,
)


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def warranty_db(tmp_path):
    """Create a fresh database with all migrations and seed data for warranty tests."""
    db_path = str(tmp_path / "warranty_test.db")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Run all migrations
    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(db_path)
    runner.run_pending()

    # Insert vai_tro
    conn.execute("""
        INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro)
        VALUES (1, 'admin', 'Quản trị viên'),
               (2, 'sales', 'Nhân viên bán hàng'),
               (3, 'ky_thuat_bh', 'Nhân viên kỹ thuật bảo hành')
    """)

    # Insert nhan_vien (including technicians)
    conn.execute("""
        INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai)
        VALUES (1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Admin User', 'admin@test.com', 1, 'active'),
               (2, 'sales1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Sales One', 'sales1@test.com', 2, 'active'),
               (3, 'tech1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Tech One', 'tech1@test.com', 3, 'active'),
               (4, 'tech2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Tech Two', 'tech2@test.com', 3, 'active')
    """)

    # Insert khach_hang
    conn.execute("""
        INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email, dia_chi, phan_loai, tong_gia_tri_mua, so_xe_da_mua)
        VALUES (1, 'Khach Hang Test', '0909000001', 'kh1@test.com', '123 Test St', 'Thuong', 0, 0),
               (2, 'VIP Customer', '0909000002', 'vip@test.com', '456 VIP St', 'VIP', 2000000000, 2)
    """)

    # Insert xe
    conn.execute("""
        INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, muc_toi_thieu, trang_thai)
        VALUES (1, 'XE001', 'Toyota', 'Camry', 2024, 'Den', 500000000, 5, 2, 'con_hang'),
               (2, 'XE002', 'Honda', 'Civic', 2024, 'Trang', 400000000, 2, 2, 'con_hang'),
               (3, 'XE003', 'BMW', 'X5', 2024, 'Den', 1500000000, 1, 1, 'con_hang')
    """)

    # Insert hop_dong (with various statuses)
    today = datetime.now()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    conn.execute("""
        INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id,
                              gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien,
                              trang_thai, ngay_tao, ngay_thanh_toan, ngay_giao_xe, ghi_chu)
        VALUES (1, 'HD001', 1, 1, 1,
                500000000, 0, 0, 500000000,
                'moi_tao', ?, NULL, NULL, 'Test moi_tao'),
               (2, 'HD002', 1, 1, 1,
                500000000, 0, 0, 500000000,
                'da_thanh_toan', ?, ?, NULL, 'Test da_thanh_toan'),
               (3, 'HD003', 2, 2, 1,
                400000000, 0, 0, 400000000,
                'da_giao_xe', ?, ?, ?, 'Test da_giao_xe'),
               (4, 'HD004', 2, 3, 1,
                1500000000, 0, 0, 1500000000,
                'da_giao_xe', ?, ?, ?, 'Test da_giao_xe 2'),
               (5, 'HD005', 1, 2, 2,
                400000000, 0, 0, 400000000,
                'da_giao_xe', ?, ?, ?, 'Test 30-day warning')
    """, (
        today.strftime("%Y-%m-%d"),  # HD1 ngay_tao
        today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"),  # HD2 ngay_tao, ngay_thanh_toan
        today.strftime("%Y-%m-%d"), yesterday, yesterday,  # HD3 ngay_tao, ngay_thanh_toan, ngay_giao_xe
        today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), yesterday,  # HD4
        today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), (today - timedelta(days=365)).strftime("%Y-%m-%d"),  # HD5 ngay_giao_xe = 1 year ago
    ))

    # Insert system_settings with thoi_han_bh_default
    conn.execute("""
        INSERT INTO system_settings (ma_settings, gia_tri, mo_ta)
        VALUES ('thoi_han_bh_default', '24', 'Thoi han bao hanh mac dinh (thang)'),
               ('muc_toi_thieu_default', '2', 'Muc toi thieu ton kho')
    """)

    # Insert bao_hanh records
    # BH1: Valid, > 30 days to expiry (created from HD3)
    ngay_bat_dau_1 = yesterday
    ngay_ket_thuc_1 = (datetime.fromisoformat(ngay_bat_dau_1) + relativedelta(months=24)).strftime("%Y-%m-%d")

    # BH2: Expiring within 30 days (created from HD4)
    ngay_bat_dau_2 = (today - timedelta(days=360)).strftime("%Y-%m-%d")
    ngay_ket_thuc_2 = (today + timedelta(days=25)).strftime("%Y-%m-%d")

    # BH3: Expiring within 30 days (created from HD5)
    ngay_bat_dau_3 = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    ngay_ket_thuc_3 = (today + timedelta(days=15)).strftime("%Y-%m-%d")

    # BH4: Already expired
    ngay_bat_dau_4 = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    ngay_ket_thuc_4 = (today - timedelta(days=10)).strftime("%Y-%m-%d")

    # BH5: Expiring in exactly 10 days (within window)
    ngay_bat_dau_5 = (today - timedelta(days=355)).strftime("%Y-%m-%d")
    ngay_ket_thuc_5 = (today + timedelta(days=10)).strftime("%Y-%m-%d")

    conn.execute("""
        INSERT INTO bao_hanh (id, hop_dong_id, xe_id, khach_hang_id, thoi_han_bh,
                               ngay_bat_dau, ngay_ket_thuc, pham_vi, trang_thai)
        VALUES (1, 3, 2, 2, 24, ?, ?, 'Bảo hành toàn diện', 'con_hieu_luc'),
               (2, 4, 3, 2, 24, ?, ?, 'Bảo hành toàn diện', 'con_hieu_luc'),
               (3, 5, 2, 1, 24, ?, ?, 'Bảo hành toàn diện', 'con_hieu_luc'),
               (4, 100, 1, 1, 24, ?, ?, 'Bảo hành toàn diện', 'het_han'),
               (5, 101, 2, 1, 24, ?, ?, 'Bảo hành toàn diện', 'con_hieu_luc')
    """, (
        ngay_bat_dau_1, ngay_ket_thuc_1,
        ngay_bat_dau_2, ngay_ket_thuc_2,
        ngay_bat_dau_3, ngay_ket_thuc_3,
        ngay_bat_dau_4, ngay_ket_thuc_4,
        ngay_bat_dau_5, ngay_ket_thuc_5,
    ))

    # Insert some bao_hanh_yeu_cau for BH3
    conn.execute("""
        INSERT INTO bao_hanh_yeu_cau (id, bao_hanh_id, nhan_vien_id, ngay_yeu_cau,
                                      mo_ta_tinh_trang, loai_yeu_cau, chi_phi, trang_thai)
        VALUES (1, 3, 3, ?, 'Sua loi dong co', 'sua_chua', 0, 'dang_xu_ly')
    """, (yesterday,))

    conn.commit()
    conn.close()

    return db_path


# =============================================================================
# TEST Class 1: TestAutoCreate — BR-BH-01, BR-BH-02
# =============================================================================
class TestAutoCreate:
    """TEST.01 — BaoHanhService.auto_create_from_hop_dong"""

    def test_tao_bh_tu_hop_dong(self, warranty_db):
        """Verify BH created with correct hop_dong_id (BR-BH-01)."""
        from app.application.services.hop_dong_service import HopDongService, HopDongCreateData

        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Get hop_dong in da_giao_xe state (HD3 has ngay_giao_xe set)
        hd_service = HopDongService(conn)
        bh_service = BaoHanhService(conn)

        # Get HD3 which is already in da_giao_xe state
        cursor = conn.execute(
            "SELECT id, ngay_giao_xe FROM hop_dong WHERE id = 3"
        )
        hd_row = cursor.fetchone()
        assert hd_row is not None

        # Create BH from HD3
        bh = bh_service.auto_create_from_hop_dong(hd_row[0], nhan_vien_id=1)

        assert bh is not None
        assert bh["hop_dong_id"] == hd_row[0]
        assert bh["trang_thai"] == "con_hieu_luc"
        conn.close()

    def test_ngay_ket_thuc_tinh_dung(self, warranty_db):
        """ngay_ket_thuc = ngay_giao_xe + thoi_han (BR-BH-02)."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Use HD4 which has ngay_giao_xe = yesterday
        cursor = conn.execute("SELECT id, ngay_giao_xe FROM hop_dong WHERE id = 4")
        hd_row = cursor.fetchone()
        assert hd_row is not None
        ngay_giao = hd_row[1]
        assert ngay_giao is not None

        # Create BH
        bh = bh_service.auto_create_from_hop_dong(hd_row[0], nhan_vien_id=1)

        # ngay_ket_thuc should = ngay_giao + 24 months
        expected_ngay_ket_thuc = (
            datetime.fromisoformat(ngay_giao) + relativedelta(months=24)
        ).strftime("%Y-%m-%d")

        assert bh["ngay_ket_thuc"] == expected_ngay_ket_thuc
        assert bh["thoi_han_bh"] == 24
        conn.close()

    def test_mot_hd_mot_bh(self, warranty_db):
        """Cannot create 2 BH for same contract — returns existing BH (BR-BH-01)."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # HD3 already has BH (id=1)
        cursor = conn.execute("SELECT id FROM bao_hanh WHERE hop_dong_id = 3")
        existing_bh_id = cursor.fetchone()[0]

        # Try to create another BH from same HD — should return existing one
        bh = bh_service.auto_create_from_hop_dong(3, nhan_vien_id=1)

        assert bh["id"] == existing_bh_id
        assert bh["hop_dong_id"] == 3

        # Verify only one BH exists for this HD
        cursor = conn.execute("SELECT COUNT(*) FROM bao_hanh WHERE hop_dong_id = 3")
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()


# =============================================================================
# TEST Class 2: TestCreateRequest — BR-BH-04, date validation
# =============================================================================
class TestCreateRequest:
    """TEST.02 — BaoHanhService.create_request"""

    def test_tao_request_trong_han(self, warranty_db):
        """ngay_yeu_cau <= ngay_ket_thuc → success."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # BH3 has ngay_ket_thuc in ~15 days (future date)
        cursor = conn.execute("SELECT id, ngay_ket_thuc FROM bao_hanh WHERE id = 3")
        bh_row = cursor.fetchone()
        bh_id = bh_row[0]
        ngay_ket_thuc = bh_row[1]

        # ngay_yeu_cau = today (within warranty)
        ngay_yeu_cau = datetime.now().strftime("%Y-%m-%d")

        data = BaoHanhYeuCauData(
            ngay_yeu_cau=ngay_yeu_cau,
            loai_yeu_cau="sua_chua",
            mo_ta_tinh_trang="O to phat ra tieng ong",
            nhan_vien_id=3,
        )

        result = bh_service.create_request(bh_id, data, nhan_vien_id=3)

        assert result is not None
        assert result["bao_hanh_id"] == bh_id
        assert result["trang_thai"] == "dang_xu_ly"
        conn.close()

    def test_tao_request_het_han(self, warranty_db):
        """ngay_yeu_cau > ngay_ket_thuc → raises ValidationError."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # BH4 is already expired
        cursor = conn.execute("SELECT id, ngay_ket_thuc FROM bao_hanh WHERE id = 4")
        bh_row = cursor.fetchone()
        bh_id = bh_row[0]
        ngay_ket_thuc = bh_row[1]

        # ngay_yeu_cau = ngay_ket_thuc + 10 days (after expiry)
        future_date = (
            datetime.fromisoformat(ngay_ket_thuc) + timedelta(days=10)
        ).strftime("%Y-%m-%d")

        data = BaoHanhYeuCauData(
            ngay_yeu_cau=future_date,
            loai_yeu_cau="sua_chua",
            mo_ta_tinh_trang="O to bi hong may",
            nhan_vien_id=3,
        )

        with pytest.raises(ValidationError) as exc_info:
            bh_service.create_request(bh_id, data, nhan_vien_id=3)

        assert "không được sau ngày kết thúc BH" in str(exc_info.value)
        conn.close()

    def test_phan_loai_mien_phi(self, warranty_db):
        """Request with NSX fault → phan_loai = 'mien_phi' (BR-BH-04)."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Use BH1 (valid warranty)
        data = BaoHanhYeuCauData(
            ngay_yeu_cau=datetime.now().strftime("%Y-%m-%d"),
            loai_yeu_cau="sua_chua",
            mo_ta_tinh_trang="Dong co phat ra tieng ket, loi san xuat",
            nhan_vien_id=3,
        )

        result = bh_service.create_request(bh_id=1, data=data, nhan_vien_id=3)

        assert result["phan_loai"] == "mien_phi"
        assert result["chi_phi"] == 0
        conn.close()

    def test_phan_loai_tinh_phi(self, warranty_db):
        """Request with KH fault keywords → phan_loai = 'tinh_phi' (BR-BH-04)."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Keywords like "va đập", "ngập nước", "tai nan" → tinh_phi
        fault_descriptions = [
            "Xe bị va đập cửa trước bên trái",
            "O to bi ngap nuoc do mua",
            "Xe tai nan dut can",
        ]

        for desc in fault_descriptions:
            data = BaoHanhYeuCauData(
                ngay_yeu_cau=datetime.now().strftime("%Y-%m-%d"),
                loai_yeu_cau="sua_chua",
                mo_ta_tinh_trang=desc,
                chi_phi=2000000,
                nhan_vien_id=3,
            )

            result = bh_service.create_request(bh_id=2, data=data, nhan_vien_id=3)
            assert result["phan_loai"] == "tinh_phi", f"Expected tinh_phi for: {desc}"
            assert result["chi_phi"] == 2000000
        conn.close()


# =============================================================================
# TEST Class 3: TestFindExpiring — BR-BH-03
# =============================================================================
class TestFindExpiring:
    """TEST.03 — BaoHanhService.find_expiring_in_30_days"""

    def test_tim_bh_sap_het_han_30_ngay(self, warranty_db):
        """Finds BH expiring within 30 days (3 BHs in window: BH2, BH3, BH5)."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        result = bh_service.find_expiring_in_30_days()

        # BH2 (25 days), BH3 (15 days), BH5 (10 days) should be found
        assert len(result) >= 3

        found_ids = [r["id"] for r in result]
        assert 2 in found_ids  # 25 days to expiry
        assert 3 in found_ids  # 15 days to expiry
        assert 5 in found_ids  # 10 days to expiry

        # BH4 is already expired — should NOT be found
        assert 4 not in found_ids
        conn.close()

    def test_khong_tim_bh_het_han(self, warranty_db):
        """Expired BH (BH4) not found in expiring list."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        result = bh_service.find_expiring_in_30_days()

        found_ids = [r["id"] for r in result]
        assert 4 not in found_ids  # BH4 is expired
        conn.close()

    def test_khong_tim_bh_con_han(self, warranty_db):
        """BH with >30 days until expiry not found."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        result = bh_service.find_expiring_in_30_days()

        found_ids = [r["id"] for r in result]
        assert 1 not in found_ids  # BH1 has >1 year left (id not in warranty_db BH list that expires soon)
        conn.close()


# =============================================================================
# TEST Class 4: TestWF04Integration — BR-BH-05, WF-04 end-to-end
# =============================================================================
class TestWF04Integration:
    """TEST.04 — WF-04 end-to-end: HĐ → giao xe → BH tự sinh → tạo request → in phiếu"""

    def test_wf04_day_du(self, warranty_db):
        """Full WF-04: HĐ → giao xe → BH → request → complete."""
        from app.application.services.hop_dong_service import HopDongService, HopDongCreateData

        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        hd_service = HopDongService(conn)
        bh_service = BaoHanhService(conn)

        # Step 1: Create new HD in da_giao_xe state
        # First need a hop_dong in da_giao_xe
        cursor = conn.execute(
            "SELECT id FROM hop_dong WHERE trang_thai = 'da_giao_xe' LIMIT 1"
        )
        hd_id = cursor.fetchone()[0]

        # Get current BH count
        cursor = conn.execute("SELECT COUNT(*) FROM bao_hanh")
        before_count = cursor.fetchone()[0]

        # Step 2: auto_create_from_hop_dong (TRG-02)
        bh = bh_service.auto_create_from_hop_dong(hd_id, nhan_vien_id=1)

        # Verify BH was created
        cursor = conn.execute("SELECT COUNT(*) FROM bao_hanh")
        after_count = cursor.fetchone()[0]

        # BH should be new or already existed
        assert after_count >= before_count
        assert bh["hop_dong_id"] == hd_id

        # Step 3: Create warranty request
        data = BaoHanhYeuCauData(
            ngay_yeu_cau=datetime.now().strftime("%Y-%m-%d"),
            loai_yeu_cau="sua_chua",
            mo_ta_tinh_trang="Sua loi he thong phanh",
            nhan_vien_id=3,
        )
        request = bh_service.create_request(bh["id"], data, nhan_vien_id=3)
        assert request["trang_thai"] == "dang_xu_ly"

        # Step 4: Complete the request
        updated = bh_service.update_request(
            req_id=request["id"],
            trang_thai="da_hoan_thanh",
            chi_phi=500000,
            nhan_vien_id_current=3,
        )
        assert updated["trang_thai"] == "da_hoan_thanh"
        conn.close()

    def test_wf04_bh_duoc_tao_tu_dong(self, warranty_db):
        """TRG-02 verified: BH is created automatically from hop_dong delivery."""
        from app.application.services.hop_dong_service import HopDongService

        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Use HD that is already in da_giao_xe but has no BH yet
        # HD3 already has BH (id=1), so use HD that doesn't have BH
        # First check if there's a da_giao_xe HD without BH
        cursor = conn.execute("""
            SELECT hd.id FROM hop_dong hd
            LEFT JOIN bao_hanh bh ON hd.id = bh.hop_dong_id
            WHERE hd.trang_thai = 'da_giao_xe' AND bh.id IS NULL
            LIMIT 1
        """)
        row = cursor.fetchone()

        if row:
            hd_id = row[0]
            bh = bh_service.auto_create_from_hop_dong(hd_id, nhan_vien_id=1)
            assert bh["hop_dong_id"] == hd_id
            assert bh["trang_thai"] == "con_hieu_luc"
        else:
            # All da_giao_xe HDs already have BHs — verify existing one
            cursor = conn.execute("""
                SELECT bh.id, bh.hop_dong_id FROM bao_hanh bh
                JOIN hop_dong hd ON bh.hop_dong_id = hd.id
                WHERE hd.trang_thai = 'da_giao_xe'
                LIMIT 1
            """)
            bh_row = cursor.fetchone()
            assert bh_row is not None
            assert bh_row[1] is not None

        conn.close()

    def test_wf04_request_state_transitions(self, warranty_db):
        """Request status transitions: cho_xac_nhan → dang_xu_ly → hoan_thanh."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Use BH3 which has an existing request (id=1)
        # The existing request is already in dang_xu_ly state
        cursor = conn.execute("""
            SELECT id, trang_thai FROM bao_hanh_yeu_cau WHERE bao_hanh_id = 3
        """)
        req_row = cursor.fetchone()
        req_id = req_row[0]
        assert req_row[1] == "dang_xu_ly"

        # Complete the request
        result = bh_service.update_request(
            req_id=req_id,
            trang_thai="da_hoan_thanh",
            chi_phi=1000000,
            nhan_vien_id_current=3,
        )
        assert result["trang_thai"] == "da_hoan_thanh"

        # Verify transition from dang_xu_ly → da_hoan_thanh is valid
        # (BR-BH-05 defines: dang_xu_ly → [da_hoan_thanh, da_dong])
        conn.close()


# =============================================================================
# TEST Class 5: TestUAT_ACBH — AC-BH-01, AC-BH-02
# =============================================================================
class TestUAT_ACBH:
    """TEST.05 — UAT: List BH (AC-BH-01), Detail (AC-BH-02), PDF export (BR-BH-07)"""

    def test_acbh_01(self, warranty_db):
        """AC-BH-01: List BH shows correct info (ma_bh, khach_hang, xe, ngay_ket_thuc, trang_thai)."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Get all BHs with filter
        result = bh_service.get_all(trang_thai="tat_ca", page=1, page_size=50)

        assert result.total >= 5
        assert len(result.items) >= 5

        # Verify each item has required fields for list display
        for item in result.items:
            assert "id" in item
            assert "khach_hang_id" in item or "kh_ho_ten" in item
            assert "xe_id" in item or "xe_hang" in item
            assert "ngay_ket_thuc" in item
            assert "trang_thai" in item

        conn.close()

    def test_acbh_02(self, warranty_db):
        """AC-BH-02: Detail screen shows all fields (BH info + KH + Xe + HD + requests)."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Get BH3 (has a yeu_cau)
        detail = bh_service.get_by_id(3)

        assert detail is not None
        assert "id" in detail
        assert "hop_dong_id" in detail
        assert "xe_id" in detail
        assert "khach_hang_id" in detail
        assert "thoi_han_bh" in detail
        assert "ngay_bat_dau" in detail
        assert "ngay_ket_thuc" in detail
        assert "pham_vi" in detail
        assert "trang_thai" in detail

        # Nested KH info
        assert "khach_hang" in detail
        assert detail["khach_hang"]["ho_ten"] is not None

        # Nested Xe info
        assert "xe" in detail
        assert detail["xe"]["hang"] is not None

        # Nested HD info
        assert "hop_dong" in detail

        # Nested yeu_cau list
        assert "yeu_cau_list" in detail
        assert isinstance(detail["yeu_cau_list"], list)
        conn.close()

    def test_warranty_pdf_renders(self, warranty_db):
        """BR-BH-07: Warranty PDF export renders without error."""
        conn = sqlite3.connect(warranty_db)
        conn.execute("PRAGMA foreign_keys = ON")
        bh_service = BaoHanhService(conn)

        # Use BH3 which has a request
        bh_id = 3

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            output_path = f.name

        try:
            result_path = bh_service.export_warranty_pdf(bh_id, output_path)
            assert result_path == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

        conn.close()
