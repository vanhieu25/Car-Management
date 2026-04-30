"""Accessory list screen - S-PK-01 - Accessory listing with search and filters.

Features:
- Table: ma_pk, ten_pk, phan_loai, gia_ban, ton_kho
- Filter by phan_loai (5 categories: noi_that, ngoai_that, dien_tu, bao_ve, trang_tri)
- Highlight row red when ton_kho <= 0 (BR-PK-05)
- Search by ten_pk/ma_pk
- Pagination
- Empty/Loading/Error states
- Add/Edit/Delete buttons (permission-based)
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QStyledItemDelegate, QStyleOptionViewItem, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QColor, QPalette, QRegularExpressionValidator

from app.application.services.phu_kien_service import PhuKienService, PhuKienSearchResult
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


PHAN_LOAI_LABELS = {
    "noi_that": "Nội thất",
    "ngoai_that": "Ngoại thất",
    "dien_tu": "Điện tử",
    "bao_ve": "Bảo vệ",
    "trang_tri": "Trang trí",
}

PHAN_LOAI_OPTIONS = ["Tất cả"] + list(PHAN_LOAI_LABELS.values())


class AccessoryListScreen(QWidget):
    """Accessory list screen - S-PK-01.

    Signals:
        add_accessory_clicked: User clicked add accessory button.
        edit_accessory_clicked(pk_id: int): User wants to edit an accessory.
    """

    add_accessory_clicked = pyqtSignal()
    edit_accessory_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize accessory list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._pk_service = PhuKienService(db_conn, session)

        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[PhuKienSearchResult] = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Quản lý phụ kiện")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add accessory button (only for admin)
        if self._session and self._session.vai_tro_ma in ("A-01",):
            self._add_btn = QPushButton("➕ Thêm phụ kiện")
            self._add_btn.setStyleSheet("""
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
            self._add_btn.clicked.connect(self._on_add_clicked)
            header_layout.addWidget(self._add_btn)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo mã, tên phụ kiện...")
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

        filter_layout.addWidget(QLabel("Phân loại:"))

        self._phan_loai_combo = QComboBox()
        self._phan_loai_combo.addItems(PHAN_LOAI_OPTIONS)
        self._phan_loai_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._phan_loai_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._phan_loai_combo)

        filter_layout.addStretch()

        # Legend for out of stock
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        out_of_stock_label = QLabel("<span style='background:#ff3b30; color:white; padding:2px 8px; border-radius:4px; font-size:12px;'>Hết hàng</span>")
        legend_layout.addWidget(QLabel("Chú thích:"))
        legend_layout.addWidget(out_of_stock_label)

        filter_layout.addLayout(legend_layout)

        layout.addWidget(filter_group)

        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Mã PK", "Tên phụ kiện", "Phân loại", "Giá bán", "Tồn kho"
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

        self._total_label = QLabel("Tổng: 0 phụ kiện")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        self._current_page = 1
        self._load_data()

    def _load_data(self):
        """Load accessory data based on filters."""
        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None

        # Map label to value
        phan_loai_value_map = {v: k for k, v in PHAN_LOAI_LABELS.items()}
        phan_loai = None
        if self._phan_loai_combo.currentText() != "Tất cả":
            phan_loai = phan_loai_value_map.get(self._phan_loai_combo.currentText())

        try:
            result = self._pk_service.search(
                keyword=keyword,
                phan_loai=phan_loai,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )

            self._current_result = result
            self._total_pages = result.total_pages

            self._populate_table(result.items)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} phụ kiện")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, items):
        """Populate table with accessory data.

        Args:
            items: List of PhuKien entities.
        """
        self._table.setRowCount(len(items))

        for row, pk in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(pk.id))
            self._table.setItem(row, 0, item_id)

            # Mã PK
            self._table.setItem(row, 1, QTableWidgetItem(pk.ma_pk))

            # Tên phụ kiện
            self._table.setItem(row, 2, QTableWidgetItem(pk.ten_pk))

            # Phân loại
            phan_loai_text = PHAN_LOAI_LABELS.get(pk.phan_loai, pk.phan_loai)
            self._table.setItem(row, 3, QTableWidgetItem(phan_loai_text))

            # Giá bán
            gia_ban_text = f"{pk.gia_ban:,} đ".replace(",", ".")
            item_gia = QTableWidgetItem(gia_ban_text)
            item_gia.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_gia)

            # Tồn kho - highlight red when <= 0 (BR-PK-05)
            item_ton_kho = QTableWidgetItem(str(pk.ton_kho))
            item_ton_kho.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if pk.ton_kho <= 0:
                item_ton_kho.setBackground(QColor("#ff3b30"))
                item_ton_kho.setForeground(QColor(255, 255, 255))
            self._table.setItem(row, 5, item_ton_kho)

            # Store ID for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, pk.id)

        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(1, 100)   # Mã PK
        self._table.setColumnWidth(3, 120)  # Phân loại
        self._table.setColumnWidth(4, 120)  # Giá bán
        self._table.setColumnWidth(5, 80)   # Tồn kho

    def _on_search(self):
        """Handle search button click."""
        self._current_page = 1
        self._load_data()

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
            pk_id = item.data(Qt.ItemDataRole.UserRole)
            if pk_id:
                self.edit_accessory_clicked.emit(pk_id)

    def _on_add_clicked(self):
        """Handle add accessory button click."""
        self.add_accessory_clicked.emit()

    def refresh(self):
        """Refresh the data."""
        self._load_data()
