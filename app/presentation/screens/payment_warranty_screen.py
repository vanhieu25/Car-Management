"""Payment warranty screen - S-BH-PAY2 - Record payment for warranty/repair requests.

Features:
- List warranty requests needing payment (status: dang_xu_ly)
- Show request info, estimated cost
- Record final cost and complete payment
- Auto-update status: dang_xu_ly → da_hoan_thanh on payment

References:
- BR-BH-05: Request status transitions
- BR-BH-06: chi_phi validation
"""

from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QAbstractItemView, QDialog, QLineEdit, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.bao_hanh_service import BaoHanhService
from app.application.services.session import CurrentSession


class PaymentWarrantyScreen(QWidget):
    """Payment warranty screen - S-BH-PAY2.

    Signals:
        back_clicked(): User wants to go back.
        payment_recorded(req_id: int): Payment was successfully recorded.
    """

    back_clicked = pyqtSignal()
    payment_recorded = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize payment warranty screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bh_service = BaoHanhService(db_conn)

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

        title = QLabel("Thanh toán bảo hành/sửa chữa")
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

        # Request table
        table_group = QGroupBox("Danh sách yêu cầu đang xử lý")
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
            "ID", "Ngày yêu cầu", "Khách hàng", "Xe", "Loại", "Chi phí ước tính", "Trạng thái"
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
        """Load warranty requests needing payment."""
        try:
            # Get requests with status dang_xu_ly (needing completion payment)
            query = """
                SELECT yc.id, yc.ngay_yeu_cau, yc.loai_yeu_cau, yc.chi_phi,
                       yc.trang_thai, yc.bao_hanh_id,
                       kh.ho_ten as kh_ho_ten,
                       xe.hang as xe_hang, xe.dong_xe as xe_dong_xe
                FROM bao_hanh_yeu_cau yc
                JOIN bao_hanh bh ON yc.bao_hanh_id = bh.id
                JOIN khach_hang kh ON bh.khach_hang_id = kh.id
                JOIN xe ON bh.xe_id = xe.id
                WHERE yc.trang_thai = 'dang_xu_ly'
                ORDER BY yc.ngay_yeu_cau DESC
            """
            cursor = self._db_conn.execute(query)
            rows = cursor.fetchall()

            self._populate_table(rows)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, rows):
        """Populate table with request data.

        Args:
            rows: List of database rows.
        """
        self._table.setRowCount(len(rows))

        loai_map = {
            "bao_duong": "Bảo dưỡng",
            "sua_chua": "Sửa chữa",
            "thay_the": "Thay thế",
        }

        status_colors = {
            "moi": "#007aff",
            "dang_xu_ly": "#ff9500",
            "da_hoan_thanh": "#34c759",
            "da_dong": "#8e8e93",
        }

        status_labels = {
            "dang_xu_ly": "Đang xử lý",
        }

        for row_idx, row in enumerate(rows):
            # ID
            item_id = QTableWidgetItem(str(row[0]))
            item_id.setData(Qt.ItemDataRole.UserRole, row[0])
            self._table.setItem(row_idx, 0, item_id)

            # Ngày yêu cầu
            ngay_yc = row[1][:10] if row[1] else "-"
            self._table.setItem(row_idx, 1, QTableWidgetItem(ngay_yc))

            # Khách hàng
            self._table.setItem(row_idx, 2, QTableWidgetItem(row[6] or "-"))

            # Xe
            xe_info = f"{row[7] or ''} {row[8] or ''}".strip()
            self._table.setItem(row_idx, 3, QTableWidgetItem(xe_info or "-"))

            # Loại
            loai = loai_map.get(row[2], row[2])
            self._table.setItem(row_idx, 4, QTableWidgetItem(loai))

            # Chi phí ước tính (display current chi_phi or placeholder)
            chi_phi = int(row[3] or 0)
            tien_text = f"{chi_phi:,} đ".replace(",", ".")
            item_tien = QTableWidgetItem(tien_text)
            item_tien.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._table.setItem(row_idx, 5, item_tien)

            # Trạng thái
            trang_thai = row[4]
            status_text = status_labels.get(trang_thai, trang_thai)
            item_status = QTableWidgetItem(status_text)
            color_hex = status_colors.get(trang_thai, "#8e8e93")
            item_status.setBackground(QColor(color_hex))
            item_status.setForeground(QColor(255, 255, 255))
            self._table.setItem(row_idx, 6, item_status)

        self._store_rows(rows)

    def _store_rows(self, rows):
        """Store row data for later reference."""
        self._rows_data = []
        for row in rows:
            self._rows_data.append({
                "id": row[0],
                "chi_phi": row[3] or 0,
                "loai_yeu_cau": row[2],
            })

    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click."""
        self._show_payment_dialog()

    def _on_pay_clicked(self):
        """Handle pay button click."""
        self._show_payment_dialog()

    def _show_payment_dialog(self):
        """Show payment dialog for selected request."""
        selected = self._table.selectedItems()
        if not selected:
            return

        row_idx = selected[0].row()
        req_id_item = self._table.item(row_idx, 0)
        if not req_id_item:
            return

        req_id = req_id_item.data(Qt.ItemDataRole.UserRole)

        # Find request data
        request_data = None
        for data in self._rows_data:
            if data["id"] == req_id:
                request_data = data
                break

        if not request_data:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thông tin yêu cầu")
            return

        # Show payment dialog
        dialog = PaymentWarrantyDialog(
            self._db_conn,
            self._session,
            request_data,
            self
        )
        dialog.payment_completed.connect(self._on_payment_completed)
        dialog.exec()

    def _on_payment_completed(self, req_id: int):
        """Handle payment completed."""
        QMessageBox.information(self, "Thành công", "Đã ghi nhận thanh toán!")
        self._table.clearSelection()
        self._pay_btn.setEnabled(False)
        self._load_data()
        self.payment_recorded.emit(req_id)

    def refresh(self):
        """Refresh data."""
        self._load_data()


class PaymentWarrantyDialog(QDialog):
    """Dialog for recording warranty payment and completing request."""

    payment_completed = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, request_data: Dict, parent=None):
        """Initialize payment dialog.

        Args:
            db_conn: Database connection.
            session: Current session.
            request_data: Request info dict with id, chi_phi, loai_yeu_cau.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._request_data = request_data

        loai_map = {
            "bao_duong": "Bảo dưỡng",
            "sua_chua": "Sửa chữa",
            "thay_the": "Thay thế",
        }
        loai_text = loai_map.get(request_data.get('loai_yeu_cau', ''), request_data.get('loai_yeu_cau', ''))

        self.setWindowTitle(f"Thanh toán - {loai_text}")
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

        # Request info
        info_group = QGroupBox("Thông tin yêu cầu")
        info_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        info_layout = QVBoxLayout(info_group)

        req_id_label = QLabel(f"Mã yêu cầu: {self._request_data['id']}")
        info_layout.addWidget(req_id_label)

        chi_phi = self._request_data.get('chi_phi', 0)
        phi_text = f"{chi_phi:,} đ".replace(",", ".") if chi_phi > 0 else "Chưa có"
        phi_label = QLabel(f"Chi phí ước tính: {phi_text}")
        phi_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        info_layout.addWidget(phi_label)

        layout.addWidget(info_group)

        # Payment amount
        amount_group = QGroupBox("Chi phí hoàn thành")
        amount_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        amount_layout = QHBoxLayout(amount_group)

        amount_layout.addWidget(QLabel("Chi phí (VNĐ):"))

        self._amount_input = QLineEdit()
        self._amount_input.setPlaceholderText("Nhập chi phí hoàn thành...")
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
        # Pre-fill with estimated cost
        if chi_phi > 0:
            self._amount_input.setText(str(chi_phi))
        amount_layout.addWidget(self._amount_input, stretch=1)

        layout.addWidget(amount_group)

        # Info note
        note_label = QLabel("Sau khi thanh toán, yêu cầu sẽ được chuyển sang trạng thái 'Hoàn thành'.")
        note_label.setStyleSheet("color: #86868b; font-size: 13px; padding: 8px;")
        layout.addWidget(note_label)

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
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập chi phí")
                return

            chi_phi = int(amount_text.replace(",", ""))
            if chi_phi < 0:
                QMessageBox.warning(self, "Lỗi", "Chi phí không thể âm")
                return

            # Process payment - update request to da_hoan_thanh
            self._process_payment(chi_phi)

        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Chi phí không hợp lệ")

    def _process_payment(self, chi_phi: int):
        """Process the payment and complete the request.

        Args:
            chi_phi: Final cost.
        """
        try:
            req_id = self._request_data['id']
            nhan_vien_id = self._session.nhan_vien_id if self._session else None

            # Use BaoHanhService to update request status
            service = BaoHanhService(self._db_conn)
            service.update_request(
                req_id=req_id,
                trang_thai='da_hoan_thanh',
                chi_phi=chi_phi,
                nhan_vien_id_current=nhan_vien_id,
            )

            self.payment_completed.emit(req_id)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể ghi nhận thanh toán: {str(e)}")