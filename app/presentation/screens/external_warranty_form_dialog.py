"""External warranty creation dialog - S-BH-05 - Create warranty for vehicles sold by other dealerships.

Features:
- Search/select existing customer or create new
- Input so_khung (chassis number) - required
- Input so_may (engine number) - required
- Input hang_xe, dong_xe for display
- Select warranty start date (default today)
- Select warranty period in months (default from system settings)
- Creates external warranty record, then opens request form

References:
- BR-BH-02: ngay_ket_thuc = ngay_bat_dau + thoi_han_bh months
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QDateEdit, QTextEdit, QSpinBox, QCompleter, QWidget,
    QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.bao_hanh_service import BaoHanhService, ExternalBaoHanhData
from app.application.services.khach_hang_service import KhachHangService, KhachHangCreateData
from app.application.services.bao_hiem_service import BaoHiemService, InsuranceData
from app.application.services.session import CurrentSession
from app.application.services.system_settings_service import SystemSettingsService

# Import CustomerFormDialog lazily to avoid circular imports
CustomerFormDialog = None


class ExternalWarrantyCreateDialog(QDialog):
    """Dialog for creating warranty for external vehicle - S-BH-05.

    Signals:
        warranty_created(bh_id: int): Emitted when warranty was created successfully.
        request_needed(bh_id: int): Emitted when user wants to create a request.
    """

    warranty_created = pyqtSignal(int)
    request_needed = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize external warranty creation dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bh_service = BaoHanhService(db_conn)
        self._kh_service = KhachHangService(db_conn)
        self._bh_insurance_service = BaoHiemService(db_conn)
        self._settings_service = SystemSettingsService(db_conn)

        self._selected_kh_id = None
        self._bh_id = None

        self._setup_ui()
        self._load_defaults()

    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Tiếp nhận bảo hành xe ngoài")
        self.setMinimumWidth(600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title_label = QLabel("Tiếp nhận bảo hành xe ngoài")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title_label)

        # Info note
        note_label = QLabel("Xe không bán qua hệ thống — cần nhập số khung/số máy để xác minh")
        note_label.setStyleSheet("font-size: 13px; color: #86868b; padding: 8px; background: #f5f5f7; border-radius: 6px;")
        layout.addWidget(note_label)

        # Customer section
        kh_group = QGroupBox("Khách hàng")
        kh_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
            }
        """)
        kh_layout = QVBoxLayout(kh_group)

        # Customer search/create row
        kh_search_layout = QHBoxLayout()
        kh_search_layout.addWidget(QLabel("SĐT / Tên:"))
        self._kh_input = QLineEdit()
        self._kh_input.setPlaceholderText("Nhập SĐT hoặc tên khách hàng...")
        self._kh_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._kh_input.textChanged.connect(self._on_khach_hang_search)
        kh_search_layout.addWidget(self._kh_input, stretch=1)

        self._kh_select_btn = QPushButton("Chọn")
        self._kh_select_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._kh_select_btn.clicked.connect(self._on_khach_hang_selected)
        kh_search_layout.addWidget(self._kh_select_btn)

        self._kh_create_btn = QPushButton("+ Tạo mới")
        self._kh_create_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._kh_create_btn.clicked.connect(self._on_create_khach_hang)
        kh_search_layout.addWidget(self._kh_create_btn)
        kh_layout.addLayout(kh_search_layout)

        # Selected customer display
        self._kh_display = QLabel("Chưa chọn khách hàng")
        self._kh_display.setStyleSheet("font-size: 13px; color: #86868b; padding: 4px;")
        kh_layout.addWidget(self._kh_display)

        layout.addWidget(kh_group)

        # Vehicle section
        xe_group = QGroupBox("Thông tin xe")
        xe_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
            }
        """)
        xe_layout = QVBoxLayout(xe_group)

        # So khung
        sk_layout = QHBoxLayout()
        sk_layout.addWidget(QLabel("Số khung (*):"))
        self._so_khung = QLineEdit()
        self._so_khung.setPlaceholderText("VD: JMT12345ABCDEF...")
        self._so_khung.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        sk_layout.addWidget(self._so_khung, stretch=1)
        xe_layout.addLayout(sk_layout)

        # So may
        sm_layout = QHBoxLayout()
        sm_layout.addWidget(QLabel("Số máy (*):"))
        self._so_may = QLineEdit()
        self._so_may.setPlaceholderText("VD: 4D56ABCDEF123456...")
        self._so_may.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        sm_layout.addWidget(self._so_may, stretch=1)
        xe_layout.addLayout(sm_layout)

        # Hang xe
        hang_layout = QHBoxLayout()
        hang_layout.addWidget(QLabel("Hãng xe:"))
        self._hang_xe = QLineEdit()
        self._hang_xe.setPlaceholderText("VD: Toyota, Honda, Ford...")
        self._hang_xe.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        hang_layout.addWidget(self._hang_xe, stretch=1)
        xe_layout.addLayout(hang_layout)

        # Dong xe
        dong_layout = QHBoxLayout()
        dong_layout.addWidget(QLabel("Dòng xe:"))
        self._dong_xe = QLineEdit()
        self._dong_xe.setPlaceholderText("VD: Camry, Civic, Everest...")
        self._dong_xe.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        dong_layout.addWidget(self._dong_xe, stretch=1)
        xe_layout.addLayout(dong_layout)

        layout.addWidget(xe_group)

        # Warranty period section
        bh_period_group = QGroupBox("Thời hạn bảo hành")
        bh_period_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
            }
        """)
        period_layout = QHBoxLayout(bh_period_group)

        period_layout.addWidget(QLabel("Ngày bắt đầu:"))
        self._ngay_bat_dau = QDateEdit()
        self._ngay_bat_dau.setDate(QDate.currentDate())
        self._ngay_bat_dau.setCalendarPopup(True)
        self._ngay_bat_dau.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        period_layout.addWidget(self._ngay_bat_dau)

        period_layout.addWidget(QLabel("Thời hạn (tháng):"))
        self._thoi_han_bh = QSpinBox()
        self._thoi_han_bh.setMinimum(1)
        self._thoi_han_bh.setMaximum(60)
        self._thoi_han_bh.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        period_layout.addWidget(self._thoi_han_bh)

        self._thoi_han_label = QLabel()
        self._thoi_han_label.setStyleSheet("font-size: 13px; color: #86868b;")
        period_layout.addWidget(self._thoi_han_label)
        period_layout.addStretch()

        self._ngay_bat_dau.dateChanged.connect(self._update_end_date_label)
        self._thoi_han_bh.valueChanged.connect(self._update_end_date_label)

        layout.addWidget(bh_period_group)

        # Insurance section (optional for external vehicles)
        bh_group = QGroupBox("★ Thông tin bảo hiểm (tùy chọn)")
        bh_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
                background-color: #fffef5;
            }
            QGroupBox::title {
                color: #ff9500;
            }
        """)
        bh_layout = QVBoxLayout(bh_group)

        # Checkbox to enable insurance
        self._has_insurance_check = QPushButton("☐ Xe có bảo hiểm")
        self._has_insurance_check.setCheckable(True)
        self._has_insurance_check.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #fff9f0;
                border: 1px solid #ff9500;
                color: #ff9500;
            }
        """)
        self._has_insurance_check.clicked.connect(self._on_insurance_toggle)
        bh_layout.addWidget(self._has_insurance_check)

        # Insurance fields (initially hidden)
        self._insurance_widget = QWidget()
        ins_layout = QVBoxLayout(self._insurance_widget)
        ins_layout.setContentsMargins(0, 8, 0, 0)

        # Cong ty BH
        cty_layout = QHBoxLayout()
        cty_layout.addWidget(QLabel("Công ty BH:"))
        self._cong_ty_bh_combo = QComboBox()
        self._cong_ty_bh_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        self._load_cong_ty_bh()
        cty_layout.addWidget(self._cong_ty_bh_combo)
        cty_layout.addStretch()
        ins_layout.addLayout(cty_layout)

        # So HĐ BH
        sohd_layout = QHBoxLayout()
        sohd_layout.addWidget(QLabel("Số HĐ BH:"))
        self._so_policy = QLineEdit()
        self._so_policy.setPlaceholderText("VD: BH-2024-001")
        self._so_policy.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        sohd_layout.addWidget(self._so_policy, stretch=1)
        ins_layout.addLayout(sohd_layout)

        # Ngay hieu luc
        nhl_layout = QHBoxLayout()
        nhl_layout.addWidget(QLabel("Ngày hiệu lực:"))
        self._ngay_hieu_luc = QDateEdit()
        self._ngay_hieu_luc.setDate(QDate.currentDate())
        self._ngay_hieu_luc.setCalendarPopup(True)
        self._ngay_hieu_luc.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        nhl_layout.addWidget(self._ngay_hieu_luc)
        nhl_layout.addWidget(QLabel("Ngày hết hạn:"))
        self._ngay_het_han = QDateEdit()
        self._ngay_het_han.setDate(QDate.currentDate().addYears(1))
        self._ngay_het_han.setCalendarPopup(True)
        self._ngay_het_han.setStyleSheet(self._ngay_hieu_luc.styleSheet())
        nhl_layout.addWidget(self._ngay_het_han)
        nhl_layout.addStretch()
        ins_layout.addLayout(nhl_layout)

        # Trang thaiBH
        tt_layout = QHBoxLayout()
        tt_layout.addWidget(QLabel("Trạng thái:"))
        self._trang_thai_bh = QComboBox()
        self._trang_thai_bh.addItems(["Còn hiệu lực", "Hết hạn"])
        self._trang_thai_bh.setCurrentText("Còn hiệu lực")
        self._trang_thai_bh.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        tt_layout.addWidget(self._trang_thai_bh)
        tt_layout.addStretch()
        ins_layout.addLayout(tt_layout)

        self._insurance_widget.setVisible(False)
        bh_layout.addWidget(self._insurance_widget)

        layout.addWidget(bh_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Hủy bỏ")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._submit_btn = QPushButton("Tiếp nhận BH")
        self._submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_layout.addWidget(self._submit_btn)

        layout.addLayout(btn_layout)

    def _load_defaults(self):
        """Load default values from system settings."""
        default_months = self._settings_service.get_warranty_months()
        self._thoi_han_bh.setValue(default_months)
        self._update_end_date_label()

    def _update_end_date_label(self):
        """Update end date label."""
        from dateutil.relativedelta import relativedelta
        start_date = self._ngay_bat_dau.date().toString("yyyy-MM-dd")
        months = self._thoi_han_bh.value()
        from datetime import date
        d = date.fromisoformat(start_date)
        end_date = d + relativedelta(months=months)
        self._thoi_han_label.setText(f"→ Kết thúc: {end_date.strftime('%d-%m-%Y')}")

    def _on_khach_hang_search(self, text: str):
        """Handle customer search input."""
        # Could implement autocomplete here
        pass

    def _on_khach_hang_selected(self):
        """Show dialog to select from found customers."""
        search_text = self._kh_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập SĐT hoặc tên khách hàng")
            return

        # Search for customers
        results = self._search_khach_hang(search_text)
        if not results:
            QMessageBox.information(self, "Không tìm thấy", "Không tìm thấy khách hàng. Vui lòng tạo mới.")
            return

        if len(results) == 1:
            self._select_khach_hang(results[0])
        else:
            # Show selection dialog
            self._show_khach_hang_selection(results)

    def _on_insurance_toggle(self, checked):
        """Toggle insurance section visibility."""
        self._insurance_widget.setVisible(checked)
        if checked:
            self._has_insurance_check.setText("☑ Xe có bảo hiểm")
        else:
            self._has_insurance_check.setText("☐ Xe có bảo hiểm")

    def _load_cong_ty_bh(self):
        """Load insurance companies from database."""
        cursor = self._db_conn.execute(
            "SELECT id, ma_cty, ten_cty FROM cong_ty_bh WHERE trang_thai = 'hoat_dong' ORDER BY ma_cty"
        )
        self._cong_ty_bh_combo.clear()
        self._cong_ty_bh_combo.addItem("-- Chọn công ty --", None)
        for row in cursor.fetchall():
            self._cong_ty_bh_combo.addItem(f"{row[1]} - {row[2]}", row[0])

    def _search_khach_hang(self, keyword: str):
        """Search customers by phone or name."""
        cursor = self._db_conn.execute(
            """SELECT id, ho_ten, so_dien_thoai, email FROM khach_hang
               WHERE so_dien_thoai LIKE ? OR ho_ten LIKE ?
               LIMIT 10""",
            (f"%{keyword}%", f"%{keyword}%")
        )
        return list(cursor.fetchall())

    def _show_khach_hang_selection(self, results):
        """Show customer selection dialog."""
        from PyQt6.QtWidgets import QInputDialog
        items = [f"{r[1]} ({r[2]})" for r in results]
        item, ok = QInputDialog.getItem(self, "Chọn khách hàng", "Tìm thấy nhiều khách hàng:", items, 0, False)
        if ok and item:
            idx = items.index(item)
            self._select_khach_hang(results[idx])

    def _select_khach_hang(self, row):
        """Select a customer from search result."""
        self._selected_kh_id = row[0]
        self._kh_display.setText(f"<b>{row[1]}</b> — {row[2]} — {row[3]}")
        self._kh_display.setStyleSheet("font-size: 13px; color: #1d1d1f; padding: 4px;")

    def _on_create_khach_hang(self):
        """Create new customer inline."""
        global CustomerFormDialog
        if CustomerFormDialog is None:
            from app.presentation.screens.customer_form_dialog import CustomerFormDialog

        dialog = CustomerFormDialog(self._db_conn, self._session, parent=self)
        dialog.saved.connect(lambda: self._on_khach_hang_created(dialog))
        dialog.exec()

    def _on_khach_hang_created(self, dialog):
        """Handle customer creation."""
        # Get the newly created customer from dialog
        pass

    def _on_submit(self):
        """Handle submit button."""
        # Validate
        if not self._selected_kh_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn khách hàng!")
            return

        so_khung = self._so_khung.text().strip()
        so_may = self._so_may.text().strip()

        if not so_khung:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số khung xe!")
            return

        if not so_may:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số máy xe!")
            return

        ngay_bat_dau = self._ngay_bat_dau.date().toString("yyyy-MM-dd")
        thoi_han_bh = self._thoi_han_bh.value()

        data = ExternalBaoHanhData(
            khach_hang_id=self._selected_kh_id,
            so_khung=so_khung,
            so_may=so_may,
            hang_xe=self._hang_xe.text().strip(),
            dong_xe=self._dong_xe.text().strip(),
            thoi_han_bh=thoi_han_bh,
            ngay_bat_dau=ngay_bat_dau,
            pham_vi="Bảo hành toàn diện theo điều khoản chuẩn của nhà sản xuất",
            nhan_vien_id=self._session.nhan_vien_id if self._session else None,
        )

        try:
            result = self._bh_service.create_external_warranty(data)
            self._bh_id = result.get("id")

            # Create insurance record if checkbox is checked
            if self._has_insurance_check.isChecked():
                try:
                    ngay_hieu_luc = self._ngay_hieu_luc.date().toString("yyyy-MM-dd")
                    ngay_het_han = self._ngay_het_han.date().toString("yyyy-MM-dd")
                    trang_thai = "con_hieu_luc" if self._trang_thai_bh.currentText() == "Còn hiệu lực" else "het_han"

                    ins_data = InsuranceData(
                        bao_hanh_id=self._bh_id,
                        loai_bh="tnds",
                        so_policy=self._so_policy.text().strip(),
                        ngay_mua=ngay_hieu_luc,
                        ngay_hieu_luc=ngay_hieu_luc,
                        ngay_het_han=ngay_het_han,
                        phi_bh=0,
                        cong_ty_bh_id=self._cong_ty_bh_combo.currentData(),
                        trang_thai=trang_thai,
                    )
                    self._bh_insurance_service.create(ins_data, self._session.nhan_vien_id if self._session else None)
                except Exception as ins_err:
                    # Log but don't fail the warranty creation
                    import logging
                    logging.getLogger("car_management").warning(f"Failed to create insurance: {ins_err}")

            QMessageBox.information(self, "Thành công", f"Đã tiếp nhận bảo hành BH{self._bh_id}!")
            self.warranty_created.emit(self._bh_id)

            # Ask if user wants to create a request
            reply = QMessageBox.question(
                self, "Tạo yêu cầu",
                "Bạn có muốn tạo yêu cầu bảo hành ngay?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.request_needed.emit(self._bh_id)
                self.accept()
            else:
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo bảo hành: {str(e)}")