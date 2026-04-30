"""Screens module - UI screens for the application."""

from app.presentation.screens.login_screen import LoginScreen
from app.presentation.screens.change_password_dialog import ChangePasswordDialog
from app.presentation.screens.audit_log_screen import AuditLogScreen, AuditLogDetailDialog
from app.presentation.screens.system_settings_screen import SystemSettingsScreen
from app.presentation.screens.vehicle_list_screen import VehicleListScreen
from app.presentation.screens.vehicle_form_dialog import VehicleFormDialog
from app.presentation.screens.vehicle_detail_screen import VehicleDetailScreen
from app.presentation.screens.vehicle_delete_dialog import VehicleDeleteDialog
from app.presentation.screens.customer_list_screen import CustomerListScreen
from app.presentation.screens.customer_form_dialog import CustomerFormDialog
from app.presentation.screens.customer_detail_screen import CustomerDetailScreen

__all__ = [
    "LoginScreen",
    "ChangePasswordDialog",
    "AuditLogScreen",
    "AuditLogDetailDialog",
    "SystemSettingsScreen",
    "VehicleListScreen",
    "VehicleFormDialog",
    "VehicleDetailScreen",
    "VehicleDeleteDialog",
    "CustomerListScreen",
    "CustomerFormDialog",
    "CustomerDetailScreen",
]
