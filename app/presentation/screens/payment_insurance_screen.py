"""Payment insurance screen - S-BH-PAY - Record payments for insurance.

Features:
- List insurance records needing payment (status: con_hieu_luc with phi_bh > 0 unpaid)
- Show insurance info, phi_bh, and payment status
- Record payment with amount and date
- Auto-update status: con_hieu_luc → da_thanh_toan on payment

References:
- BR-BH-INS: Insurance payment
"""

from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QAbstractItemView, QDialog, QLineEdit,
    QComboBox, QDateEdit, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.bao_hiem_service import BaoHiemService
from app.application.services.session import CurrentSession


class PaymentInsuranceScreen(QWidget):
    """Payment insurance screen - S-BH-PAY.

    Signals:
        back_clicked(): User wants to go back.
        payment_recorded(bh_id: int): Payment was successfully recorded.
    """

    back_clicked = pyqtSignal()
    payment_recorded = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize payment insurance screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bh_service = BaoHiemService(db_conn)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        self._back_btn = QPushButton("← Quay lại")
        self._back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._back_btn.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self._back_btn)

        header_layout.addStretch()

        title = QLabel("Thanh toán bảo hiểm")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        scroll.setMinimumHeight(500)

        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f5f5f7;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(24, 24, 24, 24)

        # Insurance table
        table_group = QGroupBox("Danh sách bảo hiểm chờ thanh toán")
        table_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        table_layout = QVBoxLayout(table_group)

        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Mã BH", "Loại", "Số policy", "Khách hàng", "Phí BH", "Ngày mua", "Ngày hết hạn", "Trạng thái"
        ])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                gridline-color: #e5e5ea;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px 8px;
                font-weight: 600;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)
        self._table.setMinimumHeight(400)
        table_layout.addWidget(self._table)

        # Action button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._pay_btn = QPushButton("💰 Thanh toán")
        self._pay_btn.setEnabled(False)
        self._pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
            QPushButton:disabled {
                background-color: #d2d2d7;
                color: #86868b;
            }
        """)
        self._pay_btn.clicked.connect(self._on_pay_clicked)
        btn_layout.addWidget(self._pay_btn)
        table_layout.addLayout(btn_layout)

        content_layout.addWidget(table_group)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Connect selection
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_back_clicked(self):
        """Handle back button click."""
        self.back_clicked.emit()

    def _on_selection_changed(self):
        """Handle row selection change."""
        selected = self._table.selectedItems()
        if selected:
            self._pay_btn.setEnabled(True)
        else:
            self._pay_btn.setEnabled(False)

    def _load_data(self):
        """Load insurance records needing payment."""
        try:
            # Get insurance records that have phi_bh > 0 and not yet paid
            query = """
                SELECT bh.id, bh.so_policy, bh.phi_bh, bh.ngay_mua, bh.ngay_het_han,
                       bh.trang_thai, bh.loai_bh,
                       ctbh.ten_cty as cong_ty_bh,
                       kh.ho_ten as kh_ho_ten
                FROM bao_hiem bh
                LEFT JOIN cong_ty_bh ctbh ON bh.cong_ty_bh_id = ctbh.id
                LEFT JOIN bao_hanh bhref ON bh.bao_hanh_id = bhref.id
                LEFT JOIN hop_dong hd ON bh.hop_dong_id = hd.id
                     OR (bhref.hop_dong_id IS NOT NULL AND bhref.hop_dong_id = hd.id)
                LEFT JOIN khach_hang kh ON hd.khach_hang_id = kh.id
                WHERE bh.phi_bh > 0 AND bh.trang_thai = 'con_hieu_luc'
                ORDER BY bh.ngay_mua DESC
            """
            cursor = self._db_conn.execute(query)
            rows = cursor.fetchall()

            self._populate_table(rows)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, rows):
        """Populate table with insurance data.

        Args:
            rows: List of database rows.
        """
        self._table.setRowCount(len(rows))

        loai_labels = {
            "tnds": "TNDS",
            "tai_nan": "Tai nạn",
            "chao_no": "Cháy nổ",
            "that_lac": "Thất lạc",
            "khac": "Khác",
        }

        status_labels = {
            "con_hieu_luc": "Chờ thanh toán",
            "da_thanh_toan": "Đã thanh toán",
            "het_han": "Hết hạn",
            "huy": "Đã hủy",
        }

        for row_idx, row in enumerate(rows):
            # Mã BH
            item_ma = QTableWidgetItem(row[6] or f"BH-{row[0]:04d}")
            item_ma.setData(Qt.ItemDataRole.UserRole, row[0])
            self._table.setItem(row_idx, 0, item_ma)

            # Loại
            loai_text = loai_labels.get(row[6], row[6])
            self._table.setItem(row_idx, 1, QTableWidgetItem(loai_text))

            # Số policy
            self._table.setItem(row_idx, 2, QTableWidgetItem(row[1] or "-"))

            # Khách hàng
            self._table.setItem(row_idx, 3, QTableWidgetItem(row[8] or "-"))

            # Phí BH
            phi_bh = row[2] or 0
            phi_text = f"{phi_bh:,} đ".replace(",", ".")
            item_phi = QTableWidgetItem(phi_text)
            item_phi.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._table.setItem(row_idx, 4, item_phi)

            # Ngày mua
            ngay_mua = row[3][:10] if row[3] else "-"
            self._table.setItem(row_idx, 5, QTableWidgetItem(ngay_mua))

            # Ngày hết hạn
            ngay_het_han = row[4][:10] if row[4] else "-"
            self._table.setItem(row_idx, 6, QTableWidgetItem(ngay_het_han))

            # Trạng thái
            trang_thai = row[5]
            status_text = status_labels.get(trang_thai, trang_thai)
            item_status = QTableWidgetItem(status_text)
            color = "#8e8e93"  # gray for waiting
            item_status.setBackground(QColor(color))
            item_status.setForeground(QColor(255, 255, 255))
            self._table.setItem(row_idx, 7, item_status)

        self._store_rows(rows)

    def _store_rows(self, rows):
        """Store row data for later reference."""
        self._rows_data = []
        for row in rows:
            self._rows_data.append({
                "id": row[0],
                "so_policy": row[1],
                "phi_bh": row[2],
                "loai_bh": row[6],
                "kh_ho_ten": row[8],
            })

    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click."""
        self._show_payment_dialog()

    def _on_pay_clicked(self):
        """Handle pay button click."""
        self._show_payment_dialog()

    def _show_payment_dialog(self):
        """Show payment dialog for selected insurance."""
        selected = self._table.selectedItems()
        if not selected:
            return

        row_idx = selected[0].row()
        bh_id_item = self._table.item(row_idx, 0)
        if not bh_id_item:
            return

        bh_id = bh_id_item.data(Qt.ItemDataRole.UserRole)

        # Find insurance data
        insurance_data = None
        for data in self._rows_data:
            if data["id"] == bh_id:
                insurance_data = data
                break

        if not insurance_data:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thông tin bảo hiểm")
            return

        # Show payment dialog
        dialog = PaymentInsuranceDialog(
            self._db_conn,
            self._session,
            insurance_data,
            self
        )
        dialog.payment_completed.connect(self._on_payment_completed)
        dialog.exec()

    def _on_payment_completed(self, bh_id: int):
        """Handle payment completed."""
        QMessageBox.information(self, "Thành công", "Đã ghi nhận thanh toán!")
        self._table.clearSelection()
        self._pay_btn.setEnabled(False)
        self._load_data()
        self.payment_recorded.emit(bh_id)

    def refresh(self):
        """Refresh data."""
        self._load_data()


