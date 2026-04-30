"""Sidebar widget - navigation menu with module list.

Displays:
- List of navigation modules with icon + label
- Active item highlighted with #f5f5f7
- Grouped by category
- Emits signal when item clicked

Signals:
    module_selected(module_id: str)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QFont, QPainter, QPainterPath


class SidebarItem(QPushButton):
    """A single sidebar navigation item.
    
    Displays icon + label, highlights on hover/active.
    """
    
    def __init__(self, module_id: str, label: str, icon: str = "", parent=None):
        """Initialize sidebar item.
        
        Args:
            module_id: Unique module identifier.
            label: Display text.
            icon: Icon emoji or text.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.module_id = module_id
        self._icon = icon
        self._label = label
        
        self.setText(f"{icon}  {label}" if icon else label)
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Styles
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1d1d1f;
                border: none;
                text-align: left;
                padding-left: 16px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            QPushButton:hover {
                background-color: #e8e8ed;
            }
        """)
        
        self.clicked.connect(lambda: self._emit_module_selected())
    
    def _emit_module_selected(self):
        """Emit module selected signal."""
        self.parent().item_clicked(self.module_id) if self.parent() else None


class SidebarGroup(QWidget):
    """A group of sidebar items with a header label.
    
    Displays a group header and list of items.
    """
    
    def __init__(self, group_name: str, parent=None):
        """Initialize sidebar group.
        
        Args:
            group_name: Name of the group (header).
            parent: Parent widget.
        """
        super().__init__(parent)
        self.group_name = group_name
        self._items: list[SidebarItem] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 8)
        layout.setSpacing(2)
        
        # Group header
        self.header_label = QLabel(self.group_name.upper())
        self.header_label.setStyleSheet(
            "color: #86868b; font-size: 11px; font-weight: 600; "
            "letter-spacing: 0.5px; padding-left: 16px; padding-bottom: 4px;"
        )
        layout.addWidget(self.header_label)
        
        # Items container
        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(0)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.items_layout)
    
    def add_item(self, item: SidebarItem):
        """Add an item to this group.
        
        Args:
            item: SidebarItem to add.
        """
        self._items.append(item)
        self.items_layout.addWidget(item)
    
    def set_active(self, module_id: str):
        """Set the active item in this group.
        
        Args:
            module_id: Module ID to set as active.
        """
        for item in self._items:
            if item.module_id == module_id:
                item.setStyleSheet("""
                    QPushButton {
                        background-color: #f5f5f7;
                        color: #0066cc;
                        border: none;
                        text-align: left;
                        padding-left: 16px;
                        font-size: 14px;
                        font-weight: 500;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    }
                    QPushButton:hover {
                        background-color: #e8e8ed;
                    }
                """)
            else:
                item.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #1d1d1f;
                        border: none;
                        text-align: left;
                        padding-left: 16px;
                        font-size: 14px;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    }
                    QPushButton:hover {
                        background-color: #e8e8ed;
                    }
                """)


class Sidebar(QWidget):
    """Sidebar navigation widget.
    
    Displays grouped list of navigation modules.
    Filters by user role and highlights active item.
    
    Signals:
        module_selected(module_id: str): Emitted when a module is selected.
    """
    
    module_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize Sidebar widget."""
        super().__init__(parent)
        self._active_module: str = None
        self._groups: list[SidebarGroup] = []
        self._items: dict[str, SidebarItem] = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        self.setFixedWidth(240)
        self.setStyleSheet("background-color: #f5f5f7;")
        
        # Main scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        # Scroll content widget
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        self._scroll_content = scroll_content
        self._scroll_layout = scroll_layout
    
    def item_clicked(self, module_id: str):
        """Handle item click from SidebarItem.
        
        Args:
            module_id: Module ID that was clicked.
        """
        self.set_active(module_id)
        self.module_selected.emit(module_id)
    
    def clear(self):
        """Clear all sidebar items."""
        # Remove all group widgets
        for group in self._groups:
            group.deleteLater()
        
        self._groups.clear()
        self._items.clear()
        self._active_module = None
        
        # Remove from layout
        while self._scroll_layout.count() > 1:  # Keep the stretch at end
            item = self._scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_group(self, group_name: str) -> SidebarGroup:
        """Add a new group to the sidebar.
        
        Args:
            group_name: Name of the group.
            
        Returns:
            SidebarGroup instance.
        """
        group = SidebarGroup(group_name, self._scroll_content)
        
        # Insert before the stretch
        self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, group)
        
        self._groups.append(group)
        return group
    
    def add_item(self, module_id: str, label: str, icon: str = "", group: str = "Chung"):
        """Add an item to the sidebar.
        
        Args:
            module_id: Unique module identifier.
            label: Display text.
            icon: Icon emoji.
            group: Group name to add item to.
        """
        # Find or create group
        sidebar_group = None
        for g in self._groups:
            if g.group_name == group:
                sidebar_group = g
                break
        
        if sidebar_group is None:
            sidebar_group = self.add_group(group)
        
        # Create and add item
        item = SidebarItem(module_id, label, icon)
        item.move(0, 0)  # Positioned by layout
        
        sidebar_group.add_item(item)
        self._items[module_id] = item
    
    def set_active(self, module_id: str):
        """Set the active module.
        
        Args:
            module_id: Module ID to set as active.
        """
        self._active_module = module_id
        
        # Update all groups
        for group in self._groups:
            group.set_active(module_id)
    
    def get_active(self) -> str:
        """Get the currently active module ID.
        
        Returns:
            Active module ID or None.
        """
        return self._active_module
    
    def update_items(
        self,
        items: list[tuple[str, str, str, str]],
        active_module: str = None
    ):
        """Update all sidebar items.
        
        Args:
            items: List of (module_id, label, icon, group) tuples.
            active_module: Module ID to set as active.
        """
        self.clear()
        
        # Add items
        for module_id, label, icon, group in items:
            self.add_item(module_id, label, icon, group)
        
        # Set active
        if active_module:
            self.set_active(active_module)
        elif items:
            self.set_active(items[0][0])