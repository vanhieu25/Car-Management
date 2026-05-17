"""Insurance form dialog - create insurance by customer → contract → vehicle.

Business rules:
- Insurance is created by the current dealership automatically (dai_ly_ban_id = nhan_vien_id from session)
- No manual selection of insurance company (cong_ty_bh_id = None)
- Cascade: customer → contract → vehicle → warranty (for bao_hanh_id)
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from app.application.services.bao_hiem_service import BaoHiemService, InsuranceData
from app.application.services.session import CurrentSession
from app.presentation.widgets.inputs import InlineNumericEdit


class BaoHiemFormDialog(QDialog):
    """Insurance form dialog - create mode only.

    Cascade flow: customer → contract → vehicle
    dai_ly_ban_id is automatically set from session.

    Signals:
        insurance_saved(): Insurance was saved successfully.
    """

    insurance_saved = pyqtSignal()

    def __init__(
        self,
        db_conn,
        session: CurrentSession,
        parent=None
    ):
        """Initialize insurance form dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = BaoHiemService(db_conn)
        self._hop_dong_data = {}  # hop_dong_id -> {xe_id, khach_hang_id}

        self.setWindowTitle("Tạo bảo hiểm")
        self.setMinimumWidth(550)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        self._setup_ui()
        self._load_khach_hang()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Tạo bảo hiểm mới")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title)

        # Customer selection group
        customer_group = QGroupBox("Thông tin khách hàng")
        customer_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: #fafafa;
                font-weight: 600;
            }
        """)
        customer_layout = QVBoxLayout(customer_group)
        customer_layout.setSpacing(12)

        # Khach hang row
        kh_layout = QHBoxLayout()
        kh_layout.addWidget(QLabel("Khách hàng:"))
        self._kh_combo = QComboBox()
        self._kh_combo.setPlaceholderText("-- Chọn khách hàng --")
        self._kh_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 300px;
            }
        """)
        self._kh_combo.currentIndexChanged.connect(self._on_kh_changed)
        kh_layout.addWidget(self._kh_combo)
        kh_layout.addStretch()
        customer_layout.addLayout(kh_layout)

        # Hop dong row
        hd_layout = QHBoxLayout()
        hd_layout.addWidget(QLabel("Hợp đồng:"))
        self._hop_dong_combo = QComboBox()
        self._hop_dong_combo.setPlaceholderText("-- Chọn hợp đồng --")
        self._hop_dong_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 300px;
            }
        """)
        self._hop_dong_combo.currentIndexChanged.connect(self._on_hop_dong_changed)
        hd_layout.addWidget(self._hop_dong_combo)
        hd_layout.addStretch()
        customer_layout.addLayout(hd_layout)

        # Xe info (read-only display)
        xe_layout = QHBoxLayout()
        xe_layout.addWidget(QLabel("Xe:"))
        self._xe_info = QLabel("Chọn hợp đồng để xem thông tin xe")
        self._xe_info.setStyleSheet("color: #86868b; font-size: 14px; padding: 8px; background: #f5f5f7; border-radius: 6px; border: 1px solid #e5e5ea;")
        xe_layout.addWidget(self._xe_info, stretch=1)
        customer_layout.addLayout(xe_layout)

        layout.addWidget(customer_group)

        # Insurance info group
        insurance_group = QGroupBox("Thông tin bảo hiểm")
        insurance_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: #fafafa;
                font-weight: 600;
            }
        """)
        insurance_layout = QVBoxLayout(insurance_group)
        insurance_layout.setSpacing(12)

        # Loai BH
        loai_layout = QHBoxLayout()
        loai_layout.addWidget(QLabel("Loại bảo hiểm:"))
        self._loai_bh_combo = QComboBox()
        self._loai_bh_combo.addItems(["TNDS", "Tai nạn", "Cháy nổ", "Thất lạc", "Khác"])
        self._loai_bh_combo.setCurrentText("TNDS")
        self._loai_bh_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 150px;
            }
        """)
        loai_layout.addWidget(self._loai_bh_combo)
        loai_layout.addStretch()
        insurance_layout.addLayout(loai_layout)

        # So policy
        policy_layout = QHBoxLayout()
        policy_layout.addWidget(QLabel("Số Policy:"))
        self._policy_input = QLineEdit()
        self._policy_input.setPlaceholderText("VD: BH-2024-001")
        policy_layout.addWidget(self._policy_input, stretch=1)
        insurance_layout.addLayout(policy_layout)

        # Ngay mua + Ngay hieu luc row
        date_row = QHBoxLayout()

        ngay_mua_layout = QVBoxLayout()
        ngay_mua_layout.addWidget(QLabel("Ngày mua:"))
        self._ngay_mua_date = QDateEdit()
        self._ngay_mua_date.setCalendarPopup(True)
        self._ngay_mua_date.setDate(QDate.currentDate())
        self._ngay_mua_date.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        ngay_mua_layout.addWidget(self._ngay_mua_date)
        date_row.addLayout(ngay_mua_layout)

        ngay_hieu_luc_layout = QVBoxLayout()
        ngay_hieu_luc_layout.addWidget(QLabel("Ngày hiệu lực:"))
        self._ngay_hieu_luc_date = QDateEdit()
        self._ngay_hieu_luc_date.setCalendarPopup(True)
        self._ngay_hieu_luc_date.setDate(QDate.currentDate())
        self._ngay_hieu_luc_date.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        ngay_hieu_luc_layout.addWidget(self._ngay_hieu_luc_date)
        date_row.addLayout(ngay_hieu_luc_layout)

        ngay_het_han_layout = QVBoxLayout()
        ngay_het_han_layout.addWidget(QLabel("Ngày hết hạn:"))
        self._ngay_het_han_date = QDateEdit()
        self._ngay_het_han_date.setCalendarPopup(True)
        self._ngay_het_han_date.setDate(QDate.currentDate().addMonths(12))
        self._ngay_het_han_date.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        ngay_het_han_layout.addWidget(self._ngay_het_han_date)
        date_row.addLayout(ngay_het_han_layout)

        insurance_layout.addLayout(date_row)

        # Phi BH + Gia tri BH row
        phi_row = QHBoxLayout()

        phi_layout = QVBoxLayout()
        phi_layout.addWidget(QLabel("Phí bảo hiểm (VNĐ):"))
        self._phi_bh = InlineNumericEdit(
            value=0,
            minimum=0,
            maximum=999999999,
            step=100000,
            suffix="đ",
            is_float=False,
        )
        phi_layout.addWidget(self._phi_bh)
        phi_row.addLayout(phi_layout)

        gia_tri_layout = QVBoxLayout()
        gia_tri_layout.addWidget(QLabel("Giá trị bảo hiểm (VNĐ):"))
        self._gia_tri_bh = InlineNumericEdit(
            value=0,
            minimum=0,
            maximum=99999999999,
            step=1000000,
            suffix="đ",
            is_float=False,
        )
        gia_tri_layout.addWidget(self._gia_tri_bh)
        phi_row.addLayout(gia_tri_layout)

        insurance_layout.addLayout(phi_row)

        layout.addWidget(insurance_group)

        # Notes section
        notes_group = QGroupBox("Ghi chú")
        notes_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background-color: #fafafa;
                font-weight: 600;
            }
        """)
        notes_layout = QVBoxLayout(notes_group)
        self._notes_input = QTextEdit()
        self._notes_input.setPlaceholderText("Nhập ghi chú (nếu có)")
        self._notes_input.setMaximumHeight(60)
        self._notes_input.setStyleSheet("""
            QTextEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        notes_layout.addWidget(self._notes_input)
        layout.addWidget(notes_group)

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
                padding: 10px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._save_btn = QPushButton("Tạo bảo hiểm")
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2da44e;
            }
        """)
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)

    def _load_khach_hang(self):
        """Load customers into combo."""
        cursor = self._db_conn.execute("""
            SELECT id, ho_ten, so_dien_thoai
            FROM khach_hang
            ORDER BY ho_ten
        """)
        self._kh_combo.clear()
        self._kh_combo.addItem("-- Chọn khách hàng --", None)
        for row in cursor.fetchall():
            display = f"{row[1]} - {row[2]}" if row[2] else row[1]
            self._kh_combo.addItem(display, row[0])

    def _on_kh_changed(self, index: int):
        """Handle customer selection change."""
        self._hop_dong_combo.clear()
        self._hop_dong_data.clear()
        self._xe_info.setText("Chọn hợp đồng để xem thông tin xe")

        if index < 0:
            return

        kh_id = self._kh_combo.currentData()
        if not kh_id:
            return

        # Load hop_dong for this customer (only delivered ones)
        cursor = self._db_conn.execute("""
            SELECT hd.id, hd.ma_hop_dong, hd.ngay_giao_xe, hd.tong_tien,
                   x.hang, x.dong_xe, x.mau_sac, x.ma_xe
            FROM hop_dong hd
            JOIN xe x ON hd.xe_id = x.id
            WHERE hd.khach_hang_id = ? AND hd.trang_thai = 'da_giao_xe'
            ORDER BY hd.ngay_giao_xe DESC
        """, (kh_id,))

        self._hop_dong_combo.addItem("-- Chọn hợp đồng --", None)
        for row in cursor.fetchall():
            display = f"{row[1]} - {row[4]} {row[5]} - {row[6]} ({row[2]})" if row[2] else f"{row[1]} - {row[4]} {row[5]}"
            self._hop_dong_combo.addItem(display, row[0])
            # Store xe_id for later use
            self._hop_dong_data[row[0]] = {
                'xe_id': row[0],  # will be overwritten below
                'ma_xe': row[7],
                'hang': row[4],
                'dong_xe': row[5],
                'mau_sac': row[6],
            }

        # Re-query to get correct xe_id mapping
        cursor = self._db_conn.execute("""
            SELECT hd.id, x.id as xe_id, x.ma_xe, x.hang, x.dong_xe, x.mau_sac
            FROM hop_dong hd
            JOIN xe x ON hd.xe_id = x.id
            WHERE hd.khach_hang_id = ? AND hd.trang_thai = 'da_giao_xe'
            ORDER BY hd.ngay_giao_xe DESC
        """, (kh_id,))
        for row in cursor.fetchall():
            if row[0] in self._hop_dong_data:
                self._hop_dong_data[row[0]]['xe_id'] = row[1]
                self._hop_dong_data[row[0]]['ma_xe'] = row[2]
                self._hop_dong_data[row[0]]['hang'] = row[3]
                self._hop_dong_data[row[0]]['dong_xe'] = row[4]
                self._hop_dong_data[row[0]]['mau_sac'] = row[5]

    def _on_hop_dong_changed(self, index: int):
        """Handle contract selection change."""
        if index < 0:
            return

        hd_id = self._hop_dong_combo.currentData()
        if not hd_id or hd_id not in self._hop_dong_data:
            self._xe_info.setText("Chọn hợp đồng để xem thông tin xe")
            return

        info = self._hop_dong_data[hd_id]
        xe_text = f"{info['hang']} {info['dong_xe']} - {info['mau_sac']} - Mã: {info['ma_xe']}"
        self._xe_info.setText(xe_text)
        self._xe_info.setStyleSheet("color: #1d1d1f; font-size: 14px; padding: 8px; background: #e8f5e9; border-radius: 6px; border: 1px solid #c8e6c9;")

    def _on_save(self):
        """Handle save button."""
        # Validate customer and contract selected
        kh_id = self._kh_combo.currentData()
        if not kh_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn khách hàng")
            return

        hd_id = self._hop_dong_combo.currentData()
        if not hd_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn hợp đồng")
            return

        # Get xe_id from selected contract
        xe_id = self._hop_dong_data.get(hd_id, {}).get('xe_id')
        if not xe_id:
            QMessageBox.warning(self, "Lỗi", "Không tìm được thông tin xe từ hợp đồng")
            return

        # Find bao_hanh_id from hop_dong_id
        cursor = self._db_conn.execute(
            "SELECT id FROM bao_hanh WHERE hop_dong_id = ?",
            (hd_id,)
        )
        bh_row = cursor.fetchone()
        if not bh_row:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy bảo hành cho hợp đồng này")
            return
        bao_hanh_id = bh_row[0]

        # Validate dates
        ngay_mua = self._ngay_mua_date.date().toString("yyyy-MM-dd")
        ngay_hieu_luc = self._ngay_hieu_luc_date.date().toString("yyyy-MM-dd")
        ngay_het_han = self._ngay_het_han_date.date().toString("yyyy-MM-dd")

        if ngay_het_han <= ngay_mua:
            QMessageBox.warning(self, "Lỗi", "Ngày hết hạn phải sau ngày mua")
            return

        # Map insurance type
        loai_map = {
            "TNDS": "tnds",
            "Tai nạn": "tai_nan",
            "Cháy nổ": "chao_no",
            "Thất lạc": "that_lac",
            "Khác": "khac"
        }
        loai_bh = loai_map.get(self._loai_bh_combo.currentText(), "tnds")

        try:
            data = InsuranceData(
                bao_hanh_id=bao_hanh_id,
                xe_id=xe_id,
                hop_dong_id=hd_id,
                cong_ty_bh_id=None,  # đại lý tự tạo, không qua công ty bảo hiểm
                dai_ly_ban_id=self._session.nhan_vien_id,  # tự động từ session
                loai_bh=loai_bh,
                so_policy=self._policy_input.text().strip(),
                ngay_mua=ngay_mua,
                ngay_hieu_luc=ngay_hieu_luc,
                ngay_het_han=ngay_het_han,
                phi_bh=self._phi_bh.value(),
                gia_tri_bh=self._gia_tri_bh.value(),
                trang_thai="con_hieu_luc",
                ghi_chu=self._notes_input.toPlainText().strip(),
            )
            self._service.create(data, self._session.nhan_vien_id)
            QMessageBox.information(self, "Thành công", "Đã tạo bảo hiểm thành công!")
            self.insurance_saved.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")