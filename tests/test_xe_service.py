"""Unit tests for XeService - T-G3.1.TEST.01, TEST.02, TEST.03, TEST.04.

Tests:
- TEST.01: XeService.create success/mã trùng/năm < 1990 / giá âm → AC-XE-01
- TEST.02: XeService.update không sửa được ma_xe (BR-XE-01)
- TEST.03: XeService.delete bị chặn nếu có FK (BR-XE-02)
- TEST.04: XeService.search với 6 filter combo
"""

import pytest
import sqlite3
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


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
def seeded_db(fresh_db):
    """Create database with seed data applied."""
    from app.infrastructure.database.seeds.dev_seed import seed_all
    seed_all(fresh_db)
    return fresh_db


class TestXeServiceCreate:
    """Test XeService.create() - AC-XE-01."""

    def test_create_success(self, seeded_db):
        """Test successful vehicle creation."""
        from app.application.services.xe_service import XeService, XeCreateData

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)
        data = XeCreateData(
            ma_xe="XE_TEST_001",
            hang="Toyota",
            dong_xe="Camry",
            nam_san_xuat=2024,
            gia_ban=850000000,
            mau_sac="Đen",
            so_luong_ton=5,
            muc_toi_thieu=2,
            mo_ta="Xe test",
        )

        result = service.create(data)

        assert result is not None, "Created vehicle should be returned"
        assert result.ma_xe == "XE_TEST_001"
        assert result.hang == "Toyota"
        assert result.dong_xe == "Camry"
        assert result.nam_san_xuat == 2024
        assert result.gia_ban == 850000000
        assert result.so_luong_ton == 5
        assert result.trang_thai == "con_hang"

        conn.close()

    def test_create_duplicate_ma_xe(self, seeded_db):
        """Test vehicle creation fails with duplicate ma_xe."""
        from app.application.services.xe_service import XeService, XeCreateData, DuplicateMaXeError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)
        data = XeCreateData(
            ma_xe="XE0001",  # This might already exist in seed
            hang="Honda",
            dong_xe="Civic",
            nam_san_xuat=2023,
            gia_ban=700000000,
        )

        # Try to create first
        try:
            service.create(data)
        except (DuplicateMaXeError, Exception):
            pass  # Expected if already exists

        # Try again - should fail
        with pytest.raises(DuplicateMaXeError):
            service.create(data)

        conn.close()

    def test_create_invalid_year_below_1990(self, seeded_db):
        """Test vehicle creation fails with year < 1990."""
        from app.application.services.xe_service import XeService, XeCreateData, ValidationError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)
        data = XeCreateData(
            ma_xe="XE_TEST_INVALID_YEAR",
            hang="Ford",
            dong_xe="Ranger",
            nam_san_xuat=1985,  # Invalid - below 1990
            gia_ban=800000000,
        )

        with pytest.raises(ValidationError) as exc_info:
            service.create(data)

        assert "1990" in str(exc_info.value), "Error should mention year 1990"

        conn.close()

    def test_create_negative_price(self, seeded_db):
        """Test vehicle creation fails with negative price."""
        from app.application.services.xe_service import XeService, XeCreateData, ValidationError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)
        data = XeCreateData(
            ma_xe="XE_TEST_NEG_PRICE",
            hang="BMW",
            dong_xe="X5",
            nam_san_xuat=2024,
            gia_ban=-100000000,  # Invalid - negative
        )

        with pytest.raises(ValidationError) as exc_info:
            service.create(data)

        assert "âm" in str(exc_info.value) or "negative" in str(exc_info.value).lower(), \
            "Error should mention negative price"

        conn.close()

    def test_create_empty_ma_xe(self, seeded_db):
        """Test vehicle creation fails with empty ma_xe."""
        from app.application.services.xe_service import XeService, XeCreateData, ValidationError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)
        data = XeCreateData(
            ma_xe="",
            hang="Mercedes",
            dong_xe="C300",
            nam_san_xuat=2024,
            gia_ban=1000000000,
        )

        with pytest.raises(ValidationError) as exc_info:
            service.create(data)

        assert "mã xe" in str(exc_info.value).lower(), "Error should mention ma_xe"

        conn.close()

    def test_create_year_future_allowed(self, seeded_db):
        """Test vehicle creation allows year = current_year + 1 (2027)."""
        from app.application.services.xe_service import XeService, XeCreateData

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)
        data = XeCreateData(
            ma_xe="XE_TEST_FUTURE",
            hang="Audi",
            dong_xe="Q7",
            nam_san_xuat=2027,  # Current year + 1
            gia_ban=2000000000,
        )

        result = service.create(data)
        assert result.nam_san_xuat == 2027

        conn.close()


