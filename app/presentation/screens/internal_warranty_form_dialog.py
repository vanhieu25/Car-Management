"""Internal warranty creation dialog - S-BH-XX - Create warranty for vehicles sold internally.

Features:
- Search/select existing contract (hop_dong) that doesn't have warranty yet
- Shows contract details: customer, vehicle, delivery date
- Creates warranty with calculated end date based on system settings
- Similar to auto_create_from_hop_dong but triggered manually

References:
- BR-BH-01: One warranty per contract
- BR-BH-02: ngay_ket_thuc = ngay_bat_dau + thoi_han_bh months
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QDateEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from app.application.services.bao_hanh_service import BaoHanhService
from app.application.services.session import CurrentSession
from app.application.services.system_settings_service import SystemSettingsService


class InternalWarrantyCreateDialog(QDialog):
    """Dialog for creating warranty from existing contract - S-BH-XX.

    Signals:
        warranty_created(bh_id: int): Emitted when warranty was created successfully.
    """

    warranty_created = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize internal warranty creation dialog.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bh_service = BaoHanhService(db_conn)
        self._settings_service = SystemSettingsService(db_conn)

        self._bh_id = None

        self._setup_ui()
        self._load_contracts()

    def showEvent(self, event):
        """Refresh contracts each time dialog is shown."""
        self._load_contracts()
        super().showEvent(event)

    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Tạo bảo hành nội bộ")
        self.setMinimumWidth(550)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title_label = QLabel("Tạo bảo hành nội bộ")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        layout.addWidget(title_label)

        # Info note
        note_label = QLabel("Tạo bảo hành cho xe đã bán qua hệ thống (có hợp đồng)")
        note_label.setStyleSheet("font-size: 13px; color: #86868b; padding: 8px; background: #f5f5f7; border-radius: 6px;")
        layout.addWidget(note_label)

        # Contract selection
        contract_group = QGroupBox("Chọn hợp đồng")
        contract_group.setStyleSheet("""
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
        contract_layout = QVBoxLayout(contract_group)

        # Search row
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Tìm hợp đồng:"))

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Nhập mã HĐ, tên khách hàng, hoặc SĐT...")
        self._search_input.setStyleSheet("""
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
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input, stretch=1)

        contract_layout.addLayout(search_layout)

        # Contract dropdown
        self._contract_combo = QComboBox()
        self._contract_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                min-width: 400px;
            }
        """)
        self._contract_combo.currentIndexChanged.connect(self._on_contract_selected)
        contract_layout.addWidget(self._contract_combo)

        layout.addWidget(contract_group)

        # Contract details display
        self._details_group = QGroupBox("Thông tin hợp đồng")
        self._details_group.setStyleSheet("""
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
        details_layout = QVBoxLayout(self._details_group)

        self._details_label = QLabel("Chọn hợp đồng để xem thông tin")
        self._details_label.setStyleSheet("font-size: 13px; color: #86868b;")
        details_layout.addWidget(self._details_label)

        layout.addWidget(self._details_group)

        # Warranty period preview
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Thời hạn bảo hành:"))
        default_months = self._settings_service.get_warranty_months()
        self._thoi_han_label = QLabel(f"{default_months} tháng")
        self._thoi_han_label.setStyleSheet("font-weight: 600; color: #0066cc;")
        period_layout.addWidget(self._thoi_han_label)
        period_layout.addStretch()
        layout.addLayout(period_layout)

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

        self._submit_btn = QPushButton("Tạo bảo hành")
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
        self._submit_btn.setEnabled(False)
        btn_layout.addWidget(self._submit_btn)

        layout.addLayout(btn_layout)

    def _load_contracts(self):
        """Load contracts that don't have warranty yet."""
        # Use fresh connection to ensure we see latest committed data
        from app.infrastructure.database.connection import get_connection
        conn = get_connection()

        # Debug: Check contracts with da_giao_xe status
        debug1 = conn.execute("SELECT id, ma_hop_dong, trang_thai, xe_id FROM hop_dong WHERE trang_thai = 'da_giao_xe'").fetchall()
        print(f"[DEBUG] Contracts with da_giao_xe: {len(debug1)} rows: {debug1}")

        # Debug: Check contracts not in bao_hanh
        debug2 = conn.execute("""
            SELECT hd.id FROM hop_dong hd
            WHERE hd.trang_thai = 'da_giao_xe'
            AND NOT EXISTS (SELECT 1 FROM bao_hanh bh WHERE bh.hop_dong_id = hd.id)
        """).fetchall()
        print(f"[DEBUG] da_giao_xe without BH: {len(debug2)} rows: {debug2}")

        # Debug: Check contracts with xe_id
        debug3 = conn.execute("SELECT id, ma_hop_dong, xe_id FROM hop_dong WHERE xe_id IS NOT NULL LIMIT 10").fetchall()
        print(f"[DEBUG] Contracts with xe_id: {debug3}")

        cursor = conn.execute("""
            SELECT hd.id, hd.ma_hop_dong, kh.ho_ten, xe.hang, xe.dong_xe, hd.ngay_giao_xe
            FROM hop_dong hd
            JOIN khach_hang kh ON hd.khach_hang_id = kh.id
            JOIN xe ON hd.xe_id = xe.id
            WHERE hd.trang_thai = 'da_giao_xe'
              AND hd.xe_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM bao_hanh bh
                  WHERE bh.hop_dong_id = hd.id
              )
            ORDER BY hd.ngay_giao_xe DESC
        """)
        rows = cursor.fetchall()
        print(f"[DEBUG] Final filtered contracts: {len(rows)} rows")
        conn.close()

        self._contracts = {}
        self._contract_combo.clear()
        self._contract_combo.addItem("— Chọn hợp đồng —", None)

        for row in rows:
            hd_id, ma_hd, kh_ten, hang, dong, ngay_giao = row
            self._contracts[hd_id] = {
                'ma_hop_dong': ma_hd,
                'khach_hang': kh_ten,
                'xe': f"{hang} {dong}",
                'ngay_giao_xe': ngay_giao[:10] if ngay_giao else None,
            }
            self._contract_combo.addItem(f"{ma_hd} — {kh_ten} — {hang} {dong}", hd_id)

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        text_lower = text.lower().strip()
        if not text_lower:
            self._load_contracts()
            return

        # Filter contracts
        self._contract_combo.blockSignals(True)
        self._contract_combo.clear()
        self._contract_combo.addItem("— Chọn hợp đồng —", None)

        count = 0
        for hd_id, info in self._contracts.items():
            if (text_lower in info['ma_hop_dong'].lower() or
                text_lower in info['khach_hang'].lower() or
                text_lower in info['xe'].lower()):
                self._contract_combo.addItem(
                    f"{info['ma_hop_dong']} — {info['khach_hang']} — {info['xe']}",
                    hd_id
                )
                count += 1

        self._contract_combo.blockSignals(False)

        if count == 0 and text_lower:
            self._contract_combo.addItem("Không tìm thấy hợp đồng", None)

    def _on_contract_selected(self, index: int):
        """Handle contract selection."""
        hd_id = self._contract_combo.currentData()
        if hd_id is None or hd_id not in self._contracts:
            self._details_label.setText("Chọn hợp đồng để xem thông tin")
            self._details_label.setStyleSheet("font-size: 13px; color: #86868b;")
            self._submit_btn.setEnabled(False)
            return

        info = self._contracts[hd_id]
        default_months = self._settings_service.get_warranty_months()

        from dateutil.relativedelta import relativedelta
        from datetime import date

        ngay_giao = info['ngay_giao_xe']
        if ngay_giao:
            d = date.fromisoformat(ngay_giao)
            ngay_ket_thuc = d + relativedelta(months=default_months)
            end_str = ngay_ket_thuc.strftime("%d-%m-%Y")
        else:
            end_str = "N/A"

        self._details_label.setText(f"""
            <b>Mã HĐ:</b> {info['ma_hop_dong']}<br>
            <b>Khách hàng:</b> {info['khach_hang']}<br>
            <b>Xe:</b> {info['xe']}<br>
            <b>Ngày giao xe:</b> {ngay_giao or 'N/A'}<br>
            <b>Ngày kết thúc BH (dự kiến):</b> {end_str}
        """)
        self._details_label.setStyleSheet("font-size: 13px; color: #1d1d1f;")
        self._submit_btn.setEnabled(True)

    def _on_submit(self):
        """Handle submit button."""
        hd_id = self._contract_combo.currentData()
        if hd_id is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn hợp đồng!")
            return

        try:
            result = self._bh_service.auto_create_from_hop_dong(
                hop_dong_id=hd_id,
                nhan_vien_id=self._session.nhan_vien_id if self._session else None,
            )
            self._bh_id = result.get("id")

            QMessageBox.information(
                self, "Thành công",
                f"Đã tạo bảo hành BH{self._bh_id} cho hợp đồng!"
            )
            self.warranty_created.emit(self._bh_id)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo bảo hành: {str(e)}")