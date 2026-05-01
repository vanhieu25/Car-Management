"""Unit tests for NhaCungCapService + DonDatHangService - Sprint G4.4.

Tests:
- T-G4.4.TEST.01: add_rating + calculate_avg_rating (7 cases)
- T-G4.4.TEST.02: set_received → tồn kho tăng (3 cases)
- T-G4.4.TEST.03: WF-01 integration (4 cases)
- T-G4.4.TEST.04: UAT AC-NCC-* (3 cases)

Business Rules:
- BR-NCC-01: CRUD operations with validation
- BR-NCC-02: Rating system (chat_luong, thoi_gian_giao, gia_ca) each 1-5
- BR-NCC-03: avg_rating = (chat_luong + thoi_gian_giao + gia_ca) / 3
- BR-NCC-04: Create order with status 'nhap' (cho_xu_ly in service layer)
- BR-NCC-05: set_received creates nhap_kho and increases stock
- BR-NCC-06: Cannot delete supplier with nhap_kho history
- TRG-04: If xe was da_ban and stock > 0 → trang_thai = 'con_hang'
"""

import os
import sys
import tempfile
import sqlite3

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.application.services.nha_cung_cap_service import (
    NhaCungCapService,
    NhaCungCapCreateData,
    NhaCungCapUpdateData,
    ValidationError,
    DuplicateCodeError,
    NotFoundError,
    DeleteNotAllowedError,
)
from app.application.services.don_dat_hang_service import (
    DonDatHangService,
    DonDatHangCreateData,
    DonDatHangItemData,
    ValidationError as DDHValidationError,
    NotFoundError as DDHNotFoundError,
    InvalidStateTransitionError,
)
from app.application.services.nhap_kho_service import NhapKhoService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fresh_db():
    """Create a fresh database with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    runner = MigrationRunner(db_path)
    runner.run_pending()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def supplier_db(fresh_db):
    """Create database with supplier-specific test data.

    Seeds:
    - 3 nha_cung_cap
    - 5 don_dat_hang across different statuses
    - chi_tiet_don_dat for each order
    - xe with initial so_luong_ton
    - phu_kien with initial ton_kho
    - 2 nhan_vien for FK
    """
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Insert nhan_vien (needed for FK on don_dat_hang)
    conn.execute("""
        INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai, created_at)
        VALUES
            (1, 'admin', '$2b$12$dummy', 'Admin User', 'admin@test.com', 1, 'active', datetime('now')),
            (2, 'staff', '$2b$12$dummy', 'Staff User', 'staff@test.com', 2, 'active', datetime('now'))
    """)

    # Insert nha_cung_cap (3 suppliers)
    conn.execute("""
        INSERT INTO nha_cung_cap (id, ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email, nguoi_lien_he, diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca, diem_tong, created_at)
        VALUES
            (1, 'NCC001', 'Nha Cung Cap Mot', '123 Duong A, TP.HCM', '0909000001', 'ncc1@test.com', 'Nguyen Van A', 4, 5, 3, 12, datetime('now')),
            (2, 'NCC002', 'Nha Cung Cap Hai', '456 Duong B, HN', '0909000002', 'ncc2@test.com', 'Tran Van B', 0, 0, 0, 0, datetime('now')),
            (3, 'NCC003', 'Nha Cung Cap Ba', '789 Duong C, DN', '0909000003', 'ncc3@test.com', 'Le Van C', 5, 4, 5, 14, datetime('now'))
    """)

    # Insert xe (for order items)
    conn.execute("""
        INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, muc_toi_thieu, trang_thai, created_at)
        VALUES
            (1, 'XE001', 'Toyota', 'Camry', 2024, 'Den', 500000000, 5, 2, 'con_hang', datetime('now')),
            (2, 'XE002', 'Honda', 'Civic', 2024, 'Trang', 400000000, 3, 2, 'con_hang', datetime('now')),
            (3, 'XE003', 'BMW', 'X5', 2024, 'Den', 1500000000, 0, 1, 'da_ban', datetime('now'))
    """)

    # Insert phu_kien (for order items)
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta, created_at)
        VALUES
            (1, 'PK001', 'GPS Navigator', 'Dien tu', 5000000, 20, 'GPS test', datetime('now')),
            (2, 'PK002', 'Camera lui', 'Dien tu', 3000000, 15, 'Camera test', datetime('now'))
    """)

    # Insert don_dat_hang (5 orders across statuses: nhap, da_gui, da_nhan, da_nhan, huy)
    conn.execute("""
        INSERT INTO don_dat_hang (id, nha_cung_cap_id, nhan_vien_id, ma_don, ngay_dat, trang_thai, ngay_giao, ghi_chu, created_at)
        VALUES
            (1, 1, 1, 'DDH2026-0001', '2026-04-01', 'nhap', NULL, 'Don nhap', datetime('now')),
            (2, 1, 1, 'DDH2026-0002', '2026-04-02', 'da_gui', NULL, 'Don da gui', datetime('now')),
            (3, 2, 1, 'DDH2026-0003', '2026-04-03', 'da_nhan', '2026-04-10', 'Don da nhan', datetime('now')),
            (4, 2, 2, 'DDH2026-0004', '2026-04-04', 'da_nhan', '2026-04-11', 'Don da nhan 2', datetime('now')),
            (5, 3, 2, 'DDH2026-0005', '2026-04-05', 'huy', NULL, 'Don da huy', datetime('now'))
    """)

    # Insert chi_tiet_don_dat for each order
    conn.execute("""
        INSERT INTO chi_tiet_don_dat (id, don_dat_hang_id, loai_item, item_id, so_luong, gia_don, created_at)
        VALUES
            (1, 1, 'xe', 1, 2, 500000000, datetime('now')),
            (2, 1, 'phu_kien', 1, 5, 5000000, datetime('now')),
            (3, 2, 'xe', 2, 1, 400000000, datetime('now')),
            (4, 3, 'xe', 1, 3, 500000000, datetime('now')),
            (5, 3, 'phu_kien', 2, 10, 3000000, datetime('now')),
            (6, 4, 'xe', 2, 2, 400000000, datetime('now')),
            (7, 5, 'xe', 3, 1, 1500000000, datetime('now'))
    """)

    conn.commit()
    conn.close()

    yield fresh_db

    if os.path.exists(fresh_db):
        os.unlink(fresh_db)


