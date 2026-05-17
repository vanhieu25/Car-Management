"""Payment contract screen - S-HD-PAY - Record payments for contracts.

Features:
- List contracts needing payment (status: moi_tao)
- Show contract info, total, amount paid, remaining
- Record payment with type: dat_coc, thanhtoan_dot, thanhtoan_du
- Auto-update status: moi_tao → da_coc (if >= 10% deposit) → da_thanh_toan (if 100% paid)

References:
- BR-HD-03: Payment transitions
- BR-CALC-01: Total calculation
"""

from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QAbstractItemView, QDialog, QLineEdit,
    QComboBox, QDateEdit, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.hop_dong_service import HopDongService
from app.application.services.session import CurrentSession


class PaymentContractScreen(QWidget):
    """Payment contract screen - S-HD-PAY.

    Signals:
        back_clicked(): User wants to go back.
        payment_recorded(hop_dong_id: int): Payment was successfully recorded.
    """

    back_clicked = pyqtSignal()
    payment_recorded = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize payment contract screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._hd_service = HopDongService(db_conn)

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

        title = QLabel("Thanh toán hợp đồng")
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

        # Contract table
        table_group = QGroupBox("Danh sách hợp đồng chờ thanh toán")
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
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Mã HĐ", "Khách hàng", "Xe", "Tổng tiền", "Đã thanh toán", "Còn lại", "Trạng thái"
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
        """Load contracts needing payment."""
        try:
            # Get contracts with status 'moi_tao' that need payment
            query = """
                SELECT hd.id, hd.ma_hop_dong, hd.tong_tien, hd.trang_thai,
                       kh.ho_ten as kh_ten, kh.so_dien_thoai as kh_sdt,
                       xe.hang as xe_hang, xe.dong_xe as xe_dong,
                       COALESCE(hd.da_thanh_toan, 0) as da_thanh_toan
                FROM hop_dong hd
                JOIN khach_hang kh ON hd.khach_hang_id = kh.id
                JOIN xe ON hd.xe_id = xe.id
                WHERE hd.trang_thai = 'moi_tao'
                ORDER BY hd.ngay_tao DESC
            """
            cursor = self._db_conn.execute(query)
            rows = cursor.fetchall()

            self._populate_table(rows)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, rows):
        """Populate table with contract data.

        Args:
            rows: List of database rows.
        """
        self._table.setRowCount(len(rows))

        status_labels = {
            "moi_tao": "Chờ thanh toán",
        }

        for row_idx, row in enumerate(rows):
            # Mã HĐ
            item_ma = QTableWidgetItem(row[1])
            item_ma.setData(Qt.ItemDataRole.UserRole, row[0])
            self._table.setItem(row_idx, 0, item_ma)

            # Khách hàng
            self._table.setItem(row_idx, 1, QTableWidgetItem(row[4] or "-"))

            # Xe
            xe_info = f"{row[6] or ''} {row[7] or ''}".strip()
            self._table.setItem(row_idx, 2, QTableWidgetItem(xe_info or "-"))

            # Tổng tiền
            tong_tien = row[2] or 0
            tien_text = f"{tong_tien:,} đ".replace(",", ".")
            item_tong = QTableWidgetItem(tien_text)
            item_tong.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._table.setItem(row_idx, 3, item_tong)

            # Đã thanh toán
            da_thanh_toan = row[8] or 0
            tien_da_text = f"{da_thanh_toan:,} đ".replace(",", ".")
            item_da = QTableWidgetItem(tien_da_text)
            item_da.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._table.setItem(row_idx, 4, item_da)

            # Còn lại
            con_lai = tong_tien - da_thanh_toan
            tien_con_text = f"{con_lai:,} đ".replace(",", ".")
            item_con = QTableWidgetItem(tien_con_text)
            item_con.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._table.setItem(row_idx, 5, item_con)

            # Trạng thái
            trang_thai = row[3]
            status_text = status_labels.get(trang_thai, trang_thai)
            item_status = QTableWidgetItem(status_text)
            item_status.setBackground(QColor("#8e8e93"))
            item_status.setForeground(QColor(255, 255, 255))
            self._table.setItem(row_idx, 6, item_status)

        self._store_rows(rows)

    def _store_rows(self, rows):
        """Store row data for later reference."""
        self._rows_data = []
        for row in rows:
            self._rows_data.append({
                "id": row[0],
                "ma_hop_dong": row[1],
                "tong_tien": row[2],
                "da_thanh_toan": row[8] if len(row) > 8 else 0,
            })

    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click."""
        self._show_payment_dialog()

    def _on_pay_clicked(self):
        """Handle pay button click."""
        self._show_payment_dialog()

    def _show_payment_dialog(self):
        """Show payment dialog for selected contract."""
        selected = self._table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        hd_id_item = self._table.item(row, 0)
        if not hd_id_item:
            return

        hd_id = hd_id_item.data(Qt.ItemDataRole.UserRole)

        # Find contract data
        contract_data = None
        for data in self._rows_data:
            if data["id"] == hd_id:
                contract_data = data
                break

        if not contract_data:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thông tin hợp đồng")
            return

        # Show payment dialog
        dialog = PaymentContractDialog(
            self._db_conn,
            self._session,
            contract_data,
            self
        )
        dialog.payment_completed.connect(self._on_payment_completed)
        dialog.exec()

    def _on_payment_completed(self, hop_dong_id: int):
        """Handle payment completed."""
        QMessageBox.information(self, "Thành công", "Đã ghi nhận thanh toán!")
        self._table.clearSelection()
        self._pay_btn.setEnabled(False)
        self._load_data()
        self.payment_recorded.emit(hop_dong_id)

    def refresh(self):
        """Refresh data."""
        self._load_data()


class PaymentContractDialog(QDialog):
    """Dialog for recording contract payment."""

    payment_completed = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, contract_data: Dict, parent=None):
        """Initialize payment dialog.

        Args:
            db_conn: Database connection.
            session: Current session.
            contract_data: Contract info dict with id, ma_hop_dong, tong_tien.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._contract_data = contract_data

        self.setWindowTitle(f"Thanh toán - {contract_data['ma_hop_dong']}")
        self.setMinimumWidth(450)
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

        # Contract info
        info_group = QGroupBox("Thông tin hợp đồng")
        info_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        info_layout = QVBoxLayout(info_group)

        ma_hd_label = QLabel(f"Mã HĐ: {self._contract_data['ma_hop_dong']}")
        info_layout.addWidget(ma_hd_label)

        tong_tien = self._contract_data['tong_tien']
        tong_text = f"{tong_tien:,} đ".replace(",", ".")
        tong_label = QLabel(f"Tổng tiền: {tong_text}")
        tong_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        info_layout.addWidget(tong_label)

        # Current paid amount
        da_thanh_toan = self._contract_data.get('da_thanh_toan', 0)
        if da_thanh_toan > 0:
            da_text = f"{da_thanh_toan:,} đ".replace(",", ".")
            da_label = QLabel(f"Đã thanh toán: {da_text}")
            da_label.setStyleSheet("color: #34c759; font-size: 14px;")
            info_layout.addWidget(da_label)
            con_lai = tong_tien - da_thanh_toan
            con_text = f"{con_lai:,} đ".replace(",", ".")
            con_label = QLabel(f"Còn lại: {con_text}")
            con_label.setStyleSheet("color: #ff9500; font-size: 14px;")
            info_layout.addWidget(con_label)

        # Minimum deposit info (10%)
        min_deposit = int(tong_tien * 0.1)
        min_text = f"{min_deposit:,} đ".replace(",", ".")
        deposit_hint = QLabel(f"Đặt cọc tối thiểu (10%): {min_text}")
        deposit_hint.setStyleSheet("color: #86868b; font-size: 13px;")
        info_layout.addWidget(deposit_hint)

        layout.addWidget(info_group)

        # Payment type
        type_group = QGroupBox("Loại thanh toán")
        type_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        type_layout = QVBoxLayout(type_group)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["Đặt cọc (thanh toán trước)", "Thanh toán đợt", "Thanh toán đầy đủ"])
        self._type_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
        """)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self._type_combo)

        layout.addWidget(type_group)

        # Amount input
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
        amount_layout.addWidget(self._amount_input, stretch=1)

        layout.addWidget(amount_group)

        # Quick amount buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Nhanh:"))

        # 10% button
        min_btn = QPushButton("10%")
        min_btn.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 4px;
                font-size: 12px;
                background: white;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        min_btn.clicked.connect(lambda: self._set_quick_amount(10))
        quick_layout.addWidget(min_btn)

        # 50% button
        half_btn = QPushButton("50%")
        half_btn.setStyleSheet(min_btn.styleSheet())
        half_btn.clicked.connect(lambda: self._set_quick_amount(50))
        quick_layout.addWidget(half_btn)

        # 100% button
        full_btn = QPushButton("100%")
        full_btn.setStyleSheet(min_btn.styleSheet())
        full_btn.clicked.connect(lambda: self._set_quick_amount(100))
        quick_layout.addWidget(full_btn)

        layout.addLayout(quick_layout)

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

    def _on_type_changed(self):
        """Handle payment type change."""
        # Set default amount based on type
        tong_tien = self._contract_data['tong_tien']
        type_index = self._type_combo.currentIndex()

        if type_index == 0:  # Đặt cọc - 10%
            amount = int(tong_tien * 0.1)
        elif type_index == 1:  # Thanh toán đợt - 50%
            amount = int(tong_tien * 0.5)
        else:  # Thanh toán đầy đủ - 100%
            amount = tong_tien

        self._amount_input.setText(str(amount))

    def _set_quick_amount(self, percent: int):
        """Set quick amount based on percentage."""
        tong_tien = self._contract_data['tong_tien']
        amount = int(tong_tien * percent / 100)
        self._amount_input.setText(str(amount))

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

            tong_tien = self._contract_data['tong_tien']

            # Validate minimum deposit (10%)
            min_deposit = int(tong_tien * 0.1)
            type_index = self._type_combo.currentIndex()

            if type_index == 0 and amount < min_deposit:
                QMessageBox.warning(self, "Lỗi", f"Đặt cọc tối thiểu là {min_deposit:,} đ".replace(",", "."))
                return

            if amount > tong_tien:
                QMessageBox.warning(self, "Lỗi", "Số tiền không thể lớn hơn tổng tiền")
                return

            # Process payment based on type
            self._process_payment(amount, type_index)

        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Số tiền không hợp lệ")

    def _process_payment(self, amount: int, payment_type: int):
        """Process the payment.

        Args:
            amount: Payment amount.
            payment_type: 0=dat_coc, 1=thanhtoan_dot, 2=thanhtoan_du
        """
        try:
            hd_id = self._contract_data['id']
            nhan_vien_id = self._session.nhan_vien_id if self._session else None

            # Map payment_type to loai_thanh_toan
            loai_map = {
                0: 'dat_coc',
                1: 'thanhtoan_dot',
                2: 'thanhtoan_du',
            }
            loai_thanh_toan = loai_map.get(payment_type, 'thanhtoan_dot')

            # Use service to record payment
            service = HopDongService(self._db_conn)
            service.record_payment(
                hop_dong_id=hd_id,
                so_tien=amount,
                loai_thanh_toan=loai_thanh_toan,
                nhan_vien_id=nhan_vien_id,
            )

            self.payment_completed.emit(hd_id)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể ghi nhận thanh toán: {str(e)}")

    def get_values(self):
        """Get payment values.

        Returns:
            Dict with payment info.
        """
        return {
            "hop_dong_id": self._contract_data['id'],
            "amount": int(self._amount_input.text().replace(",", "")),
            "payment_type": self._type_combo.currentIndex(),
        }