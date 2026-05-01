"""Unit tests for TraGopService - T-G4.5.TEST.01..05.

Tests:
- TEST.01: calculate_monthly_payment 6 cases (BR-CALC-04)
- TEST.02: create 4 cases (BR-TG-01..03)
- TEST.03: daily_overdue_check TRG-07
- TEST.04: WF-03 integration 3 cases
- TEST.05: UAT AC-TG-* 3 cases

References:
- BR-CALC-04: M = P × r × (1+r)^n / ((1+r)^n − 1)
- BR-TG-01: UNIQUE hop_dong_id (only 1 installment per contract)
- BR-TG-02: P <= hop_dong.tong_tien
- BR-TG-03: Auto-generate n rows of payment schedule
- BR-TG-04: Record payment updates kỳ to 'da_tra'
- BR-TG-05: All kỳ paid → tra_gop.status = 'hoan_thanh'
- TRG-07: Daily check for overdue (ngay_den_han + 5 days < today)
"""

import pytest
import sqlite3
import os
import sys
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.application.services.tra_gop_service import (
    TraGopService,
    TraGopNotFoundError,
    TraGopAlreadyExistsError,
    ValidationError,
)
from app.infrastructure.repositories.tra_gop_repository import TraGopRepository


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fresh_db():
    """Create a fresh database with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(db_path)
    runner.run_pending()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def installment_db(fresh_db):
    """Create database with seed data for installment tests."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Run migrations
    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(fresh_db)
    runner.run_pending()

    # Insert test vai_tro
    conn.execute("""
        INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro)
        VALUES (1, 'admin', 'Quản trị viên'),
               (2, 'sales', 'Nhân viên bán hàng')
    """)

    # Insert test nhan_vien
    conn.execute("""
        INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai)
        VALUES (1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Admin User', 'admin@test.com', 1, 'active'),
               (2, 'sales1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Sales One', 'sales1@test.com', 2, 'active')
    """)

    # Insert test khach_hang
    conn.execute("""
        INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email, dia_chi, phan_loai, tong_gia_tri_mua, so_xe_da_mua)
        VALUES (1, 'Khach Hang Test', '0909000001', 'kh1@test.com', '123 Test St', 'Thuong', 0, 0),
               (2, 'VIP Customer', '0909000002', 'vip@test.com', '456 VIP St', 'VIP', 2000000000, 2)
    """)

    # Insert test xe with known stock
    conn.execute("""
        INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, muc_toi_thieu, trang_thai)
        VALUES (1, 'XE001', 'Toyota', 'Camry', 2024, 'Den', 500000000, 5, 2, 'con_hang'),
               (2, 'XE002', 'Honda', 'Civic', 2024, 'Trang', 400000000, 2, 2, 'con_hang')
    """)

    # Insert test hop_dong (various statuses)
    # HD1: da_thanh_toan - for creating installment
    conn.execute("""
        INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, ngay_tao, trang_thai, gia_xe, tong_tien)
        VALUES (1, 'HD001', 1, 1, 1, '2026-01-01', 'da_thanh_toan', 500000000, 500000000)
    """)

    # HD2: da_giao_xe - for creating installment
    conn.execute("""
        INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, ngay_tao, trang_thai, gia_xe, tong_tien, ngay_thanh_toan)
        VALUES (2, 'HD002', 1, 2, 1, '2026-01-05', 'da_giao_xe', 400000000, 400000000, '2026-01-10')
    """)

    # HD3: moi_tao - should not allow installment
    conn.execute("""
        INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, ngay_tao, trang_thai, gia_xe, tong_tien)
        VALUES (3, 'HD003', 1, 1, 1, '2026-01-15', 'moi_tao', 500000000, 500000000)
    """)

    # HD4: for duplicate test
    conn.execute("""
        INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, ngay_tao, trang_thai, gia_xe, tong_tien)
        VALUES (4, 'HD004', 1, 1, 1, '2026-01-20', 'da_giao_xe', 500000000, 500000000)
    """)

    conn.commit()
    conn.close()

    yield fresh_db

    if os.path.exists(fresh_db):
        os.unlink(fresh_db)


