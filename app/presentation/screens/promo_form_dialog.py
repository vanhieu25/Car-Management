"""Promotion form dialog - S-KM-02 - Create/Edit promotion form.

Features:
- Form dialog for creating/editing KM
- Dropdown for loai_km: giam_tien_mat, giam_phan_tram, tang_phu_kien, giam_lai_suat, combo
- Dynamic field based on loai_km:
  - giam_tien_mat: gia_tri (number, VND)
  - giam_phan_tram: gia_tri (number, %), and optional gia_tri_toi_da
  - tang_phu_kien: gia_tri (number of items free)
  - giam_lai_suat: gia_tri (%), lai_suat_toi_da
  - combo: gia_tri (% discount on combo price)
- Multi-select for pham_vi: checkbox for each type (all/hang/dong_xe/xe/ton_lau)
- Date pickers for tu_ngay, den_ngay
- Validate on save

References:
- BR-KM-01..10: Promotion lifecycle management
- BR-KM-03: 5 types of promotions
- BR-KM-04: Scope (pham_vi)
- BR-DATA-07: den_ngay > tu_ngay
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QMessageBox,
    QGroupBox, QComboBox, QCheckBox, QDateEdit,
    QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from app.application.services.khuyen_mai_service import (
    KhuyenMaiService,
    KhuyenMaiCreateData,
    KhuyenMaiPhamViData,
    InvalidDateRangeError,
    InvalidGiaTriError,
    InvalidLoaiKMError,
)
from app.application.services.session import CurrentSession


LOAI_KM_OPTIONS = {
    "giam_tien_mat": ("Giảm tiền mặt", "VND"),
    "giam_phan_tram": ("Giảm phần trăm", "%"),
    "tang_phu_kien": ("Tặng phụ kiện", "Số lượng"),
    "giam_lai_suat": ("Giảm lãi suất", "%"),
    "combo": ("Combo", "%"),
}

LOAI_KM_DISPLAY = {
    "giam_tien_mat": "Giảm tiền mặt",
    "giam_phan_tram": "Giảm phần trăm",
    "tang_phu_kien": "Tặng phụ kiện",
    "giam_lai_suat": "Giảm lãi suất",
    "combo": "Combo",
}


class PromoFormDialog(QDialog):
    """Dialog for adding or editing a promotion.

    Signals:
        saved: Emitted when promotion was saved successfully.
    """

    saved = pyqtSignal()

    def __init__(
        self,
        db_conn,
        session: CurrentSession,
        km=None,
        parent=None
    ):
        """Initialize promotion form dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            km: KhuyenMai entity to edit, or None for adding new.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._km_service = KhuyenMaiService(db_conn, session)
        self._km = km
        self._is_edit = km is not None

        self._setup_ui()

        if self._is_edit:
            self._populate_form(km)

    def _setup_ui(self):
        """Set up UI components."""
        title = "Thêm khuyến mãi mới" if not self._is_edit else f"Sửa khuyến mãi - {self._km.ten_km}"
        self.setWindowTitle(title)
        self.setMinimumSize(650, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-size: 14px;
                color: #1d1d1f;
            }
            QGroupBox {
                font-size: 14px;
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

        # === Basic info group ===
        basic_group = QGroupBox("Thông tin cơ bản")
        basic_layout = QFormLayout()
        basic_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        basic_layout.setSpacing(12)

        # ten_km
        self._ten_km_input = QLineEdit()
        self._ten_km_input.setPlaceholderText("VD: Giảm 10 triệu cho Toyota Vios")
        self._ten_km_input.setMaxLength(200)
        self._ten_km_input.setStyleSheet("""
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
        basic_layout.addRow("Tên khuyến mãi *:", self._ten_km_input)

        # mo_ta
        self._mo_ta_input = QLineEdit()
        self._mo_ta_input.setPlaceholderText("Mô tả chi tiết chương trình...")
        self._mo_ta_input.setMaxLength(500)
        self._mo_ta_input.setStyleSheet(self._ten_km_input.styleSheet())
        basic_layout.addRow("Mô tả:", self._mo_ta_input)

        # loai_km (dropdown)
        self._loai_km_combo = QComboBox()
        self._loai_km_combo.addItem("-- Chọn loại KM --", "")
        for key, (label, _) in LOAI_KM_OPTIONS.items():
            self._loai_km_combo.addItem(label, key)
        self._loai_km_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 200px;
            }
        """)
        self._loai_km_combo.currentIndexChanged.connect(self._on_loai_km_changed)
        basic_layout.addRow("Loại khuyến mãi *:", self._loai_km_combo)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # === Discount value group (dynamic) ===
        self._value_group = QGroupBox("Giá trị khuyến mãi")
        value_layout = QFormLayout()
        value_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        value_layout.setSpacing(12)

        # gia_tri (dynamic based on loai_km)
        self._gia_tri_spin = QSpinBox()
        self._gia_tri_spin.setRange(0, 999999999)
        self._gia_tri_spin.setStyleSheet("""
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
        self._value_unit_label = QLabel("đ")
        self._value_unit_label.setStyleSheet("font-size: 14px; color: #86868b;")

        gia_tri_layout = QHBoxLayout()
        gia_tri_layout.addWidget(self._gia_tri_spin)
        gia_tri_layout.addWidget(self._value_unit_label)
        gia_tri_layout.addStretch()
        value_layout.addRow("Giá trị *:", gia_tri_layout)

        # gia_tri_toi_da (for phan_tram only)
        self._gia_tri_max_layout = QHBoxLayout()
        self._gia_tri_max_spin = QSpinBox()
        self._gia_tri_max_spin.setRange(0, 9999999999)
        self._gia_tri_max_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        self._gia_tri_max_layout.addWidget(self._gia_tri_max_spin)
        self._gia_tri_max_layout.addWidget(QLabel("đ"))
        self._gia_tri_max_layout.addStretch()
        self._gia_tri_max_label = QLabel("Giá trị tối đa:")
        self._gia_tri_max_label.setStyleSheet("font-size: 14px; color: #1d1d1f;")
        value_layout.addRow(self._gia_tri_max_label, self._gia_tri_max_layout)

        # lai_suat_toi_da (for giam_lai_suat only)
        self._lai_suat_max_layout = QHBoxLayout()
        self._lai_suat_max_spin = QDoubleSpinBox()
        self._lai_suat_max_spin.setRange(0, 100)
        self._lai_suat_max_spin.setDecimals(2)
        self._lai_suat_max_spin.setSuffix(" %")
        self._lai_suat_max_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        self._lai_suat_max_layout.addWidget(self._lai_suat_max_spin)
        self._lai_suat_max_layout.addStretch()
        self._lai_suat_max_label = QLabel("Lãi suất tối đa:")
        self._lai_suat_max_label.setStyleSheet("font-size: 14px; color: #1d1d1f;")
        value_layout.addRow(self._lai_suat_max_label, self._lai_suat_max_layout)

        self._value_group.setLayout(value_layout)
        layout.addWidget(self._value_group)

        # Initially hide dynamic fields
        self._gia_tri_max_label.setVisible(False)
        self._gia_tri_max_layout.setVisible(False)
        self._lai_suat_max_label.setVisible(False)
        self._lai_suat_max_layout.setVisible(False)

        # === Date range group ===
        date_group = QGroupBox("Thời gian áp dụng")
        date_layout = QFormLayout()
        date_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        date_layout.setSpacing(12)

        # tu_ngay
        self._tu_ngay_edit = QDateEdit()
        self._tu_ngay_edit.setCalendarPopup(True)
        self._tu_ngay_edit.setDate(QDate.currentDate())
        self._tu_ngay_edit.setStyleSheet("""
            QDateEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        date_layout.addRow("Từ ngày *:", self._tu_ngay_edit)

        # den_ngay
        self._den_ngay_edit = QDateEdit()
        self._den_ngay_edit.setCalendarPopup(True)
        self._den_ngay_edit.setDate(QDate.currentDate().addMonths(1))
        self._den_ngay_edit.setStyleSheet("""
            QDateEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        date_layout.addRow("Đến ngày *:", self._den_ngay_edit)

        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        # === Scope (pham_vi) group ===
        scope_group = QGroupBox("Phạm vi áp dụng")
        scope_layout = QVBoxLayout()
        scope_layout.setSpacing(8)

        scope_note = QLabel("Chọn một hoặc nhiều phạm vi áp dụng:")
        scope_note.setStyleSheet("font-size: 13px; color: #86868b; font-style: italic;")
        scope_layout.addWidget(scope_note)

        # Checkboxes for each scope type
        self._scope_checkboxes = {}

        # all
        cb_all = QCheckBox("Tất cả các xe")
        cb_all.setStyleSheet("QCheckBox { spacing: 8px; font-size: 14px; }")
        scope_layout.addWidget(cb_all)
        self._scope_checkboxes["all"] = cb_all

        # hang
        cb_hang = QCheckBox("Theo hãng xe (chọn hãng cụ thể)")
        cb_hang.setStyleSheet("QCheckBox { spacing: 8px; font-size: 14px; }")
        scope_layout.addWidget(cb_hang)
        self._scope_checkboxes["hang"] = cb_hang

        self._hang_input = QLineEdit()
        self._hang_input.setPlaceholderText("VD: Toyota, Honda, Ford...")
        self._hang_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                margin-left: 24px;
            }
        """)
        scope_layout.addWidget(self._hang_input)

        # dong_xe
        cb_dong = QCheckBox("Theo dòng xe (chọn dòng cụ thể)")
        cb_dong.setStyleSheet("QCheckBox { spacing: 8px; font-size: 14px; }")
        scope_layout.addWidget(cb_dong)
        self._scope_checkboxes["dong_xe"] = cb_dong

        self._dong_xe_input = QLineEdit()
        self._dong_xe_input.setPlaceholderText("VD: Camry, Civic, Everest...")
        self._dong_xe_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                margin-left: 24px;
            }
        """)
        scope_layout.addWidget(self._dong_xe_input)

        # xe (specific vehicle)
        cb_xe = QCheckBox("Theo xe cụ thể (nhập mã xe)")
        cb_xe.setStyleSheet("QCheckBox { spacing: 8px; font-size: 14px; }")
        scope_layout.addWidget(cb_xe)
        self._scope_checkboxes["xe"] = cb_xe

        self._xe_input = QLineEdit()
        self._xe_input.setPlaceholderText("VD: XE001, XE002...")
        self._xe_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
                background: white;
                margin-left: 24px;
            }
        """)
        scope_layout.addWidget(self._xe_input)

        # ton_lau (old inventory > 90 days)
        cb_ton = QCheckBox("Xe tồn lâu (hơn 90 ngày)")
        cb_ton.setStyleSheet("QCheckBox { spacing: 8px; font-size: 14px; }")
        scope_layout.addWidget(cb_ton)
        self._scope_checkboxes["ton_lau"] = cb_ton

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

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

    def _on_loai_km_changed(self):
        """Handle loai_km dropdown change - show/hide dynamic fields."""
        loai_km = self._loai_km_combo.currentData()

        # Reset visibility
        self._gia_tri_max_label.setVisible(False)
        self._gia_tri_max_layout.setVisible(False)
        self._lai_suat_max_label.setVisible(False)
        self._lai_suat_max_layout.setVisible(False)

        if loai_km == "giam_phan_tram":
            self._gia_tri_spin.setRange(0, 100)
            self._gia_tri_spin.setSuffix(" %")
            self._value_unit_label.setText("%")
            self._gia_tri_max_label.setVisible(True)
            self._gia_tri_max_layout.setVisible(True)
        elif loai_km == "giam_tien_mat":
            self._gia_tri_spin.setRange(0, 999999999)
            self._gia_tri_spin.setSuffix(" đ")
            self._value_unit_label.setText("VND")
        elif loai_km == "tang_phu_kien":
            self._gia_tri_spin.setRange(0, 9999)
            self._gia_tri_spin.setSuffix(" sản phẩm")
            self._value_unit_label.setText("")
        elif loai_km == "giam_lai_suat":
            self._gia_tri_spin.setRange(0, 30)
            self._gia_tri_spin.setSuffix(" %")
            self._value_unit_label.setText("%")
            self._lai_suat_max_label.setVisible(True)
            self._lai_suat_max_layout.setVisible(True)
        elif loai_km == "combo":
            self._gia_tri_spin.setRange(0, 100)
            self._gia_tri_spin.setSuffix(" %")
            self._value_unit_label.setText("% giảm")
        else:
            self._gia_tri_spin.setRange(0, 999999999)
            self._gia_tri_spin.setSuffix("")
            self._value_unit_label.setText("")

    def _populate_form(self, km):
        """Populate form with existing promotion data.

        Args:
            km: KhuyenMai entity to edit.
        """
        self._ten_km_input.setText(km.ten_km)
        self._mo_ta_input.setText(km.mo_ta or "")

        # Set loai_km
        for i in range(self._loai_km_combo.count()):
            if self._loai_km_combo.itemData(i) == km.loai_km:
                self._loai_km_combo.setCurrentIndex(i)
                break

        self._on_loai_km_changed()

        # Set gia_tri
        self._gia_tri_spin.setValue(km.gia_tri)

        # Set dates
        if km.tu_ngay:
            parts = km.tu_ngay[:10].split("-")
            if len(parts) == 3:
                self._tu_ngay_edit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
        if km.den_ngay:
            parts = km.den_ngay[:10].split("-")
            if len(parts) == 3:
                self._den_ngay_edit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))

        # Load pham_vi
        pham_vi_list = self._km_service._repo.get_pham_vi(km.id)
        for pv in pham_vi_list:
            loai = pv.loai_ap_dung
            if loai in self._scope_checkboxes:
                self._scope_checkboxes[loai].setChecked(True)
                if loai == "hang":
                    self._hang_input.setText(pv.gia_tri_ap_dung or "")
                elif loai == "dong_xe":
                    self._dong_xe_input.setText(pv.gia_tri_ap_dung or "")
                elif loai == "xe":
                    self._xe_input.setText(pv.gia_tri_ap_dung or "")

    def _validate(self) -> bool:
        """Validate form inputs.

        Returns:
            True if valid, False otherwise.
        """
        errors = []

        # Required fields
        if not self._ten_km_input.text().strip():
            errors.append("Tên khuyến mãi không được để trống")

        loai_km = self._loai_km_combo.currentData()
        if not loai_km:
            errors.append("Vui lòng chọn loại khuyến mãi")

        # Date validation
        tu_ngay = self._tu_ngay_edit.date().toString("yyyy-MM-dd")
        den_ngay = self._den_ngay_edit.date().toString("yyyy-MM-dd")
        if den_ngay <= tu_ngay:
            errors.append("Ngày kết thúc phải lớn hơn ngày bắt đầu")

        # gia_tri > 0
        if self._gia_tri_spin.value() <= 0:
            errors.append("Giá trị khuyến mãi phải lớn hơn 0")

        # Scope validation
        has_scope = any(cb.isChecked() for cb in self._scope_checkboxes.values())
        if not has_scope:
            errors.append("Vui lòng chọn ít nhất một phạm vi áp dụng")

        # If hang/dong_xe/xe selected, must provide value
        if self._scope_checkboxes["hang"].isChecked() and not self._hang_input.text().strip():
            errors.append("Vui lòng nhập tên hãng xe khi chọn phạm vi 'Theo hãng'")
        if self._scope_checkboxes["dong_xe"].isChecked() and not self._dong_xe_input.text().strip():
            errors.append("Vui lòng nhập tên dòng xe khi chọn phạm vi 'Theo dòng'")
        if self._scope_checkboxes["xe"].isChecked() and not self._xe_input.text().strip():
            errors.append("Vui lòng nhập mã xe khi chọn phạm vi 'Theo xe cụ thể'")

        if errors:
            QMessageBox.warning(self, "Lỗi validation", "\n".join(f"• {e}" for e in errors))
            return False

        return True

    def _on_save(self):
        """Handle save button click."""
        if not self._validate():
            return

        try:
            loai_km = self._loai_km_combo.currentData()

            # Determine kieu_gia_tri
            if loai_km in ("giam_phan_tram", "combo", "giam_lai_suat"):
                kieu_gia_tri = "phan_tram"
            else:
                kieu_gia_tri = "tien"

            tu_ngay = self._tu_ngay_edit.date().toString("yyyy-MM-dd")
            den_ngay = self._den_ngay_edit.date().toString("yyyy-MM-dd")

            data = KhuyenMaiCreateData(
                ten_km=self._ten_km_input.text().strip(),
                mo_ta=self._mo_ta_input.text().strip() or "",
                loai_km=loai_km,
                gia_tri=self._gia_tri_spin.value(),
                kieu_gia_tri=kieu_gia_tri,
                tu_ngay=tu_ngay,
                den_ngay=den_ngay,
                trang_thai="dang_chay",
                created_by=self._session.nhan_vien_id if self._session else None,
            )

            # Build pham_vi list
            pham_vi_list = []
            if self._scope_checkboxes["all"].isChecked():
                pham_vi_list.append(KhuyenMaiPhamViData(loai_ap_dung="all"))
            if self._scope_checkboxes["hang"].isChecked():
                pham_vi_list.append(KhuyenMaiPhamViData(
                    loai_ap_dung="hang",
                    gia_tri_ap_dung=self._hang_input.text().strip()
                ))
            if self._scope_checkboxes["dong_xe"].isChecked():
                pham_vi_list.append(KhuyenMaiPhamViData(
                    loai_ap_dung="dong_xe",
                    gia_tri_ap_dung=self._dong_xe_input.text().strip()
                ))
            if self._scope_checkboxes["xe"].isChecked():
                pham_vi_list.append(KhuyenMaiPhamViData(
                    loai_ap_dung="xe",
                    gia_tri_ap_dung=self._xe_input.text().strip()
                ))
            if self._scope_checkboxes["ton_lau"].isChecked():
                pham_vi_list.append(KhuyenMaiPhamViData(loai_ap_dung="ton_lau"))

            self._km_service.create(data, pham_vi_list)

            QMessageBox.information(self, "Thành công", "Đã lưu khuyến mãi thành công!")
            self.saved.emit()
            self.accept()

        except InvalidDateRangeError as e:
            QMessageBox.warning(self, "Lỗi ngày", str(e))
        except InvalidGiaTriError as e:
            QMessageBox.warning(self, "Lỗi giá trị", str(e))
        except InvalidLoaiKMError as e:
            QMessageBox.warning(self, "Lỗi loại KM", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")