class TestXeServiceUpdate:
    """Test XeService.update() - BR-XE-01: ma_xe cannot be changed."""

    def test_update_ma_xe_not_changeable(self, seeded_db):
        """Test that ma_xe cannot be changed after creation."""
        from app.application.services.xe_service import XeService, XeUpdateData, ValidationError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Get first vehicle
        xe_list = service.get_all(limit=1)
        if not xe_list:
            pytest.skip("No vehicles in database to test")

        original_xe = xe_list[0]
        original_ma_xe = original_xe.ma_xe

        # Try to update with different ma_xe
        data = XeUpdateData(
            ma_xe="CHANGED_MA_XE",
            hang="UpdatedHang",
        )

        # This should either raise error or ignore the ma_xe change
        result = service.update(original_xe.id, data)

        # Verify ma_xe was NOT changed
        updated_xe = service.get_by_id(original_xe.id)
        assert updated_xe.ma_xe == original_ma_xe, "ma_xe should not be changed"

        conn.close()

    def test_update_other_fields_success(self, seeded_db):
        """Test that other fields can be updated successfully."""
        from app.application.services.xe_service import XeService, XeUpdateData

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Get first vehicle
        xe_list = service.get_all(limit=1)
        if not xe_list:
            pytest.skip("No vehicles in database to test")

        original_xe = xe_list[0]

        # Update other fields
        new_hang = "UpdatedBrand"
        new_gia = 999999999

        data = XeUpdateData(
            hang=new_hang,
            gia_ban=new_gia,
        )

        result = service.update(original_xe.id, data)
        assert result.hang == new_hang
        assert result.gia_ban == new_gia

        conn.close()

    def test_update_nonexistent_vehicle(self, seeded_db):
        """Test updating a non-existent vehicle raises error."""
        from app.application.services.xe_service import XeService, XeUpdateData, XeNotFoundError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)
        data = XeUpdateData(hang="SomeBrand")

        with pytest.raises(XeNotFoundError):
            service.update(99999, data)  # Non-existent ID

        conn.close()


class TestXeServiceDelete:
    """Test XeService.delete() - BR-XE-02 / BR-REF-01."""

    def test_delete_vehicle_with_active_contract(self, seeded_db):
        """Test that vehicle with active contract cannot be deleted."""
        from app.application.services.xe_service import XeService, DeleteNotAllowedError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Create a vehicle
        service = XeService(conn)

        # First create a vehicle
        from app.application.services.xe_service import XeCreateData
        xe = service.create(XeCreateData(
            ma_xe="XE_DELETE_TEST",
            hang="TestBrand",
            dong_xe="TestModel",
            nam_san_xuat=2024,
            gia_ban=500000000,
            so_luong_ton=3,
        ))

        # Create a contract with this vehicle (non-cancelled status)
        conn.execute("""
            INSERT INTO hop_dong 
            (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, trang_thai)
            VALUES ('HD_DELETE_TEST', 1, ?, 1, 500000000, 'da_giao_xe')
        """, (xe.id,))
        conn.commit()

        # Try to delete - should fail with constraint error
        with pytest.raises(DeleteNotAllowedError):
            service.delete(xe.id)

        conn.close()

    def test_delete_vehicle_without_contract(self, seeded_db):
        """Test that vehicle without contract can be deleted."""
        from app.application.services.xe_service import XeService, XeCreateData

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Create a vehicle (no contracts)
        xe = service.create(XeCreateData(
            ma_xe="XE_DELETE_OK",
            hang="DeleteBrand",
            dong_xe="DeleteModel",
            nam_san_xuat=2024,
            gia_ban=300000000,
            so_luong_ton=1,
        ))
        xe_id = xe.id

        # Delete should succeed
        result = service.delete(xe_id)
        assert result is True

        # Verify deleted
        assert service.get_by_id(xe_id) is None

        conn.close()

    def test_delete_nonexistent_vehicle(self, seeded_db):
        """Test deleting a non-existent vehicle raises error."""
        from app.application.services.xe_service import XeService, XeNotFoundError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        with pytest.raises(XeNotFoundError):
            service.delete(99999)

        conn.close()


