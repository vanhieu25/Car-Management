"""Supplier form dialog - S-NCC-02 - Add/Edit supplier form.

Features:
- Form inputs for all supplier fields
- Inline validation with error messages
- Email validation (BR-DATA-04)
- SĐT Vietnam validation (BR-DATA-05)
- Code (ma_ncc) uniqueness check

References:
- UC-NCC-01: Thêm mới nhà cung cấp
- UC-NCC-02: Sửa thông tin nhà cung cấp
- BR-NCC-01: Required fields
- BR-DATA-04: Email validation
- BR-DATA-05: SĐT validation
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression

from app.application.services.nha_cung_cap_service import (
    NhaCungCapService, NhaCungCapCreateData, NhaCungCapUpdateData,
    ValidationError, DuplicateCodeError, NotFoundError
)
from app.domain.entities import NhaCungCap


class SupplierFormDialog(QDialog):
    """Dialog for adding or editing a supplier.
    
    Signals:
        saved: Emitted when supplier was saved successfully.
    """
    
    saved = pyqtSignal()
    
    def __init__(
        self,
        db_conn,
        session,
        ncc: NhaCungCap = None,
        parent=None
    ):
        """Initialize supplier form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            ncc: NhaCungCap entity to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._ncc_service = NhaCungCapService(db_conn)
        self._ncc = ncc
        self._is_edit = ncc is not None
        
        self._setup_ui()
        
        if self._is_edit:
            self._populate_form(ncc)
    
    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm nhà cung cấp mới" if not self._is_edit else f"Sửa thông tin - {self._ncc.ten_ncc}"
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
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton[primary="true"] {
                background-color: #0066cc;
                color: white;
                border: none;
            }
            QPushButton[primary="true"]:hover {
                background-color: #0055aa;
            }
            QPushButton[secondary="true"] {
                background-color: #f2f2f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
            }
            QPushButton[secondary="true"]:hover {
                background-color: #e5e5ea;
            }
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
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Form group
        form_group = QGroupBox("Thông tin nhà cung cấp")
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
        
        # ma_ncc (required, only in add mode)
        ma_ncc_layout = QHBoxLayout()
        ma_ncc_layout.setSpacing(8)
        
        label = QLabel("Mã NCC *:")
        label.setMinimumWidth(100)
        ma_ncc_layout.addWidget(label)
        
        self._ma_ncc_input = QLineEdit()
        self._ma_ncc_input.setPlaceholderText("Nhập mã nhà cung cấp...")
        self._ma_ncc_input.setStyleSheet("""
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
        ma_ncc_layout.addWidget(self._ma_ncc_input, stretch=1)
        
        self._ma_ncc_error = QLabel("")
        self._ma_ncc_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        ma_ncc_error_layout = QHBoxLayout()
        ma_ncc_error_layout.addWidget(self._ma_ncc_input)
        ma_ncc_error_layout.addWidget(self._ma_ncc_error)
        form_layout.addLayout(ma_ncc_error_layout)
        form_layout.addLayout(ma_ncc_layout)
        
        # ten_ncc (required)
        ten_ncc_layout = QHBoxLayout()
        ten_ncc_layout.setSpacing(8)
        
        label = QLabel("Tên NCC *:")
        label.setMinimumWidth(100)
        ten_ncc_layout.addWidget(label)
        
        self._ten_ncc_input = QLineEdit()
        self._ten_ncc_input.setPlaceholderText("Nhập tên nhà cung cấp...")
        self._ten_ncc_input.setStyleSheet("""
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
        ten_ncc_layout.addWidget(self._ten_ncc_input, stretch=1)
        
        self._ten_ncc_error = QLabel("")
        self._ten_ncc_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        ten_ncc_error_layout = QHBoxLayout()
        ten_ncc_error_layout.addWidget(self._ten_ncc_input)
        ten_ncc_error_layout.addWidget(self._ten_ncc_error)
        form_layout.addLayout(ten_ncc_error_layout)
        form_layout.addLayout(ten_ncc_layout)
        
        # dia_chi
        dia_chi_layout = QHBoxLayout()
        dia_chi_layout.setSpacing(8)
        
        label = QLabel("Địa chỉ:")
        label.setMinimumWidth(100)
        dia_chi_layout.addWidget(label)
        
        self._dia_chi_input = QLineEdit()
        self._dia_chi_input.setPlaceholderText("Nhập địa chỉ...")
        self._dia_chi_input.setStyleSheet("""
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
        dia_chi_layout.addWidget(self._dia_chi_input, stretch=1)
        form_layout.addLayout(dia_chi_layout)
        
        # so_dien_thoai
        sdt_layout = QHBoxLayout()
        sdt_layout.setSpacing(8)
        
        label = QLabel("SĐT:")
        label.setMinimumWidth(100)
        sdt_layout.addWidget(label)
        
        self._sdt_input = QLineEdit()
        self._sdt_input.setPlaceholderText("Nhập số điện thoại (10-11 số bắt đầu bằng 0)...")
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
        
        self._sdt_error = QLabel("")
        self._sdt_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        sdt_error_layout = QHBoxLayout()
        sdt_error_layout.addWidget(self._sdt_input)
        sdt_error_layout.addWidget(self._sdt_error)
        form_layout.addLayout(sdt_error_layout)
        form_layout.addLayout(sdt_layout)
        
        # email
        email_layout = QHBoxLayout()
        email_layout.setSpacing(8)
        
        label = QLabel("Email:")
        label.setMinimumWidth(100)
        email_layout.addWidget(label)
        
        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Nhập email (VD: ncc@example.com)...")
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
        
        # nguoi_lien_he
        nguoi_lh_layout = QHBoxLayout()
        nguoi_lh_layout.setSpacing(8)
        
        label = QLabel("Người liên hệ:")
        label.setMinimumWidth(100)
        nguoi_lh_layout.addWidget(label)
        
        self._nguoi_lh_input = QLineEdit()
        self._nguoi_lh_input.setPlaceholderText("Nhập tên người liên hệ...")
        self._nguoi_lh_input.setStyleSheet("""
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
        nguoi_lh_layout.addWidget(self._nguoi_lh_input, stretch=1)
        form_layout.addLayout(nguoi_lh_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self._save_btn = QPushButton("Lưu")
        self._save_btn.setProperty("primary", True)
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self._save_btn)
        
        layout.addLayout(button_layout)
        
        # Disable ma_ncc in edit mode
        if self._is_edit:
            self._ma_ncc_input.setEnabled(False)
            self._ma_ncc_input.setToolTip("Mã NCC không thể thay đổi")
    
    def _populate_form(self, ncc: NhaCungCap):
        """Populate form with existing supplier data."""
        self._ma_ncc_input.setText(ncc.ma_ncc)
        self._ten_ncc_input.setText(ncc.ten_ncc)
        self._dia_chi_input.setText(ncc.dia_chi or "")
        self._sdt_input.setText(ncc.so_dien_thoai or "")
        self._email_input.setText(ncc.email or "")
        self._nguoi_lh_input.setText(ncc.nguoi_lien_he or "")
    
    def _clear_errors(self):
        """Clear all error messages."""
        self._ma_ncc_error.setText("")
        self._ten_ncc_error.setText("")
        self._sdt_error.setText("")
        self._email_error.setText("")
    
    def _on_save(self):
        """Handle save button click."""
        self._clear_errors()
        
        # Get values
        ma_ncc = self._ma_ncc_input.text().strip()
        ten_ncc = self._ten_ncc_input.text().strip()
        dia_chi = self._dia_chi_input.text().strip()
        sdt = self._sdt_input.text().strip()
        email = self._email_input.text().strip()
        nguoi_lh = self._nguoi_lh_input.text().strip()
        
        # Validate in add mode
        if not self._is_edit:
            if not ma_ncc:
                self._ma_ncc_error.setText("Mã NCC không được trống")
                self._ma_ncc_input.setFocus()
                return
        
        if not ten_ncc:
            self._ten_ncc_error.setText("Tên NCC không được trống")
            self._ten_ncc_input.setFocus()
            return
        
        # Validate email format
        if email:
            import re
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(pattern, email):
                self._email_error.setText("Email không hợp lệ")
                self._email_input.setFocus()
                return
        
        # Validate phone format (VN)
        if sdt:
            phone_clean = sdt.replace(" ", "").replace("-", "")
            pattern = r"^0[0-9]{9,10}$"
            if not re.match(pattern, phone_clean):
                self._sdt_error.setText("SĐT không hợp lệ (cần 10-11 số bắt đầu bằng 0)")
                self._sdt_input.setFocus()
                return
        
        try:
            if self._is_edit:
                # Update existing
                update_data = NhaCungCapUpdateData(
                    ten_ncc=ten_ncc,
                    dia_chi=dia_chi,
                    so_dien_thoai=sdt,
                    email=email,
                    nguoi_lien_he=nguoi_lh,
                )
                self._ncc_service.update(self._ncc.id, update_data)
                QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin nhà cung cấp")
            else:
                # Create new
                create_data = NhaCungCapCreateData(
                    ma_ncc=ma_ncc,
                    ten_ncc=ten_ncc,
                    dia_chi=dia_chi,
                    so_dien_thoai=sdt,
                    email=email,
                    nguoi_lien_he=nguoi_lh,
                )
                self._ncc_service.create(create_data)
                QMessageBox.information(self, "Thành công", "Đã thêm nhà cung cấp mới")
            
            self.saved.emit()
            self.accept()
            
        except DuplicateCodeError as e:
            self._ma_ncc_error.setText(str(e))
            self._ma_ncc_input.setFocus()
        except ValidationError as e:
            field = getattr(e, 'field', None)
            if field == 'ten_ncc':
                self._ten_ncc_error.setText(str(e))
                self._ten_ncc_input.setFocus()
            elif field == 'so_dien_thoai':
                self._sdt_error.setText(str(e))
                self._sdt_input.setFocus()
            elif field == 'email':
                self._email_error.setText(str(e))
                self._email_input.setFocus()
            else:
                QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")
