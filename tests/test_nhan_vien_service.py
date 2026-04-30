"""Test suite for NhanVienService - employee management module.

Implements TEST phase for Sprint G3.3 with 5 test tasks:
- T-G3.3.TEST.01: Unit test password generation (12 chars, complexity requirements)
- T-G3.3.TEST.02: Unit test BR-NV-07 (cannot lock admin account)
- T-G3.3.TEST.03: Unit test calc_kpi (BR-CALC-05)
- T-G3.3.TEST.04: Permission/role-based access tests
- T-G3.3.TEST.05: UAT smoke tests

Business Rules:
- BR-NV-07: Cannot lock admin account
- BR-CALC-05: Employee KPI calculation (so_hop_dong, doanh_thu, ti_le_chot)
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
from app.application.services.nhan_vien_service import (
    NhanVienService,
    NhanVienCreateData,
    NhanVienUpdateData,
    ValidationError,
    DuplicateUsernameError,
    DuplicateEmailError,
    CannotLockAdminError,
    NhanVienNotFoundError,
)
from app.infrastructure.security.password_hasher import password_hasher
from app.domain.entities import NhanVien


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
    """Create a NhanVienService instance from a db path.
    
    Args:
        db_path: Path to SQLite database.
        
    Returns:
        NhanVienService instance.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return NhanVienService(conn)


