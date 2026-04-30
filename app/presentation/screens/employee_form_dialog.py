"""Employee form dialog - S-NV-02 - Add/Edit employee form.

Features:
- Form inputs for all employee fields
- Inline validation with error messages
- Email validation
- On save: show generated password in a dialog with "Sao chép" button
- Warning text: "Hãy lưu lại mật khẩu này. Không thể hiện lại sau."

References:
- BR-NV-01..08: Employee management rules
- BR-SEC-01: Password hashing with bcrypt
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.nhan_vien_service import (
    NhanVienService, NhanVienCreateData, NhanVienUpdateData,
    DuplicateUsernameError, DuplicateEmailError,
    ValidationError as NVValidationError
)
from app.domain.entities import NhanVien


class PasswordDisplayDialog(QDialog):
    """Dialog to display generated password after employee creation."""
    
    def __init__(self, username: str, password: str, parent=None):
        """Initialize password display dialog.
        
        Args:
            username: Employee username.
            password: Generated password.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._username = username
        self._password = password
        self.setWindowTitle("Mật khẩu được tạo")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Warning icon
        warning_label = QLabel("⚠️", self)
        warning_label.setStyleSheet("font-size: 48px;")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)
        
        # Warning text
        warning_text = QLabel(
            "Hãy lưu lại mật khẩu này.\nKhông thể hiện lại sau.",
            self
        )
        warning_text.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #FF3B30;
        """)
        warning_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_text.setWordWrap(True)
        layout.addWidget(warning_text)
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:", self)
        username_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        username_layout.addWidget(username_label)
        
        username_value = QLabel(self._username, self)
        username_value.setStyleSheet("font-size: 14px; color: #1C1C1E;")
        username_layout.addWidget(username_value)
        username_layout.addStretch()
        
        layout.addLayout(username_layout)
        
        # Password field
        password_layout = QHBoxLayout()
        password_label = QLabel("Mật khẩu:", self)
        password_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        password_layout.addWidget(password_label)
        
        self._password_input = QLineEdit(self)
        self._password_input.setText(self._password)
        self._password_input.setReadOnly(True)
        self._password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                font-size: 14px;
                font-family: monospace;
                background-color: #F2F2F7;
            }
        """)
        password_layout.addWidget(self._password_input, stretch=1)
        
        self._copy_btn = QPushButton("📋 Sao chép", self)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0055BB;
            }
        """)
        self._copy_btn.clicked.connect(self._on_copy)
        password_layout.addWidget(self._copy_btn)
        
        layout.addLayout(password_layout)
        
        # Note
        note_label = QLabel(
            "Nhân viên sẽ phải đổi mật khẩu khi đăng nhập lần đầu.",
            self
        )
        note_label.setStyleSheet("font-size: 12px; color: #8E8E93;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # Close button
        close_btn = QPushButton("Đóng", self)
        close_btn.setMinimumHeight(44)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2DB14E;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _on_copy(self):
        """Handle copy button click."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._password_input.text())
        
        self._copy_btn.setText("✓ Đã sao chép")
        self._copy_btn.setEnabled(False)
        
        # Show toast-like feedback
        QMessageBox.information(
            self,
            "Đã sao chép",
            "Mật khẩu đã được sao chép vào clipboard."
        )