# =============================================================================
# T-G4.4.TEST.01: add_rating + calculate_avg_rating
# =============================================================================

class TestAddRating:
    """TEST.01 — NhaCungCapService.add_rating — 4 cases."""

    def test_add_rating_cap_nhat_diem(self, supplier_db):
        """Add 3 ratings → diem_tong = sum of 3 ratings."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        result = service.add_rating(
            ncc_id=2,
            ratings={"chat_luong": 4, "thoi_gian_giao": 5, "gia_ca": 3}
        )

        assert result["diem_chat_luong"] == 4
        assert result["diem_thoi_gian_giao"] == 5
        assert result["diem_gia_ca"] == 3
        assert result["diem_tong"] == 12  # 4 + 5 + 3
        conn.close()

    def test_add_rating_tinh_avg(self, supplier_db):
        """avg = diem_tong / 3."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        service.add_rating(
            ncc_id=1,
            ratings={"chat_luong": 3, "thoi_gian_giao": 4, "gia_ca": 5}
        )

        avg = service.calculate_avg_rating(ncc_id=1)
        assert avg == 4.0  # (3 + 4 + 5) / 3 = 4.0
        conn.close()

    def test_add_rating_khong_cho_ngoai_range(self, supplier_db):
        """Rating > 5 → raises ValidationError."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        with pytest.raises(ValidationError) as exc_info:
            service.add_rating(
                ncc_id=1,
                ratings={"chat_luong": 6, "thoi_gian_giao": 4, "gia_ca": 3}
            )
        assert "chat_luong" in str(exc_info.value)
        conn.close()

    def test_add_rating_khong_am(self, supplier_db):
        """Rating < 1 → raises ValidationError."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        with pytest.raises(ValidationError) as exc_info:
            service.add_rating(
                ncc_id=1,
                ratings={"chat_luong": 0, "thoi_gian_giao": 3, "gia_ca": 4}
            )
        assert "chat_luong" in str(exc_info.value)
        conn.close()


