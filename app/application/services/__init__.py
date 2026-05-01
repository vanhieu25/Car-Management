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
    setup_navigation_registry,
    get_sidebar_items,
    get_sidebar_items_flat,
)
from app.application.services.audit_log_service import (
    AuditLogService,
    AuditLogEntry,
    AuditAction,
    get_audit_service,
    reset_audit_service,
)
from app.application.services.audit_decorator import audit, audit_login, audit_logout
from app.application.services.chien_dich_mk_service import (
    ChienDichMkService,
    ChienDichMkServiceError,
    ValidationError,
    ChienDichMkNotFoundError,
    ChienDichMkCreateData,
    ChienDichMkUpdateData,
)
from app.application.services.lead_service import (
    LeadService,
    LeadServiceError,
    ValidationError as LeadValidationError,
    LeadNotFoundError,
    LeadConvertError,
    LeadCreateData,
    LeadUpdateData,
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
    "setup_navigation_registry",
    "get_sidebar_items",
    "get_sidebar_items_flat",
    "AuditLogService",
    "AuditLogEntry",
    "AuditAction",
    "get_audit_service",
    "reset_audit_service",
    "audit",
    "audit_login",
    "audit_logout",
    "ChienDichMkService",
    "ChienDichMkServiceError",
    "ChienDichMkNotFoundError",
    "ChienDichMkCreateData",
    "ChienDichMkUpdateData",
    "LeadService",
    "LeadServiceError",
    "LeadNotFoundError",
    "LeadConvertError",
    "LeadCreateData",
    "LeadUpdateData",
]
