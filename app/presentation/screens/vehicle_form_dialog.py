"""Vehicle form dialog - S-XE-02 - Add/Edit vehicle form.

Features:
- Form inputs for all vehicle fields
- ma_xe disabled when editing (BR-XE-01: immutable)
- Inline validation with error messages
- BR-XE-09: nam_san_xuat ∈ [1990, current_year + 1]
- BR-DATA-01: gia_ban ≥ 0
- BR-DATA-02: so_luong_ton ≥ 0

References:
- UC-XE-01: Thêm mới xe
- UC-XE-02: Sửa thông tin xe
- BR-XE-01: ma_xe cannot be changed after creation
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QFormLayout, QMessageBox,
    QGroupBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.xe_service import (
    XeService, XeCreateData, XeUpdateData,
    ValidationError, DuplicateMaXeError
)
from app.domain.entities import Xe


class VehicleFormDialog(QDialog):
    """Dialog for adding or editing a vehicle.
    
    Signals:
        saved: Emitted when vehicle was saved successfully.
    """
    
    saved = pyqtSignal()
    
    def __init__(
        self,
        db_conn,
        session,
        xe: Xe = None,
        parent=None
    ):
        """Initialize vehicle form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            xe: Xe entity to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._xe_service = XeService(db_conn)
        self._xe = xe
        self._is_edit = xe is not None
        
        self._setup_ui()
        
        if self._is_edit:
            self._populate_form(xe)
    
    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm xe mới" if not self._is_edit else f"Sửa thông tin xe - {self._xe.ma_xe}"
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
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
        form_group = QGroupBox("Thông tin xe")
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
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setSpacing(12)
        
        # ma_xe - disabled when editing (BR-XE-01)
        self._ma_xe_input = QLineEdit()
        self._ma_xe_input.setPlaceholderText("VD: XE001")
        self._ma_xe_input.setMaxLength(50)
        self._ma_xe_input.setStyleSheet("""
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
            QLineEdit:disabled {
                background: #f5f5f7;
                color: #86868b;
            }
        """)
        if self._is_edit:
            self._ma_xe_input.setDisabled(True)
        form_layout.addRow("Mã xe *:", self._ma_xe_input)
        
        # hang
        self._hang_input = QLineEdit()
        self._hang_input.setPlaceholderText("VD: Toyota, Honda, Ford...")
        self._hang_input.setMaxLength(100)
        self._hang_input.setStyleSheet(self._ma_xe_input.styleSheet())
        form_layout.addRow("Hãng xe *:", self._hang_input)
        
        # dong_xe
        self._dong_input = QLineEdit()
        self._dong_input.setPlaceholderText("VD: Camry, Civic, Everest...")
        self._dong_input.setMaxLength(100)
        self._dong_input.setStyleSheet(self._ma_xe_input.styleSheet())
        form_layout.addRow("Dòng xe *:", self._dong_input)
        
        # nam_san_xuat (BR-XE-09: 1990 - current_year+1)
        self._nam_spin = QSpinBox()
        self._nam_spin.setRange(1990, 2027)
        self._nam_spin.setSuffix("")
        self._nam_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QSpinBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        form_layout.addRow("Năm sản xuất *:", self._nam_spin)
        
        # mau_sac
        self._mau_input = QLineEdit()
        self._mau_input.setPlaceholderText("VD: Đen, Trắng, Đỏ, Xanh...")
        self._mau_input.setMaxLength(50)
        self._mau_input.setStyleSheet(self._ma_xe_input.styleSheet())
        form_layout.addRow("Màu sắc:", self._mau_input)
        
        # gia_ban (BR-DATA-01: ≥ 0)
        self._gia_spin = QDoubleSpinBox()
        self._gia_spin.setRange(0, 9999999999)
        self._gia_spin.setDecimals(0)
        self._gia_spin.setSuffix(" đ")
        self._gia_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        form_layout.addRow("Giá bán *:", self._gia_spin)
        
        # so_luong_ton (BR-DATA-02: ≥ 0)
        self._ton_spin = QSpinBox()
        self._ton_spin.setRange(0, 9999)
        self._ton_spin.setSuffix(" xe")
        self._ton_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QSpinBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        form_layout.addRow("Số lượng tồn:", self._ton_spin)
        
        # muc_toi_thieu
        self._muc_spin = QSpinBox()
        self._muc_spin.setRange(0, 100)
        self._muc_spin.setSuffix(" xe")
        self._muc_spin.setStyleSheet(self._ton_spin.styleSheet())
        self._muc_spin.setValue(2)
        form_layout.addRow("Mức tồn tối thiểu:", self._muc_spin)
        
        # mo_ta
        self._mo_ta_input = QLineEdit()
        self._mo_ta_input.setPlaceholderText("Mô tả thêm về xe...")
        self._mo_ta_input.setMaxLength(500)
        self._mo_ta_input.setStyleSheet(self._ma_xe_input.styleSheet())
        form_layout.addRow("Mô tả:", self._mo_ta_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Note about required fields
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
    
    def _populate_form(self, xe: Xe):
        """Populate form with existing vehicle data.
        
        Args:
            xe: Xe entity to edit.
        """
        self._ma_xe_input.setText(xe.ma_xe)
        self._hang_input.setText(xe.hang)
        self._dong_input.setText(xe.dong_xe)
        self._nam_spin.setValue(xe.nam_san_xuat)
        self._mau_input.setText(xe.mau_sac or "")
        self._gia_spin.setValue(xe.gia_ban)
        self._ton_spin.setValue(xe.so_luong_ton)
        self._muc_spin.setValue(xe.muc_toi_thieu)
        self._mo_ta_input.setText(xe.mo_ta or "")
    
    def _validate(self) -> bool:
        """Validate form inputs.
        
        Returns:
            True if valid, False otherwise.
        """
        errors = []
        
        # Check required fields
        if not self._ma_xe_input.text().strip():
            errors.append("Mã xe không được để trống")
        
        if not self._hang_input.text().strip():
            errors.append("Hãng xe không được để trống")
        
        if not self._dong_input.text().strip():
            errors.append("Dòng xe không được để trống")
        
        # Check year range (BR-XE-09)
        year = self._nam_spin.value()
        current_year = 2026
        if year < 1990 or year > current_year + 1:
            errors.append(f"Năm sản xuất phải từ 1990 đến {current_year + 1}")
        
        # Check price (BR-DATA-01)
        if self._gia_spin.value() < 0:
            errors.append("Giá bán không được âm")
        
        # Check stock (BR-DATA-02)
        if self._ton_spin.value() < 0:
            errors.append("Số lượng tồn không được âm")
        
        if errors:
            QMessageBox.warning(self, "Lỗi validation", "\n".join(f"• {e}" for e in errors))
            return False
        
        return True
    
    def _on_save(self):
        """Handle save button click."""
        if not self._validate():
            return
        
        try:
            if self._is_edit:
                # Update existing vehicle
                data = XeUpdateData(
                    hang=self._hang_input.text().strip(),
                    dong_xe=self._dong_input.text().strip(),
                    nam_san_xuat=self._nam_spin.value(),
                    mau_sac=self._mau_input.text().strip() or None,
                    gia_ban=int(self._gia_spin.value()),
                    so_luong_ton=self._ton_spin.value(),
                    muc_toi_thieu=self._muc_spin.value(),
                    mo_ta=self._mo_ta_input.text().strip() or None,
                )
                
                self._xe_service.update(
                    xe_id=self._xe.id,
                    data=data,
                    nhan_vien_id=self._session.nhan_vien_id if self._session else None,
                )
                
                QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin xe thành công!")
            else:
                # Create new vehicle
                data = XeCreateData(
                    ma_xe=self._ma_xe_input.text().strip(),
                    hang=self._hang_input.text().strip(),
                    dong_xe=self._dong_input.text().strip(),
                    nam_san_xuat=self._nam_spin.value(),
                    gia_ban=int(self._gia_spin.value()),
                    mau_sac=self._mau_input.text().strip() or "",
                    so_luong_ton=self._ton_spin.value(),
                    muc_toi_thieu=self._muc_spin.value(),
                    mo_ta=self._mo_ta_input.text().strip() or "",
                    created_by=self._session.nhan_vien_id if self._session else None,
                )
                
                self._xe_service.create(
                    data=data,
                    nhan_vien_id=self._session.nhan_vien_id if self._session else None,
                )
                
                QMessageBox.information(self, "Thành công", "Đã thêm xe mới thành công!")
            
            self.saved.emit()
            self.accept()
            
        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi validation", str(e))
        except DuplicateMaXeError as e:
            QMessageBox.warning(self, "Lỗi", f"Mã xe '{self._ma_xe_input.text().strip()}' đã tồn tại. Vui lòng chọn mã khác.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")
