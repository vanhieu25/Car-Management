"""Order list screen - S-NCC-03 - Purchase order listing with filters.

Features:
- Order list: table by trang_thai (cho_xu_ly / da_xac_nhan / da_nhan / da_huy)
- Filter by trang_thai and date range
- "Tạo đơn mới" button → opens order_form_dialog
- "Đánh dấu đã nhận" button on da_xac_nhan orders → confirm dialog

References:
- BR-NCC-04: Order creation with status 'cho_xu_ly'
- BR-NCC-05: set_received transitions to 'da_nhan' and creates nhap_kho

UI Tasks: T-G4.4.UI.03, T-G4.4.UI.04
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor

from app.application.services.don_dat_hang_service import (
    DonDatHangService,
    DonDatHangSearchResult,
    DonDatHangServiceError,
)
from app.application.services.session import CurrentSession

PAGE_SIZE = 50

# Status mapping for display
STATUS_MAP = {
    "cho_xu_ly": "Chờ xử lý",
    "da_xac_nhan": "Đã xác nhận",
    "da_nhan": "Đã nhận",
    "da_huy": "Đã hủy",
}

# Status colors
STATUS_COLORS = {
    "cho_xu_ly": "#ff9500",  # Orange
    "da_xac_nhan": "#007aff",  # Blue
    "da_nhan": "#34c759",  # Green
    "da_huy": "#8e8e93",  # Gray
}


class OrderListScreen(QWidget):
    """Order list screen - S-NCC-03.

    Signals:
        create_order_clicked: User clicked create order button.
        view_order_clicked(don_id: int): User wants to view order details.
        mark_received_clicked(don_id: int): User wants to mark order as received.
    """

    create_order_clicked = pyqtSignal()
    view_order_clicked = pyqtSignal(int)
    mark_received_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize order list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._ddh_service = DonDatHangService(db_conn)

        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[DonDatHangSearchResult] = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Quản lý đơn đặt hàng")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Create order button (only for A-01, A-02)
        if self._session and self._session.vai_tro_ma in ("A-01", "A-02"):
            self._create_btn = QPushButton("🛒 Tạo đơn mới")
            self._create_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34c759;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #2db14e;
                }
            """)
            self._create_btn.clicked.connect(self._on_create_clicked)
            header_layout.addWidget(self._create_btn)

        layout.addLayout(header_layout)

        # Filter bar
        filter_group = QGroupBox()
        filter_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 12px 16px;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                font-weight: 600;
                color: #1d1d1f;
            }
        """)
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)

        filter_layout.addWidget(QLabel("Trạng thái:"))

        self._status_combo = QComboBox()
        self._status_combo.addItems(["Tất cả", "Chờ xử lý", "Đã xác nhận", "Đã nhận", "Đã hủy"])
        self._status_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 140px;
                background: white;
            }
        """)
        self._status_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._status_combo)

        filter_layout.addWidget(QLabel("Từ ngày:"))

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_from.setStyleSheet("""
            QDateEdit {
                padding: 6px 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_from.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("đến:"))

        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setStyleSheet("""
            QDateEdit {
                padding: 6px 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_to.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_to)

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Mã đơn", "Nhà cung cấp", "Ngày đặt", "Tổng giá", "Trạng thái", "Thao tác"
        ])

        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f7;
                padding: 10px 8px;
                border: none;
                font-weight: 600;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #0066cc;
                color: white;
            }
        """)

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        layout.addWidget(self._table)

        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self._prev_btn = QPushButton("◀ Trước")
        self._prev_btn.setStyleSheet("""
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
        self._prev_btn.clicked.connect(self._on_prev_page)
        pagination_layout.addWidget(self._prev_btn)

        self._page_label = QLabel("Trang 1 / 1")
        self._page_label.setStyleSheet("font-size: 14px; color: #86868b; padding: 0 16px;")
        pagination_layout.addWidget(self._page_label)

        self._next_btn = QPushButton("Sau ▶")
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        self._next_btn.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(self._next_btn)

        self._total_label = QLabel("Tổng: 0 đơn hàng")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        self._current_page = 1
        self._load_data()

    def _load_data(self):
        """Load order data based on filters."""
        # Map display text to status code
        status_map = {
            "Tất cả": None,
            "Chờ xử lý": "cho_xu_ly",
            "Đã xác nhận": "da_xac_nhan",
            "Đã nhận": "da_nhan",
            "Đã hủy": "da_huy",
        }
        trang_thai = status_map.get(self._status_combo.currentText())

        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        try:
            result = self._ddh_service.search(
                trang_thai=trang_thai,
                ngay_dat_from=date_from,
                ngay_dat_to=date_to,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )

            self._current_result = result
            self._total_pages = result.total_pages

            self._populate_table(result.items)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} đơn hàng")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, items: List[dict]):
        """Populate table with order data.

        Args:
            items: List of order dicts.
        """
        self._table.setRowCount(len(items))

        for row, order in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(order["id"]))
            self._table.setItem(row, 0, item_id)

            # Mã đơn
            self._table.setItem(row, 1, QTableWidgetItem(order.get("ma_don", "")))

            # Nhà cung cấp
            self._table.setItem(row, 2, QTableWidgetItem(order.get("ten_ncc", "-")))

            # Ngày đặt
            ngay_dat = order.get("ngay_dat", "")
            if ngay_dat:
                ngay_dat = ngay_dat[:10]
            self._table.setItem(row, 3, QTableWidgetItem(ngay_dat))

            # Tổng giá
            tong_gia = order.get("tong_gia", 0)
            gia_text = f"{tong_gia:,.0f} đ".replace(",", ".")
            item_gia = QTableWidgetItem(gia_text)
            item_gia.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_gia)

            # Trạng thái
            trang_thai = order.get("trang_thai", "")
            status_text = STATUS_MAP.get(trang_thai, trang_thai)
            item_status = QTableWidgetItem(status_text)
            color = STATUS_COLORS.get(trang_thai, "#8e8e93")
            item_status.setBackground(QColor(color))
            item_status.setForeground(QColor(255, 255, 255))
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, item_status)

            # Thao tác buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(4)

            # View button
            view_btn = QPushButton("👁️")
            view_btn.setFixedSize(30, 30)
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f7;
                    border: 1px solid #d2d2d7;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e5e5ea;
                }
            """)
            view_btn.clicked.connect(lambda _, o=order: self._on_view_clicked(o))
            action_layout.addWidget(view_btn)

            # Mark received button (only for da_xac_nhan orders)
            if trang_thai == "da_xac_nhan":
                receive_btn = QPushButton("📦")
                receive_btn.setFixedSize(30, 30)
                receive_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #34c759;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #2db14e;
                    }
                """)
                receive_btn.clicked.connect(lambda _, o=order: self._on_mark_received_clicked(o))
                action_layout.addWidget(receive_btn)

            self._table.setCellWidget(row, 6, action_widget)

            # Store ID for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, order["id"])

        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(1, 100)  # Mã đơn
        self._table.setColumnWidth(3, 100)  # Ngày đặt
        self._table.setColumnWidth(4, 120)  # Tổng giá
        self._table.setColumnWidth(5, 100)  # Trạng thái

    def _on_view_clicked(self, order: dict):
        """Handle view button click."""
        self.view_order_clicked.emit(order["id"])

    def _on_mark_received_clicked(self, order: dict):
        """Handle mark received button click - show confirm dialog."""
        chi_tiet = order.get("chi_tiet", [])
        item_count = sum(item.get("so_luong", 0) for item in chi_tiet)

        reply = QMessageBox.question(
            self,
            "Xác nhận đã nhận hàng",
            f"Sẽ tạo phiếu nhập kho cho {item_count} items.\n\n"
            f"Đơn hàng: {order.get('ma_don', '')}\n"
            f"Nhà cung cấp: {order.get('ten_ncc', '-')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.mark_received_clicked.emit(order["id"])

    def _on_create_clicked(self):
        """Handle create order button click."""
        self.create_order_clicked.emit()

    def _on_prev_page(self):
        """Go to previous page."""
        if self._current_page > 1:
            self._current_page -= 1
            self._load_data()

    def _on_next_page(self):
        """Go to next page."""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_data()

    def refresh(self):
        """Refresh the data."""
        self._load_data()