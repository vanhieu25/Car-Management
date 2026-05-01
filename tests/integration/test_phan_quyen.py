"""SIT Integration Tests — T-G6.1.TEST.09: Phân quyền (Permission Matrix).

Tests 3 roles × all modules to verify permission matrix matches BRD §3.4 and BR-SEC-08.
Tests are performed programmatically using service/repo layers (not UI).

Permission matrix (from permission_service.py):
- Admin (vai_tro_id=1): full CRUD on all modules
- Sales (vai_tro_id=2): view xe; view/create khach_hang; view/create hop_dong;
  view phu_kien, khuyen_mai, tra_gop, marketing, bao_cao; no delete anywhere
- Kỹ thuật BH (vai_tro_id=3): view xe, khach_hang, hop_dong, phu_kien;
  create/update on bao_hanh, bao_duong, cuu_ho; no access to most other modules

Run via:
    pytest tests/integration/test_phan_quyen.py -v
    pytest tests/integration/test_phan_quyen.py::TestPhanQuyenAdmin -v
"""

import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.infrastructure.database.seeds.dev_seed import (
    seed_vai_tro,
    seed_xe,
    seed_khach_hang,
    seed_nha_cung_cap,
    seed_khuyen_mai,
    seed_phu_kien,
    seed_nhan_vien,
)
from app.application.services.permission_service import (
    PermissionService,
    Module,
    Action,
)
from app.application.services.khach_hang_service import (
    KhachHangService,
    KhachHangCreateData,
    KhachHangUpdateData,
)
from app.application.services.hop_dong_service import (
    HopDongService,
    HopDongCreateData,
)
from app.application.services.bao_hanh_service import (
    BaoHanhService,
)
from app.application.services.bao_duong_service import (
    BaoDuongService,
    BaoDuongCreateData,
    BaoDuongUpdateData,
)
from app.application.services.xe_service import XeService
from app.application.services.nhan_vien_service import NhanVienService
from app.application.services.tra_gop_service import TraGopService
from app.application.services.khieu_nai_service import (
    KhieuNaiService,
    KhieuNaiCreateData,
)


# =============================================================================
# Test Configuration
# =============================================================================

SIT_DB_NAME = "car_management_sit_phan_quyen.db"
SIT_DB_DIR = Path(__file__).parent.parent.parent / "data"


