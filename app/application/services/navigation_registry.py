"""Navigation registry - maps module IDs to screen classes.

Allows dynamic screen loading based on sidebar navigation.
Each module registers its main screen class.
"""

from dataclasses import dataclass
from typing import Optional, Type, Callable
from enum import Enum


class ModuleId(Enum):
    """Module identifier constants."""
    DASHBOARD = "dashboard"
    XE = "xe"
    KHACH_HANG = "khach_hang"
    NHAN_VIEN = "nhan_vien"
    HOP_DONG = "hop_dong"
    KHO = "kho"
    PHU_KIEN = "phu_kien"
    KHUYEN_MAI = "khuyen_mai"
    BAO_HANH = "bao_hanh"
    NHA_CUNG_CAP = "nha_cung_cap"
    TRA_GOP = "tra_gop"
    BAO_DUONG = "bao_duong"
    CUU_HO = "cuu_ho"
    MARKETING = "marketing"
    KHIEU_NAI = "khieu_nai"
    BAO_CAO = "bao_cao"
    HE_THONG = "he_thong"


@dataclass
class NavigationItem:
    """Represents a navigation menu item."""
    module_id: str
    label: str
    icon: str  # Emoji or icon name
    screen_class: Optional[Type] = None  # QWidget class for this screen
    permission_module: str  # Maps to permission_service module
    parent: Optional[str] = None  # Parent module_id for nested items
    order: int = 0  # Display order
    shortcut: Optional[str] = None  # Keyboard shortcut e.g. "Ctrl+1"


@dataclass
class NavigationGroup:
    """Groups of navigation items."""
    name: str
    items: list[NavigationItem]
    order: int = 0


class NavigationRegistry:
    """Registry for all navigation items and their screens.
    
    Manages:
    - Module registration
    - Screen class mapping
    - Sidebar filtering by role
    """

    def __init__(self):
        """Initialize empty registry."""
        self._items: dict[str, NavigationItem] = {}
        self._groups: list[NavigationGroup] = []
        self._default_module: Optional[str] = None

    def register(
        self,
        module_id: str,
        label: str,
        icon: str,
        screen_class: Type = None,
        permission_module: str = None,
        parent: str = None,
        order: int = 0,
        shortcut: str = None,
        group_order: int = 0,
        group_name: str = "Chung",
    ) -> "NavigationRegistry":
        """Register a navigation item.
        
        Args:
            module_id: Unique module identifier.
            label: Display label for sidebar.
            icon: Icon emoji or name.
            screen_class: QWidget class for this screen.
            permission_module: Module name for permission checking.
            parent: Parent module_id for nested items.
            order: Display order within group.
            shortcut: Keyboard shortcut.
            group_order: Order of the group.
            group_name: Name of the navigation group.
            
        Returns:
            Self for chaining.
        """
        item = NavigationItem(
            module_id=module_id,
            label=label,
            icon=icon,
            screen_class=screen_class,
            permission_module=permission_module or module_id,
            parent=parent,
            order=order,
            shortcut=shortcut,
        )

        if module_id in self._items:
            # Update existing
            self._items[module_id] = item
        else:
            self._items[module_id] = item

        # Add to group
        self._add_to_group(group_name, item, group_order)

        return self

    def _add_to_group(self, group_name: str, item: NavigationItem, order: int):
        """Add item to appropriate group."""
        for group in self._groups:
            if group.name == group_name:
                # Remove if already exists
                group.items = [i for i in group.items if i.module_id != item.module_id]
                group.items.append(item)
                group.items.sort(key=lambda x: x.order)
                return

        # Create new group
        group = NavigationGroup(
            name=group_name,
            items=[item],
            order=order,
        )
        self._groups.append(group)
        self._groups.sort(key=lambda x: x.order)

    def set_default(self, module_id: str) -> "NavigationRegistry":
        """Set the default module to show on startup."""
        self._default_module = module_id
        return self

    def get_item(self, module_id: str) -> Optional[NavigationItem]:
        """Get navigation item by module_id."""
        return self._items.get(module_id)

    def get_screen_class(self, module_id: str) -> Optional[Type]:
        """Get screen class for a module."""
        item = self._items.get(module_id)
        return item.screen_class if item else None

    def get_items_for_role(
        self,
        vai_tro_id: int,
        permission_checker: Callable[[int, str, str], bool],
    ) -> list[NavigationItem]:
        """Get navigation items visible for a role.
        
        Args:
            vai_tro_id: Role ID to filter by.
            permission_checker: Function(role_id, module, action) -> bool.
            
        Returns:
            List of visible navigation items.
        """
        visible_items = []
        for item in self._items.values():
            # Check if user has view permission for this module
            if permission_checker(vai_tro_id, item.permission_module, "view"):
                visible_items.append(item)
        return visible_items

    def get_all_items(self) -> list[NavigationItem]:
        """Get all registered navigation items."""
        return list(self._items.values())

    def get_groups(self) -> list[NavigationGroup]:
        """Get all navigation groups with their items."""
        return self._groups

    def get_default_module(self) -> Optional[str]:
        """Get default module ID."""
        return self._default_module


# Global registry instance
navigation_registry = NavigationRegistry()


def register_module(
    module_id: str,
    label: str,
    icon: str,
    screen_class: Type = None,
    permission_module: str = None,
    parent: str = None,
    order: int = 0,
    shortcut: str = None,
    group_order: int = 0,
    group_name: str = "Chung",
):
    """Convenience function to register a module."""
    navigation_registry.register(
        module_id=module_id,
        label=label,
        icon=icon,
        screen_class=screen_class,
        permission_module=permission_module,
        parent=parent,
        order=order,
        shortcut=shortcut,
        group_order=group_order,
        group_name=group_name,
    )


def get_navigation_registry() -> NavigationRegistry:
    """Get the global navigation registry."""
    return navigation_registry