# =============================================================================
# TEST.01 — calculate_monthly_payment
# =============================================================================
class TestCalculateMonthlyPayment:
    """TEST.01 — calculate_monthly_payment with 6 cases [BLOCKER]"""

    def test_p500m_r10_n24(self, installment_db):
        """P=500,000,000, r=10%, n=24 → M ≈ 23,270,000"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        M = service.calculate_monthly_payment(500_000_000, 10.0, 24)
        # M = P * r * (1+r)^n / ((1+r)^n - 1)
        # r = 10/12/100 = 0.008333...
        # (1+r)^24 ≈ 1.2209
        # M = 500M * 0.008333 * 1.2209 / 0.2209 ≈ 23,270,000
        assert 23_200_000 <= M <= 23_300_000, f"Expected ~23,270,000, got {M:,}"
        conn.close()

    def test_p1t_r8_n36(self, installment_db):
        """P=1,000,000,000, r=8%, n=36 → M ≈ 30,400,000"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        M = service.calculate_monthly_payment(1_000_000_000, 8.0, 36)
        # M ≈ 30,400,000
        assert 30_300_000 <= M <= 30_500_000, f"Expected ~30,400,000, got {M:,}"
        conn.close()

    def test_r0_edge(self, installment_db):
        """r=0% → M = P/n (no interest)"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        M = service.calculate_monthly_payment(1_000_000_000, 0.0, 10)
        assert M == 100_000_000, f"Expected 100,000,000, got {M:,}"
        conn.close()

    def test_r30_max(self, installment_db):
        """r=30% → still valid, verify formula works"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        M = service.calculate_monthly_payment(500_000_000, 30.0, 12)
        # Should calculate without error
        assert M > 0, "Should return positive value"
        # At 30% annual, monthly ~2.5%, with 12 periods
        # (1+r)^12 ≈ 1.34, M ≈ 500M * 0.025 * 1.34 / 0.34 ≈ 49.4M
        assert M > 40_000_000, f"Expected > 40M at 30%, got {M:,}"
        conn.close()

    def test_n6_short(self, installment_db):
        """n=6 months (minimum)"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        M = service.calculate_monthly_payment(600_000_000, 10.0, 6)
        assert M > 0, "Should return positive value"
        # Check that it's roughly P/n + interest
        # P/n = 100M, interest adds ~5M → ~105M
        assert M > 100_000_000, f"Expected > 100M for n=6, got {M:,}"
        conn.close()

    def test_n84_long(self, installment_db):
        """n=84 months (maximum)"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        M = service.calculate_monthly_payment(500_000_000, 10.0, 84)
        assert M > 0, "Should return positive value"
        # Longer term = lower monthly payment
        # At n=84, M should be much lower than n=24 case (23.27M)
        assert M < 10_000_000, f"Expected < 10M for n=84, got {M:,}"
        conn.close()


# =============================================================================
# TEST.02 — create installment
# =============================================================================
class TestCreateInstallment:
    """TEST.02 — create installment with 4 cases"""

    def test_create_sinh_n_ky_lich_su(self, installment_db):
        """create with n=12 → 12 rows in tra_gop_lich_su"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        tra_gop = service.create(
            hop_dong_id=1,
            ngan_hang="Vietcombank",
            P=400_000_000,
            r_year=10.0,
            n=12,
            nhan_vien_id=1
        )

        # Verify 12 lich_su rows
        cursor = conn.execute(
            "SELECT COUNT(*) FROM tra_gop_lich_su WHERE tra_gop_id = ?",
            (tra_gop.id,)
        )
        count = cursor.fetchone()[0]
        assert count == 12, f"Expected 12 lich_su rows, got {count}"
        conn.close()

    def test_create_tien_thang_dung(self, installment_db):
        """so_tien_phai_tra = M (calculated correctly)"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        P = 500_000_000
        r = 10.0
        n = 24
        expected_M = service.calculate_monthly_payment(P, r, n)

        tra_gop = service.create(
            hop_dong_id=1,
            ngan_hang="Vietcombank",
            P=P,
            r_year=r,
            n=n,
            nhan_vien_id=1
        )

        assert tra_gop.so_tien_tra_thang == expected_M, \
            f"Expected {expected_M:,}, got {tra_gop.so_tien_tra_thang:,}"
        conn.close()

    def test_create_ngay_den_han_tang_dan(self, installment_db):
        """ngay_den_han for ky1 < ky2 < ... < kyn"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # HD2 has ngay_thanh_toan = '2026-01-10'
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="ACB",
            P=300_000_000,
            r_year=8.0,
            n=6,
            nhan_vien_id=1
        )

        cursor = conn.execute(
            """SELECT ky_thu, ngay_den_han FROM tra_gop_lich_su
               WHERE tra_gop_id = ? ORDER BY ky_thu""",
            (tra_gop.id,)
        )
        rows = cursor.fetchall()

        dates = [row[1] for row in rows]
        assert dates == sorted(dates), f"Dates should be ascending: {dates}"

        # Check each ky increments by 1 month
        for i, row in enumerate(rows, start=1):
            assert row[0] == i, f"Expected ky {i}, got {row[0]}"
        conn.close()

    def test_create_mot_hd_mot_tg(self, installment_db):
        """UNIQUE hop_dong_id prevents duplicate"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # First create
        service.create(
            hop_dong_id=4,
            ngan_hang="Vietcombank",
            P=400_000_000,
            r_year=10.0,
            n=12,
            nhan_vien_id=1
        )

        # Second create for same contract → should raise
        with pytest.raises(TraGopAlreadyExistsError):
            service.create(
                hop_dong_id=4,
                ngan_hang="ACB",
                P=300_000_000,
                r_year=8.0,
                n=6,
                nhan_vien_id=1
            )
        conn.close()


