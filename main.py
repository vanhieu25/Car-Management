"""Main entry point for Car Management application.

Integrates:
- Login screen (S-AUTH-01) with session management
- MainWindow with TopBar, Sidebar, ContentArea, StatusBar
- Change password dialog for forced password changes (BR-NV-08)
"""

import sys

from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.infrastructure.database.connection import get_connection
from app.presentation.screens.login_screen import LoginScreen
from app.presentation.screens.change_password_dialog import ChangePasswordDialog
from app.presentation.screens.main_window import MainWindow
from app.application.services.session import SessionManager, CurrentSession


def run_migrations():
    """Run database migrations if needed."""
    try:
        runner = MigrationRunner()
        runner.run_pending()
    except Exception as e:
        print(f"Migration warning: {e}")


class Application(QApplication):
    """Main application class managing login flow."""
    
    def __init__(self, argv):
        super().__init__(argv)
        self._main_window = None
        self._login_screen = None
        self._change_password_dialog = None
        self._current_user_id = None
        self._session_manager = SessionManager()
        
        # Run migrations on startup
        run_migrations()
    
    def start(self) -> int:
        """Start the application with login screen."""
        self._show_login()
        return self.exec()
    
    def _show_login(self):
        """Show login screen."""
        self._login_screen = LoginScreen()
        self._login_screen.login_successful.connect(self._on_login_successful)
        self._login_screen.change_password_requested.connect(self._on_change_password_requested)
        self._login_screen.exec()
    
    def _on_login_successful(self, session: CurrentSession):
        """Handle successful login.
        
        Args:
            session: CurrentSession with user info.
        """
        self._login_screen = None
        
        # Check if password change is required
        if session.must_change_password:
            self._show_change_password_dialog(session.user_id)
        else:
            self._show_main_window(session)
    
    def _on_change_password_requested(self, user_id: int):
        """Handle forced password change request.
        
        Args:
            user_id: User ID needing password change.
        """
        self._current_user_id = user_id
        self._show_change_password_dialog(user_id)
    
    def _show_change_password_dialog(self, user_id: int):
        """Show change password dialog.
        
        Args:
            user_id: User ID for password change.
        """
        self._change_password_dialog = ChangePasswordDialog(
            user_id=user_id,
            require_old_password=False,
            force_change=True,
        )
        self._change_password_dialog.password_changed.connect(
            lambda: self._on_password_changed(user_id)
        )
        self._change_password_dialog.cancelled.connect(
            self._on_password_change_cancelled
        )
        self._change_password_dialog.exec()
    
    def _on_password_changed(self, user_id: int):
        """Handle successful password change.
        
        Args:
            user_id: User ID that changed password.
        """
        self._change_password_dialog = None
        
        # Re-fetch session and show main window
        # For simplicity, create a new session from stored user info
        from app.application.services.auth_service import AuthService
        from app.infrastructure.database.connection import get_connection
        
        conn = get_connection()
        auth_service = AuthService(conn)
        
        # Get user info to recreate session
        from app.infrastructure.repositories.nhan_vien_repository import NhanVienRepository
        repo = NhanVienRepository(conn)
        nhan_vien = repo.find_by_id(user_id)
        
        if nhan_vien:
            session = self._session_manager.login(
                user_id=nhan_vien.id,
                username=nhan_vien.username,
                ho_ten=nhan_vien.ho_ten,
                vai_tro_id=nhan_vien.vai_tro_id,
                vai_tro_ma=nhan_vien.vai_tro_ma,
                must_change_password=False,  # Just changed
            )
            self._show_main_window(session)
    
    def _on_password_change_cancelled(self):
        """Handle password change cancellation."""
        # Cannot cancel forced password change
        # Keep dialog open - this should not happen in normal flow
        pass
    
    def _show_main_window(self, session: CurrentSession = None):
        """Show main application window.
        
        Args:
            session: CurrentSession instance. If None, uses current session.
        """
        if session is None:
            session = self._session_manager.current_session
        
        self._main_window = MainWindow(session)
        
        # Set database connection
        conn = get_connection()
        self._main_window.set_db_connection(conn)
        
        # Connect logout signal
        self._main_window.logout_requested.connect(self._on_logout)
        
        # Connect module change signal
        self._main_window.module_changed.connect(self._on_module_changed)
        
        self._main_window.show()
    
    def _on_logout(self):
        """Handle user logout."""
        if self._main_window:
            self._main_window.close()
            self._main_window = None
        
        # Clear session
        self._session_manager.logout()
        
        # Show login again
        self._show_login()
    
    def _on_module_changed(self, module_id: str):
        """Handle module change from sidebar.
        
        Args:
            module_id: New active module ID.
        """
        # Module change is handled within MainWindow
        pass


def main() -> int:
    """Application entry point."""
    app = Application(sys.argv)
    return app.start()


if __name__ == "__main__":
    sys.exit(main())