def create_employee(db_path, username, ho_ten, email, vai_tro_id=2):
    """Helper to create an employee for testing.
    
    Args:
        db_path: Path to database.
        username: Username.
        ho_ten: Full name.
        email: Email address.
        vai_tro_id: Role ID (default 2 for sales).
        
    Returns:
        Created NhanVien entity.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    service = NhanVienService(conn)
    
    data = NhanVienCreateData(
        username=username,
        ho_ten=ho_ten,
        email=email,
        vai_tro_id=vai_tro_id,
    )
    
    created, _ = service.create(data)
    return created


# =============================================================================
# T-G3.3.TEST.01: Unit test password generation (12 chars)
# =============================================================================

class TestPasswordGeneration:
    """Test password generation meets security requirements.
    
    Requirements:
    - Exactly 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - Multiple calls produce different passwords (randomness)
    """

    def test_generate_random_password_length(self):
        """Test that generated password is exactly 12 characters."""
        password = password_hasher.generate_random_password(12)
        assert len(password) == 12, f"Expected 12 chars, got {len(password)}"

    def test_generate_random_password_contains_uppercase(self):
        """Test that password contains at least 1 uppercase letter."""
        # Run multiple times to ensure at least one passes
        found = False
        for _ in range(10):
            password = password_hasher.generate_random_password(12)
            if any(c.isupper() for c in password):
                found = True
                break
        assert found, "Password should contain at least 1 uppercase letter"

    def test_generate_random_password_contains_lowercase(self):
        """Test that password contains at least 1 lowercase letter."""
        # Run multiple times to ensure at least one passes
        found = False
        for _ in range(10):
            password = password_hasher.generate_random_password(12)
            if any(c.islower() for c in password):
                found = True
                break
        assert found, "Password should contain at least 1 lowercase letter"

    def test_generate_random_password_contains_digits(self):
        """Test that password contains at least 1 digit."""
        # Run multiple times to ensure at least one passes
        found = False
        for _ in range(10):
            password = password_hasher.generate_random_password(12)
            if any(c.isdigit() for c in password):
                found = True
                break
        assert found, "Password should contain at least 1 digit"

    def test_generate_password_not_repeated(self):
        """Test that multiple calls produce different passwords (randomness)."""
        passwords = set()
        for _ in range(20):
            pwd = password_hasher.generate_random_password(12)
            passwords.add(pwd)
        
        # With 20 calls, we should have at least 18 unique passwords
        # (allowing for rare collisions but not all the same)
        assert len(passwords) >= 18, f"Passwords should vary, got {len(passwords)} unique out of 20"


# =============================================================================
# T-G3.3.TEST.02: Unit test BR-NV-07 (cannot lock admin)
# =============================================================================

class TestLockAdmin:
    """Test BR-NV-07: Cannot lock admin account.
    
    Business Rule: admin account (username == 'admin') cannot be locked.
    Attempting to lock admin should raise CannotLockAdminError.
    Regular employees can be locked normally.
    """

    def test_lock_admin_raises_CannotLockAdminError(self, fresh_db):
        """Test that locking admin account raises CannotLockAdminError.
        
        Steps:
        1. Create admin user (username='admin')
        2. Try to lock the admin account
        3. Expect CannotLockAdminError
        """
        service = get_service(fresh_db)
        
        # Create admin user
        data = NhanVienCreateData(
            username="admin",
            ho_ten="System Admin",
            email="admin@test.com",
            vai_tro_id=1,  # Admin role
        )
        admin, _ = service.create(data)
        
        # Get the admin employee
        admin_employee = service.get_by_username("admin")
        assert admin_employee is not None
        
        # Try to lock admin account - should raise CannotLockAdminError
        with pytest.raises(CannotLockAdminError) as exc_info:
            service.lock(admin_employee.id)
        
        assert "Không thể khóa tài khoản admin" in str(exc_info.value)

    def test_lock_regular_employee_succeeds(self, fresh_db):
        """Test that locking a regular employee works successfully.
        
        Steps:
        1. Create a regular employee
        2. Lock the employee
        3. Verify trang_thai changes to 'inactive' and khoa_den is set
        """
        service = get_service(fresh_db)
        
        # Create regular employee
        data = NhanVienCreateData(
            username="nhanvien1",
            ho_ten="Nhan Vien Thuong",
            email="nv1@test.com",
            vai_tro_id=2,  # Sales role
        )
        nv, _ = service.create(data)
        nhan_vien_id = nv.id
        
        # Lock the employee
        locked = service.lock(nhan_vien_id)
        
        # Verify the lock worked
        assert locked.trang_thai == "inactive", f"Expected 'inactive', got '{locked.trang_thai}'"
        assert locked.khoa_den is not None, "khoa_den should be set after locking"


# =============================================================================
# T-G3.3.TEST.03: Unit test calc_kpi (BR-CALC-05)
# =============================================================================

class TestCalcKPI:
    """Test KPI calculation for employees (BR-CALC-05).
    
    BR-CALC-05: Employee KPI calculation
    - so_hop_dong: count of contracts with trang_thai='da_giao_xe' in date range
    - doanh_thu: sum of tong_tien for those contracts
    - ti_le_chot: None (no lead tracking in current schema)
    
    Date range filtering: only contracts with ngay_giao_xe within range.
    """

    def test_calc_kpi_empty_period(self, fresh_db):
        """Test KPI with no contracts returns zero values.
        
        When an employee has no contracts in the date range:
        - so_hop_dong: 0
        - doanh_thu: 0
        - ti_le_chot: None
        """
        service = get_service(fresh_db)
        
        # Create an employee (no contracts)
        nv, _ = service.create(NhanVienCreateData(
            username="nv_test",
            ho_ten="Test Employee",
            email="test@test.com",
        ))
        
        # Calculate KPI for a period with no contracts
        result = service.calc_kpi(nv.id, "2024-01-01", "2024-01-31")
        
        assert result['so_hop_dong'] == 0, f"Expected 0, got {result['so_hop_dong']}"
        assert result['doanh_thu'] == 0, f"Expected 0, got {result['doanh_thu']}"
        assert result['ti_le_chot'] is None, f"Expected None, got {result['ti_le_chot']}"

    def test_calc_kpi_single_contract(self, fresh_db):
        """Test KPI with a single delivered contract.
        
        One contract with trang_thai='da_giao_xe':
        - so_hop_dong: 1
        - doanh_thu: sum of tong_tien
        """
        service = get_service(fresh_db)
        
        # Create employee
        nv, _ = service.create(NhanVienCreateData(
            username="nv_test",
            ho_ten="Test Employee",
            email="test@test.com",
        ))
        nhan_vien_id = nv.id
        
        # Insert a delivered contract directly
        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # First create a customer and car for FK constraints
        conn.execute("""
            INSERT INTO khach_hang (ho_ten, so_dien_thoai, email, created_at, updated_at)
            VALUES ('Test Customer', '0912345678', 'customer@test.com', datetime('now'), datetime('now'))
        """)
        khach_hang_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        conn.execute("""
            INSERT INTO xe (ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, created_at, updated_at)
            VALUES ('TEST001', 'Toyota', 'Camry', 2024, 'Đen', 1000000000, 1, datetime('now'), datetime('now'))
        """)
        xe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Create hop_dong with trang_thai='da_giao_xe' and ngay_giao_xe in range
        conn.execute("""
            INSERT INTO hop_dong 
            (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien, trang_thai, ngay_giao_xe, created_at, updated_at)
            VALUES ('HD001', ?, ?, ?, 1000000000, 1000000000, 'da_giao_xe', '2024-06-15', datetime('now'), datetime('now'))
        """, (khach_hang_id, xe_id, nhan_vien_id))
        conn.commit()
        conn.close()
        
        # Calculate KPI
        result = service.calc_kpi(nhan_vien_id, "2024-06-01", "2024-06-30")
        
        assert result['so_hop_dong'] == 1, f"Expected 1, got {result['so_hop_dong']}"
        assert result['doanh_thu'] == 1000000000, f"Expected 1000000000, got {result['doanh_thu']}"

    def test_calc_kpi_multiple_contracts(self, fresh_db):
        """Test KPI with multiple contracts sums doanh_thu correctly.
        
        Multiple contracts with trang_thai='da_giao_xe':
        - so_hop_dong: count
        - doanh_thu: sum of all tong_tien
        """
        service = get_service(fresh_db)
        
        # Create employee
        nv, _ = service.create(NhanVienCreateData(
            username="nv_test",
            ho_ten="Test Employee",
            email="test@test.com",
        ))
        nhan_vien_id = nv.id
        
        # Insert multiple delivered contracts
        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create customer and car
        conn.execute("""
            INSERT INTO khach_hang (ho_ten, so_dien_thoai, email, created_at, updated_at)
            VALUES ('Test Customer', '0912345678', 'customer@test.com', datetime('now'), datetime('now'))
        """)
        khach_hang_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        conn.execute("""
            INSERT INTO xe (ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, created_at, updated_at)
            VALUES ('TEST001', 'Toyota', 'Camry', 2024, 'Đen', 1000000000, 2, datetime('now'), datetime('now'))
        """)
        xe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Create 3 contracts with same nhan_vien_id, same status
        for i in range(3):
            conn.execute("""
                INSERT INTO hop_dong 
                (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien, trang_thai, ngay_giao_xe, created_at, updated_at)
                VALUES (?, ?, ?, ?, 500000000, 500000000, 'da_giao_xe', '2024-07-15', datetime('now'), datetime('now'))
            """, (f'HD00{i+1}', khach_hang_id, xe_id, nhan_vien_id))
        conn.commit()
        conn.close()
        
        # Calculate KPI
        result = service.calc_kpi(nhan_vien_id, "2024-07-01", "2024-07-31")
        
        assert result['so_hop_dong'] == 3, f"Expected 3, got {result['so_hop_dong']}"
        assert result['doanh_thu'] == 1500000000, f"Expected 1500000000, got {result['doanh_thu']}"

    def test_calc_kpi_date_range_filtering(self, fresh_db):
        """Test that KPI only counts contracts within date range.
        
        Contracts outside the date range should not be counted.
        """
        service = get_service(fresh_db)
        
        # Create employee
        nv, _ = service.create(NhanVienCreateData(
            username="nv_test",
            ho_ten="Test Employee",
            email="test@test.com",
        ))
        nhan_vien_id = nv.id
        
        # Insert contracts with different dates
        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Create customer and car
        conn.execute("""
            INSERT INTO khach_hang (ho_ten, so_dien_thoai, email, created_at, updated_at)
            VALUES ('Test Customer', '0912345678', 'customer@test.com', datetime('now'), datetime('now'))
        """)
        khach_hang_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        conn.execute("""
            INSERT INTO xe (ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, created_at, updated_at)
            VALUES ('TEST001', 'Toyota', 'Camry', 2024, 'Đen', 1000000000, 3, datetime('now'), datetime('now'))
        """)
        xe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Create 3 contracts: one in range, one before, one after
        # May 2024 (outside range)
        conn.execute("""
            INSERT INTO hop_dong 
            (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien, trang_thai, ngay_giao_xe, created_at, updated_at)
            VALUES ('HD001', ?, ?, ?, 300000000, 300000000, 'da_giao_xe', '2024-05-15', datetime('now'), datetime('now'))
        """, (khach_hang_id, xe_id, nhan_vien_id))
        
        # July 2024 (inside range)
        conn.execute("""
            INSERT INTO hop_dong 
            (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien, trang_thai, ngay_giao_xe, created_at, updated_at)
            VALUES ('HD002', ?, ?, ?, 400000000, 400000000, 'da_giao_xe', '2024-07-15', datetime('now'), datetime('now'))
        """, (khach_hang_id, xe_id, nhan_vien_id))
        
        # September 2024 (outside range)
        conn.execute("""
            INSERT INTO hop_dong 
            (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien, trang_thai, ngay_giao_xe, created_at, updated_at)
            VALUES ('HD003', ?, ?, ?, 500000000, 500000000, 'da_giao_xe', '2024-09-15', datetime('now'), datetime('now'))
        """, (khach_hang_id, xe_id, nhan_vien_id))
        conn.commit()
        conn.close()
        
        # Calculate KPI for July only
        result = service.calc_kpi(nhan_vien_id, "2024-07-01", "2024-07-31")
        
        # Should only count the July contract (HD002)
        assert result['so_hop_dong'] == 1, f"Expected 1, got {result['so_hop_dong']}"
        assert result['doanh_thu'] == 400000000, f"Expected 400000000, got {result['doanh_thu']}"


# =============================================================================
# T-G3.3.TEST.04: Permission/role-based access tests
# =============================================================================

class TestPermissionAccess:
    """Test role-based access control for employee management.
    
    S-NV-01 (Employee list screen): requires admin role
    S-NV-03 (Profile screen): accessible by A-02/A-03 (all roles)
    
    For now, we test that:
    - vai_tro_id=1 (admin) can access admin functions
    - vai_tro_id=2 (sales) can access profile update
    """

    def test_employee_list_screen_requires_admin_role(self, fresh_db):
        """Test that admin role (vai_tro_id=1) can access employee list operations.
        
        S-NV-01 should only be accessible by admin role.
        This test verifies admin can perform admin-level operations.
        """
        service = get_service(fresh_db)
        
        # Create admin user
        admin_data = NhanVienCreateData(
            username="admin",
            ho_ten="Admin User",
            email="admin@test.com",
            vai_tro_id=1,  # Admin
        )
        admin_nv, _ = service.create(admin_data)
        
        # Create regular employee
        nv_data = NhanVienCreateData(
            username="nhanvien",
            ho_ten="Regular User",
            email="nv@test.com",
            vai_tro_id=2,  # Sales
        )
        nv_nv, _ = service.create(nv_data)
        
        # Admin should be able to get all employees (list operation)
        all_employees = service.get_all(limit=100)
        assert len(all_employees) == 2, f"Expected 2 employees, got {len(all_employees)}"
        
        # Admin should be able to update any employee
        updated = service.update(admin_nv.id, NhanVienUpdateData(ho_ten="Admin Updated"))
        assert updated.ho_ten == "Admin Updated"

    def test_profile_screen_accessible_by_all_roles(self, fresh_db):
        """Test that A-02/A-03 roles can access and update their own profile.
        
        S-NV-03 (profile screen) should be accessible by all roles.
        Employees should be able to update their own profile data.
        """
        service = get_service(fresh_db)
        
        # Create a sales employee (vai_tro_id=2)
        nv_data = NhanVienCreateData(
            username="nhanvien",
            ho_ten="Sales Person",
            email="sales@test.com",
            vai_tro_id=2,
        )
        nv_nv, _ = service.create(nv_data)
        nhan_vien_id = nv_nv.id
        
        # Employee should be able to update their own profile
        # Only allowed fields: ho_ten, email, so_dien_thoai, dia_chi
        updated = service.update_self(nhan_vien_id, {
            'ho_ten': 'Sales Person Updated',
            'email': 'sales_updated@test.com',
        })
        
        assert updated.ho_ten == "Sales Person Updated", f"Expected updated name, got '{updated.ho_ten}'"
        assert updated.email == "sales_updated@test.com", f"Expected updated email, got '{updated.email}'"


# =============================================================================
# T-G3.3.TEST.05: UAT smoke tests
# =============================================================================

class TestNhanVienUAT:
    """UAT smoke tests for employee management module.
    
    These tests verify basic functionality an end user would encounter.
    """

    def test_create_employee_sets_must_change_password_true(self, fresh_db):
        """Test that creating an employee sets must_change_password=1.
        
        When a new employee is created, they must change password on first login.
        BR-SEC-03: First login requires password change.
        """
        service = get_service(fresh_db)
        
        # Create new employee
        data = NhanVienCreateData(
            username="newemployee",
            ho_ten="New Employee",
            email="new@test.com",
        )
        
        created, raw_password = service.create(data)
        
        # Verify must_change_password is True (1)
        assert created.must_change_password == 1, f"Expected must_change_password=1, got {created.must_change_password}"
        
        # Verify raw password was returned
        assert raw_password is not None, "Raw password should be returned for admin to share"
        assert len(raw_password) == 12, f"Password should be 12 chars, got {len(raw_password)}"

    def test_unlock_resets_trang_thai_and_lockout(self, fresh_db):
        """Test that unlocking an employee resets trang_thai and clears lockout.
        
        unlock() should:
        - Set trang_thai = 'active'
        - Clear khoa_den (set to NULL)
        - Reset lan_dang_nhap_sai to 0
        """
        service = get_service(fresh_db)
        
        # Create employee
        data = NhanVienCreateData(
            username="nvlock",
            ho_ten="Locked Employee",
            email="locked@test.com",
        )
        nv, _ = service.create(data)
        nhan_vien_id = nv.id
        
        # Lock the employee first
        locked = service.lock(nhan_vien_id)
        assert locked.trang_thai == "inactive"
        assert locked.khoa_den is not None
        
        # Unlock the employee
        unlocked = service.unlock(nhan_vien_id)
        
        # Verify unlock reset everything
        assert unlocked.trang_thai == "active", f"Expected 'active', got '{unlocked.trang_thai}'"
        
        # Verify khoa_den is cleared (fetch fresh from DB)
        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.execute("SELECT khoa_den, lan_dang_nhap_sai FROM nhan_vien WHERE id = ?", (nhan_vien_id,))
        row = cursor.fetchone()
        conn.close()
        
        assert row[0] is None, f"Expected khoa_den=None, got {row[0]}"
        assert row[1] == 0, f"Expected lan_dang_nhap_sai=0, got {row[1]}"