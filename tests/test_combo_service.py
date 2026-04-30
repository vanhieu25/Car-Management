"""Unit tests for ComboService and PhuKienService - T-G4.1.TEST.01..04."""

import pytest
import sqlite3
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.application.services.combo_service import (
    ComboService,
    ComboNotFoundError,
    ValidationError as ComboValidationError,
)
from app.application.services.phu_kien_service import (
    PhuKienService,
    PhuKienNotFoundError,
    InventoryError,
    ValidationError as PhuKienValidationError,
)


# Custom exception for BR-PK-04 (not in original service, simulating spec)
class InsufficientItemsError(Exception):
    """Raised when combo has fewer than 2 accessories."""
    pass


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
def contract_db(fresh_db):
    """Create database with contract-specific test data for phu_kien and combo."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Run migrations (already done in fresh_db, but re-ensure)
    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(fresh_db)
    runner.run_pending()

    # Insert test vai_tro
    conn.execute("""
        INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro)
        VALUES (1, 'admin', 'Quản trị viên'),
               (2, 'sales', 'Nhân viên bán hàng'),
               (3, 'ky_thuat_bh', 'Nhân viên kỹ thuật bảo hành')
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

    # Insert 10+ phu_kien across 5 categories
    # Category: noi_that
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta)
        VALUES (1, 'PK00001', 'Ghế da cao cấp', 'noi_that', 5000000, 20, 'Ghế da nhập khẩu'),
               (2, 'PK00002', 'Vô lăng thể thao', 'noi_that', 3000000, 15, 'Vô lăng cácbon')
    """)

    # Category: ngoai_that
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta)
        VALUES (3, 'PK00003', 'Body kit thể thao', 'ngoai_that', 8000000, 10, 'Bộ Body kit full'),
               (4, 'PK00004', 'Đèn LED chiếu sáng', 'ngoai_that', 2500000, 25, 'Đèn LED 3 màu')
    """)

    # Category: dien_tu
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta)
        VALUES (5, 'PK00005', 'Màn hình Android 10 inch', 'dien_tu', 4500000, 12, 'Màn hình cảm ứng'),
               (6, 'PK00006', 'Camera 360 độ', 'dien_tu', 6000000, 8, 'Camera toàn cảnh')
    """)

    # Category: bao_ve
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta)
        VALUES (7, 'PK00007', 'Camera hành trình', 'bao_ve', 2000000, 30, 'Camera trước + sau'),
               (8, 'PK00008', 'Cảm biến áp suất lốp', 'bao_ve', 1500000, 20, 'Cảm biến TPMS')
    """)

    # Category: trang_tri
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta)
        VALUES (9, 'PK00009', 'Dải LED RGB nội thất', 'trang_tri', 800000, 50, 'Dải LED dẻo'),
               (10, 'PK00010', 'Mâm xe thể thao', 'trang_tri', 3500000, 6, 'Mâm 18 inch')
    """)

    # Extra PK for various test scenarios
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta)
        VALUES (11, 'PK00011', 'Thảm lót sàn da', 'noi_that', 1200000, 40, 'Thảm da 4 lớp')
    """)

    # Insert 3+ combo_phu_kien combos
    conn.execute("""
        INSERT INTO combo_phu_kien (id, ten_combo, he_so_giam, mo_ta)
        VALUES (1, 'Combo Tiện Nghi', 0.80, 'Combo ghế da + vô lăng'),
               (2, 'Combo An Toàn', 0.85, 'Combo camera + cảm biến'),
               (3, 'Combo Giải Trí', 0.90, 'Combo màn hình + camera 360')
    """)

    # Insert combo_chi_tiet for combos
    # Combo 1: Ghế da (5M) + Vô lăng (3M) = 8M → combo price = 8M * 0.80 = 6.4M
    conn.execute("""
        INSERT INTO combo_chi_tiet (combo_id, phu_kien_id, so_luong)
        VALUES (1, 1, 1),
               (1, 2, 1)
    """)

    # Combo 2: Camera (2M) + Cảm biến (1.5M) = 3.5M → combo price = 3.5M * 0.85 = 2.975M
    conn.execute("""
        INSERT INTO combo_chi_tiet (combo_id, phu_kien_id, so_luong)
        VALUES (2, 7, 1),
               (2, 8, 1)
    """)

    # Combo 3: Màn hình (4.5M) + Camera 360 (6M) = 10.5M → combo price = 10.5M * 0.90 = 9.45M
    conn.execute("""
        INSERT INTO combo_chi_tiet (combo_id, phu_kien_id, so_luong)
        VALUES (3, 5, 1),
               (3, 6, 1)
    """)

    # Insert hop_dong for BR-PK-06 test (active contract referencing PK)
    conn.execute("""
        INSERT INTO hop_dong (id, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien, trang_thai, ngay_tao)
        VALUES (1, 1, 1, 1, 500000000, 5000000, 0, 505000000, 'moi_tao', '2026-04-01')
    """)

    # hop_dong_phu_kien referencing PK id=1 (for BR-PK-06 test)
    conn.execute("""
        INSERT INTO hop_dong_phu_kien (hop_dong_id, phu_kien_id, so_luong, gia_ban)
        VALUES (1, 1, 1, 5000000)
    """)

    conn.commit()
    conn.close()

    return fresh_db