class TestCalculateAvgRating:
    """TEST.01 — NhaCungCapService.calculate_avg_rating — 3 cases."""

    def test_avg_rating_chinh_xac(self, supplier_db):
        """avg = (chat_luong + thoi_gian_giao + gia_ca) / 3."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        # NCC003 already has diem_tong=14 (5+4+5)
        avg = service.calculate_avg_rating(ncc_id=3)
        assert avg == round(14 / 3, 2)
        conn.close()

    def test_avg_rating_khi_chua_co_diem(self, supplier_db):
        """diem_tong = 0 → returns 0.0."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        # NCC002 has diem_tong = 0
        avg = service.calculate_avg_rating(ncc_id=2)
        assert avg == 0.0
        conn.close()

    def test_avg_rating_sau_khi_update(self, supplier_db):
        """Re-calculate after new rating → avg updated."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        # Initial NCC002 had diem_tong = 0
        avg_before = service.calculate_avg_rating(ncc_id=2)
        assert avg_before == 0.0

        # Add new ratings
        service.add_rating(
            ncc_id=2,
            ratings={"chat_luong": 5, "thoi_gian_giao": 5, "gia_ca": 4}
        )

        avg_after = service.calculate_avg_rating(ncc_id=2)
        assert avg_after == round(14 / 3, 2)  # (5+5+4)/3 = 4.67
        conn.close()


# =============================================================================
# T-G4.4.TEST.02: set_received → tồn kho tăng
# =============================================================================

class TestSetReceived:
    """TEST.02 — DonDatHangService.set_received → 3 cases."""

    def test_set_received_tao_nhap_kho(self, supplier_db):
        """When status changes to da_nhan, nhap_kho record is created."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DonDatHangService(conn)

        # Get initial nhap_kho count
        cursor = conn.execute("SELECT COUNT(*) FROM nhap_kho")
        count_before = cursor.fetchone()[0]

        # Order 1 is in 'nhap' status (like cho_xu_ly)
        result = service.set_received(don_id=1)

        assert result["trang_thai"] == "da_nhan"

        # nhap_kho should be created
        cursor = conn.execute("SELECT COUNT(*) FROM nhap_kho")
        count_after = cursor.fetchone()[0]
        assert count_after == count_before + 1
        conn.close()

    def test_set_received_ton_xe_tang(self, supplier_db):
        """After set_received, xe.so_luong_ton increases."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DonDatHangService(conn)

        # Get initial stock for xe_id=1 (order 1 has xe_id=1, so_luong=2)
        cursor = conn.execute("SELECT so_luong_ton FROM xe WHERE id = 1")
        stock_before = cursor.fetchone()[0]

        service.set_received(don_id=1)

        cursor = conn.execute("SELECT so_luong_ton FROM xe WHERE id = 1")
        stock_after = cursor.fetchone()[0]
        assert stock_after == stock_before + 2  # chi_tiet_don_dat #1: xe_id=1, so_luong=2
        conn.close()

    def test_set_received_khong_nhan_huy_don(self, supplier_db):
        """Cannot set_received if status is 'huy'."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DonDatHangService(conn)

        # Order 5 is in 'huy' status
        with pytest.raises(InvalidStateTransitionError):
            service.set_received(don_id=5)
        conn.close()


# =============================================================================
# T-G4.4.TEST.03: WF-01 integration
# =============================================================================

class TestWF01Integration:
    """TEST.03 — WF-01 end-to-end: NCC → Order → Confirm → Received → nhap_kho."""

    def test_wf01_day_du(self, supplier_db):
        """Full WF-01: Create NCC → create order → confirm → mark received → check nhap_kho."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        ncc_service = NhaCungCapService(conn)
        ddh_service = DonDatHangService(conn)

        # 1. Create new NCC
        ncc_data = NhaCungCapCreateData(
            ma_ncc="NCCWF01",
            ten_ncc="WF01 Supplier",
            dia_chi="123 WF St",
            so_dien_thoai="0909111222",
            email="wf01@test.com"
        )
        ncc = ncc_service.create(ncc_data)
        assert ncc["id"] is not None
        assert ncc["diem_tong"] == 0

        # 2. Create order for this NCC
        ddh_data = DonDatHangCreateData(
            nha_cung_cap_id=ncc["id"],
            items=[
                DonDatHangItemData(loai_item="xe", item_id=1, so_luong=2, gia_don=500000000),
                DonDatHangItemData(loai_item="phu_kien", item_id=1, so_luong=5, gia_don=5000000),
            ],
            ngay_dat="2026-04-15",
            ghi_chu="WF01 test order"
        )
        order = ddh_service.create(ddh_data)
        assert order["trang_thai"] == "nhap"
        assert order["nha_cung_cap_id"] == ncc["id"]
        assert len(order["chi_tiet"]) == 2

        # 3. Mark as received
        result = ddh_service.set_received(don_id=order["id"])
        assert result["trang_thai"] == "da_nhan"

        # 4. Check nhap_kho was created
        cursor = conn.execute(
            "SELECT COUNT(*) FROM nhap_kho WHERE nha_cung_cap_id = ?",
            (ncc["id"],)
        )
        count = cursor.fetchone()[0]
        assert count >= 1

        conn.close()

    def test_wf01_nhap_kho_voi_items(self, supplier_db):
        """set_received creates nhap_kho for each item in the order."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        ddh_service = DonDatHangService(conn)

        # Order 1 has: xe_id=1 (2 units) + phu_kien_id=1 (5 units)
        cursor = conn.execute("SELECT COUNT(*) FROM chi_tiet_nhap_kho")
        count_before = cursor.fetchone()[0]

        ddh_service.set_received(don_id=1)

        # After receiving order 1, chi_tiet_nhap_kho should have entries
        cursor = conn.execute("SELECT COUNT(*) FROM chi_tiet_nhap_kho")
        count_after = cursor.fetchone()[0]
        assert count_after >= count_before + 2  # at least 2 items
        conn.close()

    def test_wf01_huy_don_khong_tao_nhap_kho(self, supplier_db):
        """Cancelled order doesn't create nhap_kho."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        ddh_service = DonDatHangService(conn)

        # Order 5 is already 'huy', set_received should fail
        with pytest.raises(InvalidStateTransitionError):
            ddh_service.set_received(don_id=5)

        conn.close()

    def test_wf01_ton_kho_chinh_xac(self, supplier_db):
        """Stock increases by correct amount after set_received."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        ddh_service = DonDatHangService(conn)

        # Capture initial stock for order 3 items
        cursor = conn.execute("SELECT so_luong_ton FROM xe WHERE id = 1")
        xe1_stock_before = cursor.fetchone()[0]

        cursor = conn.execute("SELECT ton_kho FROM phu_kien WHERE id = 2")
        pk2_stock_before = cursor.fetchone()[0]

        # Order 3 has: xe_id=1 (3 units) + phu_kien_id=2 (10 units)
        ddh_service.set_received(don_id=3)

        cursor = conn.execute("SELECT so_luong_ton FROM xe WHERE id = 1")
        xe1_stock_after = cursor.fetchone()[0]

        cursor = conn.execute("SELECT ton_kho FROM phu_kien WHERE id = 2")
        pk2_stock_after = cursor.fetchone()[0]

        assert xe1_stock_after == xe1_stock_before + 3
        assert pk2_stock_after == pk2_stock_before + 10
        conn.close()