class PaymentInsuranceDialog(QDialog):
    """Dialog for recording insurance payment."""

    payment_completed = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, insurance_data: Dict, parent=None):
        """Initialize payment dialog.

        Args:
            db_conn: Database connection.
            session: Current session.
            insurance_data: Insurance info dict with id, so_policy, phi_bh, loai_bh.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._insurance_data = insurance_data

        loai_labels = {
            "tnds": "TNDS",
            "tai_nan": "Tai nạn",
            "chao_no": "Cháy nổ",
            "that_lac": "Thất lạc",
            "khac": "Khác",
        }
        loai_text = loai_labels.get(insurance_data.get('loai_bh', ''), insurance_data.get('loai_bh', ''))

        self.setWindowTitle(f"Thanh toán bảo hiểm - {loai_text}")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { font-size: 14px; color: #1d1d1f; }
        """)

        self._setup_ui()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Insurance info
        info_group = QGroupBox("Thông tin bảo hiểm")
        info_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        info_layout = QVBoxLayout(info_group)

        so_policy = self._insurance_data.get('so_policy', '-')
        policy_label = QLabel(f"Số policy: {so_policy}")
        info_layout.addWidget(policy_label)

        phi_bh = self._insurance_data.get('phi_bh', 0)
        phi_text = f"{phi_bh:,} đ".replace(",", ".")
        phi_label = QLabel(f"Phí bảo hiểm: {phi_text}")
        phi_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        info_layout.addWidget(phi_label)

        layout.addWidget(info_group)

        # Payment amount
        amount_group = QGroupBox("Số tiền thanh toán")
        amount_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        amount_layout = QHBoxLayout(amount_group)

        amount_layout.addWidget(QLabel("Số tiền (VNĐ):"))

        self._amount_input = QLineEdit()
        self._amount_input.setPlaceholderText("Nhập số tiền...")
        self._amount_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        # Pre-fill with phi_bh
        self._amount_input.setText(str(phi_bh))
        amount_layout.addWidget(self._amount_input, stretch=1)

        layout.addWidget(amount_group)

        # Payment date
        date_group = QGroupBox("Ngày thanh toán")
        date_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        date_layout = QHBoxLayout(date_group)

        date_layout.addWidget(QLabel("Ngày TT:"))

        self._date_input = QDateEdit()
        self._date_input.setCalendarPopup(True)
        self._date_input.setDate(QDate.currentDate())
        self._date_input.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        date_layout.addWidget(self._date_input)
        date_layout.addStretch()

        layout.addWidget(date_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._ok_btn = QPushButton("Xác nhận thanh toán")
        self._ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._ok_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self._ok_btn)

        self._cancel_btn = QPushButton("Huỷ")
        self._cancel_btn.setStyleSheet("""
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
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        layout.addLayout(btn_layout)

    def _on_confirm(self):
        """Handle confirm button."""
        try:
            amount_text = self._amount_input.text().strip()
            if not amount_text:
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số tiền")
                return

            amount = int(amount_text.replace(",", ""))
            if amount <= 0:
                QMessageBox.warning(self, "Lỗi", "Số tiền phải lớn hơn 0")
                return

            phi_bh = self._insurance_data.get('phi_bh', 0)
            if amount > phi_bh:
                QMessageBox.warning(self, "Lỗi", "Số tiền không thể lớn hơn phí bảo hiểm")
                return

            # Process payment
            self._process_payment(amount)

        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Số tiền không hợp lệ")

    def _process_payment(self, amount: int):
        """Process the payment.

        Args:
            amount: Payment amount.
        """
        try:
            bh_id = self._insurance_data['id']
            nhan_vien_id = self._session.nhan_vien_id if self._session else None

            # Get current insurance status
            cursor = self._db_conn.execute(
                "SELECT trang_thai FROM bao_hiem WHERE id = ?", (bh_id,)
            )
            row = cursor.fetchone()
            if not row:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy bảo hiểm")
                return

            current_status = row[0]
            phi_bh = self._insurance_data.get('phi_bh', 0)

            # Only process if status is con_hieu_luc
            if current_status != 'con_hieu_luc':
                QMessageBox.warning(self, "Lỗi", f"Bảo hiểm đang ở trạng thái '{current_status}' không thể thanh toán")
                return

            # Update to da_thanh_toan if full amount paid
            new_status = current_status
            if amount >= phi_bh:
                new_status = 'da_thanh_toan'

            # Get payment date
            payment_date = self._date_input.date().toString("yyyy-MM-dd")

            # Update insurance record
            now = datetime.now().isoformat()
            self._db_conn.execute(
                """UPDATE bao_hiem
                   SET trang_thai = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (new_status, now, bh_id)
            )

            # Audit log
            self._db_conn.execute(
                """INSERT INTO audit_log (nhan_vien_id, hanh_dong, bang_anh_huong, ban_ghi_id, noi_dung, thoi_gian)
                   VALUES (?, 'RECORD_BH_PAYMENT', 'bao_hiem', ?, ?, ?)""",
                (None, bh_id, f'{{"so_tien": {amount}, "ngay_thanh_toan": "{payment_date}"}}', now)
            )

            self._db_conn.commit()

            self.payment_completed.emit(bh_id)
            self.accept()

        except Exception as e:
            self._db_conn.rollback()
            QMessageBox.critical(self, "Lỗi", f"Không thể ghi nhận thanh toán: {str(e)}")