# =============================================================================
# TEST.03 — daily_overdue_check TRG-07
# =============================================================================
class TestDailyOverdueCheck:
    """TEST.03 — TRG-07 daily overdue check"""

    def test_qua_han_sau_5_ngay(self, installment_db):
        """ngay_den_han + 5 days < today → status = 'qua_han'"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="Vietcombank",
            P=300_000_000,
            r_year=8.0,
            n=3,
            nhan_vien_id=1
        )

        # Manually set ngay_den_han to 10 days ago (so +5 days < today)
        today = date.today()
        past_date = (today - timedelta(days=10)).isoformat()

        conn.execute(
            """UPDATE tra_gop_lich_su
               SET ngay_den_han = ?
               WHERE tra_gop_id = ? AND ky_thu = 1""",
            (past_date, tra_gop.id)
        )
        conn.commit()

        # Run daily check
        updated = service.daily_overdue_check()

        # Should mark 1 record as qua_han
        assert updated == 1, f"Expected 1 update, got {updated}"

        # Verify status changed
        cursor = conn.execute(
            "SELECT trang_thai FROM tra_gop_lich_su WHERE tra_gop_id = ? AND ky_thu = 1",
            (tra_gop.id,)
        )
        status = cursor.fetchone()[0]
        assert status == "qua_han", f"Expected 'qua_han', got '{status}'"
        conn.close()

    def test_chua_qua_han_4_ngay(self, installment_db):
        """ngay_den_han + 4 days < today → still 'chua_tra'"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="ACB",
            P=200_000_000,
            r_year=10.0,
            n=3,
            nhan_vien_id=1
        )

        # Set ngay_den_han to 4 days ago (so +4 days == today, not < today)
        today = date.today()
        recent_date = (today - timedelta(days=4)).isoformat()

        conn.execute(
            """UPDATE tra_gop_lich_su
               SET ngay_den_han = ?
               WHERE tra_gop_id = ? AND ky_thu = 1""",
            (recent_date, tra_gop.id)
        )
        conn.commit()

        # Run daily check
        updated = service.daily_overdue_check()

        # Should NOT mark as qua_han (exactly 4 days ago, +4 days == today, not < today)
        assert updated == 0, f"Expected 0 updates, got {updated}"

        # Verify still chua_tra
        cursor = conn.execute(
            "SELECT trang_thai FROM tra_gop_lich_su WHERE tra_gop_id = ? AND ky_thu = 1",
            (tra_gop.id,)
        )
        status = cursor.fetchone()[0]
        assert status == "chua_tra", f"Expected 'chua_tra', got '{status}'"
        conn.close()


