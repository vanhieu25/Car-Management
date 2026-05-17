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

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox
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
from app.presentation.screens.customer_list_screen import CustomerListScreen
from app.presentation.screens.customer_form_dialog import CustomerFormDialog
from app.presentation.screens.customer_detail_screen import CustomerDetailScreen


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
        if module_id == "dashboard":
            # S-DASH-01: Dashboard
            import logging
            from app.infrastructure.database.connection import get_connection
            logger = logging.getLogger("car_management")
            logger.info(f"[MainWindow] Creating dashboard - db_conn: {self._db_conn}, session: {self._session}")
            # Use self._db_conn if available, otherwise get new connection
            conn = self._db_conn if self._db_conn else get_connection()
            if self._session:
                from app.presentation.screens.dashboard_screen import DashboardScreen
                screen = DashboardScreen(conn, self._session)
                logger.info(f"[MainWindow] Dashboard screen created: {screen}")
                return screen
            else:
                logger.warning(f"[MainWindow] Cannot create dashboard - session is None")
        elif module_id == "audit_log":
            # S-SYS-01: Audit log viewer
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] audit_log - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                return AuditLogScreen(conn, self._session)
        elif module_id == "he_thong":
            # S-CFG-01: System settings
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] he_thong - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                return SystemSettingsScreen(conn, self._session)
        elif module_id == "xe":
            # S-XE-01: Vehicle list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info(f"[Module] xe - session vai_tro_ma: {self._session.vai_tro_ma if self._session else None}")
            logger.info("[Module] xe - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                screen = VehicleListScreen(conn, self._session)
                # Connect signals
                screen.add_vehicle_clicked.connect(lambda: self._show_vehicle_form(None))
                screen.edit_vehicle_clicked.connect(self._show_vehicle_form)
                screen.view_vehicle_clicked.connect(self._show_vehicle_detail)
                return screen
        elif module_id == "khach_hang":
            # S-KH-01: Customer list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] khach_hang - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                screen = CustomerListScreen(conn, self._session)
                # Connect signals
                screen.add_customer_clicked.connect(lambda: self._show_customer_form(None))
                screen.edit_customer_clicked.connect(self._show_customer_form)
                screen.view_customer_clicked.connect(self._show_customer_detail)
                return screen
        elif module_id == "tra_gop":
            # S-TG-01: Installment list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] tra_gop - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.installment_list_screen import InstallmentListScreen
                from app.presentation.screens.installment_create_dialog import InstallmentCreateDialog
                from app.presentation.screens.installment_progress_screen import InstallmentProgressScreen
                screen = InstallmentListScreen(conn, self._session)
                screen.create_installment_clicked.connect(self._show_installment_create_dialog)
                screen.view_installment_clicked.connect(self._show_installment_progress)
                return screen
        elif module_id == "marketing":
            # S-MK-01: Campaign list + Lead manager (tabbed)
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] marketing - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.campaign_list_screen import CampaignListScreen
                from app.presentation.screens.campaign_form_dialog import CampaignFormDialog
                from app.presentation.screens.lead_manager_screen import LeadManagerScreen
                from app.presentation.screens.lead_form_dialog import LeadFormDialog
                screen = CampaignListScreen(conn, self._session)
                screen.add_campaign_clicked.connect(self._show_campaign_form)
                screen.edit_campaign_clicked.connect(self._show_campaign_form)
                return screen
        elif module_id == "khieu_nai":
            # S-KN-01: Complaint list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] khieu_nai - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.complaint_list_screen import ComplaintListScreen
                screen = ComplaintListScreen(conn, self._session)
                screen.add_complaint_clicked.connect(self._show_complaint_form)
                screen.view_complaint_clicked.connect(self._show_complaint_detail)
                return screen


        elif module_id == "nhan_vien":
            # S-NV-01: Employee list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] nhan_vien - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.employee_list_screen import EmployeeListScreen
                screen = EmployeeListScreen(conn, self._session)
                screen.add_employee_clicked.connect(self._show_employee_form)
                screen.edit_employee_clicked.connect(self._show_employee_form)
                screen.view_employee_clicked.connect(self._show_employee_detail)
                return screen

        elif module_id == "hop_dong":
            # S-HD-01: Contract list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] hop_dong - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.contract_list_screen import ContractListScreen
                screen = ContractListScreen(conn, self._session)
                screen.create_contract_clicked.connect(self._show_contract_wizard)

                screen.view_contract_clicked.connect(self._show_contract_detail)
                return screen

        elif module_id == "thanh_toan_hd":
            # S-HD-PAY: Payment contract screen
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] thanh_toan_hd - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.payment_contract_screen import PaymentContractScreen
                screen = PaymentContractScreen(conn, self._session)
                screen.back_clicked.connect(lambda: self.navigate_to("hop_dong"))
                return screen

        elif module_id == "phu_kien":
            # S-PK-01: Accessory list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] phu_kien - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.accessory_list_screen import AccessoryListScreen
                screen = AccessoryListScreen(conn, self._session)
                screen.add_accessory_clicked.connect(self._show_accessory_form)
                screen.edit_accessory_clicked.connect(self._show_accessory_form)
                return screen

        elif module_id == "bao_hanh":
            # S-BH-01: Warranty list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] bao_hanh - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.warranty_list_screen import WarrantyListScreen
                screen = WarrantyListScreen(conn, self._session)

                screen.view_warranty_clicked.connect(self._show_warranty_detail)
                screen.create_external_warranty_clicked.connect(self._show_external_warranty_form)
                screen.create_internal_warranty_clicked.connect(self._show_internal_warranty_form)
                return screen

        elif module_id == "bao_hiem":
            # S-BH-01: Insurance list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] bao_hiem - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.bao_hiem_list_screen import BaoHiemListScreen
                screen = BaoHiemListScreen(conn, self._session)
                screen.view_insurance_clicked.connect(self._show_bao_hiem_detail)
                screen.create_insurance_clicked.connect(self._show_bao_hiem_form)
                return screen

        elif module_id == "thanh_toan_bh":
            # S-BH-PAY: Payment insurance screen
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] thanh_toan_bh - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.payment_insurance_screen import PaymentInsuranceScreen
                screen = PaymentInsuranceScreen(conn, self._session)
                screen.back_clicked.connect(lambda: self.navigate_to("bao_hiem"))
                return screen

        elif module_id == "yeu_cau_bh":
            # S-BH-01a: Warranty request list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] yeu_cau_bh - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.warranty_request_list_screen import WarrantyRequestListScreen
                screen = WarrantyRequestListScreen(conn, self._session)
                screen.view_request_clicked.connect(self._show_warranty_request_detail)
                screen.create_request_clicked.connect(self._show_warranty_request_form)
                return screen

        elif module_id == "nha_cung_cap":
            # S-NCC-01: Supplier list
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] nha_cung_cap - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.supplier_list_screen import SupplierListScreen
                screen = SupplierListScreen(conn, self._session)
                screen.add_supplier_clicked.connect(self._show_supplier_form)
                screen.edit_supplier_clicked.connect(self._show_supplier_detail)
                screen.view_supplier_clicked.connect(self._show_supplier_detail)
                return screen

        elif module_id == "bao_duong":
            # S-BD-01: Maintenance schedule
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] bao_duong - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.maintenance_schedule_screen import MaintenanceScheduleScreen
                screen = MaintenanceScheduleScreen(conn, self._session)
                screen.add_maintenance_clicked.connect(self._show_maintenance_form)
                screen.edit_maintenance_clicked.connect(self._show_maintenance_form)
                return screen

        elif module_id == "khuyen_mai":
            # S-KM-01: Promotion - use promo_list_screen
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] khuyen_mai - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.promo_list_screen import PromoListScreen
                screen = PromoListScreen(conn, self._session)
                screen.add_promo_clicked.connect(self._show_promo_form)
                screen.edit_promo_clicked.connect(self._show_promo_form)
                return screen

        elif module_id == "cuu_ho":
            # S-CH-01: Rescue requests - use RescueRequestListScreen
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] cuu_ho - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.rescue_request_list_screen import RescueRequestListScreen
                screen = RescueRequestListScreen(conn, self._session)
                screen.add_rescue_clicked.connect(self._show_rescue_form)
                screen.edit_rescue_clicked.connect(self._show_rescue_form)
                return screen

        elif module_id == "bao_cao":
            # S-BC-HUB: Reports Hub with 5 tabs
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] bao_cao - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.reports_hub_screen import ReportsHubScreen
                screen = ReportsHubScreen(conn, self._session)
                return screen

        elif module_id == "kho":
            # S-KHO-01: Warehouse - use InventoryOverviewScreen
            import logging
            logger = logging.getLogger("car_management")
            from app.infrastructure.database.connection import get_connection
            conn = self._db_conn if self._db_conn else get_connection()
            logger.info("[Module] kho - conn: %s, session: %s" % (conn, self._session))
            if conn and self._session:
                from app.presentation.screens.inventory_overview_screen import InventoryOverviewScreen
                screen = InventoryOverviewScreen(conn, self._session)
                screen.stock_in_clicked.connect(self._show_stock_in_dialog)
                return screen

        # Default: placeholder
        import logging
        logger = logging.getLogger("car_management")
        logger.warning("[Module] %s - NO SCREEN IMPLEMENTED, showing EmptyScreen" % module_id)
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

        if self.content_area.has_screen("xe_detail"):
            self.content_area.unregister_screen("xe_detail")

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

    def _show_customer_form(self, khach_hang_id: int = None):
        """Show customer add/edit form dialog.

        Args:
            khach_hang_id: Customer ID to edit, or None for add new.
        """
        from app.presentation.screens.customer_form_dialog import CustomerFormDialog
        from app.domain.entities import KhachHang

        khach_hang = None
        if khach_hang_id:
            # Create a minimal KhachHang entity for the form
            khach_hang = KhachHang()
            khach_hang.id = khach_hang_id

        dialog = CustomerFormDialog(self._db_conn, self._session, khach_hang, self)
        dialog.saved.connect(self._on_customer_saved)
        dialog.exec()

    def _show_customer_detail(self, khach_hang_id: int):
        """Show customer detail screen.

        Args:
            khach_hang_id: Customer ID to display.
        """
        from app.presentation.screens.customer_detail_screen import CustomerDetailScreen

        if self.content_area.has_screen("khach_hang_detail"):
            self.content_area.unregister_screen("khach_hang_detail")

        screen = CustomerDetailScreen(self._db_conn, self._session, khach_hang_id, self)
        screen.edit_clicked.connect(self._show_customer_form)
        screen.close_clicked.connect(lambda: self.navigate_to("khach_hang"))

        # Replace current screen with detail
        self.content_area.register_screen("khach_hang_detail", screen)
        self.content_area.show_screen("khach_hang_detail")

    def _on_customer_saved(self):
        """"Handle customer saved signal - refresh list."""
        # Refresh customer list if visible
        if self.content_area.has_screen("khach_hang"):
            screen = self.content_area.get_screen("khach_hang")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_stock_in_dialog(self):
        """Show stock-in dialog."""
        from app.presentation.screens.stock_in_form_dialog import StockInFormDialog

        dialog = StockInFormDialog(self._db_conn, self._session, self)
        dialog.saved.connect(self._on_stock_in_saved)
        dialog.exec()

    def _show_rescue_form(self, cuu_ho_id: int = None):
        """Show rescue request form dialog.

        Args:
            cuu_ho_id: CuuHo ID to edit, or None for add new.
        """
        from app.presentation.screens.rescue_request_form_dialog import RescueRequestFormDialog
        from app.domain.entities import CuuHo

        cuu_ho = None
        if cuu_ho_id:
            from app.application.services.cuu_ho_service import CuuHoService
            service = CuuHoService(self._db_conn)
            cuu_ho = service.get_by_id(cuu_ho_id)

        dialog = RescueRequestFormDialog(self._db_conn, self._session, cuu_ho, self)
        dialog.saved.connect(self._on_rescue_saved)
        dialog.exec()

    def _on_rescue_saved(self):
        """Handle rescue saved signal - refresh cuu_ho screen."""
        if self.content_area.has_screen("cuu_ho"):
            screen = self.content_area.get_screen("cuu_ho")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _on_stock_in_saved(self):
        """Handle stock-in saved signal - refresh kho screen and supplier detail."""
        if self.content_area.has_screen("kho"):
            screen = self.content_area.get_screen("kho")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Refresh supplier detail screen if visible (to update lich su nhap tab)
        if self.content_area.has_screen("supplier_detail"):
            screen = self.content_area.get_screen("supplier_detail")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_installment_create_dialog(self):
        """"Show installment create dialog."""
        from app.presentation.screens.installment_create_dialog import InstallmentCreateDialog

        dialog = InstallmentCreateDialog(self._db_conn, self._session, self)
        dialog.created.connect(self._on_installment_created)
        dialog.exec()

    def _on_installment_created(self, tra_gop_id: int):
        """"Handle installment created signal - refresh list."""
        if self.content_area.has_screen("tra_gop"):
            screen = self.content_area.get_screen("tra_gop")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_installment_progress(self, tra_gop_id: int):
        """Show installment progress screen.

        Args:
            tra_gop_id: TraGop ID to display.
        """
        from app.presentation.screens.installment_progress_screen import InstallmentProgressScreen

        screen = InstallmentProgressScreen(self._db_conn, self._session, tra_gop_id, self)
        screen.back_clicked.connect(lambda: self.navigate_to("tra_gop"))

        # Replace current screen with detail
        self.content_area.register_screen("tra_gop_detail", screen)
        self.content_area.show_screen("tra_gop_detail")

    def _show_campaign_form(self, campaign_id: int = None):
        """Show campaign add/edit form dialog.

        Args:
            campaign_id: Campaign ID to edit, or None for add new.
        """
        from app.presentation.screens.campaign_form_dialog import CampaignFormDialog

        campaign = None
        if campaign_id:
            from app.application.services.chien_dich_mk_service import ChienDichMkService
            service = ChienDichMkService(self._db_conn)
            campaign = service.get_by_id(campaign_id)

        dialog = CampaignFormDialog(self._db_conn, self._session, campaign, self)
        dialog.saved.connect(self._on_campaign_saved)
        dialog.exec()
    
    def _show_promo_form(self, promo_id: int = None):
        """Show promotion add/edit form dialog.

        Args:
            promo_id: Promotion ID to edit, or None for add new.
        """
        from app.presentation.screens.promo_form_dialog import PromoFormDialog

        promo = None
        if promo_id:
            from app.application.services.khuyen_mai_service import KhuyenMaiService
            service = KhuyenMaiService(self._db_conn)
            promo = service.get_by_id(promo_id)

        dialog = PromoFormDialog(self._db_conn, self._session, promo, self)
        dialog.saved.connect(self._on_promo_saved)
        dialog.exec()
    
    def _on_promo_saved(self):
        """Handle promotion saved signal - refresh list."""
        if self.content_area.has_screen("khuyen_mai"):
            screen = self.content_area.get_screen("khuyen_mai")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _on_campaign_saved(self):
        """Handle campaign saved signal - refresh list."""
        for screen_name in ("marketing", "khuyen_mai"):
            if self.content_area.has_screen(screen_name):
                screen = self.content_area.get_screen(screen_name)
                if hasattr(screen, 'refresh'):
                    screen.refresh()

    def _show_lead_form(self, lead_id: int = None):
        """Show lead add/edit form dialog.

        Args:
            lead_id: Lead ID to edit, or None for add new.
        """
        from app.presentation.screens.lead_form_dialog import LeadFormDialog

        lead = None
        if lead_id:
            from app.application.services.lead_service import LeadService
            service = LeadService(self._db_conn)
            lead = service.get_by_id(lead_id)

        dialog = LeadFormDialog(self._db_conn, self._session, lead, self)
        dialog.saved.connect(self._on_lead_saved)
        dialog.exec()

    def _on_lead_saved(self):
        """Handle lead saved signal - refresh list."""
        if self.content_area.has_screen("marketing"):
            screen = self.content_area.get_screen("marketing")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_complaint_form(self):
        """Show complaint add form dialog."""
        from app.presentation.screens.complaint_form_dialog import ComplaintFormDialog

        dialog = ComplaintFormDialog(self._db_conn, self._session, self)
        dialog.saved.connect(self._on_complaint_saved)
        dialog.exec()

    def _show_complaint_detail(self, kn_id: int):
        """Show complaint detail screen.

        Args:
            kn_id: Complaint ID to display.
        """
        from app.presentation.screens.complaint_detail_screen import ComplaintDetailScreen

        screen = ComplaintDetailScreen(self._db_conn, self._session, kn_id, self)
        screen.back_clicked.connect(lambda: self.navigate_to("khieu_nai"))
        screen.closed.connect(self._on_complaint_saved)

        # Replace current screen with detail
        self.content_area.register_screen("khieu_nai_detail", screen)
        self.content_area.show_screen("khieu_nai_detail")

    def _on_complaint_saved(self):
        """Handle complaint saved signal - refresh list."""
        if self.content_area.has_screen("khieu_nai"):
            screen = self.content_area.get_screen("khieu_nai")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_employee_form(self, nhan_vien_id: int = None):
        """Show employee add/edit form dialog.

        Args:
            nhan_vien_id: Employee ID to edit, or None for add new.
        """
        from app.presentation.screens.employee_form_dialog import EmployeeFormDialog
        from app.application.services.nhan_vien_service import NhanVienService
        nhan_vien = None
        if nhan_vien_id:
            service = NhanVienService(self._db_conn, self._session)
            nhan_vien = service.get_by_id(nhan_vien_id)
        dialog = EmployeeFormDialog(self._db_conn, self._session, nhan_vien, self)
        dialog.saved.connect(self._on_employee_saved)
        dialog.exec()

    def _on_employee_saved(self):
        """Handle employee saved signal - refresh list."""
        if self.content_area.has_screen("nhan_vien"):
            screen = self.content_area.get_screen("nhan_vien")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_employee_detail(self, nhan_vien_id: int):
        """Show employee profile screen."""
        from app.presentation.screens.employee_profile_screen import EmployeeProfileScreen
        screen = EmployeeProfileScreen(self._db_conn, self._session, parent=self)
        self.content_area.register_screen("employee_detail", screen)
        self.content_area.show_screen("employee_detail")

    def _show_contract_wizard(self, hop_dong_id: int = None):
        """Show contract creation wizard."""
        from app.presentation.screens.contract_wizard_dialog import ContractWizardDialog
        dialog = ContractWizardDialog(self._db_conn, self._session, self)
        dialog.saved.connect(self._on_contract_saved)
        dialog.exec()

    def _on_contract_saved(self):
        """Handle contract saved signal - refresh list."""
        if self.content_area.has_screen("hop_dong"):
            screen = self.content_area.get_screen("hop_dong")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Also refresh payment contract screen if visible
        if self.content_area.has_screen("thanh_toan_hd"):
            screen = self.content_area.get_screen("thanh_toan_hd")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_contract_detail(self, hop_dong_id: int):
        """Show contract detail screen."""
        from app.presentation.screens.contract_detail_screen import ContractDetailScreen

        # Unregister old screen if exists to avoid leaks
        if self.content_area.has_screen("contract_detail"):
            self.content_area.unregister_screen("contract_detail")

        screen = ContractDetailScreen(self._db_conn, self._session, hop_dong_id, self)

        def on_action_completed():
            """Refresh list immediately when status changes."""
            if self.content_area.has_screen("hop_dong"):
                list_screen = self.content_area.get_screen("hop_dong")
                if hasattr(list_screen, 'refresh'):
                    list_screen.refresh()

        def on_detail_closed():
            self.navigate_to("hop_dong")

        screen.action_completed.connect(on_action_completed)
        screen.closed.connect(on_detail_closed)
        self.content_area.register_screen("contract_detail", screen)
        self.content_area.show_screen("contract_detail")

    def _show_maintenance_form(self, lich_bao_duong_id: int = None):
        """Show maintenance add/edit form dialog.

        Args:
            lich_bao_duong_id: Maintenance schedule ID to edit, or None for add new.
        """
        from app.presentation.screens.maintenance_form_dialog import MaintenanceFormDialog
        from app.application.services.bao_duong_service import BaoDuongService

        bao_duong = None
        if lich_bao_duong_id is not None:
            bd_service = BaoDuongService(self._db_conn)
            bao_duong = bd_service.get_by_id(lich_bao_duong_id)

        dialog = MaintenanceFormDialog(self._db_conn, self._session, bao_duong, self)
        dialog.saved.connect(self._on_maintenance_saved)
        dialog.exec()

    def _on_maintenance_saved(self):
        """Handle maintenance saved signal - refresh list."""
        if self.content_area.has_screen("bao_duong"):
            screen = self.content_area.get_screen("bao_duong")
            if hasattr(screen, 'refresh'):
                # Switch to list view to show newly added maintenance
                screen._set_view("list")
                screen.refresh()

    def _show_accessory_form(self, phu_kien_id: int = None):
        """Show accessory add/edit form dialog."""
        from app.presentation.screens.accessory_form_dialog import AccessoryFormDialog
        dialog = AccessoryFormDialog(self._db_conn, self._session, phu_kien_id, self)
        dialog.saved.connect(self._on_accessory_saved)
        dialog.exec()

    def _on_accessory_saved(self):
        """Handle accessory saved - refresh accessory list."""
        if self.content_area.has_screen("phu_kien"):
            screen = self.content_area.get_screen("phu_kien")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_warranty_request_form(self, bh_id: int = None):
        """Show warranty request form dialog."""
        from app.presentation.screens.warranty_request_form_dialog import WarrantyRequestFormDialog

        if bh_id is None:
            # Show dialog to get warranty ID
            from PyQt6.QtWidgets import QInputDialog, QLineEdit
            dialog = QInputDialog(self)
            dialog.setWindowTitle("Tạo yêu cầu bảo hành")
            dialog.setLabelText("Nhập mã bảo hành (BH ID):")
            dialog.setInputMode(QInputDialog.InputMode.TextInput)
            dialog.resize(400, 100)
            if dialog.exec():
                try:
                    bh_id = int(dialog.textValue())
                except ValueError:
                    return
            else:
                return

        dialog = WarrantyRequestFormDialog(self._db_conn, self._session, bh_id, self)
        dialog.request_created.connect(self._on_warranty_request_created)
        dialog.exec()

    def _print_warranty(self, bh_id: int):
        """Print warranty PDF."""
        from app.presentation.screens.warranty_print_dialog import WarrantyPrintDialog
        dialog = WarrantyPrintDialog(self._db_conn, bh_id, self)
        dialog.exec()

    def _on_warranty_request_created(self):
        """Handle warranty request created - refresh list."""
        if self.content_area.has_screen("yeu_cau_bh"):
            screen = self.content_area.get_screen("yeu_cau_bh")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Also refresh warranty list since requests belong to warranties
        if self.content_area.has_screen("bao_hanh"):
            screen = self.content_area.get_screen("bao_hanh")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Refresh thanh toan bao hiem screen if visible
        if self.content_area.has_screen("thanh_toan_bh"):
            screen = self.content_area.get_screen("thanh_toan_bh")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_warranty_request_detail(self, req_id: int):
        """Show warranty request detail screen.

        Args:
            req_id: Warranty request ID to display.
        """
        from app.presentation.screens.warranty_detail_screen import WarrantyDetailScreen

        # Get the bao_hanh_id from the request
        cursor = self._db_conn.execute(
            "SELECT bao_hanh_id FROM bao_hanh_yeu_cau WHERE id = ?", (req_id,)
        )
        row = cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy yêu cầu bảo hành")
            return

        bao_hanh_id = row[0]

        if self.content_area.has_screen("warranty_request_detail"):
            self.content_area.unregister_screen("warranty_request_detail")

        screen = WarrantyDetailScreen(self._db_conn, self._session, bao_hanh_id, self)
        screen.create_request_clicked.connect(self._show_warranty_request_form)
        screen.closed.connect(lambda: self.navigate_to("yeu_cau_bh"))
        self.content_area.register_screen("warranty_request_detail", screen)
        self.content_area.show_screen("warranty_request_detail")

    def _show_warranty_detail(self, bao_hanh_id: int):
        """Show warranty detail screen."""
        from app.presentation.screens.warranty_detail_screen import WarrantyDetailScreen

        # Unregister old screen if exists to avoid showing stale data
        if self.content_area.has_screen("warranty_detail"):
            self.content_area.unregister_screen("warranty_detail")

        screen = WarrantyDetailScreen(self._db_conn, self._session, bao_hanh_id, self)
        screen.create_request_clicked.connect(self._show_warranty_request_form)
        screen.print_warranty_clicked.connect(self._print_warranty)
        screen.closed.connect(lambda: self.navigate_to("bao_hanh"))
        self.content_area.register_screen("warranty_detail", screen)
        self.content_area.show_screen("warranty_detail")

    def _show_external_warranty_form(self):
        """Show external warranty creation dialog."""
        from app.presentation.screens.external_warranty_form_dialog import ExternalWarrantyCreateDialog
        dialog = ExternalWarrantyCreateDialog(self._db_conn, self._session, self)
        dialog.warranty_created.connect(self._on_external_warranty_created)
        dialog.request_needed.connect(self._on_external_warranty_request_needed)
        dialog.exec()

    def _show_internal_warranty_form(self):
        """Show internal warranty creation dialog."""
        from app.presentation.screens.internal_warranty_form_dialog import InternalWarrantyCreateDialog
        dialog = InternalWarrantyCreateDialog(self._db_conn, self._session, self)
        dialog.warranty_created.connect(self._on_internal_warranty_created)
        dialog.exec()

    def _on_external_warranty_created(self, bh_id: int):
        """Handle external warranty created event."""
        # Refresh warranty list screen
        if self.content_area.has_screen("bao_hanh"):
            screen = self.content_area.get_screen("bao_hanh")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Refresh insurance list screen
        if self.content_area.has_screen("bao_hiem"):
            screen = self.content_area.get_screen("bao_hiem")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Refresh payment insurance screen if visible
        if self.content_area.has_screen("thanh_toan_bh"):
            screen = self.content_area.get_screen("thanh_toan_bh")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _on_internal_warranty_created(self, bh_id: int):
        """Handle internal warranty created event."""
        if self.content_area.has_screen("bao_hanh"):
            screen = self.content_area.get_screen("bao_hanh")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Refresh insurance list screen
        if self.content_area.has_screen("bao_hiem"):
            screen = self.content_area.get_screen("bao_hiem")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        # Refresh payment insurance screen if visible
        if self.content_area.has_screen("thanh_toan_bh"):
            screen = self.content_area.get_screen("thanh_toan_bh")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _on_external_warranty_request_needed(self, bh_id: int):
        """Handle request needed after external warranty created."""
        self._show_warranty_detail(bh_id)

    def _show_bao_hiem_detail(self, bao_hiem_id: int):
        """Show insurance detail screen."""
        from app.presentation.screens.bao_hiem_detail_screen import BaoHiemDetailScreen

        if self.content_area.has_screen("bao_hiem_detail"):
            self.content_area.unregister_screen("bao_hiem_detail")

        screen = BaoHiemDetailScreen(self._db_conn, self._session, bao_hiem_id, self)
        # Edit mode not yet supported in new cascade dialog
        screen.closed.connect(lambda: self.navigate_to("bao_hiem"))
        screen.action_completed.connect(lambda: self.navigate_to("bao_hiem"))
        self.content_area.register_screen("bao_hiem_detail", screen)
        self.content_area.show_screen("bao_hiem_detail")

    def _show_bao_hiem_form(self, bao_hiem_id: int = None, warranty_id: int = None):
        """Show insurance form dialog (create mode only)."""
        from app.presentation.screens.bao_hiem_form_dialog import BaoHiemFormDialog

        dialog = BaoHiemFormDialog(
            self._db_conn,
            self._session,
            parent=self
        )
        dialog.insurance_saved.connect(self._on_bao_hiem_saved)
        dialog.exec()

    def _on_bao_hiem_saved(self):
        """Handle insurance saved signal - refresh list."""
        if self.content_area.has_screen("bao_hiem"):
            screen = self.content_area.get_screen("bao_hiem")
            if hasattr(screen, 'refresh'):
                screen.refresh()
        if self.content_area.has_screen("thanh_toan_bh"):
            screen = self.content_area.get_screen("thanh_toan_bh")
            if hasattr(screen, 'refresh'):
                screen.refresh()

    def _show_supplier_form(self, nha_cung_cap_id: int = None):
        """Show supplier add/edit dialog.


        Args:
            nha_cung_cap_id: Supplier ID to edit, or None for add new.
        """
        from app.presentation.screens.supplier_form_dialog import SupplierFormDialog
        from app.application.services.nha_cung_cap_service import NhaCungCapService
        from app.domain.entities import NhaCungCap
        ncc = None
        if nha_cung_cap_id:
            service = NhaCungCapService(self._db_conn)
            ncc_dict = service.get_by_id(nha_cung_cap_id)
            if ncc_dict:
                ncc = NhaCungCap.from_row(ncc_dict)
        dialog = SupplierFormDialog(self._db_conn, self._session, ncc, self)
        dialog.saved.connect(self._on_supplier_saved)
        dialog.exec()

    def _show_supplier_detail(self, nha_cung_cap_id: int):
        """Show supplier detail screen."""
        from app.presentation.screens.supplier_detail_screen import SupplierDetailScreen
        screen = SupplierDetailScreen(self._db_conn, self._session, nha_cung_cap_id, self)
        screen.back_clicked.connect(lambda: self.navigate_to("nha_cung_cap"))
        screen.edit_clicked.connect(self._show_supplier_form)
        self.content_area.register_screen("supplier_detail", screen)
        self.content_area.show_screen("supplier_detail")

    def _on_supplier_saved(self):
        """Handle supplier saved event - refresh supplier list and detail."""
        if hasattr(self, 'content_area') and self.content_area.has_screen("nha_cung_cap"):
            screen = self.content_area.get_screen("nha_cung_cap")
            screen.refresh()
        # Refresh supplier detail screen if visible (to update thong tin tab)
        if self.content_area.has_screen("supplier_detail"):
            screen = self.content_area.get_screen("supplier_detail")
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
        import logging
        logger = logging.getLogger("car_management")

        if module_id in ["change_password", "profile"]:
            # Handle special modules
            return

        logger.info(f"[navigate_to] module_id={module_id}, existing screens={list(self.content_area._screens.keys())}")

        if module_id in self.content_area._screens:
            screen = self.content_area._screens.get(module_id)
            logger.info(f"[navigate_to] Found existing screen: {type(screen).__name__}, has_refresh={hasattr(screen, 'refresh')}")
            # Refresh existing screen if it has refresh method
            if hasattr(screen, 'refresh'):
                logger.info(f"[navigate_to] Calling refresh on {module_id}")
                screen.refresh()
            self.sidebar.set_active(module_id)
            self.content_area.show_screen(module_id)
        else:
            # Load actual screen or placeholder
            logger.info(f"[navigate_to] Creating new screen for {module_id}")
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