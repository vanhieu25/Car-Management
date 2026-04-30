"""Unit tests for PermissionService - T-G2.2.TEST.04.

Tests permission matrix for admin, sales, and ky_thuat_bh roles.
Implements BR-SEC-08: Sales only see their own KPI data.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestPermissionService:
    """Test PermissionService.has_permission() - BR-SEC-08."""

    def test_admin_has_full_access(self):
        """Test admin role has full access to all modules."""
        from app.application.services.permission_service import PermissionService

        ps = PermissionService()

        # Admin (vai_tro_id = 1) should have all permissions
        assert ps.has_permission(1, "xe", "view") is True
        assert ps.has_permission(1, "xe", "create") is True
        assert ps.has_permission(1, "xe", "update") is True
        assert ps.has_permission(1, "xe", "delete") is True

        assert ps.has_permission(1, "khach_hang", "view") is True
        assert ps.has_permission(1, "khach_hang", "create") is True
        assert ps.has_permission(1, "khach_hang", "update") is True
        assert ps.has_permission(1, "khach_hang", "delete") is True

        assert ps.has_permission(1, "nhan_vien", "view") is True
        assert ps.has_permission(1, "nhan_vien", "create") is True
        assert ps.has_permission(1, "nhan_vien", "update") is True
        assert ps.has_permission(1, "nhan_vien", "delete") is True

        assert ps.has_permission(1, "hop_dong", "view") is True
        assert ps.has_permission(1, "hop_dong", "create") is True
        assert ps.has_permission(1, "hop_dong", "update") is True
        assert ps.has_permission(1, "hop_dong", "delete") is True

        assert ps.has_permission(1, "bao_cao", "view") is True
        assert ps.has_permission(1, "bao_cao", "export") is True

        assert ps.has_permission(1, "he_thong", "view") is True
        assert ps.has_permission(1, "he_thong", "create") is True
        assert ps.has_permission(1, "he_thong", "update") is True
        assert ps.has_permission(1, "he_thong", "delete") is True

    def test_sales_limited_access(self):
        """Test sales role has limited access per BR-SEC-08."""
        from app.application.services.permission_service import PermissionService

        ps = PermissionService()

        # Sales (vai_tro_id = 2) should have limited permissions
        # Can view xe
        assert ps.has_permission(2, "xe", "view") is True
        # Cannot create/update/delete xe
        assert ps.has_permission(2, "xe", "create") is False
        assert ps.has_permission(2, "xe", "update") is False
        assert ps.has_permission(2, "xe", "delete") is False

        # Can view and create khach_hang
        assert ps.has_permission(2, "khach_hang", "view") is True
        assert ps.has_permission(2, "khach_hang", "create") is True
        # Cannot update/delete khach_hang
        assert ps.has_permission(2, "khach_hang", "update") is False
        assert ps.has_permission(2, "khach_hang", "delete") is False

        # No access to nhan_vien (own data only)
        assert ps.has_permission(2, "nhan_vien", "view") is False
        assert ps.has_permission(2, "nhan_vien", "create") is False

        # Can view hop_dong and create
        assert ps.has_permission(2, "hop_dong", "view") is True
        assert ps.has_permission(2, "hop_dong", "create") is True
        # Cannot update/delete hop_dong
        assert ps.has_permission(2, "hop_dong", "update") is False
        assert ps.has_permission(2, "hop_dong", "delete") is False

        # Can view bao_cao (own KPI only - enforced at service level)
        assert ps.has_permission(2, "bao_cao", "view") is True
        # Cannot export or access he_thong
        assert ps.has_permission(2, "bao_cao", "export") is False
        assert ps.has_permission(2, "he_thong", "view") is False

    def test_ky_thuat_bh_access(self):
        """Test kỹ thuật bảo hành role has appropriate access."""
        from app.application.services.permission_service import PermissionService

        ps = PermissionService()

        # Kỹ thuật (vai_tro_id = 3) has specific access
        # Can view xe
        assert ps.has_permission(3, "xe", "view") is True
        assert ps.has_permission(3, "xe", "create") is False

        # Can view khach_hang
        assert ps.has_permission(3, "khach_hang", "view") is True

        # No access to hop_dong modification
        assert ps.has_permission(3, "hop_dong", "view") is True
        assert ps.has_permission(3, "hop_dong", "create") is False

        # Can work with bao_hanh (create and update)
        assert ps.has_permission(3, "bao_hanh", "view") is True
        assert ps.has_permission(3, "bao_hanh", "create") is True
        assert ps.has_permission(3, "bao_hanh", "update") is True
        assert ps.has_permission(3, "bao_hanh", "delete") is False

        # Can work with bao_duong
        assert ps.has_permission(3, "bao_duong", "view") is True
        assert ps.has_permission(3, "bao_duong", "create") is True
        assert ps.has_permission(3, "bao_duong", "update") is True

        # Can work with cuu_ho
        assert ps.has_permission(3, "cuu_ho", "view") is True
        assert ps.has_permission(3, "cuu_ho", "create") is True
        assert ps.has_permission(3, "cuu_ho", "update") is True

        # No access to nhan_vien, marketing, khieu_nai
        assert ps.has_permission(3, "nhan_vien", "view") is False
        assert ps.has_permission(3, "marketing", "view") is False
        assert ps.has_permission(3, "khieu_nai", "view") is False

    def test_unknown_role_has_no_permissions(self):
        """Test that unknown role IDs have no permissions."""
        from app.application.services.permission_service import PermissionService

        ps = PermissionService()

        assert ps.has_permission(999, "xe", "view") is False
        assert ps.has_permission(0, "xe", "view") is False
        assert ps.has_permission(None, "xe", "view") is False

    def test_check_permission_raises_on_denied(self):
        """Test that check_permission raises PermissionDeniedError."""
        from app.application.services.permission_service import PermissionService, PermissionDeniedError

        ps = PermissionService()

        # Should not raise for allowed permission
        ps.check_permission(1, "xe", "view")

        # Should raise for denied permission
        with pytest.raises(PermissionDeniedError):
            ps.check_permission(2, "nhan_vien", "view")

    def test_get_allowed_modules(self):
        """Test getting all allowed modules for a role."""
        from app.application.services.permission_service import PermissionService

        ps = PermissionService()

        # Admin can do view on all modules
        admin_view_modules = ps.get_allowed_modules(1, "view")
        assert "xe" in admin_view_modules
        assert "khach_hang" in admin_view_modules
        assert "nhan_vien" in admin_view_modules

        # Sales can only view certain modules
        sales_view_modules = ps.get_allowed_modules(2, "view")
        assert "xe" in sales_view_modules
        assert "khach_hang" in sales_view_modules
        assert "nhan_vien" not in sales_view_modules
        assert "bao_hanh" not in sales_view_modules

    def test_get_role_permissions(self):
        """Test getting all permissions for a role."""
        from app.application.services.permission_service import PermissionService

        ps = PermissionService()

        perms = ps.get_role_permissions(1)
        assert "xe" in perms
        assert "create" in perms["xe"]
        assert "delete" in perms["xe"]

        perms = ps.get_role_permissions(2)
        assert "xe" in perms
        assert "delete" not in perms["xe"]

    def test_role_name_mapping(self):
        """Test role name from vai_tro_id."""
        from app.application.services.permission_service import PermissionService

        ps = PermissionService()

        assert ps.get_role_name(1) == "admin"
        assert ps.get_role_name(2) == "sales"
        assert ps.get_role_name(3) == "ky_thuat_bh"
        assert ps.get_role_name(999) == ""