class EmployeeFormDialog(QDialog):
    """Dialog for adding or editing an employee.
    
    Signals:
        saved: Emitted when employee was saved successfully.
    """
    
    saved = pyqtSignal()
    
    def __init__(
        self,
        db_conn,
        session,
        nhan_vien: NhanVien = None,
        parent=None
    ):
        """Initialize employee form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            nhan_vien: NhanVien entity to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._nv_service = NhanVienService(db_conn, session)
        self._nhan_vien = nhan_vien
        self._is_edit = nhan_vien is not None
        self._generated_password: str = None
        
        self._setup_ui()
        
        if self._is_edit:
            self._populate_form(nhan_vien)
    
    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm nhân viên mới" if not self._is_edit else f"Sửa thông tin - {self._nhan_vien.ho_ten}"
        self.setWindowTitle(title)
        self.setMinimumSize(550, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-size: 14px;
                color: #1d1d1f;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Form group
        form_group = QGroupBox("Thông tin nhân viên")
        form_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 16px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        # username (required for new)
        username_layout = QHBoxLayout()
        username_layout.setSpacing(8)
        
        label = QLabel("Username *:")
        label.setMinimumWidth(100)
        username_layout.addWidget(label)
        
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("VD: nguyenvana")
        self._username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        username_layout.addWidget(self._username_input, stretch=1)
        
        self._username_error = QLabel("")
        self._username_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        username_layout.addWidget(self._username_error)
        
        # Disable username editing in edit mode
        if self._is_edit:
            self._username_input.setEnabled(False)
            self._username_input.setStyleSheet("""
                QLineEdit {
                    padding: 10px 12px;
                    border: 1px solid #d2d2d7;
                    border-radius: 6px;
                    font-size: 14px;
                    background: #f5f5f7;
                }
            """)
        
        form_layout.addLayout(username_layout)
        
        # ho_ten (required)
        ho_ten_layout = QHBoxLayout()
        ho_ten_layout.setSpacing(8)
        
        label = QLabel("Họ tên *:")
        label.setMinimumWidth(100)
        ho_ten_layout.addWidget(label)
        
        self._ho_ten_input = QLineEdit()
        self._ho_ten_input.setPlaceholderText("VD: Nguyễn Văn A")
        self._ho_ten_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        ho_ten_layout.addWidget(self._ho_ten_input, stretch=1)
        
        self._ho_ten_error = QLabel("")
        self._ho_ten_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        ho_ten_layout.addWidget(self._ho_ten_error)
        
        form_layout.addLayout(ho_ten_layout)
        
        # email (required)
        email_layout = QHBoxLayout()
        email_layout.setSpacing(8)
        
        email_label = QLabel("Email *:")
        email_label.setMinimumWidth(100)
        email_layout.addWidget(email_label)
        
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("VD: nguyenvana@email.com")
        self._email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        email_layout.addWidget(self._email_input, stretch=1)
        
        self._email_error = QLabel("")
        self._email_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        email_layout.addWidget(self._email_error)
        
        form_layout.addLayout(email_layout)
        
        # so_dien_thoai (optional)
        sdt_layout = QHBoxLayout()
        sdt_layout.setSpacing(8)
        
        sdt_label = QLabel("SĐT:")
        sdt_label.setMinimumWidth(100)
        sdt_layout.addWidget(sdt_label)
        
        self._sdt_input = QLineEdit()
        self._sdt_input.setPlaceholderText("VD: 0989123456")
        self._sdt_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        sdt_layout.addWidget(self._sdt_input, stretch=1)
        
        form_layout.addLayout(sdt_layout)
        
        # dia_chi (optional)
        dc_layout = QHBoxLayout()
        dc_layout.setSpacing(8)
        
        dc_label = QLabel("Địa chỉ:")
        dc_label.setMinimumWidth(100)
        dc_layout.addWidget(dc_label)
        
        self._dc_input = QLineEdit()
        self._dc_input.setPlaceholderText("VD: 123 Nguyễn Trãi, Q1, TP.HCM")
        self._dc_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        dc_layout.addWidget(self._dc_input, stretch=1)
        form_layout.addLayout(dc_layout)
        
        # vai_tro (optional, default to sales)
        vt_layout = QHBoxLayout()
        vt_layout.setSpacing(8)
        
        vt_label = QLabel("Vai trò:")
        vt_label.setMinimumWidth(100)
        vt_layout.addWidget(vt_label)
        
        self._vai_tro_combo = QComboBox()
        self._vai_tro_combo.addItems(["Sales", "Kỹ thuật BH", "Admin"])
        self._vai_tro_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        vt_layout.addWidget(self._vai_tro_combo, stretch=1)
        
        form_layout.addLayout(vt_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Note
        note_label = QLabel("* Trường bắt buộc" + (" (Username không thể sửa sau khi tạo)" if not self._is_edit else ""))
        note_label.setStyleSheet("color: #86868b; font-size: 12px; font-style: italic;")
        layout.addWidget(note_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._cancel_btn = QPushButton("Huỷ bỏ")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        
        self._save_btn = QPushButton("💾 Lưu")
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)
        
        layout.addLayout(btn_layout)
    
    def _populate_form(self, nv: NhanVien):
        """Populate form with existing employee data.
        
        Args:
            nv: NhanVien entity to edit.
        """
        self._username_input.setText(nv.username)
        self._ho_ten_input.setText(nv.ho_ten)
        self._email_input.setText(nv.email or "")
        self._sdt_input.setText(nv.so_dien_thoai or "")
        self._dc_input.setText(nv.dia_chi or "")
        
        # Set vai_tro combo (0-indexed, vai_tro_id is 1-3)
        vai_tro_index = nv.vai_tro_id - 1 if nv.vai_tro_id in (1, 2, 3) else 0
        self._vai_tro_combo.setCurrentIndex(vai_tro_index)
    
    def _on_save(self):
        """Handle save button click."""
        # Clear previous errors
        self._username_error.setText("")
        self._ho_ten_error.setText("")
        self._email_error.setText("")
        
        try:
            if self._is_edit:
                # Update existing employee
                # Map combo index to vai_tro_id (1-indexed)
                vai_tro_map = {0: 2, 1: 3, 2: 1}  # Sales, Ky thuat BH, Admin
                
                data = NhanVienUpdateData(
                    ho_ten=self._ho_ten_input.text().strip(),
                    email=self._email_input.text().strip(),
                    so_dien_thoai=self._sdt_input.text().strip() or None,
                    dia_chi=self._dc_input.text().strip() or None,
                )
                
                self._nv_service.update(self._nhan_vien.id, data)
                
                QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin nhân viên thành công!")
            else:
                # Create new employee
                vai_tro_map = {0: 2, 1: 3, 2: 1}  # Sales, Ky thuat BH, Admin
                
                data = NhanVienCreateData(
                    username=self._username_input.text().strip(),
                    ho_ten=self._ho_ten_input.text().strip(),
                    email=self._email_input.text().strip(),
                    so_dien_thoai=self._sdt_input.text().strip(),
                    dia_chi=self._dc_input.text().strip(),
                    vai_tro_id=vai_tro_map[self._vai_tro_combo.currentIndex()],
                )
                
                created_nv, raw_password = self._nv_service.create(data)
                self._generated_password = raw_password
                
                QMessageBox.information(
                    self,
                    "Thành công",
                    "Đã thêm nhân viên mới thành công!"
                )
                
                # Show password display dialog
                password_dialog = PasswordDisplayDialog(
                    created_nv.username,
                    raw_password,
                    self
                )
                password_dialog.exec()
            
            self.saved.emit()
            self.accept()
            
        except NVValidationError as e:
            # Show field-specific errors
            for error in e.errors:
                if "username" in error.lower():
                    self._username_error.setText(error)
                elif "ho_ten" in error.lower() or "họ tên" in error.lower():
                    self._ho_ten_error.setText(error)
                elif "email" in error.lower():
                    self._email_error.setText(error)
                else:
                    QMessageBox.warning(self, "Lỗi", error)
                    
        except DuplicateUsernameError as e:
            self._username_error.setText("Username đã được sử dụng")
            QMessageBox.warning(self, "Trùng Username", str(e))
            
        except DuplicateEmailError as e:
            self._email_error.setText("Email đã được sử dụng")
            QMessageBox.warning(self, "Trùng Email", str(e))
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")
