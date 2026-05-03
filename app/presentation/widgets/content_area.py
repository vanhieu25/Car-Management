"""ContentArea widget - manages screen content with QStackedWidget.

Handles:
- Screen registration and switching
- Screen instance management
- Loading indicators
- Error states

Signals:
    screen_changed(module_id: str)
"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class ContentArea(QStackedWidget):
    """Content area widget with stacked screens.
    
    Manages multiple screens and provides switching capability.
    
    Signals:
        screen_changed(module_id: str): Emitted when screen changes.
    """
    
    screen_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize ContentArea widget."""
        super().__init__(parent)
        self._screens: dict[str, QWidget] = {}
        self._current_module: str = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Set up the stacked widget
        self.setStyleSheet("background-color: #ffffff;")
    
    def register_screen(self, module_id: str, screen: QWidget) -> bool:
        """Register a screen widget for a module.
        
        Args:
            module_id: Unique module identifier.
            screen: QWidget instance for the screen.
            
        Returns:
            True if registered, False if module already exists.
        """
        if module_id in self._screens:
            return False
        
        # Add to stacked widget
        index = self.addWidget(screen)
        self._screens[module_id] = screen
        
        return True
    
    def unregister_screen(self, module_id: str) -> bool:
        """Unregister a screen.
        
        Args:
            module_id: Module ID to unregister.
            
        Returns:
            True if unregistered, False if not found.
        """
        if module_id not in self._screens:
            return False
        
        # Remove from stacked widget
        screen = self._screens.pop(module_id)
        self.removeWidget(screen)
        
        return True
    
    def show_screen(self, module_id: str) -> bool:
        """Show a registered screen.
        
        Args:
            module_id: Module ID to show.
            
        Returns:
            True if screen found and shown, False otherwise.
        """
        if module_id not in self._screens:
            return False
        
        self.setCurrentWidget(self._screens[module_id])
        self._current_module = module_id
        self.screen_changed.emit(module_id)
        
        return True
    
    def get_screen(self, module_id: str) -> QWidget:
        """Get a registered screen widget.
        
        Args:
            module_id: Module ID.
            
        Returns:
            Screen widget or None if not registered.
        """
        return self._screens.get(module_id)
    
    def get_current_module(self) -> str:
        """Get the currently displayed module ID.
        
        Returns:
            Current module ID or None.
        """
        return self._current_module
    
    def has_screen(self, module_id: str) -> bool:
        """Check if a screen is registered.
        
        Args:
            module_id: Module ID to check.
            
        Returns:
            True if registered, False otherwise.
        """
        return module_id in self._screens
    
    def clear(self):
        """Clear all registered screens."""
        for module_id in list(self._screens.keys()):
            self.unregister_screen(module_id)
        self._current_module = None


class LoadingScreen(QWidget):
    """Placeholder loading screen."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel("Đang tải...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #86868b; font-size: 16px;")
        layout.addWidget(self.label)
        
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setFixedWidth(200)
        self.progress.setStyleSheet(
            "QProgressBar { border: none; background: transparent; }"
            "QProgressBar::chunk { background: #0066cc; }"
        )
        layout.addWidget(self.progress)


class ErrorScreen(QWidget):
    """Placeholder error screen."""
    
    def __init__(self, message: str = "Đã xảy ra lỗi", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("⚠️")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.icon_label)
        
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: #ff3b30; font-size: 16px;")
        layout.addWidget(self.message_label)


class PermissionDeniedScreen(QWidget):
    """Placeholder permission denied screen."""
    
    def __init__(self, message: str = "Bạn không có quyền truy cập", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("🔒")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.icon_label)
        
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: #1d1d1f; font-size: 16px;")
        layout.addWidget(self.message_label)
        
        self.sub_message_label = QLabel("Liên hệ quản trị viên để được cấp quyền.")
        self.sub_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_message_label.setStyleSheet("color: #86868b; font-size: 14px;")
        layout.addWidget(self.sub_message_label)


class EmptyScreen(QWidget):
    """Placeholder empty screen."""
    
    def __init__(self, module_name: str = "Module", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("📋")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(self.icon_label)
        
        self.name_label = QLabel(f"{module_name}")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: #1d1d1f; font-size: 20px; font-weight: 600;")
        layout.addWidget(self.name_label)
        
        self.sub_label = QLabel("Chức năng đang được phát triển")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("color: #86868b; font-size: 14px;")
        layout.addWidget(self.sub_label)