# =============================================================================
# TEST CLASS 1: TestComboCalculatePrice — 5 cases
# BR-CALC-07: gia_combo = SUM(gia_pk × so_luong) × he_so_giam
# =============================================================================
class TestComboCalculatePrice:
    """T-G4.1.TEST.01 — Unit test Combo.calculate_price 5 cases."""

    def test_gia_combo_binh_thuong(self, contract_db):
        """Combo 3 PK (5M + 3M + 2M) × 0.8 = 8M.
        Uses existing combo 1: Ghế da (5M) + Vô lăng (3M) × 0.80 = 6.4M."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = ComboService(conn)

        result = service.calculate_price(combo_id=1)

        # PK1: 5M, PK2: 3M → gia_goc = 8M
        assert result["gia_goc"] == 8000000
        # he_so_giam = 0.80
        assert result["he_so_giam"] == 0.80
        # gia_combo = 8M × 0.80 = 6.4M
        assert result["gia_combo"] == 6400000
        conn.close()

    def test_gia_combo_100_percent(self, contract_db):
        """he_so_giam=1.0 → gia_combo = gia_goc (no discount).
        Create a new combo with he_so_giam=1.0."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)
        from app.application.services.combo_service import ComboCreateData, ComboItemData

        data = ComboCreateData(
            ten_combo="Combo Khong Giam",
            items=[
                ComboItemData(phu_kien_id=7, so_luong=1),  # Camera 2M
                ComboItemData(phu_kien_id=8, so_luong=1),  # Cam bien 1.5M
            ],
            he_so_giam=1.0,
        )
        combo = combo_service.create(data)

        result = combo_service.calculate_price(combo_id=combo.id)

        # gia_goc = 2M + 1.5M = 3.5M
        assert result["gia_goc"] == 3500000
        # he_so_giam = 1.0 → gia_combo = gia_goc
        assert result["gia_combo"] == 3500000
        assert result["he_so_giam"] == 1.0
        conn.close()

    def test_gia_combo_70_percent(self, contract_db):
        """he_so_giam=0.7 → giảm 30%.
        Create a new combo with he_so_giam=0.7."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)
        from app.application.services.combo_service import ComboCreateData, ComboItemData

        data = ComboCreateData(
            ten_combo="Combo Giam 30",
            items=[
                ComboItemData(phu_kien_id=1, so_luong=1),   # 5M
                ComboItemData(phu_kien_id=2, so_luong=1),   # 3M
                ComboItemData(phu_kien_id=11, so_luong=1),  # 1.2M
            ],
            he_so_giam=0.7,
        )
        combo = combo_service.create(data)

        result = combo_service.calculate_price(combo_id=combo.id)

        # gia_goc = 5M + 3M + 1.2M = 9.2M
        assert result["gia_goc"] == 9200000
        # gia_combo = 9.2M × 0.7 = 6.44M
        assert result["gia_combo"] == 6440000
        assert result["he_so_giam"] == 0.7
        conn.close()

    def test_gia_combo_nhieu_items(self, contract_db):
        """4 PK × various prices × 0.85.
        Create a new 4-item combo with he_so_giam=0.85."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)
        from app.application.services.combo_service import ComboCreateData, ComboItemData

        data = ComboCreateData(
            ten_combo="Combo 4 Items",
            items=[
                ComboItemData(phu_kien_id=1, so_luong=1),   # 5M
                ComboItemData(phu_kien_id=3, so_luong=1),   # 8M
                ComboItemData(phu_kien_id=5, so_luong=1),   # 4.5M
                ComboItemData(phu_kien_id=7, so_luong=1),   # 2M
            ],
            he_so_giam=0.85,
        )
        combo = combo_service.create(data)

        result = combo_service.calculate_price(combo_id=combo.id)

        # gia_goc = 5M + 8M + 4.5M + 2M = 19.5M
        assert result["gia_goc"] == 19500000
        # gia_combo = 19.5M × 0.85 = 16.575M
        assert result["gia_combo"] == 16575000
        assert result["he_so_giam"] == 0.85
        conn.close()

    def test_tien_tiet_kiem(self, contract_db):
        """gia_goc - gia_combo = tien_tiet_kiem."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)

        result = combo_service.calculate_price(combo_id=1)

        # Combo 1: gia_goc=8M, gia_combo=6.4M
        expected_tien_tiet_kiem = result["gia_goc"] - result["gia_combo"]
        assert result["tien_tiet_kiem"] == expected_tien_tiet_kiem
        assert result["tien_tiet_kiem"] == 1600000  # 8M - 6.4M = 1.6M
        conn.close()


# =============================================================================
# TEST CLASS 2: TestComboConstraint — 3 cases
# BR-PK-04: Combo must have >= 2 accessories
# =============================================================================
class TestComboConstraint:
    """T-G4.1.TEST.02 — Test combo phải có ≥ 2 PK (BR-PK-04)."""

    def test_combo_it_hon_2_pk(self, contract_db):
        """Create combo with only 1 PK → raises ValidationError about >= 2 items."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)
        from app.application.services.combo_service import ComboCreateData, ComboItemData

        data = ComboCreateData(
            ten_combo="Combo Lei",
            items=[
                ComboItemData(phu_kien_id=1, so_luong=1),
            ],
            he_so_giam=0.90,
        )

        with pytest.raises(ComboValidationError) as exc_info:
            combo_service.create(data)

        # Error message should mention the 2-PK constraint
        assert "2" in str(exc_info.value) or "ít nhất" in str(exc_info.value).lower()
        conn.close()

    def test_combo_du_2_pk(self, contract_db):
        """Create combo with exactly 2 PK → success."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)
        from app.application.services.combo_service import ComboCreateData, ComboItemData

        data = ComboCreateData(
            ten_combo="Combo Chuan 2 PK",
            items=[
                ComboItemData(phu_kien_id=9, so_luong=1),  # 800k
                ComboItemData(phu_kien_id=10, so_luong=1), # 3.5M
            ],
            he_so_giam=0.80,
        )

        combo = combo_service.create(data)
        assert combo is not None
        assert combo.ten_combo == "Combo Chuan 2 PK"
        assert len(combo.items) == 2
        conn.close()

    def test_combo_he_so_giam_ngoai_range(self, contract_db):
        """he_so_giam=1.5 → raises error (must be ≤ 1)."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)
        from app.application.services.combo_service import ComboCreateData, ComboItemData

        data = ComboCreateData(
            ten_combo="Combo He So Loi",
            items=[
                ComboItemData(phu_kien_id=1, so_luong=1),
                ComboItemData(phu_kien_id=2, so_luong=1),
            ],
            he_so_giam=1.5,  # Invalid: must be <= 1
        )

        with pytest.raises(ComboValidationError) as exc_info:
            combo_service.create(data)

        # Error should mention the he_so_giam constraint
        assert "hệ số" in str(exc_info.value).lower() or "he so" in str(exc_info.value).lower()
        conn.close()