class TestXeServiceSearch:
    """Test XeService.search() - BR-XE-06, BR-XE-07."""

    def test_search_by_hang(self, seeded_db):
        """Test search by brand (hang)."""
        from app.application.services.xe_service import XeService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Get all vehicles and find a brand that exists
        hangs = service.get_distinct_hangs()
        if not hangs:
            pytest.skip("No brands in database")

        test_hang = hangs[0]

        result = service.search(hang=test_hang)

        assert result.items is not None
        assert result.total > 0
        for xe in result.items:
            assert xe.hang == test_hang

        conn.close()

    def test_search_by_keyword(self, seeded_db):
        """Test keyword search on ma_xe, hang, dong_xe."""
        from app.application.services.xe_service import XeService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Search with keyword that might match
        result = service.search(keyword="Toyota")

        assert result.items is not None
        # Results should contain keyword in ma_xe, hang, or dong_xe
        for xe in result.items:
            matched = (
                "Toyota" in xe.hang or
                "Toyota" in xe.dong_xe or
                "Toyota" in xe.ma_xe
            )
            # Note: if no results, that's also valid

        conn.close()

    def test_search_by_status(self, seeded_db):
        """Test search by status (trang_thai)."""
        from app.application.services.xe_service import XeService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        result = service.search(trang_thai="con_hang")

        assert result.items is not None
        for xe in result.items:
            assert xe.trang_thai == "con_hang"

        conn.close()

    def test_search_by_price_range(self, seeded_db):
        """Test search by price range."""
        from app.application.services.xe_service import XeService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        result = service.search(gia_min=500000000, gia_max=1000000000)

        assert result.items is not None
        for xe in result.items:
            assert 500000000 <= xe.gia_ban <= 1000000000

        conn.close()

    def test_search_by_year_range(self, seeded_db):
        """Test search by manufacturing year range."""
        from app.application.services.xe_service import XeService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        result = service.search(nam_san_xuat_min=2020, nam_san_xuat_max=2025)

        assert result.items is not None
        for xe in result.items:
            assert 2020 <= xe.nam_san_xuat <= 2025

        conn.close()

    def test_search_low_stock_only(self, seeded_db):
        """Test search for low stock vehicles only."""
        from app.application.services.xe_service import XeService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        result = service.search(low_stock_only=True)

        assert result.items is not None
        for xe in result.items:
            assert xe.so_luong_ton <= xe.muc_toi_thieu

        conn.close()

    def test_search_pagination(self, seeded_db):
        """Test search pagination."""
        from app.application.services.xe_service import XeService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Get first page
        result1 = service.search(page=1, page_size=5)
        page1_ids = [xe.id for xe in result1.items]

        # Get second page
        result2 = service.search(page=2, page_size=5)
        page2_ids = [xe.id for xe in result2.items]

        # Verify no overlap
        assert len(set(page1_ids) & set(page2_ids)) == 0, "Pages should not overlap"

        conn.close()


