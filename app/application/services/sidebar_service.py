"""Sidebar service - filters navigation items by user role.

Provides role-based navigation filtering for the sidebar menu.
Admin (A-01): all 15 modules
Sales (A-02): 11 modules (no NV, BH, NCC, TG, BD, CH, KN, HT)
Kỹ thuật (A-03): 5 modules (only BH, BD, CH related)
"""

from typing import Optional

from app.application.services.navigation_registry import (
    NavigationRegistry,
    NavigationItem,
    NavigationGroup,
    navigation_registry,
    register_module,
)
from app.application.services.permission_service import PermissionService


# Sidebar module definitions with permission mappings
# Format: (module_id, label, icon, permission_module, order, shortcut, group_name, group_order)
SIDEBAR_MODULES = [
    # Dashboard
    ("dashboard", "Dashboard", "📊", "bao_cao", 0, "Ctrl+1", "Chung", 0),
    
    # Nghiệp vụ lõi
    ("xe", "Quản lý xe", "🚗", "xe", 1, "Ctrl+2", "Nghiệp vụ", 1),
    ("khach_hang", "Khách hàng", "👥", "khach_hang", 2, "Ctrl+3", "Nghiệp vụ", 1),
    ("nhan_vien", "Nhân viên", "👤", "nhan_vien", 3, "Ctrl+4", "Nghiệp vụ", 1),
    ("hop_dong", "Hợp đồng", "📄", "hop_dong", 4, "Ctrl+5", "Nghiệp vụ", 1),
    ("kho", "Kho hàng", "📦", "nha_cung_cap", 5, "Ctrl+6", "Nghiệp vụ", 1),
    
    # Nghiệp vụ mở rộng
    ("phu_kien", "Phụ kiện", "🔧", "phu_kien", 10, "Ctrl+7", "Mở rộng", 2),
    ("khuyen_mai", "Khuyến mãi", "🎁", "khuyen_mai", 11, None, "Mở rộng", 2),
    ("bao_hanh", "Bảo hành", "🛡️", "bao_hanh", 12, "Ctrl+8", "Mở rộng", 2),
    ("nha_cung_cap", "Nhà cung cấp", "🏭", "nha_cung_cap", 13, None, "Mở rộng", 2),
    ("tra_gop", "Trả góp", "💳", "tra_gop", 14, None, "Mở rộng", 2),
    
    # Hậu mãi
    ("bao_duong", "Bảo dưỡng", "🔧", "bao_duong", 20, None, "Hậu mãi", 3),
    ("cuu_ho", "Cứu hộ", "🚨", "cuu_ho", 21, None, "Hậu mãi", 3),
    
    # Marketing & Khiếu nại
    ("marketing", "Marketing", "📢", "marketing", 30, None, "Marketing", 4),
    ("khieu_nai", "Khiếu nại", "⚠️", "khieu_nai", 31, None, "Marketing", 4),
    
    # Báo cáo & Hệ thống
    ("bao_cao", "Báo cáo", "📈", "bao_cao", 40, "Ctrl+9", "Hệ thống", 5),
    ("he_thong", "Cài đặt", "⚙️", "he_thong", 41, None, "Hệ thống", 5),
]


def setup_navigation_registry() -> NavigationRegistry:
    """Set up the navigation registry with all sidebar modules.
    
    Returns:
        Configured NavigationRegistry instance.
    """
    for module_id, label, icon, perm_module, order, shortcut, group_name, group_order in SIDEBAR_MODULES:
        register_module(
            module_id=module_id,
            label=label,
            icon=icon,
            permission_module=perm_module,
            order=order,
            shortcut=shortcut,
            group_name=group_name,
            group_order=group_order,
        )
    
    # Set dashboard as default
    navigation_registry.set_default("dashboard")
    
    return navigation_registry


def get_sidebar_items(
    vai_tro_id: int,
    permission_service: PermissionService = None,
) -> list[NavigationGroup]:
    """Get sidebar navigation items filtered by user role.
    
    Args:
        vai_tro_id: Role ID to filter by.
        permission_service: Optional PermissionService instance.
                          If None, creates a new one.
    
    Returns:
        List of NavigationGroups with visible items.
    """
    if permission_service is None:
        permission_service = PermissionService()
    
    def has_view_permission(role_id: int, module: str, action: str = "view") -> bool:
        return permission_service.has_permission(role_id, module, action)
    
    # Ensure registry is set up
    if not navigation_registry._items:
        setup_navigation_registry()
    
    # Get filtered items
    visible_items = navigation_registry.get_items_for_role(
        vai_tro_id,
        has_view_permission,
    )
    
    # Group visible items
    visible_module_ids = {item.module_id for item in visible_items}
    
    # Rebuild groups with only visible items
    result_groups = []
    for group in navigation_registry.get_groups():
        group_items = [item for item in group.items if item.module_id in visible_module_ids]
        if group_items:
            result_groups.append(
                NavigationGroup(
                    name=group.name,
                    items=group_items,
                    order=group.order,
                )
            )
    
    return result_groups


def get_sidebar_items_flat(
    vai_tro_id: int,
    permission_service: PermissionService = None,
) -> list[NavigationItem]:
    """Get sidebar items as flat list (not grouped).
    
    Args:
        vai_tro_id: Role ID to filter by.
        permission_service: Optional PermissionService instance.
    
    Returns:
        Flat list of visible NavigationItems sorted by order.
    """
    groups = get_sidebar_items(vai_tro_id, permission_service)
    items = []
    for group in groups:
        items.extend(group.items)
    return items


# Initialize registry on module load
setup_navigation_registry()
