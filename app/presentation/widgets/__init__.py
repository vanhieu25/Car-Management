"""Common UI widgets for the application."""

from app.presentation.widgets.buttons import PrimaryButton, DangerButton, SecondaryButton
from app.presentation.widgets.inputs import PasswordLineEdit, ValidatedLineEdit
from app.presentation.widgets.dialogs import ToastDialog
from app.presentation.widgets.top_bar import TopBar
from app.presentation.widgets.sidebar import Sidebar
from app.presentation.widgets.status_bar import StatusBar
from app.presentation.widgets.content_area import (
    ContentArea,
    LoadingScreen,
    ErrorScreen,
    PermissionDeniedScreen,
    EmptyScreen,
)

__all__ = [
    "PrimaryButton",
    "DangerButton",
    "SecondaryButton",
    "PasswordLineEdit",
    "ValidatedLineEdit",
    "ToastDialog",
    "TopBar",
    "Sidebar",
    "StatusBar",
    "ContentArea",
    "LoadingScreen",
    "ErrorScreen",
    "PermissionDeniedScreen",
    "EmptyScreen",
]