# =============================================================================
# TEST CLASS 3: TestAdjustInventory — 4 cases
# BR-PK-05: ton_kho >= 0; adjust_inventory cannot go negative
# =============================================================================
class TestAdjustInventory:
    """T-G4.1.TEST.03 — Test adjust_inventory không cho âm (BR-PK-05)."""

    def test_adjust_inventory_tang(self, contract_db):
        """Add 10 to stock → ton_kho increases."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        pk_service = PhuKienService(conn)

        # PK1 starts with ton_kho = 20
        cursor = conn.execute("SELECT ton_kho FROM phu_kien WHERE id = 1")
        initial = cursor.fetchone()[0]

        result = pk_service.adjust_inventory(1, 10)

        assert result.ton_kho == initial + 10
        conn.close()

    def test_adjust_inventory_giam(self, contract_db):
        """Subtract from stock → ton_kho decreases."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        pk_service = PhuKienService(conn)

        # PK1 starts with ton_kho = 20
        cursor = conn.execute("SELECT ton_kho FROM phu_kien WHERE id = 1")
        initial = cursor.fetchone()[0]

        result = pk_service.adjust_inventory(1, -5)

        assert result.ton_kho == initial - 5
        conn.close()

    def test_adjust_inventory_khong_cho_am(self, contract_db):
        """Result < 0 → raises InventoryError."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        pk_service = PhuKienService(conn)

        # PK1 starts with ton_kho = 20
        # Try to subtract more than available
        with pytest.raises(InventoryError):
            pk_service.adjust_inventory(1, -100)

        conn.close()

    def test_adjust_inventory_ve_khong(self, contract_db):
        """Subtract exactly what's in stock → OK, ton_kho becomes 0."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        pk_service = PhuKienService(conn)

        # PK1 starts with ton_kho = 20
        cursor = conn.execute("SELECT ton_kho FROM phu_kien WHERE id = 1")
        initial = cursor.fetchone()[0]

        result = pk_service.adjust_inventory(1, -initial)

        assert result.ton_kho == 0
        conn.close()


