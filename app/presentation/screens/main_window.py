"""MainWindow - primary application window with Apple-style layout.

Layout structure:
┌───────────────────────────────────────────────────────────────┐
│  TopBar (44px)    | Logo | Dealer Name     | User · Menu    │
├──────────────┬────────────────────────────────────────────────┤
│              │                                                │
│  Sidebar     │            ContentArea                        │
│  (240px)     │         (QStackedWidget)                      │
│              │                                                │
├──────────────┴────────────────────────────────────────────────┤
│  StatusBar (28px) | User · Time · Version · DB Status        │
└───────────────────────────────────────────────────────────────┘

Signals:
    logout_requested: User requested logout
    module_changed(module_id: str): Active module changed
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QKeySequence

from app.presentation.widgets.top_bar import TopBar
from app.presentation.widgets.sidebar import Sidebar
from app.presentation.widgets.content_area import ContentArea, EmptyScreen
from app.presentation.widgets.status_bar import StatusBar

from app.application.services.session import SessionManager, CurrentSession
from app.application.services.system_settings_service import SystemSettingsService
from app.application.services.sidebar_service import get_sidebar_items_flat, get_sidebar_items
from app.application.services.audit_log_service import AuditLogService
from app.presentation.screens.audit_log_screen import AuditLogScreen
from app.presentation.screens.system_settings_screen import SystemSettingsScreen
from app.presentation.screens.vehicle_list_screen import VehicleListScreen
from app.presentation.screens.vehicle_form_dialog import VehicleFormDialog
from app.presentation.screens.vehicle_detail_screen import VehicleDetailScreen


class MainWindow(QMainWindow):
    """Main application window.
    
    Contains TopBar, Sidebar, ContentArea, and StatusBar.
    Manages screen navigation and user session.
    
    Signals:
        logout_requested: Emitted when user clicks logout.
        module_changed(module_id: str): Emitted when active module changes.
    """
    
    logout_requested = pyqtSignal()
    module_changed = pyqtSignal(str)
    
    def __init__(self, session: CurrentSession = None, parent=None):
        """Initialize MainWindow.
        
        Args:
            session: CurrentSession instance with user info.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._session = session
        self._db_conn = None
        self._settings_service = None
        self._navigation_registered = False
        
        self._setup_ui()
        self._setup_connections()
        self._apply_styles()
        self._load_user_session()
        
        # Set initial size
        self.setMinimumSize(1280, 720)
        self.resize(1400, 800)
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # TopBar
        self.top_bar = TopBar()
        main_layout.addWidget(self.top_bar)
        
        # Content area with sidebar
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        content_layout.addWidget(self.sidebar)
        
        # ContentArea
        self.content_area = ContentArea()
        content_layout.addWidget(self.content_area, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # StatusBar
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)
        
        # Window title
        self.setWindowTitle("Car Management")
    
    def _setup_connections(self):
        """Set up signal connections."""
        # Sidebar -> ContentArea
        self.sidebar.module_selected.connect(self._on_module_selected)
        
        # TopBar signals
        self.top_bar.logout_clicked.connect(self._on_logout_requested)
        self.top_bar.change_password_clicked.connect(self._on_change_password_requested)
        self.top_bar.profile_clicked.connect(self._on_profile_requested)
    
    def _apply_styles(self):
        """Apply Apple-style stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
        """)
    
    def _load_user_session(self):
        """Load user session and configure UI."""
        if self._session:
            # Set user info in top bar
            self.top_bar.set_user_info(
                username=self._session.username,
                ho_ten=self._session.ho_ten,
                vai_tro=self._session.vai_tro_ma,
            )
            
            # Set status bar user
            self.status_bar.set_user(
                self._session.username,
                self._session.vai_tro_ma,
            )
            
            # Load sidebar items based on role
            self._load_sidebar_items()
    
    def _load_sidebar_items(self):
        """Load and display sidebar items based on user role."""
        if not self._session:
            return
        
        # Get sidebar items for this role
        items = get_sidebar_items_flat(self._session.vai_tro_id)
        
        # Convert to format for sidebar
        sidebar_data = [
            (item.module_id, item.label, item.icon, item.permission_module)
            for item in items
        ]
        
        # Get groups for proper organization
        groups = get_sidebar_items(self._session.vai_tro_id)
        
        # Clear and rebuild sidebar
        self.sidebar.clear()
        
        # Add items grouped
        for group in groups:
            for item in group.items:
                self.sidebar.add_item(
                    module_id=item.module_id,
                    label=item.label,
                    icon=item.icon,
                    group=group.name,
                )
        
        # Set default active
        if items:
            default_module = items[0].module_id
            self.sidebar.set_active(default_module)
            self._show_placeholder_or_default(default_module)
    
    def _show_placeholder_or_default(self, module_id: str):
        """Show placeholder or navigate to module."""
        screen = self._get_module_screen(module_id)
        self.content_area.register_screen(module_id, screen)
        self.content_area.show_screen(module_id)
    
    def _on_module_selected(self, module_id: str):
        """"Handle module selection from sidebar.
        
        Args:
            module_id: Selected module ID.
        """
        self.module_changed.emit(module_id)
        
        # Load actual screen for known modules, otherwise show placeholder
        if not self.content_area.has_screen(module_id):
            screen = self._get_module_screen(module_id)
            self.content_area.register_screen(module_id, screen)
        
        self.content_area.show_screen(module_id)
    
    def _get_module_screen(self, module_id: str) -> QWidget:
        """Get or create the screen widget for a module.
        
        Args:
            module_id: Module identifier.
            
        Returns:
            QWidget screen instance.
        """
        if module_id == "audit_log":
            # S-SYS-01: Audit log viewer
            if self._db_conn and self._session:
                return AuditLogScreen(self._db_conn, self._session)
        elif module_id == "he_thong":
            # S-CFG-01: System settings
            if self._db_conn and self._session:
                return SystemSettingsScreen(self._db_conn, self._session)
        elif module_id == "xe":
            # S-XE-01: Vehicle list
            if self._db_conn and self._session:
                screen = VehicleListScreen(self._db_conn, self._session)
                # Connect signals
                screen.add_vehicle_clicked.connect(lambda: self._show_vehicle_form(None))
                screen.edit_vehicle_clicked.connect(self._show_vehicle_form)
                screen.view_vehicle_clicked.connect(self._show_vehicle_detail)
                return screen
        
        # Default: placeholder
        return EmptyScreen(module_name=module_id.replace("_", " ").title())
    
    def _show_vehicle_form(self, xe_id: int = None):
        """Show vehicle add/edit form dialog.
        
        Args:
            xe_id: Vehicle ID to edit, or None for add new.
        """
        from app.presentation.screens.vehicle_form_dialog import VehicleFormDialog
        from app.domain.entities import Xe
        
        xe = None
        if xe_id:
            xe = Xe()
            xe.id = xe_id
        
        dialog = VehicleFormDialog(self._db_conn, self._session, xe, self)
        dialog.saved.connect(self._on_vehicle_saved)
        dialog.exec()
    
    def _show_vehicle_detail(self, xe_id: int):
        """Show vehicle detail screen.
        
        Args:
            xe_id: Vehicle ID to display.
        """
        from app.presentation.screens.vehicle_detail_screen import VehicleDetailScreen
        
        screen = VehicleDetailScreen(self._db_conn, self._session, xe_id, self)
        screen.edit_clicked.connect(self._show_vehicle_form)
        screen.close_clicked.connect(lambda: self.navigate_to("xe"))
        
        # Replace current screen with detail
        self.content_area.register_screen("xe_detail", screen)
        self.content_area.show_screen("xe_detail")
    
    def _on_vehicle_saved(self):
        """Handle vehicle saved signal - refresh list."""
        # Refresh vehicle list if visible
        if self.content_area.has_screen("xe"):
            screen = self.content_area.get_screen("xe")
            if hasattr(screen, 'refresh'):
                screen.refresh()
    
    def _on_logout_requested(self):
        """Handle logout request."""
        self.logout_requested.emit()
    
    def _on_change_password_requested(self):
        """Handle change password request."""
        # Emit signal or show dialog
        self.module_changed.emit("change_password")
    
    def _on_profile_requested(self):
        """Handle profile request."""
        # Emit signal or show dialog
        self.module_changed.emit("profile")
    
    def set_db_connection(self, conn):
        """Set database connection for services.
        
        Args:
            conn: sqlite3.Connection instance.
        """
        self._db_conn = conn
        self._settings_service = SystemSettingsService(conn)
        
        # Load settings
        settings = self._settings_service.load_settings()
        
        # Update top bar with dealer info
        self.top_bar.set_dealer_name(settings.ten_dai_ly)
        
        # Update status bar version
        self.status_bar.set_version(f"v{settings.version}")
        
        # Check DB connection
        self._check_db_connection()
    
    def _check_db_connection(self):
        """Check database connection and update status."""
        if self._db_conn:
            try:
                cursor = self._db_conn.execute("SELECT 1")
                cursor.fetchone()
                self.status_bar.set_db_status(True)
            except Exception as e:
                self.status_bar.set_db_status(False, f"● Lỗi DB")
        else:
            self.status_bar.set_db_status(False, "● Chưa kết nối")
    
    def set_session(self, session: CurrentSession):
        """Set the current session.
        
        Args:
            session: CurrentSession instance.
        """
        self._session = session
        self._load_user_session()
    
    def get_session(self) -> CurrentSession:
        """Get the current session.
        
        Returns:
            CurrentSession instance or None.
        """
        return self._session
    
    def register_screen(self, module_id: str, screen: QWidget):
        """Register a screen for a module.
        
        Args:
            module_id: Module identifier.
            screen: QWidget screen instance.
        """
        self.content_area.register_screen(module_id, screen)
    
    def navigate_to(self, module_id: str):
        """Navigate to a specific module.
        
        Args:
            module_id: Module ID to navigate to.
        """
        if module_id in ["change_password", "profile"]:
            # Handle special modules
            return
        
        if module_id in self.content_area._screens:
            self.sidebar.set_active(module_id)
            self.content_area.show_screen(module_id)
        else:
            # Load actual screen or placeholder
            screen = self._get_module_screen(module_id)
            self.content_area.register_screen(module_id, screen)
            self.content_area.show_screen(module_id)
            self.sidebar.set_active(module_id)
    
    def closeEvent(self, event):
        """Handle window close event.
        
        Args:
            event: Close event.
        """
        # Stop timers
        self.status_bar.stop_timer()
        
        # Accept close
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts.
        
        Args:
            event: Key press event.
        """
        # Ctrl+1..9 for module switching
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            key = event.key()
            
            # Number keys 1-9
            if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
                index = key - Qt.Key.Key_1
                items = get_sidebar_items_flat(self._session.vai_tro_id if self._session else 1)
                
                if index < len(items):
                    self.navigate_to(items[index].module_id)
                    return
            
            # Ctrl+L for logout
            if key == Qt.Key.Key_L:
                self._on_logout_requested()
                return
        
        # F1 for help
        if event.key() == Qt.Key.Key_F1:
            # TODO: Show help dialog
            return
        
        super().keyPressEvent(event)