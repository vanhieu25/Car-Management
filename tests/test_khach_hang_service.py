"""Test suite for KhachHangService - customer management module.

Implements TEST phase for Sprint G3.2 with 5 test tasks:
- T-G3.2.TEST.01: Unit test validate email/SĐT (BR-DATA-04, BR-DATA-05)
- T-G3.2.TEST.02: Unit test duplicate phone (BR-KH-02)
- T-G3.2.TEST.03: Unit test update_classification (BR-CALC-03)
- T-G3.2.TEST.04: Integration tests
- T-G3.2.TEST.05: UAT smoke tests

Business Rules:
- BR-KH-01: Required fields (ho_ten, so_dien_thoai, email)
- BR-KH-02: so_dien_thoai must be unique
- BR-KH-06: Email valid (BR-DATA-04), SĐT VN (BR-DATA-05)
- BR-CALC-03: Customer classification thresholds
"""

import os
import sys
import tempfile
import sqlite3
from datetime import datetime

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.infrastructure.database.seeds.dev_seed import seed_all
from app.application.services.khach_hang_service import (
    KhachHangService,
    KhachHangCreateData,
    KhachHangUpdateData,
    ValidationError,
    DuplicatePhoneError,
    KhachHangNotFoundError,
    DeleteNotAllowedError,
)
from app.application.validators.khach_hang_validator import KhachHangValidator
from app.domain.entities import KhachHang


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def fresh_db():
    """Create a database with migrations applied (no seed data).
    
    Use this for tests that need a clean database without seed data.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    runner = MigrationRunner(db_path)
    runner.run_pending()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def seeded_db():
    """Create a database with migrations and seed data applied.
    
    Use this for integration tests and UAT smoke tests.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    runner = MigrationRunner(db_path)
    runner.run_pending()

    seed_all(db_path)

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


