"""Insurance list screen - insurance listing with filters and search.

Features:
- Search by policy number, customer name, or vehicle plate
- Filter by insurance type (loai_bh): TNDS, Tai nạn, Cháy nổ, Thất lạc, Khác
- Filter by status: Còn hiệu lực, Hết hạn, Đã hủy
- Table: ID, Số Policy, Loại BH, Khách hàng, Xe (biển số), Ngày mua, Ngày hết hạn, Phí BH, Trạng thái
- Shows "Xe ngoài" badge for external vehicles
- Pagination
- Double-click row to open insurance detail
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QHeaderView,
    QAbstractItemView, QMessageBox, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.bao_hiem_service import BaoHiemService, InsuranceSearchResult
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


class BaoHiemListScreen(QWidget):
    """Insurance list screen.

    Signals:
        view_insurance_clicked(bh_id: int): User wants to view insurance details.
        create_insurance_clicked(): User wants to create new insurance.
    """

    view_insurance_clicked = pyqtSignal(int)
    create_insurance_clicked = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize insurance list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = BaoHiemService(db_conn)

        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[InsuranceSearchResult] = None
        self._current_loai_bh = None
        self._current_trang_thai = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Quản lý bảo hiểm")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Create insurance button
        self._create_btn = QPushButton("+ Tạo bảo hiểm")
        self._create_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2da44e;
            }
        """)
        self._create_btn.clicked.connect(self._on_create)
        header_layout.addWidget(self._create_btn)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Tìm kiếm theo số policy, tên khách hàng, biển số...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self._search_input, stretch=1)

        self._search_btn = QPushButton("Tìm kiếm")
        self._search_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0055aa;
            }
        """)
        self._search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self._search_btn)

        layout.addLayout(search_layout)

        # Filters row
        filters_group = QGroupBox()
        filters_group.setStyleSheet("""
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
        filters_layout = QHBoxLayout(filters_group)
        filters_layout.setSpacing(16)

        # Loai BH filter
        filters_layout.addWidget(QLabel("Loại BH:"))
        self._loai_bh_combo = QComboBox()
        self._loai_bh_combo.addItem("Tất cả", None)
        self._loai_bh_combo.addItem("TNDS", "tnds")
        self._loai_bh_combo.addItem("Tai nạn", "tai_nan")
        self._loai_bh_combo.addItem("Cháy nổ", "chao_no")
        self._loai_bh_combo.addItem("Thất lạc", "that_lac")
        self._loai_bh_combo.addItem("Khác", "khac")
        self._loai_bh_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 13px;
                background: white;
            }
        """)
        self._loai_bh_combo.currentIndexChanged.connect(self._on_loai_bh_changed)
        filters_layout.addWidget(self._loai_bh_combo)

        # Trang thai filter
        filters_layout.addWidget(QLabel("Trạng thái:"))
        self._trang_thai_combo = QComboBox()
        self._trang_thai_combo.addItem("Tất cả", None)
        self._trang_thai_combo.addItem("Còn hiệu lực", "con_hieu_luc")
        self._trang_thai_combo.addItem("Hết hạn", "het_han")
        self._trang_thai_combo.addItem("Đã hủy", "huy")
        self._trang_thai_combo.setStyleSheet(self._loai_bh_combo.styleSheet())
        self._trang_thai_combo.currentIndexChanged.connect(self._on_trang_thai_changed)
        filters_layout.addWidget(self._trang_thai_combo)

        filters_layout.addStretch()

        layout.addWidget(filters_group)

        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "ID", "Số Policy", "Loại BH", "Khách hàng", "Xe (biển số)",
            "Ngày mua", "Ngày hết hạn", "Phí BH", "Trạng thái"
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
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        layout.addWidget(self._table)

        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self._prev_btn = QPushButton("Trước")
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

        self._next_btn = QPushButton("Sau")
        self._next_btn.setStyleSheet(self._prev_btn.styleSheet())
        self._next_btn.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(self._next_btn)

        self._total_label = QLabel("Tổng: 0 bảo hiểm")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _on_loai_bh_changed(self):
        """Handle insurance type filter change."""
        self._current_loai_bh = self._loai_bh_combo.currentData()
        self._current_page = 1
        self._load_data()

    def _on_trang_thai_changed(self):
        """Handle status filter change."""
        self._current_trang_thai = self._trang_thai_combo.currentData()
        self._current_page = 1
        self._load_data()

    def _on_search(self):
        """Handle search button click."""
        self._current_page = 1
        self._load_data()

    def _on_create(self):
        """Handle create insurance button."""
        self.create_insurance_clicked.emit()

    def _load_data(self):
        """Load insurance data based on filters."""
        import logging
        logger = logging.getLogger("car_management")
        logger.info(f"[BaoHiemListScreen._load_data] Starting with conn={self._db_conn}")

        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None
        logger.info(f"[BaoHiemListScreen._load_data] keyword={keyword}, loai_bh={self._current_loai_bh}, trang_thai={self._current_trang_thai}")

        try:
            result = self._service.get_all(
                loai_bh=self._current_loai_bh,
                trang_thai=self._current_trang_thai,
                search_keyword=keyword,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )

            logger.info(f"[BaoHiemListScreen._load_data] Got result: total={result.total}, items={len(result.items)}")

            self._current_result = result
            self._total_pages = result.total_pages

            self._populate_table(result.items)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} bảo hiểm")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            logger.error(f"[BaoHiemListScreen._load_data] Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, items: List[dict]):
        """Populate table with insurance data.

        Args:
            items: List of insurance dicts.
        """
        self._table.setRowCount(len(items))

        for row, item in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(item.get("id", "")))
            self._table.setItem(row, 0, item_id)

            # So policy
            self._table.setItem(row, 1, QTableWidgetItem(item.get("so_policy", "")))

            # Loai BH
            loai_bh = item.get("loai_bh", "")
            loai_label = BaoHiemService.get_loai_bh_label(loai_bh)
            self._table.setItem(row, 2, QTableWidgetItem(loai_label))

            # Khach hang
            self._table.setItem(row, 3, QTableWidgetItem(item.get("kh_ho_ten", "")))

            # Xe (bien so) - show "Xe ngoài" for external vehicles
            is_external = item.get("is_external", False)
            ma_xe = item.get("ma_xe", "")
            if is_external:
                xe_display = "Xe ngoài"
            elif ma_xe:
                hang = item.get("hang", "")
                dong_xe = item.get("dong_xe", "")
                xe_display = f"{ma_xe}" + (f" - {hang} {dong_xe}" if hang else "")
            else:
                so_khung = item.get("so_khung", "")
                so_may = item.get("so_may", "")
                xe_display = f"Khung: {so_khung}" if so_khung else f"Máy: {so_may}" if so_may else "N/A"
            self._table.setItem(row, 4, QTableWidgetItem(xe_display))

            # Ngay mua
            ngay_mua = item.get("ngay_mua", "")[:10] if item.get("ngay_mua") else ""
            self._table.setItem(row, 5, QTableWidgetItem(ngay_mua))

            # Ngay het han
            ngay_het_han = item.get("ngay_het_han", "")[:10] if item.get("ngay_het_han") else ""
            self._table.setItem(row, 6, QTableWidgetItem(ngay_het_han))

            # Phi BH
            phi_bh = item.get("phi_bh", 0)
            phi_label = f"{phi_bh:,} đ" if phi_bh else "0 đ"
            self._table.setItem(row, 7, QTableWidgetItem(phi_label))

            # Trang thai
            trang_thai = item.get("trang_thai", "")
            status_item = QTableWidgetItem()
            status_label = BaoHiemService.get_trang_thai_label(trang_thai)

            if trang_thai == "het_han":
                bg_color = QColor("#ff3b30")
                fg_color = QColor(255, 255, 255)
            elif trang_thai == "huy":
                bg_color = QColor("#86868b")
                fg_color = QColor(255, 255, 255)
            else:
                bg_color = QColor("#34c759")
                fg_color = QColor(255, 255, 255)

            status_item.setText(status_label)
            status_item.setBackground(bg_color)
            status_item.setForeground(fg_color)
            self._table.setItem(row, 8, status_item)

            # Store ID for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item.get("id"))

        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(1, 120)  # So policy
        self._table.setColumnWidth(2, 90)   # Loai BH
        self._table.setColumnWidth(3, 150)  # Khach hang
        self._table.setColumnWidth(4, 160)  # Xe
        self._table.setColumnWidth(5, 100)  # Ngay mua
        self._table.setColumnWidth(6, 110)  # Ngay het han
        self._table.setColumnWidth(7, 100)  # Phi BH
        self._table.setColumnWidth(8, 100)  # Trang thai

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

    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click."""
        item = self._table.item(row, 0)
        if item:
            bh_id = item.data(Qt.ItemDataRole.UserRole)
            if bh_id:
                self.view_insurance_clicked.emit(bh_id)

    def refresh(self):
        """Refresh the data."""
        self._load_data()