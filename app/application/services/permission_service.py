"""Permission service - role-based access control.

Implements permission matrix from BRD §3.4 and BR-SEC-08.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Module(Enum):
    """System modules that can have permissions."""
    XE = "xe"                    # Quản lý xe
    KHACH_HANG = "khach_hang"    # Quản lý khách hàng
    NHAN_VIEN = "nhan_vien"      # Quản lý nhân viên
    HOP_DONG = "hop_dong"        # Hợp đồng
    PHU_KIEN = "phu_kien"        # Phụ kiện
    KHUYEN_MAI = "khuyen_mai"     # Khuyến mãi
    BAO_HANH = "bao_hanh"        # Bảo hành
    NHA_CUNG_CAP = "nha_cung_cap"  # Nhà cung cấp
    TRA_GOP = "tra_gop"          # Trả góp
    BAO_DUONG = "bao_duong"      # Bảo dưỡng
    CUU_HO = "cuu_ho"            # Cứu hộ
    MARKETING = "marketing"      # Marketing
    KHIEU_NAI = "khieu_nai"      # Khiếu nại
    BAO_CAO = "bao_cao"          # Báo cáo
    HE_THONG = "he_thong"         # Hệ thống (settings, audit log)


class Action(Enum):
    """Possible actions on modules."""
    VIEW = "view"        # Xem (Read)
    CREATE = "create"    # Tạo mới
    UPDATE = "update"    # Cập nhật
    DELETE = "delete"    # Xóa
    EXPORT = "export"    # Xuất báo cáo


@dataclass
class Permission:
    """Represents a permission entry."""
    module: str
    action: str


class PermissionDeniedError(Exception):
    """Raised when a user lacks required permission."""
    def __init__(self, module: str, action: str, message: Optional[str] = None):
        self.module = module
        self.action = action
        self.message = message or f"Không có quyền thực hiện hành động '{action}' trên module '{module}'"
        super().__init__(self.message)


# Permission matrix based on BRD §3.4
# Format: {role: {module: [allowed_actions]}}
PERMISSION_MATRIX = {
    # Admin (role_id=1) - Full access to all modules
    "admin": {
        Module.XE.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.KHACH_HANG.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.NHAN_VIEN.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.HOP_DONG.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.PHU_KIEN.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.KHUYEN_MAI.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.BAO_HANH.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.NHA_CUNG_CAP.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.TRA_GOP.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.BAO_DUONG.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.CUU_HO.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.MARKETING.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.KHIEU_NAI.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
        Module.BAO_CAO.value: [Action.VIEW, Action.EXPORT],
        Module.HE_THONG.value: [Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE],
    },
    
    # Sales (role_id=2) - Limited access per BR-SEC-08
    # Sales can only view their own KPI data (not others')
    "sales": {
        Module.XE.value: [Action.VIEW],
        Module.KHACH_HANG.value: [Action.VIEW, Action.CREATE],
        Module.NHAN_VIEN.value: [],  # No access
        Module.HOP_DONG.value: [Action.VIEW, Action.CREATE],
        Module.PHU_KIEN.value: [Action.VIEW],
        Module.KHUYEN_MAI.value: [Action.VIEW],
        Module.BAO_HANH.value: [],  # No access
        Module.NHA_CUNG_CAP.value: [],  # No access
        Module.TRA_GOP.value: [Action.VIEW],
        Module.BAO_DUONG.value: [],  # No access
        Module.CUU_HO.value: [],  # No access
        Module.MARKETING.value: [Action.VIEW],
        Module.KHIEU_NAI.value: [],  # No access
        Module.BAO_CAO.value: [Action.VIEW],  # Own KPI only - enforced at service level
        Module.HE_THONG.value: [],  # No access
    },
    
    # Kỹ thuật bảo hành (role_id=3)
    "ky_thuat_bh": {
        Module.XE.value: [Action.VIEW],
        Module.KHACH_HANG.value: [Action.VIEW],
        Module.NHAN_VIEN.value: [],  # No access
        Module.HOP_DONG.value: [Action.VIEW],
        Module.PHU_KIEN.value: [Action.VIEW],
        Module.KHUYEN_MAI.value: [],  # No access
        Module.BAO_HANH.value: [Action.VIEW, Action.CREATE, Action.UPDATE],
        Module.NHA_CUNG_CAP.value: [],  # No access
        Module.TRA_GOP.value: [],  # No access
        Module.BAO_DUONG.value: [Action.VIEW, Action.CREATE, Action.UPDATE],
        Module.CUU_HO.value: [Action.VIEW, Action.CREATE, Action.UPDATE],
        Module.MARKETING.value: [],  # No access
        Module.KHIEU_NAI.value: [],  # No access
        Module.BAO_CAO.value: [Action.VIEW],  # Own data only
        Module.HE_THONG.value: [],  # No access
    },
}


class PermissionService:
    """Service for checking and enforcing permissions.
    
    Implements BR-SEC-08: Sales chỉ xem được dữ liệu KPI của chính mình.
    """

    def __init__(self):
        """Initialize permission service."""
        self._cache = PERMISSION_MATRIX

    def get_role_name(self, vai_tro_id: int) -> str:
        """Get role name from vai_tro_id.
        
        Args:
            vai_tro_id: Role ID from database.
            
        Returns:
            Role name string.
        """
        role_map = {
            1: "admin",
            2: "sales", 
            3: "ky_thuat_bh",
        }
        return role_map.get(vai_tro_id, "")

    def has_permission(
        self,
        vai_tro_id: int,
        module: str,
        action: str,
    ) -> bool:
        """Check if a role has permission for an action on a module.
        
        Args:
            vai_tro_id: Role ID from database.
            module: Module identifier (e.g., 'xe', 'khach_hang').
            action: Action identifier (e.g., 'view', 'create').
            
        Returns:
            True if permission granted, False otherwise.
        """
        role_name = self.get_role_name(vai_tro_id)
        if not role_name:
            return False

        role_permissions = self._cache.get(role_name, {})
        allowed_actions = role_permissions.get(module, [])
        
        return action in allowed_actions

    def check_permission(
        self,
        vai_tro_id: int,
        module: str,
        action: str,
    ) -> None:
        """Check permission and raise exception if denied.
        
        Args:
            vai_tro_id: Role ID from database.
            module: Module identifier.
            action: Action identifier.
            
        Raises:
            PermissionDeniedError: If permission is not granted.
        """
        if not self.has_permission(vai_tro_id, module, action):
            raise PermissionDeniedError(module, action)

    def get_allowed_modules(
        self,
        vai_tro_id: int,
        action: str,
    ) -> list[str]:
        """Get all modules that a role has permission for.
        
        Args:
            vai_tro_id: Role ID from database.
            action: Action identifier.
            
        Returns:
            List of module identifiers the role can perform the action on.
        """
        role_name = self.get_role_name(vai_tro_id)
        if not role_name:
            return []

        role_permissions = self._cache.get(role_name, {})
        return [
            module
            for module, actions in role_permissions.items()
            if action in actions
        ]

    def get_role_permissions(self, vai_tro_id: int) -> dict[str, list[str]]:
        """Get all permissions for a role.
        
        Args:
            vai_tro_id: Role ID from database.
            
        Returns:
            Dictionary mapping module names to lists of allowed actions.
        """
        role_name = self.get_role_name(vai_tro_id)
        if not role_name:
            return {}
        return self._cache.get(role_name, {})


# Global instance
permission_service = PermissionService()