def get_service(db_path):
    """Create a KhachHangService instance from a db path.
    
    Args:
        db_path: Path to SQLite database.
        
    Returns:
        KhachHangService instance.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return KhachHangService(conn)


# =============================================================================
# T-G3.2.TEST.01: Unit test validate email/SĐT (BR-DATA-04, BR-DATA-05)
# =============================================================================

class TestKhachHangValidator:
    """Test KhachHangValidator for email and phone validation.
    
    BR-DATA-04: Email must be valid format (local@domain.tld)
    BR-DATA-05: Phone must be VN format (10 digits starting with 0, carrier prefix 03-09)
    """

    def test_validator_email_valid(self):
        """Test that valid emails pass validation without error.
        
        Valid email formats:
        - simple@example.com
        - user.name@domain.com
        - user+tag@domain.co.uk
        - user123@test-domain.io
        """
        valid_emails = [
            "simple@example.com",
            "user.name@domain.com",
            "user+tag@domain.co.uk",
            "user123@test-domain.io",
            "a@b.co",
            "user_name@company.org",
        ]
        
        for email in valid_emails:
            error = KhachHangValidator.validate_email(email)
            assert error is None, f"Expected valid email '{email}' to pass, but got: {error}"

    def test_validator_email_invalid(self):
        """Test that invalid emails raise error (BR-DATA-04).
        
        Invalid email formats that should be rejected:
        - Missing @ symbol
        - Missing domain
        - Invalid characters
        - Empty string
        """
        invalid_emails = [
            "",  # Empty
            "   ",  # Whitespace only
            "notanemail",  # No @ symbol
            "@nodomain.com",  # No local part
            "noat.com",  # No @ symbol
            "spaces in@email.com",  # Spaces in local part
            "user@ domain.com",  # Space in domain
            "user@.com",  # Empty domain
            "user@domain.",  # No TLD
            "user@domain.c",  # TLD too short
            "user@@domain.com",  # Double @
            "user@do main.com",  # Space in domain
        ]
        
        for email in invalid_emails:
            error = KhachHangValidator.validate_email(email)
            assert error is not None, f"Expected invalid email '{email}' to raise error"

    def test_validator_phone_valid(self):
        """Test that valid Vietnam phone numbers pass validation.
        
        Valid VN phone patterns (BR-DATA-05):
        - 10 digits starting with 0
        - Valid carrier prefixes: 03x, 04x, 05x, 07x, 08x, 09x
        - Examples: 0912345678, 0381234567, 0901234567, 0791234567, 0891234567
        """
        valid_phones = [
            "0912345678",
            "0381234567",
            "0901234567",
            "0791234567",
            "0891234567",
            "093 123 4567",  # With spaces (should be normalized)
            "094-123-4567",  # With dashes (should be normalized)
            "0971 234 567",  # 9 digits with spaces
        ]
        
        for phone in valid_phones:
            error = KhachHangValidator.validate_phone(phone)
            assert error is None, f"Expected valid phone '{phone}' to pass, but got: {error}"

    def test_validator_phone_invalid(self):
        """Test that invalid Vietnam phone numbers raise error (BR-DATA-05).
        
        Invalid patterns:
        - Too short/long
        - Invalid prefix (not 03-09)
        - Contains letters
        - Empty string
        """
        invalid_phones = [
            "",  # Empty
            "   ",  # Whitespace only
            "1234567890",  # No leading 0
            "012345678",  # Only 9 digits
            "01234567890",  # 11 digits
            "0112345678",  # Invalid prefix 01
            "0212345678",  # Invalid prefix 02
            "0612345678",  # Invalid prefix 06
            "12345678901",  # No leading 0, 11 digits
            "abcdefghij",  # Letters only
            "090123456a",  # Letter at end
            "090 123 456",  # Too short (9 digits with spaces)
        ]
        
        for phone in invalid_phones:
            error = KhachHangValidator.validate_phone(phone)
            assert error is not None, f"Expected invalid phone '{phone}' to raise error"


# =============================================================================
# T-G3.2.TEST.02: Unit test duplicate phone (BR-KH-02)
# =============================================================================

class TestKhachHangServiceDuplicatePhone:
    """Test duplicate phone validation in KhachHangService.
    
    BR-KH-02: so_dien_thoai must be unique across all customers.
    Duplicate phone should raise DuplicatePhoneError on create/update.
    """

    def test_create_duplicate_phone_raises_DuplicatePhoneError(self, fresh_db):
        """Test that creating customer with duplicate phone raises error (BR-KH-02).
        
        Steps:
        1. Create first customer with phone 0912345678
        2. Try to create second customer with same phone
        3. Expect DuplicatePhoneError
        """
        service = get_service(fresh_db)
        
        # Create first customer
        data1 = KhachHangCreateData(
            ho_ten="Nguyen Van A",
            so_dien_thoai="0912345678",
            email="a@example.com",
        )
        customer1 = service.create(data1)
        assert customer1 is not None
        assert customer1.so_dien_thoai == "0912345678"
        
        # Try to create second customer with same phone
        data2 = KhachHangCreateData(
            ho_ten="Tran Van B",
            so_dien_thoai="0912345678",  # Same phone
            email="b@example.com",
        )
        
        with pytest.raises(DuplicatePhoneError) as exc_info:
            service.create(data2)
        
        assert "đã được sử dụng" in str(exc_info.value)

    def test_update_duplicate_phone_raises_DuplicatePhoneError(self, fresh_db):
        """Test that updating customer with duplicate phone raises error (BR-KH-02).
        
        Steps:
        1. Create two customers with different phones
        2. Try to update second customer with first customer's phone
        3. Expect DuplicatePhoneError
        """
        service = get_service(fresh_db)
        
        # Create first customer
        data1 = KhachHangCreateData(
            ho_ten="Customer One",
            so_dien_thoai="0912345678",
            email="one@example.com",
        )
        customer1 = service.create(data1)
        customer1_id = customer1.id
        
        # Create second customer with different phone
        data2 = KhachHangCreateData(
            ho_ten="Customer Two",
            so_dien_thoai="0912345679",
            email="two@example.com",
        )
        customer2 = service.create(data2)
        customer2_id = customer2.id
        
        # Try to update second customer with first customer's phone
        update_data = KhachHangUpdateData(
            so_dien_thoai="0912345678",  # First customer's phone
        )
        
        with pytest.raises(DuplicatePhoneError) as exc_info:
            service.update(customer2_id, update_data)
        
        assert "đã được sử dụng" in str(exc_info.value)


# =============================================================================
# T-G3.2.TEST.03: Unit test update_classification (BR-CALC-03)
# =============================================================================

class TestKhachHangServiceClassification:
    """Test customer classification calculation and update.
    
    BR-CALC-03: Classification thresholds:
    - Thường: < 500,000,000 (500M)
    - Thân thiết: >= 500,000,000 and < 1,500,000,000 (1.5B)
    - VIP: >= 1,500,000,000 (1.5B)
    
    This tests the KhachHangValidator.calculate_phan_loai method directly,
    as well as the service's update_classification method.
    """

    def test_classification_below_500m(self):
        """Test classification returns 'Thuong' when tong_gia_tri_mua < 500M."""
        test_values = [
            0,
            100_000_000,
            299_999_999,
            499_999_999,
        ]
        
        for value in test_values:
            result = KhachHangValidator.calculate_phan_loai(value)
            assert result == "Thuong", f"Expected 'Thuong' for {value}, got '{result}'"

    def test_classification_at_500m(self):
        """Test classification returns 'Than_thiet' when tong_gia_tri_mua == 500M.
        
        Threshold boundary: >= 500M should be Thân thiết, not Thường.
        """
        result = KhachHangValidator.calculate_phan_loai(500_000_000)
        assert result == "Than_thiet", f"Expected 'Than_thiet' at exactly 500M, got '{result}'"

    def test_classification_between_500m_and_1_5b(self):
        """Test classification returns 'Than_thiet' when 500M <= value < 1.5B."""
        test_values = [
            500_000_001,
            700_000_000,
            999_999_999,
            1_000_000_000,
            1_299_999_999,
            1_499_999_999,
        ]
        
        for value in test_values:
            result = KhachHangValidator.calculate_phan_loai(value)
            assert result == "Than_thiet", f"Expected 'Than_thiet' for {value}, got '{result}'"

    def test_classification_at_1_5b(self):
        """Test classification returns 'VIP' when tong_gia_tri_mua == 1.5B.
        
        Threshold boundary: >= 1.5B should be VIP.
        """
        result = KhachHangValidator.calculate_phan_loai(1_500_000_000)
        assert result == "VIP", f"Expected 'VIP' at exactly 1.5B, got '{result}'"

    def test_classification_above_1_5b(self):
        """Test classification returns 'VIP' when tong_gia_tri_mua > 1.5B."""
        test_values = [
            1_500_000_001,
            2_000_000_000,
            5_000_000_000,
            10_000_000_000,
        ]
        
        for value in test_values:
            result = KhachHangValidator.calculate_phan_loai(value)
            assert result == "VIP", f"Expected 'VIP' for {value}, got '{result}'"

    def test_update_classification_via_service(self, fresh_db):
        """Test service update_classification method updates phan_loai correctly.
        
        This integration test verifies the full flow:
        1. Create customer (default Thuong)
        2. Update tong_gia_tri_mua directly in DB
        3. Call update_classification
        4. Verify phan_loai is updated
        """
        service = get_service(fresh_db)
        
        # Create customer
        data = KhachHangCreateData(
            ho_ten="VIP Customer",
            so_dien_thoai="0912345678",
            email="vip@example.com",
        )
        customer = service.create(data)
        customer_id = customer.id
        
        # Verify initial classification is Thuong (default)
        assert customer.phan_loai == "Thuong"
        
        # Update tong_gia_tri_mua to VIP threshold (1.5B)
        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "UPDATE khach_hang SET tong_gia_tri_mua = ? WHERE id = ?",
            (1_500_000_000, customer_id)
        )
        conn.commit()
        conn.close()
        
        # Call update_classification
        updated = service.update_classification(customer_id)
        
        # Verify classification changed to VIP
        assert updated.phan_loai == "VIP"


# =============================================================================
# T-G3.2.TEST.04: Integration tests
# =============================================================================

class TestKhachHangServiceIntegration:
    """Integration tests for KhachHangService.
    
    Tests the full workflow of creating, retrieving, and updating customers.
    """

    def test_create_khach_hang_via_service_and_retrieve(self, fresh_db):
        """Test that create followed by get_by_id returns the same data.
        
        Full workflow:
        1. Create customer via service
        2. Retrieve by ID
        3. Verify all fields match
        """
        service = get_service(fresh_db)
        
        # Create customer with all fields
        create_data = KhachHangCreateData(
            ho_ten="Nguyen Van Integration",
            so_dien_thoai="0912345678",
            email="integration@test.com",
            dia_chi="123 Nguyen Trai, HCM",
            ngay_sinh="1990-05-15",
            phan_loai="Thuong",
        )
        
        created = service.create(create_data)
        
        # Retrieve by ID
        retrieved = service.get_by_id(created.id)
        
        # Verify fields match
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.ho_ten == "Nguyen Van Integration"
        assert retrieved.so_dien_thoai == "0912345678"
        assert retrieved.email == "integration@test.com"
        assert retrieved.dia_chi == "123 Nguyen Trai, HCM"
        assert retrieved.ngay_sinh == "1990-05-15"
        assert retrieved.phan_loai == "Thuong"

    def test_update_classification_after_purchase(self, fresh_db):
        """Test that setting tong_gia_tri_mua causes classification auto-calculation.
        
        This tests BR-CALC-03: classification auto-update based on purchase value.
        
        Steps:
        1. Create customer with 0 purchase value (Thuong)
        2. Simulate purchase that brings total to VIP threshold (1.5B)
        3. Update purchase stats via service
        4. Verify classification automatically becomes VIP
        """
        service = get_service(fresh_db)
        
        # Create customer (default classification is Thuong)
        create_data = KhachHangCreateData(
            ho_ten="Auto Classification Test",
            so_dien_thoai="0912345678",
            email="autoclass@test.com",
        )
        customer = service.create(create_data)
        customer_id = customer.id
        
        # Verify initial state
        assert customer.phan_loai == "Thuong"
        assert customer.tong_gia_tri_mua == 0
        
        # Simulate purchase that brings total to VIP threshold
        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "UPDATE khach_hang SET tong_gia_tri_mua = ? WHERE id = ?",
            (1_600_000_000, customer_id)  # 1.6B > 1.5B VIP threshold
        )
        conn.commit()
        conn.close()
        
        # Call update_purchase_stats_after_contract to recalculate
        service.update_purchase_stats_after_contract(customer_id, 1_600_000_000)
        
        # Verify classification is now VIP
        updated = service.get_by_id(customer_id)
        assert updated.phan_loai == "VIP", f"Expected 'VIP' after 1.6B purchase, got '{updated.phan_loai}'"


# =============================================================================
# T-G3.2.TEST.05: UAT smoke tests
# =============================================================================

class TestKhachHangServiceUAT:
    """UAT smoke tests for customer management module.
    
    These tests verify basic functionality using seed data (seeded_db).
    They test the happy path scenarios an end user would encounter.
    """

    def test_search_returns_results(self, seeded_db):
        """Test that keyword search returns matching results.
        
        Uses seeded_db which has 20 customers with various names.
        Tests search functionality that UAT users would perform.
        """
        service = get_service(seeded_db)
        
        # Search for common keyword that should match seed data
        # Seed data has customers with various names
        result = service.search(keyword="Nguyen", page=1, page_size=50)
        
        # Verify result structure
        assert result is not None
        assert hasattr(result, "items")
        assert hasattr(result, "total")
        assert hasattr(result, "page")
        assert hasattr(result, "page_size")
        assert hasattr(result, "total_pages")
        
        # Verify items are KhachHang entities
        for item in result.items:
            assert isinstance(item, KhachHang)
        
        # Verify pagination info is reasonable
        assert result.page == 1
        assert result.page_size == 50
        assert result.total_pages >= 1

    def test_delete_customer_without_contract(self, fresh_db):
        """Test that deleting customer without contracts returns True (hard delete).
        
        BR-KH-05: Cannot delete customer with active contracts.
        If customer has no contracts, deletion should succeed (hard delete).
        
        Steps:
        1. Create customer (no contracts)
        2. Delete customer
        3. Verify returns True
        4. Verify customer no longer exists
        """
        service = get_service(fresh_db)
        
        # Create customer with no contracts
        create_data = KhachHangCreateData(
            ho_ten="No Contract Customer",
            so_dien_thoai="0912345678",
            email="nocontract@test.com",
        )
        customer = service.create(create_data)
        customer_id = customer.id
        
        # Verify customer exists
        retrieved = service.get_by_id(customer_id)
        assert retrieved is not None
        
        # Delete customer
        result = service.delete(customer_id)
        
        # Verify returns True (hard delete, not soft delete)
        assert result is True, f"Expected True for hard delete, got {result}"
        
        # Verify customer no longer exists
        retrieved_after = service.get_by_id(customer_id)
        assert retrieved_after is None

    def test_search_by_classification(self, seeded_db):
        """Test that filtering by classification works.
        
        Seed data has:
        - 3 VIP customers (first 3)
        - 5 Than_thiet customers (next 5)
        - 12 Thuong customers (rest)
        """
        service = get_service(seeded_db)
        
        # Search for VIP customers
        result_vip = service.search(phan_loai="VIP", page=1, page_size=50)
        assert result_vip.total >= 3, f"Expected at least 3 VIP customers, got {result_vip.total}"
        
        # Search for Than_thiet customers
        result_than = service.search(phan_loai="Than_thiet", page=1, page_size=50)
        assert result_than.total >= 5, f"Expected at least 5 Than_thiet customers, got {result_than.total}"
        
        # Search for Thuong customers
        result_thuong = service.search(phan_loai="Thuong", page=1, page_size=50)
        assert result_thuong.total >= 12, f"Expected at least 12 Thuong customers, got {result_thuong.total}"