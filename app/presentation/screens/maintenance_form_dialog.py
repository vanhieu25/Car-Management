"""Maintenance form dialog - S-HM-02 - Add/Edit maintenance appointment form.

Features:
- Form fields: khach_hang (searchable dropdown), xe (auto-load based on KH),
  ngay_du_kien, km_xe, noi_dung, chi_phi, nhan_vien_id (technique dropdown)
- Validate: KH required, xe required, ngay > today, chi_phi >= 0
- On save → calls BaoDuongService.create()

References:
- BR-HM-01: Create bao_duong records
- BR-HM-02: Status flow
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QDateEdit, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from app.presentation.widgets.inputs import InlineNumericEdit

from app.application.services.bao_duong_service import (
    BaoDuongService, BaoDuongCreateData, BaoDuongUpdateData,
    ValidationError, BaoDuongNotFoundError
)
from app.application.services.session import CurrentSession
from app.domain.entities import BaoDuong, KhachHang, Xe


class MaintenanceFormDialog(QDialog):
    """Dialog for adding or editing a maintenance record.
    
    Signals:
        saved: Emitted when maintenance was saved successfully.
    """
    
    saved = pyqtSignal()
    
    def __init__(
        self,
        db_conn,
        session: CurrentSession,
        bao_duong: BaoDuong = None,
        parent=None
    ):
        """Initialize maintenance form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            bao_duong: BaoDuong entity to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bd_service = BaoDuongService(db_conn)
        self._bao_duong = bao_duong
        self._is_edit = bao_duong is not None
        
        self._khach_hang_id: Optional[int] = None
        self._xe_id: Optional[int] = None
        
        self._setup_ui()
        self._load_khach_hang_list()
        self._load_nhan_vien_list()
        
        if self._is_edit:
            self._populate_form(bao_duong)
    
    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm lịch bảo dưỡng" if not self._is_edit else f"Sửa lịch bảo dưỡng"
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
        form_group = QGroupBox("Thông tin bảo dưỡng")
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
        form_layout.setSpacing(14)
        
        # khach_hang (searchable dropdown) - row 1
        kh_layout = QHBoxLayout()
        kh_layout.setSpacing(8)
        
        kh_label = QLabel("Khách hàng *:")
        kh_label.setMinimumWidth(120)
        kh_layout.addWidget(kh_label)
        
        self._kh_combo = QComboBox()
        self._kh_combo.setEditable(True)
        self._kh_combo.setPlaceholderText("-- Tìm kiếm khách hàng --")
        self._kh_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-height: 30px;
            }
            QComboBox:focus {
                border: 2px solid #0066cc;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        self._kh_combo.currentIndexChanged.connect(self._on_kh_changed)
        kh_layout.addWidget(self._kh_combo, stretch=1)
        
        self._kh_error = QLabel("")
        self._kh_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        form_layout.addLayout(kh_layout)
        form_layout.addWidget(self._kh_error)
        
        # xe (auto-load based on KH) - row 2
        xe_layout = QHBoxLayout()
        xe_layout.setSpacing(8)
        
        xe_label = QLabel("Xe *:")
        xe_label.setMinimumWidth(120)
        xe_layout.addWidget(xe_label)
        
        self._xe_combo = QComboBox()
        self._xe_combo.setPlaceholderText("-- Chọn xe --")
        self._xe_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-height: 30px;
            }
            QComboBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._xe_combo.currentIndexChanged.connect(self._on_xe_changed)
        xe_layout.addWidget(self._xe_combo, stretch=1)
        
        self._xe_error = QLabel("")
        self._xe_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        form_layout.addLayout(xe_layout)
        form_layout.addWidget(self._xe_error)
        
        # ngay_du_kien - row 3
        ngay_layout = QHBoxLayout()
        ngay_layout.setSpacing(8)
        
        ngay_label = QLabel("Ngày dự kiến *:")
        ngay_label.setMinimumWidth(120)
        ngay_layout.addWidget(ngay_label)
        
        self._ngay_date = QDateEdit()
        self._ngay_date.setCalendarPopup(True)
        self._ngay_date.setDate(QDate.currentDate().addDays(1))
        self._ngay_date.setMinimumDate(QDate.currentDate().addDays(1))
        self._ngay_date.setStyleSheet("""
            QDateEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QDateEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        ngay_layout.addWidget(self._ngay_date)
        
        ngay_hint = QLabel("(Ngày phải lớn hơn hôm nay)")
        ngay_hint.setStyleSheet("color: #86868b; font-size: 12px;")
        ngay_layout.addWidget(ngay_hint)
        
        ngay_error = QLabel("")
        ngay_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        form_layout.addLayout(ngay_layout)
        form_layout.addWidget(ngay_error)
        
        # km_xe - row 4
        km_layout = QHBoxLayout()
        km_layout.setSpacing(8)
        
        km_label = QLabel("Km xe:")
        km_label.setMinimumWidth(120)
        km_layout.addWidget(km_label)
        
        self._km_spin = InlineNumericEdit(
            value=0,
            minimum=0,
            maximum=999999,
            step=1000,
            suffix="km",
            is_float=False,
        )
        km_layout.addWidget(self._km_spin)
        
        km_unit = QLabel("km")
        km_unit.setStyleSheet("color: #86868b;")
        km_layout.addWidget(km_unit)
        
        form_layout.addLayout(km_layout)
        
        # noi_dung - row 5
        nd_layout = QHBoxLayout()
        nd_layout.setSpacing(8)
        
        nd_label = QLabel("Nội dung:")
        nd_label.setMinimumWidth(120)
        nd_layout.addWidget(nd_label)
        
        self._nd_input = QLineEdit()
        self._nd_input.setPlaceholderText("VD: Thay dầu, kiểm tra phanh...")
        self._nd_input.setStyleSheet("""
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
        nd_layout.addWidget(self._nd_input, stretch=1)
        form_layout.addLayout(nd_layout)
        
        # chi_phi - row 6
        cp_layout = QHBoxLayout()
        cp_layout.setSpacing(8)
        
        cp_label = QLabel("Chi phí dự kiến:")
        cp_label.setMinimumWidth(120)
        cp_layout.addWidget(cp_label)
        
        self._cp_spin = InlineNumericEdit(
            value=0,
            minimum=0,
            maximum=999999999,
            step=100000,
            suffix="VNĐ",
            is_float=False,
        )
        cp_layout.addWidget(self._cp_spin)
        
        cp_unit = QLabel("VNĐ")
        cp_unit.setStyleSheet("color: #86868b;")
        cp_layout.addWidget(cp_unit)
        
        cp_error = QLabel("")
        cp_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        form_layout.addLayout(cp_layout)
        form_layout.addWidget(cp_error)
        
        # nhan_vien_id (technique dropdown) - row 7
        nv_layout = QHBoxLayout()
        nv_layout.setSpacing(8)
        
        nv_label = QLabel("Kỹ thuật viên:")
        nv_label.setMinimumWidth(120)
        nv_layout.addWidget(nv_label)
        
        self._nv_combo = QComboBox()
        self._nv_combo.setPlaceholderText("-- Chọn kỹ thuật viên --")
        self._nv_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-height: 30px;
            }
            QComboBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        nv_layout.addWidget(self._nv_combo, stretch=1)
        form_layout.addLayout(nv_layout)
        
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
    
    def _load_khach_hang_list(self):
        """Load customer list into dropdown."""
        try:
            cursor = self._db_conn.execute(
                """SELECT id, ho_ten, so_dien_thoai FROM khach_hang 
                   WHERE trang_thai != 'inactive' ORDER BY ho_ten"""
            )
            for row in cursor.fetchall():
                display_text = f"{row[1]} - {row[2]}"
                self._kh_combo.addItem(display_text, row[0])
        except Exception:
            pass
    
    def _load_xe_list(self, khach_hang_id: int):
        """Load vehicle list for customer into dropdown.
        
        Args:
            khach_hang_id: Customer ID to filter vehicles.
        """
        self._xe_combo.clear()
        self._xe_id = None
        
        if not khach_hang_id:
            return
        
        try:
            cursor = self._db_conn.execute(
                """SELECT x.id, x.hang, x.dong_xe, x.mau_sac, x bien_so
                   FROM xe x
                   JOIN hop_dong hd ON x.id = hd.xe_id
                   WHERE hd.khach_hang_id = ?
                   ORDER BY x.hang, x.dong_xe""",
                (khach_hang_id,)
            )
            has_vehicles = False
            for row in cursor.fetchall():
                display_text = f"{row[1]} {row[2]} - {row[3]} - {row[4]}"
                self._xe_combo.addItem(display_text, row[0])
                has_vehicles = True
            
            if not has_vehicles:
                # Also show vehicles from bao_duong history
                cursor2 = self._db_conn.execute(
                    """SELECT DISTINCT x.id, x.hang, x.dong_xe, x.mau_sac, x.bien_so
                       FROM xe x
                       JOIN bao_duong bd ON x.id = bd.xe_id
                       WHERE bd.khach_hang_id = ?
                       ORDER BY x.hang, x.dong_xe""",
                    (khach_hang_id,)
                )
                for row in cursor2.fetchall():
                    display_text = f"{row[1]} {row[2]} - {row[3]} - {row[4]}"
                    self._xe_combo.addItem(display_text, row[0])
                    
        except Exception:
            pass
    
    def _load_nhan_vien_list(self):
        """Load technique staff list into dropdown."""
        try:
            cursor = self._db_conn.execute(
                """SELECT id, ho_ten FROM nhan_vien 
                   WHERE trang_thai = 'active' AND vai_tro_id IN (4, 5)
                   ORDER BY ho_ten"""
            )
            self._nv_combo.addItem("-- Không chọn --", None)
            for row in cursor.fetchall():
                self._nv_combo.addItem(row[1], row[0])
        except Exception:
            pass
    
    def _on_kh_changed(self, index: int):
        """Handle customer selection change."""
        if index < 0:
            return
        
        kh_id = self._kh_combo.currentData()
        self._khach_hang_id = kh_id
        self._load_xe_list(kh_id)
    
    def _on_xe_changed(self, index: int):
        """Handle vehicle selection change."""
        if index < 0:
            return
        
        self._xe_id = self._xe_combo.currentData()
    
    def _populate_form(self, bd: BaoDuong):
        """Populate form with existing maintenance data.
        
        Args:
            bd: BaoDuong entity to edit.
        """
        self._khach_hang_id = bd.khach_hang_id
        self._xe_id = bd.xe_id
        
        # Set customer
        cursor = self._db_conn.execute(
            "SELECT ho_ten, so_dien_thoai FROM khach_hang WHERE id = ?",
            (bd.khach_hang_id,)
        )
        row = cursor.fetchone()
        if row:
            display_text = f"{row[0]} - {row[1]}"
            self._kh_combo.setCurrentText(display_text)
            self._load_xe_list(bd.khach_hang_id)
        
        # Set vehicle
        if bd.xe_id:
            cursor = self._db_conn.execute(
                "SELECT hang, dong_xe, mau_sac, bien_so FROM xe WHERE id = ?",
                (bd.xe_id,)
            )
            row = cursor.fetchone()
            if row:
                display_text = f"{row[0]} {row[1]} - {row[2]} - {row[3]}"
                self._xe_combo.setCurrentText(display_text)
        
        # Set date
        if bd.ngay_du_kien:
            from datetime import datetime
            try:
                dt = datetime.strptime(bd.ngay_du_kien[:10], "%Y-%m-%d")
                self._ngay_date.setDate(QDate(dt.year, dt.month, dt.day))
            except Exception:
                pass
        
        # Set other fields
        self._km_spin.setValue(bd.km_xe or 0)
        self._nd_input.setText(bd.noi_dung or "")
        self._cp_spin.setValue(bd.chi_phi or 0)
        
        if bd.nhan_vien_id:
            cursor = self._db_conn.execute(
                "SELECT ho_ten FROM nhan_vien WHERE id = ?",
                (bd.nhan_vien_id,)
            )
            row = cursor.fetchone()
            if row:
                self._nv_combo.setCurrentText(row[0])
    
    def _validate(self) -> bool:
        """Validate form fields.
        
        Returns:
            True if valid, False otherwise.
        """
        errors = []
        
        # KH required
        if not self._khach_hang_id:
            self._kh_error.setText("Vui lòng chọn khách hàng")
            errors.append("khach_hang")
        else:
            self._kh_error.setText("")
        
        # xe required
        if not self._xe_id:
            self._xe_error.setText("Vui lòng chọn xe")
            errors.append("xe")
        else:
            self._xe_error.setText("")
        
        # ngay > today
        selected_date = self._ngay_date.date()
        if selected_date <= QDate.currentDate():
            errors.append("ngay")
        
        # chi_phi >= 0
        if self._cp_spin.value() < 0:
            errors.append("chi_phi")
        
        return len(errors) == 0
    
    def _on_save(self):
        """Handle save button click."""
        if not self._validate():
            QMessageBox.warning(self, "Lỗi", "Vui lòng kiểm tra lại thông tin!")
            return
        
        try:
            ngay_du_kien = self._ngay_date.date().toString("yyyy-MM-dd")
            ngay_du_kien += " 08:00:00"
            
            if self._is_edit:
                # Update existing
                data = BaoDuongUpdateData(
                    ngay_du_kien=ngay_du_kien,
                    km_xe=self._km_spin.value(),
                    noi_dung=self._nd_input.text().strip(),
                    chi_phi=self._cp_spin.value(),
                    nhan_vien_id=self._nv_combo.currentData(),
                )
                
                self._bd_service.update(self._bao_duong.id, data)
                QMessageBox.information(self, "Thành công", "Đã cập nhật lịch bảo dưỡng!")
            else:
                # Create new
                data = BaoDuongCreateData(
                    khach_hang_id=self._khach_hang_id,
                    xe_id=self._xe_id,
                    ngay_du_kien=ngay_du_kien,
                    km_xe=self._km_spin.value(),
                    noi_dung=self._nd_input.text().strip(),
                    chi_phi=self._cp_spin.value(),
                    nhan_vien_id=self._nv_combo.currentData(),
                    created_by=self._session.nhan_vien_id if self._session else None,
                )
                
                self._bd_service.create(data)
                QMessageBox.information(self, "Thành công", "Đã thêm lịch bảo dưỡng mới!")
            
            self.saved.emit()
            self.accept()
            
        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")