def _get_sit_db_path() -> Path:
    return SIT_DB_DIR / SIT_DB_NAME


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def sit_db_path():
    """Create a fresh SIT database seeded with test data for the session."""
    db_path = _get_sit_db_path()
    SIT_DB_DIR.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    runner = MigrationRunner(str(db_path))
    runner.run_pending()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    seed_vai_tro(cursor)
    seed_nhan_vien(cursor)
    seed_xe(cursor)
    seed_khach_hang(cursor)
    seed_nha_cung_cap(cursor)
    seed_khuyen_mai(cursor)
    seed_phu_kien(cursor)

    conn.commit()
    conn.close()

    yield str(db_path)

    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sit_conn(sit_db_path):
    """Fresh connection for each test (auto-cleanup)."""
    conn = sqlite3.connect(sit_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def sample_xe_id(sit_conn):
    cursor = sit_conn.execute(
        "SELECT id FROM xe WHERE so_luong_ton > 0 LIMIT 1"
    )
    row = cursor.fetchone()
    return row[0] if row else 1


@pytest.fixture
def sample_kh_id(sit_conn):
    cursor = sit_conn.execute("SELECT id FROM khach_hang LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 1


@pytest.fixture
def admin_nv_id(sit_conn):
    cursor = sit_conn.execute(
        "SELECT id FROM nhan_vien WHERE vai_tro_id = 1 LIMIT 1"
    )
    row = cursor.fetchone()
    return row[0] if row else 1


@pytest.fixture
def sales_nv_id(sit_conn):
    cursor = sit_conn.execute(
        "SELECT id FROM nhan_vien WHERE vai_tro_id = 2 LIMIT 1"
    )
    row = cursor.fetchone()
    return row[0] if row else 2


@pytest.fixture
def kt_nv_id(sit_conn):
    cursor = sit_conn.execute(
        "SELECT id FROM nhan_vien WHERE vai_tro_id = 3 LIMIT 1"
    )
    row = cursor.fetchone()
    return row[0] if row else 3


# =============================================================================
# TEST-09: Phân quyền 3 role × all modules
# =============================================================================

class TestPhanQuyenAdmin:
    """Admin (vai_tro_id=1) has full CRUD on all modules per BRD §3.4."""

    def test_admin_can_create_khach_hang(self, sit_conn, admin_nv_id):
        """Admin: create khach_hang."""
        service = KhachHangService(sit_conn)
        data = KhachHangCreateData(
            ho_ten="Test Admin KH",
            so_dien_thoai="0999000001",
            email="admin.test1@test.com",
        )
        created = service.create(data)
        assert created is not None
        assert created.ho_ten == "Test Admin KH"
        # Cleanup
        sit_conn.execute("DELETE FROM khach_hang WHERE id = ?", (created.id,))
        sit_conn.commit()

    def test_admin_can_read_khach_hang(self, sit_conn, sample_kh_id):
        """Admin: read khach_hang."""
        service = KhachHangService(sit_conn)
        kh = service.get_by_id(sample_kh_id)
        assert kh is not None

    def test_admin_can_update_khach_hang(self, sit_conn, admin_nv_id, sample_kh_id):
        """Admin: update khach_hang."""
        service = KhachHangService(sit_conn)
        update_data = KhachHangUpdateData(ho_ten="Admin Updated Name")
        updated = service.update(sample_kh_id, update_data, nhan_vien_id=admin_nv_id)
        assert updated.ho_ten == "Admin Updated Name"

    def test_admin_can_delete_khach_hang(self, sit_conn, admin_nv_id):
        """Admin: delete khach_hang (orphan, no contracts)."""
        service = KhachHangService(sit_conn)
        # Create a throw-away KH
        data = KhachHangCreateData(
            ho_ten="Admin Delete Test",
            so_dien_thoai="0999000099",
            email="admin.delete@test.com",
        )
        created = service.create(data)
        kh_id = created.id
        # Delete should succeed
        service.delete(kh_id)
        # Verify gone
        assert service.get_by_id(kh_id) is None

    def test_admin_can_create_hop_dong(self, sit_conn, sample_kh_id, sample_xe_id, admin_nv_id):
        """Admin: create hop_dong."""
        service = HopDongService(sit_conn)
        data = HopDongCreateData(
            khach_hang_id=sample_kh_id,
            xe_id=sample_xe_id,
            nhan_vien_id=admin_nv_id,
        )
        created = service.create(data)
        assert created is not None
        # Cleanup
        sit_conn.execute("DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?", (created.id,))
        sit_conn.execute("DELETE FROM hop_dong WHERE id = ?", (created.id,))
        sit_conn.commit()

    def test_admin_full_access_matrix(self, sit_conn):
        """Admin: verify full access across all modules in permission matrix."""
        ps = PermissionService()
        all_modules = [m.value for m in Module]
        all_actions = [Action.VIEW.value, Action.CREATE.value, Action.UPDATE.value, Action.DELETE.value]

        for module in all_modules:
            if module == "bao_cao":
                # bao_cao only has view/export, not create/update/delete
                assert ps.has_permission(1, module, Action.VIEW.value)
                assert ps.has_permission(1, module, Action.EXPORT.value)
                assert not ps.has_permission(1, module, Action.CREATE.value)
                assert not ps.has_permission(1, module, Action.UPDATE.value)
                assert not ps.has_permission(1, module, Action.DELETE.value)
            else:
                for action in all_actions:
                    result = ps.has_permission(1, module, action)
                    assert result is True, f"Admin should have {action} on {module}"


class TestPhanQuyenSales:
    """Sales (vai_tro_id=2) has limited access per BR-SEC-08."""

    def test_sales_can_view_xe(self, sit_conn):
        """Sales: can view xe."""
        ps = PermissionService()
        assert ps.has_permission(2, "xe", Action.VIEW.value) is True

    def test_sales_cannot_create_xe(self, sit_conn):
        """Sales: cannot create xe."""
        ps = PermissionService()
        assert ps.has_permission(2, "xe", Action.CREATE.value) is False

    def test_sales_cannot_delete_xe(self, sit_conn):
        """Sales: cannot delete xe."""
        ps = PermissionService()
        assert ps.has_permission(2, "xe", Action.DELETE.value) is False

    def test_sales_can_view_khach_hang(self, sit_conn):
        """Sales: can view khach_hang."""
        ps = PermissionService()
        assert ps.has_permission(2, "khach_hang", Action.VIEW.value) is True

    def test_sales_can_create_khach_hang(self, sit_conn):
        """Sales: can create khach_hang."""
        ps = PermissionService()
        assert ps.has_permission(2, "khach_hang", Action.CREATE.value) is True

    def test_sales_cannot_update_khach_hang(self, sit_conn):
        """Sales: cannot update khach_hang."""
        ps = PermissionService()
        assert ps.has_permission(2, "khach_hang", Action.UPDATE.value) is False

    def test_sales_cannot_delete_khach_hang(self, sit_conn):
        """Sales: cannot delete khach_hang."""
        ps = PermissionService()
        assert ps.has_permission(2, "khach_hang", Action.DELETE.value) is False

    def test_sales_can_view_hop_dong(self, sit_conn):
        """Sales: can view hop_dong."""
        ps = PermissionService()
        assert ps.has_permission(2, "hop_dong", Action.VIEW.value) is True

    def test_sales_can_create_hop_dong(self, sit_conn):
        """Sales: can create hop_dong."""
        ps = PermissionService()
        assert ps.has_permission(2, "hop_dong", Action.CREATE.value) is True

    def test_sales_cannot_update_hop_dong(self, sit_conn):
        """Sales: cannot update hop_dong."""
        ps = PermissionService()
        assert ps.has_permission(2, "hop_dong", Action.UPDATE.value) is False

    def test_sales_cannot_delete_hop_dong(self, sit_conn):
        """Sales: cannot delete hop_dong."""
        ps = PermissionService()
        assert ps.has_permission(2, "hop_dong", Action.DELETE.value) is False

    def test_sales_cannot_access_nhan_vien(self, sit_conn):
        """Sales: no access to nhan_vien module."""
        ps = PermissionService()
        assert ps.has_permission(2, "nhan_vien", Action.VIEW.value) is False
        assert ps.has_permission(2, "nhan_vien", Action.CREATE.value) is False
        assert ps.has_permission(2, "nhan_vien", Action.UPDATE.value) is False
        assert ps.has_permission(2, "nhan_vien", Action.DELETE.value) is False

    def test_sales_cannot_access_bao_hanh(self, sit_conn):
        """Sales: no access to bao_hanh module."""
        ps = PermissionService()
        assert ps.has_permission(2, "bao_hanh", Action.VIEW.value) is False
        assert ps.has_permission(2, "bao_hanh", Action.CREATE.value) is False

    def test_sales_cannot_access_nha_cung_cap(self, sit_conn):
        """Sales: no access to nha_cung_cap module."""
        ps = PermissionService()
        assert ps.has_permission(2, "nha_cung_cap", Action.VIEW.value) is False

    def test_sales_cannot_access_khieu_nai(self, sit_conn):
        """Sales: no access to khieu_nai module."""
        ps = PermissionService()
        assert ps.has_permission(2, "khieu_nai", Action.VIEW.value) is False

    def test_sales_cannot_access_he_thong(self, sit_conn):
        """Sales: no access to he_thong module."""
        ps = PermissionService()
        assert ps.has_permission(2, "he_thong", Action.VIEW.value) is False

    def test_sales_can_only_view_bao_cao(self, sit_conn):
        """Sales: can only view bao_cao, cannot export."""
        ps = PermissionService()
        assert ps.has_permission(2, "bao_cao", Action.VIEW.value) is True
        assert ps.has_permission(2, "bao_cao", Action.EXPORT.value) is False

    def test_sales_can_view_phu_kien(self, sit_conn):
        """Sales: can view phu_kien."""
        ps = PermissionService()
        assert ps.has_permission(2, "phu_kien", Action.VIEW.value) is True

    def test_sales_cannot_update_phu_kien(self, sit_conn):
        """Sales: cannot update phu_kien."""
        ps = PermissionService()
        assert ps.has_permission(2, "phu_kien", Action.UPDATE.value) is False

    def test_sales_can_view_tra_gop(self, sit_conn):
        """Sales: can view tra_gop."""
        ps = PermissionService()
        assert ps.has_permission(2, "tra_gop", Action.VIEW.value) is True

    def test_sales_cannot_create_tra_gop(self, sit_conn):
        """Sales: cannot create tra_gop (only view)."""
        ps = PermissionService()
        assert ps.has_permission(2, "tra_gop", Action.CREATE.value) is False

    def test_sales_can_view_marketing(self, sit_conn):
        """Sales: can view marketing."""
        ps = PermissionService()
        assert ps.has_permission(2, "marketing", Action.VIEW.value) is True

    def test_sales_can_view_khuyen_mai(self, sit_conn):
        """Sales: can view khuyen_mai."""
        ps = PermissionService()
        assert ps.has_permission(2, "khuyen_mai", Action.VIEW.value) is True


class TestPhanQuyenKyThuat:
    """Kỹ thuật BH (vai_tro_id=3) has limited access per BRD §3.4."""

    def test_kt_can_view_xe(self, sit_conn):
        """KT: can view xe."""
        ps = PermissionService()
        assert ps.has_permission(3, "xe", Action.VIEW.value) is True

    def test_kt_cannot_create_xe(self, sit_conn):
        """KT: cannot create xe."""
        ps = PermissionService()
        assert ps.has_permission(3, "xe", Action.CREATE.value) is False

    def test_kt_can_view_khach_hang(self, sit_conn):
        """KT: can view khach_hang."""
        ps = PermissionService()
        assert ps.has_permission(3, "khach_hang", Action.VIEW.value) is True

    def test_kt_cannot_create_khach_hang(self, sit_conn):
        """KT: cannot create khach_hang."""
        ps = PermissionService()
        assert ps.has_permission(3, "khach_hang", Action.CREATE.value) is False

    def test_kt_can_view_hop_dong(self, sit_conn):
        """KT: can view hop_dong."""
        ps = PermissionService()
        assert ps.has_permission(3, "hop_dong", Action.VIEW.value) is True

    def test_kt_cannot_create_hop_dong(self, sit_conn):
        """KT: cannot create hop_dong."""
        ps = PermissionService()
        assert ps.has_permission(3, "hop_dong", Action.CREATE.value) is False

    def test_kt_cannot_access_khach_hang_write(self, sit_conn):
        """KT: cannot update or delete khach_hang."""
        ps = PermissionService()
        assert ps.has_permission(3, "khach_hang", Action.UPDATE.value) is False
        assert ps.has_permission(3, "khach_hang", Action.DELETE.value) is False

    def test_kt_can_view_bao_hanh(self, sit_conn):
        """KT: can view bao_hanh."""
        ps = PermissionService()
        assert ps.has_permission(3, "bao_hanh", Action.VIEW.value) is True

    def test_kt_can_create_bao_hanh(self, sit_conn):
        """KT: can create bao_hanh request."""
        ps = PermissionService()
        assert ps.has_permission(3, "bao_hanh", Action.CREATE.value) is True

    def test_kt_can_update_bao_hanh(self, sit_conn):
        """KT: can update bao_hanh."""
        ps = PermissionService()
        assert ps.has_permission(3, "bao_hanh", Action.UPDATE.value) is True

    def test_kt_cannot_delete_bao_hanh(self, sit_conn):
        """KT: cannot delete bao_hanh."""
        ps = PermissionService()
        assert ps.has_permission(3, "bao_hanh", Action.DELETE.value) is False

    def test_kt_can_view_bao_duong(self, sit_conn):
        """KT: can view bao_duong."""
        ps = PermissionService()
        assert ps.has_permission(3, "bao_duong", Action.VIEW.value) is True

    def test_kt_can_create_bao_duong(self, sit_conn):
        """KT: can create bao_duong."""
        ps = PermissionService()
        assert ps.has_permission(3, "bao_duong", Action.CREATE.value) is True

    def test_kt_can_update_bao_duong(self, sit_conn):
        """KT: can update bao_duong."""
        ps = PermissionService()
        assert ps.has_permission(3, "bao_duong", Action.UPDATE.value) is True

    def test_kt_cannot_access_hop_dong_write(self, sit_conn):
        """KT: cannot update/delete hop_dong."""
        ps = PermissionService()
        assert ps.has_permission(3, "hop_dong", Action.UPDATE.value) is False
        assert ps.has_permission(3, "hop_dong", Action.DELETE.value) is False

    def test_kt_cannot_access_nhan_vien(self, sit_conn):
        """KT: no access to nhan_vien."""
        ps = PermissionService()
        assert ps.has_permission(3, "nhan_vien", Action.VIEW.value) is False

    def test_kt_cannot_access_marketing(self, sit_conn):
        """KT: no access to marketing."""
        ps = PermissionService()
        assert ps.has_permission(3, "marketing", Action.VIEW.value) is False

    def test_kt_cannot_access_khieu_nai(self, sit_conn):
        """KT: no access to khieu_nai."""
        ps = PermissionService()
        assert ps.has_permission(3, "khieu_nai", Action.VIEW.value) is False

    def test_kt_cannot_access_khuyen_mai(self, sit_conn):
        """KT: no access to khuyen_mai."""
        ps = PermissionService()
        assert ps.has_permission(3, "khuyen_mai", Action.VIEW.value) is False

    def test_kt_cannot_access_he_thong(self, sit_conn):
        """KT: no access to he_thong."""
        ps = PermissionService()
        assert ps.has_permission(3, "he_thong", Action.VIEW.value) is False

    def test_kt_can_view_cuu_ho(self, sit_conn):
        """KT: can view cuu_ho."""
        ps = PermissionService()
        assert ps.has_permission(3, "cuu_ho", Action.VIEW.value) is True

    def test_kt_can_create_cuu_ho(self, sit_conn):
        """KT: can create cuu_ho."""
        ps = PermissionService()
        assert ps.has_permission(3, "cuu_ho", Action.CREATE.value) is True

    def test_kt_can_update_cuu_ho(self, sit_conn):
        """KT: can update cuu_ho."""
        ps = PermissionService()
        assert ps.has_permission(3, "cuu_ho", Action.UPDATE.value) is True

    def test_kt_cannot_delete_cuu_ho(self, sit_conn):
        """KT: cannot delete cuu_ho."""
        ps = PermissionService()
        assert ps.has_permission(3, "cuu_ho", Action.DELETE.value) is False

    def test_kt_can_view_phu_kien(self, sit_conn):
        """KT: can view phu_kien."""
        ps = PermissionService()
        assert ps.has_permission(3, "phu_kien", Action.VIEW.value) is True

    def test_kt_cannot_access_nha_cung_cap(self, sit_conn):
        """KT: no access to nha_cung_cap."""
        ps = PermissionService()
        assert ps.has_permission(3, "nha_cung_cap", Action.VIEW.value) is False


class TestPhanQuyenPermissionMatrix:
    """Verify the entire permission matrix is correctly implemented."""

    def test_all_roles_have_expected_module_count(self, sit_conn):
        """Each role has expected number of accessible modules."""
        ps = PermissionService()
        admin_modules = ps.get_allowed_modules(1, Action.VIEW.value)
        sales_modules = ps.get_allowed_modules(2, Action.VIEW.value)
        kt_modules = ps.get_allowed_modules(3, Action.VIEW.value)

        # Admin should have all 15 modules
        assert len(admin_modules) == 15, f"Admin should have 15 modules, got {len(admin_modules)}"
        # Sales has 8 modules with VIEW: xe, kh, hd, pk, km, tg, mk, bc
        assert len(sales_modules) == 8, f"Sales should have 8 modules, got {len(sales_modules)}"
        # KT should have 8 modules: xe, kh, hd, pk, bh, bd, ch, bc
        assert len(kt_modules) == 8, f"KT should have 8 modules, got {len(kt_modules)}"

    def test_no_delete_permission_for_sales_anywhere(self, sit_conn):
        """Sales: no delete permission on any module."""
        ps = PermissionService()
        all_modules = [m.value for m in Module]
        for module in all_modules:
            assert ps.has_permission(2, module, Action.DELETE.value) is False, \
                f"Sales should not have delete on {module}"

    def test_no_delete_permission_for_kt_on_most_modules(self, sit_conn):
        """KT: delete only where explicitly allowed."""
        ps = PermissionService()
        # KT should not have delete on core modules
        for module in ["xe", "khach_hang", "hop_dong", "bao_hanh", "bao_duong"]:
            assert ps.has_permission(3, module, Action.DELETE.value) is False, \
                f"KT should not have delete on {module}"

    def test_unknown_role_has_no_permissions(self, sit_conn):
        """Unknown vai_tro_id returns no permissions."""
        ps = PermissionService()
        assert ps.has_permission(999, "xe", Action.VIEW.value) is False
        assert ps.has_permission(0, "xe", Action.VIEW.value) is False

    def test_admin_export_permission_only_for_bao_cao(self, sit_conn):
        """Admin: export permission only for bao_cao module."""
        ps = PermissionService()
        all_modules = [m.value for m in Module]
        for module in all_modules:
            if module == "bao_cao":
                assert ps.has_permission(1, module, Action.EXPORT.value) is True
            else:
                assert ps.has_permission(1, module, Action.EXPORT.value) is False, \
                    f"Admin should not have export on {module}"
