"""Login screen - S-AUTH-01 (BRD UC-SEC-01).

Implements:
- BR-UI-01: Username + password inputs with "Đăng nhập" PrimaryButton pill
- BR-UI-02: Inline error messages
- BR-SEC-05: Show lock time when account is locked
- BR-SEC-06: Session timeout notification
"""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGraphicsOpacityEffect,
)
from PyQt6.QtWidgets import QDialog

from app.application.services.auth_service import AuthService, LoginError, LoginResult
from app.application.services.session import session_manager
from app.infrastructure.security.password_hasher import PasswordValidator, password_validator
from app.infrastructure.database.connection import get_connection
from app.presentation.widgets.buttons import PrimaryButton, SecondaryButton


class LoginScreen(QDialog):
    """Login dialog implementing S-AUTH-01 (UC-SEC-01).
    
    Signals:
        login_successful: Emitted when user logs in successfully.
        change_password_requested: Emitted when user needs to change password.
    """
    
    login_successful = pyqtSignal()
    change_password_requested = pyqtSignal(int)  # user_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng nhập - Car Management")
        self.setMinimumSize(420, 520)
        self.setMaximumSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
        """)
        
        self._auth_service = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo / App name
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(8)
        
        app_name = QLabel("🚗 Car Management", self)
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #1C1C1E;
        """)
        logo_layout.addWidget(app_name)
        
        subtitle = QLabel("Đại lý xe hơi", self)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #8E8E93;
        """)
        logo_layout.addWidget(subtitle)
        
        layout.addLayout(logo_layout)
        layout.addSpacing(20)
        
        # Login form card
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
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(6)
        
        username_label = QLabel("Tên đăng nhập", form_card)
        username_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #3C3C43;
        """)
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit(form_card)
        self.username_input.setPlaceholderText("Nhập tên đăng nhập")
        self.username_input.setMinimumHeight(48)
        self.username_input.setStyleSheet("""
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
        self.username_input.returnPressed.connect(self._on_login_clicked)
        username_layout.addWidget(self.username_input)
        form_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(6)
        
        password_label = QLabel("Mật khẩu", form_card)
        password_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #3C3C43;
        """)
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit(form_card)
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setMinimumHeight(48)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
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
        self.password_input.returnPressed.connect(self._on_login_clicked)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # Error message label
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
        
        # Login button
        self.login_btn = PrimaryButton("Đăng nhập", form_card)
        self.login_btn.setMinimumSize(0, 50)
        self.login_btn.clicked.connect(self._on_login_clicked)
        form_layout.addWidget(self.login_btn)
        
        # Version info
        version_label = QLabel("v1.0.0", form_card)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            font-size: 11px;
            color: #C7C7CC;
        """)
        form_layout.addWidget(version_label)
        
        layout.addWidget(form_card)
        
        # Spacer at bottom
        layout.addStretch()
    
    def _get_auth_service(self) -> AuthService:
        """Get or create auth service instance."""
        if self._auth_service is None:
            conn = get_connection()
            self._auth_service = AuthService(conn)
        return self._auth_service
    
    def _on_login_clicked(self):
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Clear previous error
        self._show_error("")
        
        # Basic validation
        if not username:
            self._show_error("Vui lòng nhập tên đăng nhập")
            self.username_input.setFocus()
            return
        
        if not password:
            self._show_error("Vui lòng nhập mật khẩu")
            self.password_input.setFocus()
            return
        
        # Disable button during login
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Đang đăng nhập...")
        
        try:
            auth_service = self._get_auth_service()
            result = auth_service.login(username, password)
            
            if result.success:
                self._handle_successful_login(result)
            else:
                self._handle_failed_login(result)
        
        except Exception as e:
            self._show_error(f"Lỗi hệ thống: {str(e)}")
        
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Đăng nhập")
    
    def _handle_successful_login(self, result: LoginResult):
        """Handle successful login."""
        user = result.user
        
        # Create session
        session_manager.login(
            user_id=user.id,
            username=user.username,
            ho_ten=user.ho_ten,
            vai_tro_id=user.vai_tro_id,
            vai_tro_ma=self._get_role_ma(user.vai_tro_id),
        )
        
        # Check if password change required
        if result.must_change_password:
            self.close()
            self.change_password_requested.emit(user.id)
        else:
            self.close()
            self.login_successful.emit()
    
    def _handle_failed_login(self, result: LoginResult):
        """Handle failed login attempt."""
        error = result.error
        
        if error == LoginError.ACCOUNT_LOCKED:
            lock_time = result.error_params.get("lock_time", "")
            if lock_time:
                try:
                    lock_dt = datetime.fromisoformat(lock_time)
                    lock_str = lock_dt.strftime("%H:%M ngày %d/%m/%Y")
                    msg = f"Tài khoản bị khóa đến {lock_str}. Vui lòng thử lại sau."
                except (ValueError, TypeError):
                    msg = "Tài khoản bị khóa. Vui lòng thử lại sau."
            else:
                msg = "Tài khoản bị khóa. Vui lòng thử lại sau."
            self._show_error(msg)
        
        elif error == LoginError.WRONG_PASSWORD:
            remaining = result.error_params.get("attempts_remaining", 0)
            msg = f"Mật khẩu không đúng. Còn {remaining} lần thử."
            self._show_error(msg)
        
        elif error == LoginError.ACCOUNT_INACTIVE:
            self._show_error("Tài khoản đã bị vô hiệu hóa. Liên hệ quản trị viên.")
        
        elif error == LoginError.USER_NOT_FOUND:
            self._show_error("Tài khoản không tồn tại.")
        
        else:
            self._show_error(error.value if error else "Đăng nhập thất bại")
    
    def _get_role_ma(self, vai_tro_id: int) -> str:
        """Get role code from vai_tro_id."""
        role_map = {
            1: "admin",
            2: "sales",
            3: "ky_thuat_bh",
        }
        return role_map.get(vai_tro_id, "")
    
    def _show_error(self, message: str):
        """Show or hide error message."""
        if message:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
        else:
            self.error_label.setVisible(False)
    
    def clear(self):
        """Clear form fields and errors."""
        self.username_input.clear()
        self.password_input.clear()
        self._show_error("")