# =============================================================================
# T-G4.4.TEST.04: UAT AC-NCC-*
# =============================================================================

class TestUAT_ACNCC:
    """TEST.04 — UAT smoke tests per AC-NCC-* acceptance criteria."""

    def test_acncc_01(self, supplier_db):
        """AC-NCC-01: NCC list shows all required fields."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = NhaCungCapService(conn)

        items = service.get_all(limit=10)
        assert len(items) >= 3

        # Verify all fields are present
        ncc = items[0]
        required_fields = ["id", "ma_ncc", "ten_ncc", "dia_chi", "so_dien_thoai", "email", "nguoi_lien_he"]
        for field in required_fields:
            assert field in ncc, f"Field {field} missing in NCC list item"

        # Verify rating fields present
        rating_fields = ["diem_chat_luong", "diem_thoi_gian_giao", "diem_gia_ca", "diem_tong"]
        for field in rating_fields:
            assert field in ncc, f"Field {field} missing in NCC list item"

        conn.close()

    def test_acncc_02(self, supplier_db):
        """AC-NCC-02: Order created with correct total price."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        ddh_service = DonDatHangService(conn)

        # Create order with known items
        ddh_data = DonDatHangCreateData(
            nha_cung_cap_id=1,
            items=[
                DonDatHangItemData(loai_item="xe", item_id=1, so_luong=2, gia_don=500000000),
                DonDatHangItemData(loai_item="phu_kien", item_id=1, so_luong=5, gia_don=5000000),
            ],
            ngay_dat="2026-04-20"
        )
        order = ddh_service.create(ddh_data)

        # tong_gia = (2 * 500M) + (5 * 5M) = 1000M + 25M = 1025M
        expected_total = (2 * 500000000) + (5 * 5000000)
        assert order["tong_gia"] == expected_total

        # Verify chi_tiet items
        assert len(order["chi_tiet"]) == 2
        chi_tiet_xe = next(ct for ct in order["chi_tiet"] if ct["loai_item"] == "xe")
        assert chi_tiet_xe["so_luong"] == 2
        assert chi_tiet_xe["gia_don"] == 500000000

        conn.close()

    def test_acncc_03(self, supplier_db):
        """AC-NCC-03: Rating saved and avg updated correctly."""
        conn = sqlite3.connect(supplier_db)
        conn.execute("PRAGMA foreign_keys = ON")
        ncc_service = NhaCungCapService(conn)

        # Add rating to NCC
        result = ncc_service.add_rating(
            ncc_id=1,
            ratings={"chat_luong": 4, "thoi_gian_giao": 5, "gia_ca": 3}
        )

        # Verify diem_tong updated
        assert result["diem_tong"] == 12

        # Verify avg calculation
        avg = ncc_service.calculate_avg_rating(ncc_id=1)
        assert avg == 4.0

        # Verify stored in DB
        cursor = conn.execute(
            "SELECT diem_tong FROM nha_cung_cap WHERE id = ?",
            (1,)
        )
        row = cursor.fetchone()
        assert row["diem_tong"] == 12

        conn.close()
