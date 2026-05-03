"""Rescue request form dialog - S-HM-03 - Add/Edit rescue request form.

Features:
- Form fields: khach_hang (search), xe (auto-load), vi_tri (text input for location),
  mo_ta (text area), chi_phi (estimate), thoi_gian_den_du_kien, nhan_vien_id
- Status badge display: tiep_nhan (yellow), dang_xu_ly (blue), hoan_thanh (green)
- On save → calls CuuHoService.create()

References:
- BR-HM-04: Cứu hộ has vi_tri, mo_ta, thoi_gian_yeu_cau
- BR-HM-05: Status flow: tiep_nhan -> dang_xu_ly -> hoan_thanh
- BR-HM-06: Create/Update cuu_ho records
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QDateTimeEdit, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont

from app.presentation.widgets.inputs import InlineNumericEdit

from app.application.services.cuu_ho_service import (
    CuuHoService, CuuHoCreateData, CuuHoUpdateData,
    ValidationError, CuuHoNotFoundError
)
from app.application.services.session import CurrentSession
from app.domain.entities import CuuHo


class RescueRequestFormDialog(QDialog):
    """Dialog for adding or editing a rescue request.
    
    Signals:
        saved: Emitted when rescue request was saved successfully.
    """
    
    saved = pyqtSignal()
    
    def __init__(
        self,
        db_conn,
        session: CurrentSession,
        cuu_ho: CuuHo = None,
        parent=None
    ):
        """Initialize rescue request form dialog.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            cuu_ho: CuuHo entity to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._ch_service = CuuHoService(db_conn)
        self._cuu_ho = cuu_ho
        self._is_edit = cuu_ho is not None
        
        self._khach_hang_id: Optional[int] = None
        self._xe_id: Optional[int] = None
        
        self._setup_ui()
        self._load_khach_hang_list()
        self._load_nhan_vien_list()
        
        if self._is_edit:
            self._populate_form(cuu_ho)
        else:
            # New request default status
            self._set_status_badge("tiep_nhan")
    
    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm yêu cầu cứu hộ" if not self._is_edit else f"Sửa yêu cầu cứu hộ"
        self.setWindowTitle(title)
        self.setMinimumSize(650, 550)
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
        
        # Status badge for editing
        if self._is_edit:
            status_layout = QHBoxLayout()
            status_label = QLabel("Trạng thái:")
            status_label.setStyleSheet("font-weight: 600;")
            status_layout.addWidget(status_label)
            self._status_badge = QLabel()
            status_layout.addWidget(self._status_badge)
            status_layout.addStretch()
            layout.addLayout(status_layout)
        
        # Form group
        form_group = QGroupBox("Thông tin cứu hộ")
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
        kh_label.setMinimumWidth(130)
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
        xe_label.setMinimumWidth(130)
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
        
        # vi_tri (location) - row 3
        vt_layout = QHBoxLayout()
        vt_layout.setSpacing(8)
        
        vt_label = QLabel("Vị trí *:")
        vt_label.setMinimumWidth(130)
        vt_layout.addWidget(vt_label)
        
        self._vt_input = QLineEdit()
        self._vt_input.setPlaceholderText("VD: 123 Đường ABC, Quận 1, TP.HCM")
        self._vt_input.setStyleSheet("""
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
        vt_layout.addWidget(self._vt_input, stretch=1)
        
        self._vt_error = QLabel("")
        self._vt_error.setStyleSheet("color: #ff3b30; font-size: 12px;")
        form_layout.addLayout(vt_layout)
        form_layout.addWidget(self._vt_error)
        
        # mo_ta (description) - row 4
        mt_layout = QHBoxLayout()
        mt_layout.setSpacing(8)
        
        mt_label = QLabel("Mô tả:")
        mt_label.setMinimumWidth(130)
        mt_layout.addWidget(mt_label)
        
        self._mt_text = QTextEdit()
        self._mt_text.setPlaceholderText("Mô tả tình trạng cần cứu hộ...")
        self._mt_text.setMaximumHeight(80)
        self._mt_text.setStyleSheet("""
            QTextEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QTextEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        mt_layout.addWidget(self._mt_text, stretch=1)
        form_layout.addLayout(mt_layout)
        
        # chi_phi (estimate) - row 5
        cp_layout = QHBoxLayout()
        cp_layout.setSpacing(8)
        
        cp_label = QLabel("Chi phí ước tính:")
        cp_label.setMinimumWidth(130)
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
        
        # thoi_gian_den_du_kien - row 6
        tg_layout = QHBoxLayout()
        tg_layout.setSpacing(8)
        
        tg_label = QLabel("Thời gian đến dự kiến:")
        tg_label.setMinimumWidth(130)
        tg_layout.addWidget(tg_label)
        
        self._tg_datetime = QDateTimeEdit()
        self._tg_datetime.setCalendarPopup(True)
        self._tg_datetime.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self._tg_datetime.setStyleSheet("""
            QDateTimeEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QDateTimeEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        tg_layout.addWidget(self._tg_datetime)
        
        tg_hint = QLabel("(Để trống nếu chưa xác định)")
        tg_hint.setStyleSheet("color: #86868b; font-size: 12px;")
        tg_layout.addWidget(tg_hint)
        tg_layout.addStretch()
        
        form_layout.addLayout(tg_layout)
        
        # nhan_vien_id - row 7
        nv_layout = QHBoxLayout()
        nv_layout.setSpacing(8)
        
        nv_label = QLabel("NV phụ trách:")
        nv_label.setMinimumWidth(130)
        nv_layout.addWidget(nv_label)
        
        self._nv_combo = QComboBox()
        self._nv_combo.setPlaceholderText("-- Chọn nhân viên --")
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
    
    def _set_status_badge(self, status: str):
        """Set status badge color and text."""
        if not hasattr(self, '_status_badge'):
            return
        
        status_config = {
            "tiep_nhan": ("Tiếp nhận", "#ffcc00"),    # Yellow
            "dang_xu_ly": ("Đang xử lý", "#007aff"),   # Blue
            "hoan_thanh": ("Hoàn thành", "#34c759"),   # Green
        }
        
        text, color = status_config.get(status, ("N/A", "#8e8e93"))
        self._status_badge.setText(
            f"<span style='background:{color}; color:white; padding:4px 12px; border-radius:4px; font-size:13px; font-weight:600;'>{text}</span>"
        )
    
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
                """SELECT x.id, x.hang, x.dong_xe, x.mau_sac, x.bien_so
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
                # Also show vehicles from cuu_ho history
                cursor2 = self._db_conn.execute(
                    """SELECT DISTINCT x.id, x.hang, x.dong_xe, x.mau_sac, x.bien_so
                       FROM xe x
                       JOIN cuu_ho ch ON x.id = ch.xe_id
                       WHERE ch.khach_hang_id = ?
                       ORDER BY x.hang, x.dong_xe""",
                    (khach_hang_id,)
                )
                for row in cursor2.fetchall():
                    display_text = f"{row[1]} {row[2]} - {row[3]} - {row[4]}"
                    self._xe_combo.addItem(display_text, row[0])
                    
        except Exception:
            pass
    
    def _load_nhan_vien_list(self):
        """Load staff list into dropdown."""
        try:
            cursor = self._db_conn.execute(
                """SELECT id, ho_ten FROM nhan_vien 
                   WHERE trang_thai = 'active'
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
    
    def _populate_form(self, ch: CuuHo):
        """Populate form with existing rescue data.
        
        Args:
            ch: CuuHo entity to edit.
        """
        self._khach_hang_id = ch.khach_hang_id
        self._xe_id = ch.xe_id
        
        # Set status badge
        self._set_status_badge(ch.trang_thai)
        
        # Set customer
        cursor = self._db_conn.execute(
            "SELECT ho_ten, so_dien_thoai FROM khach_hang WHERE id = ?",
            (ch.khach_hang_id,)
        )
        row = cursor.fetchone()
        if row:
            display_text = f"{row[0]} - {row[1]}"
            self._kh_combo.setCurrentText(display_text)
            self._load_xe_list(ch.khach_hang_id)
        
        # Set vehicle
        if ch.xe_id:
            cursor = self._db_conn.execute(
                "SELECT hang, dong_xe, mau_sac, bien_so FROM xe WHERE id = ?",
                (ch.xe_id,)
            )
            row = cursor.fetchone()
            if row:
                display_text = f"{row[0]} {row[1]} - {row[2]} - {row[3]}"
                self._xe_combo.setCurrentText(display_text)
        
        # Set vi_tri
        self._vt_input.setText(ch.vi_tri or "")
        
        # Set mo_ta
        self._mt_text.setText(ch.mo_ta or "")
        
        # Set chi_phi
        self._cp_spin.setValue(ch.chi_phi or 0)
        
        # Set nhan_vien
        if ch.nhan_vien_id:
            cursor = self._db_conn.execute(
                "SELECT ho_ten FROM nhan_vien WHERE id = ?",
                (ch.nhan_vien_id,)
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
        
        # vi_tri required
        if not self._vt_input.text().strip():
            self._vt_error.setText("Vui lòng nhập vị trí")
            errors.append("vi_tri")
        else:
            self._vt_error.setText("")
        
        return len(errors) == 0
    
    def _on_save(self):
        """Handle save button click."""
        if not self._validate():
            QMessageBox.warning(self, "Lỗi", "Vui lòng kiểm tra lại thông tin!")
            return
        
        try:
            tg_du_kien = self._tg_datetime.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            
            if self._is_edit:
                # Update existing
                data = CuuHoUpdateData(
                    vi_tri=self._vt_input.text().strip(),
                    mo_ta=self._mt_text.toPlainText().strip(),
                    chi_phi_thuc_te=self._cp_spin.value(),
                    nhan_vien_id=self._nv_combo.currentData(),
                )
                
                self._ch_service.update(self._cuu_ho.id, data)
                QMessageBox.information(self, "Thành công", "Đã cập nhật yêu cầu cứu hộ!")
            else:
                # Create new
                data = CuuHoCreateData(
                    khach_hang_id=self._khach_hang_id,
                    xe_id=self._xe_id,
                    vi_tri=self._vt_input.text().strip(),
                    mo_ta=self._mt_text.toPlainText().trimmed(),
                    chi_phi=self._cp_spin.value(),
                    thoi_gian_den_du_kien=tg_du_kien if self._tg_datetime.dateTime() else None,
                    nhan_vien_id=self._nv_combo.currentData(),
                    created_by=self._session.nhan_vien_id if self._session else None,
                )
                
                self._ch_service.create(data)
                QMessageBox.information(self, "Thành công", "Đã thêm yêu cầu cứu hộ mới!")
            
            self.saved.emit()
            self.accept()
            
        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")