"""Customer form dialog - S-KH-02 - Add/Edit customer form.

Features:
- Form inputs for all customer fields
- Inline validation with error messages
- Email validation (BR-DATA-04)
- SĐT Vietnam validation (BR-DATA-05)
- Warning "SĐT đã tồn tại — KH: [tên]" when phone already exists (BR-KH-02)

References:
- UC-KH-01: Thêm mới khách hàng
- UC-KH-02: Sửa thông tin khách hàng
- BR-KH-01: Required fields
- BR-KH-02: SĐT unique
- BR-KH-06: Email, SĐT validation
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression

from app.application.services.khach_hang_service import (
    KhachHangService, KhachHangCreateData, KhachHangUpdateData,
    ValidationError, DuplicatePhoneError, DuplicateEmailError
)
from app.domain.entities import KhachHang


class CustomerFormDialog(QDialog):
    """Dialog for adding or editing a customer.
    
    Signals:
        saved: Emitted when customer was saved successfully.
    """
    
    saved = pyqtSignal()
    
    def __init__(
        self,
        db_conn,
        session,
        khach_hang: KhachHang = None,
        parent=None
    ):
        """Initialize customer form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            khach_hang: KhachHang entity to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._kh_service = KhachHangService(db_conn)
        self._khach_hang = khach_hang
        self._is_edit = khach_hang is not None
        
        self._setup_ui()
        
        if self._is_edit:
            self._populate_form(khach_hang)
    
    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm khách hàng mới" if not self._is_edit else f"Sửa thông tin - {self._khach_hang.ho_ten}"
        self.setWindowTitle(title)
        self.setMinimumSize(550, 450)
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
        form_group = QGroupBox("Thông tin khách hàng")
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
        
        # ho_ten (required)
        ho_ten_layout = QHBoxLayout()
        ho_ten_layout.setSpacing(8)
        
        label = QLabel("Họ tên *:")
        label.setMinimumWidth(100)
        ho_ten_layout.addWidget(label)
        
        self._ho_ten_input = QLineEdit()
        self._ho_ten_input.setPlaceholderText("Nhập họ tên đầy đủ...")
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
        ho_ten_error_layout = QHBoxLayout()
        ho_ten_error_layout.addWidget(self._ho_ten_input)
        ho_ten_error_layout.addWidget(self._ho_ten_error)
        form_layout.addLayout(ho_ten_error_layout)
        form_layout.addLayout(ho_ten_layout)
        
        # so_dien_thoai (required, unique)
        sdt_layout = QHBoxLayout()
        sdt_layout.setSpacing(8)
        
        sdt_label = QLabel("SĐT *:")
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
        
        self._sdt_warning = QLabel("")
        self._sdt_warning.setStyleSheet("color: #ff9500; font-size: 12px;")
        sdt_warning_layout = QHBoxLayout()
        sdt_warning_layout.addWidget(self._sdt_input)
        sdt_warning_layout.addWidget(self._sdt_warning)
        form_layout.addLayout(sdt_warning_layout)
        form_layout.addLayout(sdt_layout)
        
        # email (required)
        email_layout = QHBoxLayout()
        email_layout.setSpacing(8)
        
        email_label = QLabel("Email *:")
        email_label.setMinimumWidth(100)
        email_layout.addWidget(email_label)
        
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("VD: contact@example.com")
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
        email_error_layout = QHBoxLayout()
        email_error_layout.addWidget(self._email_input)
        email_error_layout.addWidget(self._email_error)
        form_layout.addLayout(email_error_layout)
        form_layout.addLayout(email_layout)
        
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
        
        # ngay_sinh (optional)
        ns_layout = QHBoxLayout()
        ns_layout.setSpacing(8)
        
        ns_label = QLabel("Ngày sinh:")
        ns_label.setMinimumWidth(100)
        ns_layout.addWidget(ns_label)
        
        self._ns_input = QLineEdit()
        self._ns_input.setPlaceholderText("VD: 1990-05-15")
        self._ns_input.setStyleSheet("""
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
        ns_layout.addWidget(self._ns_input, stretch=1)
        
        ns_hint = QLabel("(Định dạng: YYYY-MM-DD)")
        ns_hint.setStyleSheet("color: #86868b; font-size: 12px;")
        ns_layout.addWidget(ns_hint)
        
        form_layout.addLayout(ns_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Note
        note_label = QLabel("* Trường bắt buộc")
        note_label.setStyleSheet("color: #86868b; font-size: 12px; font-style: italic;")
        layout.addWidget(note_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._cancel_btn = QPushButton("Hủy bỏ")
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
    
    def _populate_form(self, kh: KhachHang):
        """Populate form with existing customer data.
        
        Args:
            kh: KhachHang entity to edit.
        """
        self._ho_ten_input.setText(kh.ho_ten)
        self._sdt_input.setText(kh.so_dien_thoai)
        self._email_input.setText(kh.email or "")
        self._dc_input.setText(kh.dia_chi or "")
        self._ns_input.setText(kh.ngay_sinh or "")
    
    def _on_save(self):
        """Handle save button click."""
        # Clear previous errors
        self._ho_ten_error.setText("")
        self._sdt_warning.setText("")
        self._email_error.setText("")
        
        try:
            if self._is_edit:
                # Update existing customer
                data = KhachHangUpdateData(
                    ho_ten=self._ho_ten_input.text().strip(),
                    so_dien_thoai=self._sdt_input.text().strip(),
                    email=self._email_input.text().strip(),
                    dia_chi=self._dc_input.text().strip(),
                    ngay_sinh=self._ns_input.text().strip() or None,
                )
                
                self._kh_service.update(
                    self._khach_hang.id,
                    data,
                    nhan_vien_id=self._session.nhan_vien_id if self._session else None,
                )
                
                QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin khách hàng thành công!")
            else:
                # Create new customer
                data = KhachHangCreateData(
                    ho_ten=self._ho_ten_input.text().strip(),
                    so_dien_thoai=self._sdt_input.text().strip(),
                    email=self._email_input.text().strip(),
                    dia_chi=self._dc_input.text().strip(),
                    ngay_sinh=self._ns_input.text().strip() or None,
                    created_by=self._session.nhan_vien_id if self._session else None,
                )
                
                self._kh_service.create(
                    data,
                    nhan_vien_id=self._session.nhan_vien_id if self._session else None,
                )
                
                QMessageBox.information(self, "Thành công", "Đã thêm khách hàng mới thành công!")
            
            self.saved.emit()
            self.accept()
            
        except ValidationError as e:
            # Show field-specific errors
            for error in e.errors:
                if "ho_ten" in error.lower() or "họ tên" in error.lower():
                    self._ho_ten_error.setText(error)
                elif "email" in error.lower():
                    self._email_error.setText(error)
                elif "điện thoại" in error.lower() or "phone" in error.lower():
                    self._sdt_warning.setText(error)
                else:
                    QMessageBox.warning(self, "Lỗi", error)
                    
        except DuplicatePhoneError as e:
            # BR-KH-02: Show warning with customer name
            existing_kh = self._kh_service.get_by_phone(self._sdt_input.text().strip())
            name = existing_kh.ho_ten if existing_kh else "N/A"
            self._sdt_warning.setText(f"SĐT đã tồn tại — KH: {name}")
            QMessageBox.warning(self, "Trùng SĐT", f"Số điện thoại này đã được sử dụng bởi khách hàng: {name}")
            
        except DuplicateEmailError as e:
            self._email_error.setText("Email đã được sử dụng")
            QMessageBox.warning(self, "Trùng Email", str(e))
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")