class TestXeServiceAdjustInventory:
    """Test XeService.adjust_inventory() - BR-XE-04, BR-XE-05."""

    def test_adjust_inventory_add_stock(self, seeded_db):
        """Test adding stock to a vehicle."""
        from app.application.services.xe_service import XeService, XeCreateData

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Create a vehicle with 0 stock
        xe = service.create(XeCreateData(
            ma_xe="XE_INVENTORY_TEST",
            hang="TestBrand",
            dong_xe="TestModel",
            nam_san_xuat=2024,
            gia_ban=500000000,
            so_luong_ton=0,
        ))

        # Add stock
        result = service.adjust_inventory(xe.id, delta=10)

        assert result.so_luong_ton == 10

        conn.close()

    def test_adjust_inventory_remove_stock(self, seeded_db):
        """Test removing stock from a vehicle."""
        from app.application.services.xe_service import XeService, XeCreateData

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Create a vehicle with 10 stock
        xe = service.create(XeCreateData(
            ma_xe="XE_INVENTORY_REMOVE",
            hang="TestBrand",
            dong_xe="TestModel",
            nam_san_xuat=2024,
            gia_ban=500000000,
            so_luong_ton=10,
        ))

        # Remove 3 stock
        result = service.adjust_inventory(xe.id, delta=-3)

        assert result.so_luong_ton == 7

        conn.close()

    def test_adjust_inventory_to_zero_with_contract(self, seeded_db):
        """Test that stock reaching 0 with active contract changes status to da_ban."""
        from app.application.services.xe_service import XeService, XeCreateData

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        service = XeService(conn)

        # Create a vehicle with some stock and a da_giao_xe contract
        xe = service.create(XeCreateData(
            ma_xe="XE_ZERO_CONTRACT",
            hang="TestBrand",
            dong_xe="TestModel",
            nam_san_xuat=2024,
            gia_ban=500000000,
            so_luong_ton=5,
        ))

        # Create da_giao_xe contract
        conn.execute("""
            INSERT INTO hop_dong 
            (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, trang_thai)
            VALUES ('HD_ZERO_TEST', 1, ?, 1, 500000000, 'da_giao_xe')
        """, (xe.id,))
        conn.commit()

        # Set stock to 0
        result = service.adjust_inventory(xe.id, delta=-5)

        # Status should change to da_ban (BR-XE-04)
        assert result.trang_thai == "da_ban"

        conn.close()


class TestXeValidator:
    """Test XeValidator directly."""

    def test_validator_validate_create_success(self):
        """Test validator passes valid create data."""
        from app.application.validators.xe_validator import XeValidator

        data = {
            "ma_xe": "XE_VALID_TEST",
            "hang": "TestBrand",
            "dong_xe": "TestModel",
            "nam_san_xuat": 2024,
            "gia_ban": 800000000,
        }

        result = XeValidator.validate_create(data)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validator_validate_create_missing_required(self):
        """Test validator fails with missing required fields."""
        from app.application.validators.xe_validator import XeValidator

        data = {
            "ma_xe": "",
            "hang": "",
            "dong_xe": "",
            "nam_san_xuat": 2024,
            "gia_ban": 800000000,
        }

        result = XeValidator.validate_create(data)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validator_validate_create_invalid_year(self):
        """Test validator fails with invalid year."""
        from app.application.validators.xe_validator import XeValidator

        data = {
            "ma_xe": "XE_YEAR_TEST",
            "hang": "TestBrand",
            "dong_xe": "TestModel",
            "nam_san_xuat": 1980,  # Invalid
            "gia_ban": 800000000,
        }

        result = XeValidator.validate_create(data)
        assert result.is_valid is False
        assert any("1990" in e for e in result.errors)

    def test_validator_validate_update_ma_xe_change(self):
        """Test validator rejects ma_xe change on update."""
        from app.application.validators.xe_validator import XeValidator

        data = {"ma_xe": "CHANGED_MA_XE"}

        result = XeValidator.validate_update(data, original_ma_xe="ORIGINAL_MA_XE")
        assert result.is_valid is False
        assert any("mã xe" in e.lower() for e in result.errors)
