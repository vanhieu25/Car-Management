"""Test navigation and main window components.

Tests:
- Sidebar module navigation
- Role-based sidebar filtering
- Top bar user dropdown
- MainWindow integration
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def session_manager():
    """Create a fresh session manager."""
    from app.application.services.session import SessionManager
    sm = SessionManager()
    sm.logout()
    return sm


@pytest.fixture
def admin_session(session_manager):
    """Create admin session for testing."""
    session = session_manager.login(
        user_id=1,
        username="admin",
        ho_ten="Nguyễn Văn Admin",
        vai_tro_id=1,
        vai_tro_ma="admin",
    )
    return session


@pytest.fixture
def sales_session(session_manager):
    """Create sales session for testing."""
    session = session_manager.login(
        user_id=2,
        username="sales01",
        ho_ten="Trần Thị Sales",
        vai_tro_id=2,
        vai_tro_ma="sales",
    )
    return session


@pytest.fixture
def kythuat_session(session_manager):
    """Create kỹ thuật session for testing."""
    session = session_manager.login(
        user_id=3,
        username="kythuat01",
        ho_ten="Lê Văn Kỹ Thuật",
        vai_tro_id=3,
        vai_tro_ma="ky_thuat_bh",
    )
    return session


class TestNavigationRegistry:
    """Test navigation registry functionality."""

    def test_navigation_registry_has_items(self):
        """Test that navigation registry has items registered."""
        from app.application.services.navigation_registry import navigation_registry
        
        items = navigation_registry.get_all_items()
        assert len(items) > 0, "Navigation registry should have items"

    def test_navigation_registry_has_dashboard(self):
        """Test that dashboard module is registered."""
        from app.application.services.navigation_registry import navigation_registry
        
        dashboard = navigation_registry.get_item("dashboard")
        assert dashboard is not None
        assert dashboard.label == "Dashboard"

    def test_get_screen_class_returns_none_for_placeholder(self):
        """Test that get_screen_class returns None for unregistered modules."""
        from app.application.services.navigation_registry import navigation_registry
        
        screen_class = navigation_registry.get_screen_class("dashboard")
        # Should be None since we only register placeholder
        assert screen_class is None

    def test_navigation_registry_default_module(self):
        """Test that default module is set to dashboard."""
        from app.application.services.navigation_registry import navigation_registry
        
        default = navigation_registry.get_default_module()
        assert default == "dashboard"


class TestSidebarService:
    """Test sidebar service and role-based filtering."""

    def test_setup_navigation_registry(self):
        """Test that setup_navigation_registry initializes correctly."""
        from app.application.services.sidebar_service import setup_navigation_registry
        
        registry = setup_navigation_registry()
        items = registry.get_all_items()
        assert len(items) >= 15, "Should have at least 15 modules"

    def test_admin_sees_all_modules(self):
        """Test that admin sees all modules (15+)."""
        from app.application.services.sidebar_service import get_sidebar_items_flat
        
        admin_items = get_sidebar_items_flat(vai_tro_id=1)
        assert len(admin_items) >= 15, "Admin should see all modules"

    def test_sales_sees_limited_modules(self):
        """Test that sales sees limited modules (not NV, BH, NCC, TG, BD, CH, KN, HT)."""
        from app.application.services.sidebar_service import get_sidebar_items_flat
        
        sales_items = get_sidebar_items_flat(vai_tro_id=2)
        
        # Sales should NOT see these modules
        excluded = ["nhan_vien", "bao_hanh", "nha_cung_cap", "tra_gop", 
                    "bao_duong", "cuu_ho", "khieu_nai", "he_thong"]
        
        visible_ids = [item.module_id for item in sales_items]
        for module_id in excluded:
            assert module_id not in visible_ids, f"Sales should not see {module_id}"

    def test_kythuat_sees_few_modules(self):
        """Test that kỹ thuật sees only few modules (BH, BD, CH related)."""
        from app.application.services.sidebar_service import get_sidebar_items_flat
        
        ky_items = get_sidebar_items_flat(vai_tro_id=3)
        
        # Kỹ thuật should see at most 5 modules
        assert len(ky_items) <= 5, "Kỹ thuật should see limited modules"

    def test_sales_has_dashboard_xe_kh(self):
        """Test that sales at minimum has dashboard, xe, khach_hang."""
        from app.application.services.sidebar_service import get_sidebar_items_flat
        
        sales_items = get_sidebar_items_flat(vai_tro_id=2)
        visible_ids = [item.module_id for item in sales_items]
        
        assert "dashboard" in visible_ids
        assert "xe" in visible_ids
        assert "khach_hang" in visible_ids

    def test_admin_has_nhan_vien_sales_not(self):
        """Test admin has nhan_vien but sales does not."""
        from app.application.services.sidebar_service import get_sidebar_items_flat
        
        admin_items = get_sidebar_items_flat(vai_tro_id=1)
        admin_ids = [item.module_id for item in admin_items]
        
        assert "nhan_vien" in admin_ids, "Admin should see nhan_vien"
        
        sales_items = get_sidebar_items_flat(vai_tro_id=2)
        sales_ids = [item.module_id for item in sales_items]
        
        assert "nhan_vien" not in sales_ids, "Sales should not see nhan_vien"


class TestSidebarGroups:
    """Test sidebar group organization."""

    def test_groups_are_sorted(self):
        """Test that sidebar groups are sorted by order."""
        from app.application.services.sidebar_service import get_sidebar_items
        
        groups = get_sidebar_items(vai_tro_id=1)
        
        # Groups should be in order
        group_orders = [g.order for g in groups]
        assert group_orders == sorted(group_orders), "Groups should be sorted by order"

    def test_groups_have_names(self):
        """Test that each group has a name."""
        from app.application.services.sidebar_service import get_sidebar_items
        
        groups = get_sidebar_items(vai_tro_id=1)
        
        for group in groups:
            assert group.name is not None
            assert len(group.name) > 0


class TestTopBar:
    """Test TopBar widget functionality."""

    def test_topbar_set_dealer_name(self, qapp):
        """Test setting dealer name."""
        from app.presentation.widgets.top_bar import TopBar
        
        tb = TopBar()
        tb.set_dealer_name("Test Dealer")
        assert tb.dealer_name_label.text() == "Test Dealer"
        tb.close()

    def test_topbar_set_user_info(self, qapp):
        """Test setting user info."""
        from app.presentation.widgets.top_bar import TopBar
        
        tb = TopBar()
        tb.set_user_info("testuser", "Test User", "admin")
        assert "testuser" in tb.user_label.text()
        assert "admin" in tb.user_label.text()
        tb.close()

    def test_topbar_logout_signal(self, qapp):
        """Test that logout signal is emitted."""
        from app.presentation.widgets.top_bar import TopBar
        
        tb = TopBar()
        emitted = []
        tb.logout_clicked.connect(lambda: emitted.append(True))
        tb._on_logout_requested()
        assert len(emitted) == 1
        tb.close()


class TestSidebarItem:
    """Test SidebarItem widget functionality."""

    def test_sidebar_item_properties(self, qapp):
        """Test sidebar item has correct properties."""
        from app.presentation.widgets.sidebar import SidebarItem
        
        item = SidebarItem("test_module", "Test Module", "🚗")
        
        assert item.module_id == "test_module"
        assert item._label == "Test Module"
        assert item._icon == "🚗"
        
        item.close()

    def test_sidebar_item_text_format(self, qapp):
        """Test sidebar item text includes icon and label."""
        from app.presentation.widgets.sidebar import SidebarItem
        
        item = SidebarItem("test", "Test Label", "📋")
        
        assert "📋" in item.text()
        assert "Test Label" in item.text()
        
        item.close()


class TestSidebar:
    """Test Sidebar widget functionality."""

    def test_sidebar_add_item(self, qapp):
        """Test adding item to sidebar."""
        from app.presentation.widgets.sidebar import Sidebar
        
        sb = Sidebar()
        sb.add_item("test_module", "Test Module", "📋", "Test")
        
        assert "test_module" in sb._items
        sb.close()

    def test_sidebar_set_active(self, qapp):
        """Test setting active item."""
        from app.presentation.widgets.sidebar import Sidebar
        
        sb = Sidebar()
        sb.add_item("test1", "Test 1", "📋", "Test")
        sb.add_item("test2", "Test 2", "📌", "Test")
        
        sb.set_active("test1")
        assert sb.get_active() == "test1"
        
        sb.close()

    def test_sidebar_clear(self, qapp):
        """Test clearing sidebar."""
        from app.presentation.widgets.sidebar import Sidebar
        
        sb = Sidebar()
        sb.add_item("test1", "Test 1", "📋", "Test")
        sb.add_item("test2", "Test 2", "📌", "Test")
        
        sb.clear()
        assert len(sb._items) == 0
        assert sb.get_active() is None
        
        sb.close()

    def test_sidebar_module_selected_signal(self, qapp):
        """Test sidebar emits module_selected signal."""
        from app.presentation.widgets.sidebar import Sidebar
        
        sb = Sidebar()
        sb.add_item("test", "Test", "📋", "Test")
        
        emitted = []
        sb.module_selected.connect(lambda m: emitted.append(m))
        
        sb.set_active("test")
        sb.module_selected.emit("test")
        
        assert len(emitted) == 1
        assert emitted[0] == "test"
        
        sb.close()


class TestContentArea:
    """Test ContentArea widget functionality."""

    def test_content_area_register_screen(self, qapp):
        """Test registering a screen."""
        from app.presentation.widgets.content_area import ContentArea
        from PyQt6.QtWidgets import QLabel
        
        ca = ContentArea()
        screen = QLabel("Test Screen")
        
        result = ca.register_screen("test_module", screen)
        assert result is True
        assert ca.has_screen("test_module")
        
        ca.close()

    def test_content_area_show_screen(self, qapp):
        """Test showing a registered screen."""
        from app.presentation.widgets.content_area import ContentArea
        from PyQt6.QtWidgets import QLabel
        
        ca = ContentArea()
        screen = QLabel("Test Screen")
        
        ca.register_screen("test", screen)
        result = ca.show_screen("test")
        
        assert result is True
        assert ca.get_current_module() == "test"
        
        ca.close()

    def test_content_area_show_unregistered_returns_false(self, qapp):
        """Test showing unregistered module returns False."""
        from app.presentation.widgets.content_area import ContentArea
        
        ca = ContentArea()
        result = ca.show_screen("nonexistent")
        
        assert result is False
        
        ca.close()


class TestStatusBar:
    """Test StatusBar widget functionality."""

    def test_statusbar_set_user(self, qapp):
        """Test setting user info."""
        from app.presentation.widgets.status_bar import StatusBar
        
        sb = StatusBar()
        sb.set_user("testuser", "sales")
        assert "testuser" in sb.user_label.text()
        assert "sales" in sb.user_label.text()
        sb.stop_timer()
        sb.close()

    def test_statusbar_set_version(self, qapp):
        """Test setting version."""
        from app.presentation.widgets.status_bar import StatusBar
        
        sb = StatusBar()
        sb.set_version("v2.0.0")
        assert sb.version_label.text() == "v2.0.0"
        sb.stop_timer()
        sb.close()

    def test_statusbar_set_db_status(self, qapp):
        """Test setting DB status."""
        from app.presentation.widgets.status_bar import StatusBar
        
        sb = StatusBar()
        
        sb.set_db_status(True)
        assert "34c759" in sb.db_status_label.styleSheet()  # Green color
        
        sb.set_db_status(False, "Lỗi kết nối")
        assert "ff3b30" in sb.db_status_label.styleSheet()  # Red color
        
        sb.stop_timer()
        sb.close()


class TestMainWindow:
    """Test MainWindow widget functionality."""

    def test_main_window_creation(self, qapp, admin_session):
        """Test main window can be created."""
        from app.presentation.screens.main_window import MainWindow
        
        mw = MainWindow(admin_session)
        assert mw is not None
        assert mw.get_session() == admin_session
        
        mw.close()

    def test_main_window_set_session(self, qapp, admin_session, sales_session):
        """Test setting session on main window."""
        from app.presentation.screens.main_window import MainWindow
        
        mw = MainWindow(admin_session)
        
        mw.set_session(sales_session)
        assert mw.get_session() == sales_session
        
        mw.close()

    def test_main_window_register_screen(self, qapp, admin_session):
        """Test registering a screen on main window."""
        from app.presentation.screens.main_window import MainWindow
        from PyQt6.QtWidgets import QLabel
        
        mw = MainWindow(admin_session)
        
        screen = QLabel("Test Screen")
        mw.register_screen("test_module", screen)
        
        assert mw.content_area.has_screen("test_module")
        
        mw.close()

    def test_main_window_navigate_to(self, qapp, admin_session):
        """Test navigation to a module."""
        from app.presentation.screens.main_window import MainWindow
        
        mw = MainWindow(admin_session)
        
        # Navigate to dashboard
        mw.navigate_to("dashboard")
        assert mw.sidebar.get_active() == "dashboard"
        
        mw.close()

    def test_main_window_logout_signal(self, qapp, admin_session):
        """Test logout signal is emitted."""
        from app.presentation.screens.main_window import MainWindow
        
        mw = MainWindow(admin_session)
        
        emitted = []
        mw.logout_requested.connect(lambda: emitted.append(True))
        
        mw._on_logout_requested()
        
        assert len(emitted) == 1
        
        mw.close()