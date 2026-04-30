"""Change password dialog - S-AUTH-02 (BRD UC-SEC-02).

Implements:
- UI.03: 3 fields (old/new/confirm) with strength indicator
- UI.04: Force change password on first login (BR-NV-08)
- BR-SEC-02: Minimum 8 characters, at least 1 letter and 1 number
- BR-SEC-07: Requires old password verification
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from app.application.services.auth_service import AuthService, ChangePasswordResult
from app.infrastructure.security.password_hasher import PasswordValidator, password_validator
from app.infrastructure.database.connection import get_connection
from app.presentation.widgets.buttons import PrimaryButton, SecondaryButton
from app.presentation.widgets.inputs import StrengthIndicator
from app.presentation.widgets.dialogs import ToastDialog, ErrorDialog


class ChangePasswordDialog(QDialog):
    """Dialog for changing password.
    
    Can operate in two modes:
    1. Normal mode: requires old password (BR-SEC-07)
    2. Force mode: no old password required (BR-NV-08)
    
    Signals:
        password_changed: Emitted when password is changed successfully.
        cancelled: Emitted when user cancels.
    """
    
    password_changed = pyqtSignal()
    cancelled = pyqtSignal()
    
    def __init__(
        self,
        user_id: int,
        require_old_password: bool = True,
        force_change: bool = False,
        parent=None,
    ):
        """Initialize change password dialog.
        
        Args:
            user_id: ID of the user changing password.
            require_old_password: If True, require old password (normal mode).
                                 If False, skip old password (admin reset or first login).
            force_change: If True, user cannot cancel without changing (BR-NV-08).
            parent: Parent widget.
        """
        super().__init__(parent)
        self._user_id = user_id
        self._require_old = require_old_password
        self._force_change = force_change
        self._auth_service = None
        
        title = "Đổi mật khẩu" if require_old_password else "Đặt mật khẩu mới"
        if force_change:
            title = "Thay đổi mật khẩu bắt buộc"
        
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
        """)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        title = QLabel("🔐 Đổi mật khẩu", self)
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #1C1C1E;
        """)
        header_layout.addWidget(title)
        
        if self._force_change:
            note = QLabel(
                "Bạn phải thay đổi mật khẩu trước khi sử dụng hệ thống.",
                self
            )
        else:
            note = QLabel(
                "Mật khẩu mới phải có ít nhất 8 ký tự, gồm chữ và số.",
                self
            )
        note.setStyleSheet("""
            font-size: 13px;
            color: #8E8E93;
        """)
        note.setWordWrap(True)
        header_layout.addWidget(note)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Form card
        form_card = QWidget(self)
        form_card.setStyleSheet("""
            QWidget#form_card {
                background-color: white;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        form_card.setObjectName("form_card")
        
        form_layout = QVBoxLayout(form_card)
        form_layout.setSpacing(16)
        
        # Old password field (if required)
        self.old_password_layout = QVBoxLayout()
        self.old_password_layout.setSpacing(6)
        
        old_label = QLabel("Mật khẩu cũ", form_card)
        old_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #3C3C43;
        """)
        self.old_password_layout.addWidget(old_label)
        
        self.old_password_input = QLineEdit(form_card)
        self.old_password_input.setPlaceholderText("Nhập mật khẩu cũ")
        self.old_password_input.setMinimumHeight(44)
        self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D1D6;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                background-color: #F2F2F7;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
                background-color: white;
            }
        """)
        self.old_password_layout.addWidget(self.old_password_input)
        form_layout.addLayout(self.old_password_layout)
        
        if not self._require_old:
            self.old_password_layout.parent().removeItem(self.old_password_layout)
            self.old_password_layout.deleteLater()
        
        # New password field
        new_password_layout = QVBoxLayout()
        new_password_layout.setSpacing(6)
        
        new_label = QLabel("Mật khẩu mới", form_card)
        new_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #3C3C43;
        """)
        new_password_layout.addWidget(new_label)
        
        self.new_password_input = QLineEdit(form_card)
        self.new_password_input.setPlaceholderText("Nhập mật khẩu mới")
        self.new_password_input.setMinimumHeight(44)
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D1D6;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                background-color: #F2F2F7;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
                background-color: white;
            }
        """)
        self.new_password_input.textChanged.connect(self._on_new_password_changed)
        new_password_layout.addWidget(self.new_password_input)
        
        # Strength indicator
        self.strength_indicator = StrengthIndicator(form_card)
        self.strength_indicator.setMinimumWidth(200)
        new_password_layout.addWidget(self.strength_indicator)
        
        # Strength label
        self.strength_label = QLabel("", form_card)
        self.strength_label.setStyleSheet("""
            font-size: 12px;
            color: #8E8E93;
        """)
        new_password_layout.addWidget(self.strength_label)
        
        form_layout.addLayout(new_password_layout)
        
        # Confirm password field
        confirm_layout = QVBoxLayout()
        confirm_layout.setSpacing(6)
        
        confirm_label = QLabel("Xác nhận mật khẩu mới", form_card)
        confirm_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #3C3C43;
        """)
        confirm_layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit(form_card)
        self.confirm_input.setPlaceholderText("Nhập lại mật khẩu mới")
        self.confirm_input.setMinimumHeight(44)
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D1D6;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                background-color: #F2F2F7;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
                background-color: white;
            }
        """)
        self.confirm_input.returnPressed.connect(self._on_submit_clicked)
        confirm_layout.addWidget(self.confirm_input)
        
        form_layout.addLayout(confirm_layout)
        
        # Error message
        self.error_label = QLabel("", form_card)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("""
            QLabel {
                color: #FF3B30;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 12px;
                background-color: #FFF0F0;
                border-radius: 8px;
            }
        """)
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)
        
        layout.addWidget(form_card)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        if not self._force_change:
            cancel_btn = SecondaryButton("Hủy", self)
            cancel_btn.setMinimumHeight(48)
            cancel_btn.clicked.connect(self._on_cancel_clicked)
            btn_layout.addWidget(cancel_btn)
        
        self.submit_btn = PrimaryButton("Xác nhận", self)
        self.submit_btn.setMinimumHeight(48)
        self.submit_btn.clicked.connect(self._on_submit_clicked)
        btn_layout.addWidget(self.submit_btn, 1)
        
        layout.addLayout(btn_layout)
    
    def _on_new_password_changed(self, text: str):
        """Update password strength indicator."""
        score = password_validator.get_strength_score(text)
        self.strength_indicator.set_score(score)
        
        if not text:
            self.strength_label.setText("")
        elif score < 40:
            self.strength_label.setText("Mật khẩu yếu")
            self.strength_label.setStyleSheet("font-size: 12px; color: #FF3B30;")
        elif score < 70:
            self.strength_label.setText("Mật khẩu trung bình")
            self.strength_label.setStyleSheet("font-size: 12px; color: #FF9500;")
        else:
            self.strength_label.setText("Mật khẩu mạnh ✓")
            self.strength_label.setStyleSheet("font-size: 12px; color: #34C759;")
    
    def _on_submit_clicked(self):
        """Handle submit button click."""
        self._clear_error()
        
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_input.text()
        
        # Validate new password strength
        is_valid, error_msg = password_validator.validate(new_password)
        if not is_valid:
            self._show_error(error_msg)
            return
        
        # Check password match
        if new_password != confirm_password:
            self._show_error("Mật khẩu xác nhận không khớp")
            return
        
        # Get auth service
        if self._auth_service is None:
            conn = get_connection()
            self._auth_service = AuthService(conn)
        
        # Submit based on mode
        if self._require_old:
            old_password = self.old_password_input.text()
            if not old_password:
                self._show_error("Vui lòng nhập mật khẩu cũ")
                return
            
            result = self._auth_service.change_password(
                self._user_id,
                old_password,
                new_password,
            )
        else:
            result = self._auth_service.force_change_password(
                self._user_id,
                new_password,
            )
        
        if result.success:
            ToastDialog.show_success("Đổi mật khẩu thành công!")
            self.password_changed.emit()
            self.close()
        else:
            self._show_error(result.error_message or "Đổi mật khẩu thất bại")
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.cancelled.emit()
        self.close()
    
    def _show_error(self, message: str):
        """Show error message."""
        if message:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
        else:
            self._clear_error()
    
    def _clear_error(self):
        """Clear error message."""
        self.error_label.setVisible(False)
    
    def closeEvent(self, event):
        """Handle dialog close."""
        if self._force_change:
            # Don't allow closing without changing password
            pass
        else:
            self.cancelled.emit()
        super().closeEvent(event)
