"""Application services module."""

from app.application.services.auth_service import AuthService, LoginError, LoginResult, ChangePasswordResult
from app.application.services.permission_service import PermissionService, PermissionDeniedError
from app.application.services.session import SessionManager, CurrentSession
from app.application.services.system_settings_service import SystemSettingsService, SystemSettings, get_settings
from app.application.services.navigation_registry import (
    NavigationRegistry,
    NavigationItem,
    NavigationGroup,
    ModuleId,
    navigation_registry,
    register_module,
    get_navigation_registry,
)
from app.application.services.sidebar_service import (
    sidebar_service,
    setup_navigation_registry,
    get_sidebar_items,
    get_sidebar_items_flat,
)

__all__ = [
    "AuthService",
    "LoginError",
    "LoginResult",
    "ChangePasswordResult",
    "PermissionService",
    "PermissionDeniedError",
    "SessionManager",
    "CurrentSession",
    "SystemSettingsService",
    "SystemSettings",
    "get_settings",
    "NavigationRegistry",
    "NavigationItem",
    "NavigationGroup",
    "ModuleId",
    "navigation_registry",
    "register_module",
    "get_navigation_registry",
    "sidebar_service",
    "setup_navigation_registry",
    "get_sidebar_items",
    "get_sidebar_items_flat",
]