# =============================================================================
# TEST CLASS 4: TestUAT_ACPK — Integration tests
# UAT following AC-PK-* acceptance criteria
# =============================================================================
class TestUAT_ACPK:
    """T-G4.1.TEST.04 — UAT theo AC-PK-* acceptance criteria."""

    def test_acpk_01(self, contract_db):
        """AC-PK-01: Create PK → verify it appears in list."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        pk_service = PhuKienService(conn)
        from app.application.services.phu_kien_service import PhuKienCreateData

        data = PhuKienCreateData(
            ten_pk="Test PK AC01",
            phan_loai="dien_tu",
            gia_ban=1000000,
            ton_kho=10,
        )
        created = pk_service.create(data)

        # Verify in list
        all_pk = pk_service.get_all()
        pk_ids = [pk.id for pk in all_pk]
        assert created.id in pk_ids
        assert created.ten_pk == "Test PK AC01"
        assert created.gia_ban == 1000000
        conn.close()

    def test_acpk_02(self, contract_db):
        """AC-PK-02: Create combo with valid items → calculate_price works correctly."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        combo_service = ComboService(conn)
        from app.application.services.combo_service import ComboCreateData, ComboItemData

        data = ComboCreateData(
            ten_combo="Combo UAT Test",
            items=[
                ComboItemData(phu_kien_id=5, so_luong=1),  # 4.5M
                ComboItemData(phu_kien_id=6, so_luong=1),  # 6M
            ],
            he_so_giam=0.85,
        )
        combo = combo_service.create(data)

        result = combo_service.calculate_price(combo.id)

        # gia_goc = 4.5M + 6M = 10.5M
        assert result["gia_goc"] == 10500000
        # gia_combo = 10.5M × 0.85 = 8.925M
        assert result["gia_combo"] == 8925000
        assert result["ten_combo"] == "Combo UAT Test"
        assert len(result["items"]) == 2
        conn.close()

    def test_acpk_03(self, contract_db):
        """AC-PK-03 / BR-PK-06: Delete PK with active contracts → should fail."""
        conn = sqlite3.connect(contract_db)
        conn.execute("PRAGMA foreign_keys = ON")
        pk_service = PhuKienService(conn)
        from app.application.services.phu_kien_service import DeleteNotAllowedError

        # PK id=1 is referenced by hop_dong id=1 (active, trang_thai='moi_tao')
        with pytest.raises(DeleteNotAllowedError):
            pk_service.delete(1)

        conn.close()
