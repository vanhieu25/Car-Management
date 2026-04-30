"""Main entry point for Car Management application.

Integrates:
- Login screen (S-AUTH-01) with session management
- Main window placeholder for post-login
- Change password dialog for forced password changes (BR-NV-08)
"""

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.presentation.screens.login_screen import LoginScreen
from app.presentation.screens.change_password_dialog import ChangePasswordDialog


def run_migrations():
    """Run database migrations if needed."""
    try:
        runner = MigrationRunner()
        runner.run_pending()
    except Exception as e:
        print(f"Migration warning: {e}")


class MainWindow(QMainWindow):
    """Main application window after login."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Management - Dashboard")
        self.setMinimumSize(1280, 720)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup main window UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("Chào mừng đã đăng nhập!", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #1C1C1E;")
        layout.addWidget(title)
        
        subtitle = QLabel("Car Management System v1.0.0", self)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #8E8E93; margin-top: 10px;")
        layout.addWidget(subtitle)


class Application(QApplication):
    """Main application class managing login flow."""
    
    def __init__(self, argv):
        super().__init__(argv)
        self._main_window = None
        self._login_screen = None
        self._change_password_dialog = None
        self._current_user_id = None
        
        # Run migrations on startup
        run_migrations()
    
    def start(self):
        """Start the application with login screen."""
        self._show_login()
        return self.exec()
    
    def _show_login(self):
        """Show login screen."""
        self._login_screen = LoginScreen()
        self._login_screen.login_successful.connect(self._on_login_successful)
        self._login_screen.change_password_requested.connect(self._on_change_password_requested)
        self._login_screen.exec()
    
    def _on_login_successful(self):
        """Handle successful login."""
        self._login_screen = None
        self._show_main_window()
    
    def _on_change_password_requested(self, user_id: int):
        """Handle forced password change request."""
        self._current_user_id = user_id
        self._change_password_dialog = ChangePasswordDialog(
            user_id=user_id,
            require_old_password=False,
            force_change=True,
        )
        self._change_password_dialog.password_changed.connect(self._on_password_changed)
        self._change_password_dialog.cancelled.connect(self._on_password_change_cancelled)
        self._change_password_dialog.exec()
    
    def _on_password_changed(self):
        """Handle successful password change."""
        self._change_password_dialog = None
        # Now show the main window
        self._show_main_window()
    
    def _on_password_change_cancelled(self):
        """Handle password change cancellation."""
        # User tried to cancel but password change is required
        # Show error and keep dialog open
        pass
    
    def _show_main_window(self):
        """Show main application window."""
        self._main_window = MainWindow()
        self._main_window.show()


def main() -> int:
    """Application entry point."""
    app = Application(sys.argv)
    return app.start()


if __name__ == "__main__":
    sys.exit(main())