# =============================================================================
# TEST.04 — WF-03 integration
# =============================================================================
class TestWF03Integration:
    """TEST.04 — WF-03 end-to-end workflow"""

    def test_wf03_day_du(self, installment_db):
        """Create contract → add installment → record 3 payments → check status"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment with 6 kỳ
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="Vietcombank",
            P=300_000_000,
            r_year=8.0,
            n=6,
            nhan_vien_id=1
        )
        assert tra_gop.trang_thai == "dang_tra"

        # Get first 3 lich_su IDs
        cursor = conn.execute(
            """SELECT id FROM tra_gop_lich_su
               WHERE tra_gop_id = ? ORDER BY ky_thu LIMIT 3""",
            (tra_gop.id,)
        )
        lich_su_ids = [row[0] for row in cursor.fetchall()]
        assert len(lich_su_ids) == 3

        # Record 3 payments
        for ls_id in lich_su_ids:
            result = service.record_payment(ls_id, nhan_vien_id=1)
            assert result is True

        # Verify they are da_tra
        cursor = conn.execute(
            """SELECT COUNT(*) FROM tra_gop_lich_su
               WHERE tra_gop_id = ? AND trang_thai = 'da_tra'""",
            (tra_gop.id,)
        )
        paid_count = cursor.fetchone()[0]
        assert paid_count == 3, f"Expected 3 paid, got {paid_count}"

        # tra_gop still dang_tra (not all paid)
        updated = service.get_by_id(tra_gop.id)
        assert updated.trang_thai == "dang_tra"
        conn.close()

    def test_wf03_hoan_thanh_khi_tra_het(self, installment_db):
        """all kỳ paid → tra_gop.trang_thai = 'hoan_thanh'"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment with 3 kỳ
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="ACB",
            P=200_000_000,
            r_year=10.0,
            n=3,
            nhan_vien_id=1
        )

        # Get all lich_su IDs
        cursor = conn.execute(
            "SELECT id FROM tra_gop_lich_su WHERE tra_gop_id = ? ORDER BY ky_thu",
            (tra_gop.id,)
        )
        lich_su_ids = [row[0] for row in cursor.fetchall()]

        # Pay all
        for ls_id in lich_su_ids:
            service.record_payment(ls_id, nhan_vien_id=1)

        # Verify hoan_thanh
        updated = service.get_by_id(tra_gop.id)
        assert updated.trang_thai == "hoan_thanh", \
            f"Expected 'hoan_thanh', got '{updated.trang_thai}'"
        conn.close()

    def test_wf03_qua_han_xu_ly(self, installment_db):
        """overdue kỳ detected and marked"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="Vietcombank",
            P=300_000_000,
            r_year=8.0,
            n=3,
            nhan_vien_id=1
        )

        # Make first kỳ overdue (10 days ago)
        today = date.today()
        past_date = (today - timedelta(days=10)).isoformat()
        conn.execute(
            """UPDATE tra_gop_lich_su
               SET ngay_den_han = ?
               WHERE tra_gop_id = ? AND ky_thu = 1""",
            (past_date, tra_gop.id)
        )
        conn.commit()

        # Run daily check
        updated = service.daily_overdue_check()

        # Should detect overdue
        assert updated >= 1, f"Expected >= 1 overdue update, got {updated}"

        # Verify has_qua_han flag
        cursor = conn.execute(
            """SELECT 1 FROM tra_gop_lich_su
               WHERE tra_gop_id = ? AND trang_thai = 'qua_han' LIMIT 1""",
            (tra_gop.id,)
        )
        has_qua_han = cursor.fetchone() is not None
        assert has_qua_han, "Expected at least one qua_han record"
        conn.close()


# =============================================================================
# TEST.05 — UAT AC-TG-*
# =============================================================================
class TestUAT_ACTG:
    """TEST.05 — UAT AC-TG-* acceptance criteria"""

    def test_actg_01(self, installment_db):
        """AC-TG-01: Installment list shows correct info"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="Vietcombank",
            P=300_000_000,
            r_year=8.0,
            n=12,
            nhan_vien_id=1
        )

        # get_all should return this record
        items, total = service.get_all()
        assert total >= 1, "Should have at least 1 installment"

        found = False
        for item in items:
            if item.id == tra_gop.id:
                found = True
                assert item.ngan_hang == "Vietcombank"
                assert item.so_tien_vay == 300_000_000
                assert item.lai_suat_nam == 8.0
                assert item.so_ky == 12
                assert item.trang_thai == "dang_tra"
                break
        assert found, f"Installment {tra_gop.id} not found in list"
        conn.close()

    def test_actg_02(self, installment_db):
        """AC-TG-02: Progress screen shows all kỳ"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment with 6 kỳ
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="ACB",
            P=200_000_000,
            r_year=10.0,
            n=6,
            nhan_vien_id=1
        )

        # get_detail should show all 6 kỳ
        detail = service.get_detail(tra_gop.id)
        assert detail is not None
        assert len(detail.lich_su_list) == 6, \
            f"Expected 6 kỳ in detail, got {len(detail.lich_su_list)}"

        # All should start as chua_tra
        for ls in detail.lich_su_list:
            assert ls.trang_thai == "chua_tra", \
                f"Expected 'chua_tra', got '{ls.trang_thai}' for ky {ls.ky_thu}"

        # Verify khach_hang info
        assert detail.khach_hang_ten != ""
        conn.close()

    def test_actg_03(self, installment_db):
        """AC-TG-03: Payment recording works"""
        conn = sqlite3.connect(installment_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = TraGopService(conn)

        # Create installment
        tra_gop = service.create(
            hop_dong_id=2,
            ngan_hang="Vietcombank",
            P=300_000_000,
            r_year=8.0,
            n=3,
            nhan_vien_id=1
        )

        # Get first kỳ
        cursor = conn.execute(
            "SELECT id FROM tra_gop_lich_su WHERE tra_gop_id = ? ORDER BY ky_thu LIMIT 1",
            (tra_gop.id,)
        )
        first_ls_id = cursor.fetchone()[0]

        # Record payment
        result = service.record_payment(first_ls_id, nhan_vien_id=1)
        assert result is True

        # Verify status changed
        cursor = conn.execute(
            "SELECT trang_thai, ngay_thuc_te FROM tra_gop_lich_su WHERE id = ?",
            (first_ls_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "da_tra", f"Expected 'da_tra', got '{row[0]}'"
        assert row[1] is not None, "ngay_thuc_te should be set"
        conn.close()
