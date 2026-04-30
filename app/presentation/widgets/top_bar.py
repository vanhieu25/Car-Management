"""TopBar widget - displays dealer info and user dropdown.

Shows:
- Logo + dealer name (left)
- User dropdown menu with: Profile / Change Password / Logout (right)
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMenu
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QIcon


class TopBar(QWidget):
    """Top navigation bar widget.
    
    Signals:
        profile_clicked: User clicked profile menu item
        change_password_clicked: User clicked change password menu item
        logout_clicked: User clicked logout menu item
    """
    
    profile_clicked = pyqtSignal()
    change_password_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize TopBar widget."""
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        self.setFixedHeight(44)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 0, 16, 0)
        main_layout.setSpacing(12)
        
        # Left side - Logo + Dealer name
        left_layout = QHBoxLayout()
        left_layout.setSpacing(8)
        
        # Logo placeholder
        self.logo_label = QLabel("🚗")
        self.logo_label.setStyleSheet("font-size: 24px;")
        left_layout.addWidget(self.logo_label)
        
        # Dealer name
        self.dealer_name_label = QLabel("Đại lý xe hơi")
        self.dealer_name_label.setStyleSheet(
            "color: #ffffff; font-size: 15px; font-weight: 600;"
        )
        left_layout.addWidget(self.dealer_name_label)
        
        left_layout.addStretch()
        
        # Right side - User dropdown
        right_layout = QHBoxLayout()
        right_layout.setSpacing(8)
        
        # User info
        self.user_label = QLabel()
        self.user_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        right_layout.addWidget(self.user_label)
        
        # Dropdown button
        self.menu_btn = QPushButton("▼")
        self.menu_btn.setFixedWidth(24)
        self.menu_btn.setStyleSheet(
            "background: transparent; color: #ffffff; border: none; font-size: 10px;"
        )
        right_layout.addWidget(self.menu_btn)
        
        # Create menu
        self.user_menu = QMenu(self)
        self.user_menu.addAction("👤 Hồ sơ", self._on_profile)
        self.user_menu.addAction("🔑 Đổi mật khẩu", self._on_change_password)
        self.user_menu.addSeparator()
        self.user_menu.addAction("🚪 Đăng xuất", self._on_logout)
        
        self.menu_btn.setMenu(self.user_menu)
        
        main_layout.addLayout(left_layout, stretch=0)
        main_layout.addStretch()
        main_layout.addLayout(right_layout, stretch=0)
        
        # Apply stylesheet
        self.setStyleSheet(
            "background-color: #000000;"
        )
    
    def _setup_connections(self):
        """Set up signal connections."""
        pass  # Menu actions connected via lambda in _setup_ui
    
    def _on_profile(self):
        """Handle profile menu action."""
        self.profile_clicked.emit()
    
    def _on_change_password(self):
        """Handle change password menu action."""
        self.change_password_clicked.emit()
    
    def _on_logout(self):
        """Handle logout menu action."""
        self.logout_clicked.emit()
    
    def set_dealer_name(self, name: str):
        """Set the dealer name displayed in the top bar.
        
        Args:
            name: Dealer name string.
        """
        self.dealer_name_label.setText(name)
    
    def set_user_info(self, username: str, ho_ten: str = None, vai_tro: str = None):
        """Set user information displayed in the top bar.
        
        Args:
            username: User's username.
            ho_ten: User's full name (optional).
            vai_tro: User's role name (optional).
        """
        display_text = ho_ten if ho_ten else username
        if vai_tro:
            display_text += f" ({vai_tro})"
        self.user_label.setText(display_text)
    
    def set_logo(self, logo_path: str = None):
        """Set the logo image.
        
        Args:
            logo_path: Path to logo image file. If None, uses emoji placeholder.
        """
        if logo_path:
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                self.logo_label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
                return
        
        # Reset to emoji
        self.logo_label.setText("🚗")
        self.logo_label.setStyleSheet("font-size: 24px;")