"""Promotion list screen - S-KM-01 - Promotion listing with search and filters.

Features:
- Table: ma_km, ten_km, loai_km, gia_tri, tu_ngay, den_ngay, trang_thai
- Badge colors for trang_thai: 'dang_chay'=green, 'tam_dung'=yellow, 'ket_thuc'=red
- Pause/Resume button in each row (calls service)
- Filter by trang_thai, search by ten_km/ma_km
- Filter by loai_km
- Filter by date range (tu_ngay - den_ngay)
- Pagination

References:
- BR-KM-01..10: Promotion lifecycle management
- BR-FLOW: Promotion status flow (dang_chay <-> tam_dung, ket_thuc)
"""

from typing import Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor

from app.application.services.khuyen_mai_service import (
    KhuyenMaiService,
    KhuyenMaiNotFoundError,
    KhuyenMaiExpiredError,
    KhuyenMaiServiceError,
)
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


LOAI_KM_LABELS = {
    "giam_tien_mat": "Giảm tiền mặt",
    "giam_phan_tram": "Giảm phần trăm",
    "tang_phu_kien": "Tặng phụ kiện",
    "giam_lai_suat": "Giảm lãi suất",
    "combo": "Combo",
}

LOAI_KM_OPTIONS = ["Tất cả"] + list(LOAI_KM_LABELS.values())

TRANG_THAI_OPTIONS = ["Tất cả", "Đang chạy", "Tạm dừng", "Kết thúc"]
TRANG_THAI_VALUE_MAP = {
    "Đang chạy": "dang_chay",
    "Tạm dừng": "tam_dung",
    "Kết thúc": "ket_thuc",
}


class PromoListScreen(QWidget):
    """Promotion list screen - S-KM-01.

    Signals:
        add_promo_clicked: User clicked add promotion button.
        edit_promo_clicked(km_id: int): User wants to edit a promotion.
    """

    add_promo_clicked = pyqtSignal()
    edit_promo_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize promotion list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._km_service = KhuyenMaiService(db_conn, session)

        self._current_page = 1
        self._total_pages = 1

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Quản lý khuyến mãi")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add promotion button (only for admin A-01)
        if self._session and self._session.vai_tro_ma in ("A-01",):
            self._add_btn = QPushButton("➕ Thêm khuyến mãi")
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
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo mã, tên khuyến mãi...")
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

        # Status filter
        filter_layout.addWidget(QLabel("Trạng thái:"))
        self._status_combo = QComboBox()
        self._status_combo.addItems(TRANG_THAI_OPTIONS)
        self._status_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._status_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._status_combo)

        # Loai KM filter
        filter_layout.addWidget(QLabel("Loại KM:"))
        self._loai_km_combo = QComboBox()
        self._loai_km_combo.addItems(LOAI_KM_OPTIONS)
        self._loai_km_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 140px;
                background: white;
            }
        """)
        self._loai_km_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._loai_km_combo)

        # Date range - from
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-3))
        self._date_from.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_from.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_from)

        # Date range - to
        filter_layout.addWidget(QLabel("Đến ngày:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate().addMonths(3))
        self._date_to.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
            }
        """)
        self._date_to.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._date_to)

        filter_layout.addStretch()

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        legend_layout.addWidget(self._create_badge("Đang chạy", "#34c759"))
        legend_layout.addWidget(self._create_badge("Tạm dừng", "#ffcc00"))
        legend_layout.addWidget(self._create_badge("Kết thúc", "#ff3b30"))

        filter_layout.addLayout(legend_layout)

        layout.addWidget(filter_group)

        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "ID", "Mã KM", "Tên khuyến mãi", "Loại", "Giá trị", "Từ ngày", "Đến ngày", "Trạng thái"
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

        self._total_label = QLabel("Tổng: 0 khuyến mãi")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _create_badge(self, text: str, color: str) -> QLabel:
        """Create a badge label with colored background.

        Args:
            text: Badge text.
            color: Hex color code.

        Returns:
            QLabel with styled badge.
        """
        label = QLabel(f"<span style='background:{color}; color:white; padding:2px 8px; border-radius:4px; font-size:12px;'>{text}</span>")
        label.setStyleSheet("padding: 0 4px;")
        return label

    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        self._current_page = 1
        self._load_data()

    def _get_filter_params(self) -> dict:
        """Get current filter parameters."""
        params = {}

        # Status filter
        status_text = self._status_combo.currentText()
        if status_text != "Tất cả":
            params["trang_thai"] = TRANG_THAI_VALUE_MAP.get(status_text)

        # Loai KM filter
        loai_km_value_map = {v: k for k, v in LOAI_KM_LABELS.items()}
        if self._loai_km_combo.currentText() != "Tất cả":
            params["loai_km"] = loai_km_value_map.get(self._loai_km_combo.currentText())

        # Date range
        params["date_from"] = self._date_from.date().toString("yyyy-MM-dd")
        params["date_to"] = self._date_to.date().toString("yyyy-MM-dd")

        # Search keyword
        keyword = self._search_input.text().strip()
        if keyword:
            params["keyword"] = keyword

        return params

    def _load_data(self):
        """Load promotion data based on filters."""
        params = self._get_filter_params()

        try:
            # Get all and filter in memory for now (service doesn't have full search yet)
            all_km = self._km_service.get_all(limit=1000, offset=0)

            # Apply filters
            filtered_km = []
            for km in all_km:
                # Status filter
                if "trang_thai" in params and km.trang_thai != params["trang_thai"]:
                    continue

                # Loai KM filter
                if "loai_km" in params and km.loai_km != params["loai_km"]:
                    continue

                # Date range filter
                if params.get("date_from") and km.tu_ngay < params["date_from"]:
                    continue
                if params.get("date_to") and km.den_ngay > params["date_to"]:
                    continue

                # Keyword filter (search in ten_km)
                if "keyword" in params:
                    keyword = params["keyword"].lower()
                    if keyword not in km.ten_km.lower():
                        continue

                filtered_km.append(km)

            # Paginate
            total = len(filtered_km)
            self._total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            start = (self._current_page - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            page_items = filtered_km[start:end]

            self._populate_table(page_items)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {total} khuyến mãi")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, items):
        """Populate table with promotion data.

        Args:
            items: List of KhuyenMai entities.
        """
        self._table.setRowCount(len(items))

        # Status colors
        status_colors = {
            "dang_chay": "#34c759",    # Green
            "tam_dung": "#ffcc00",     # Yellow
            "ket_thuc": "#ff3b30",     # Red
        }

        status_labels = {
            "dang_chay": "Đang chạy",
            "tam_dung": "Tạm dừng",
            "ket_thuc": "Kết thúc",
        }

        for row, km in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(km.id))
            item_id.setData(Qt.ItemDataRole.UserRole, km.id)
            self._table.setItem(row, 0, item_id)

            # Mã KM (use id as ma_km since there's no separate ma_km field)
            self._table.setItem(row, 1, QTableWidgetItem(f"KM{km.id:04d}"))

            # Tên khuyến mãi
            self._table.setItem(row, 2, QTableWidgetItem(km.ten_km))

            # Loại
            loai_text = LOAI_KM_LABELS.get(km.loai_km, km.loai_km)
            self._table.setItem(row, 3, QTableWidgetItem(loai_text))

            # Giá trị
            if km.kieu_gia_tri == "phan_tram":
                gia_tri_text = f"{km.gia_tri}%"
            else:
                gia_tri_text = f"{km.gia_tri:,} đ".replace(",", ".")
            item_gia = QTableWidgetItem(gia_tri_text)
            item_gia.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_gia)

            # Từ ngày
            tu_ngay = km.tu_ngay[:10] if km.tu_ngay else "N/A"
            self._table.setItem(row, 5, QTableWidgetItem(tu_ngay))

            # Đến ngày
            den_ngay = km.den_ngay[:10] if km.den_ngay else "N/A"
            self._table.setItem(row, 6, QTableWidgetItem(den_ngay))

            # Trạng thái (with color badge)
            status_text = status_labels.get(km.trang_thai, km.trang_thai)
            item_status = QTableWidgetItem(status_text)
            color_hex = status_colors.get(km.trang_thai, "#8e8e93")
            item_status.setBackground(QColor(color_hex))
            item_status.setForeground(QColor(255, 255, 255))
            self._table.setItem(row, 7, item_status)

        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(1, 80)    # Mã KM
        self._table.setColumnWidth(3, 120)   # Loại
        self._table.setColumnWidth(4, 100)   # Giá trị
        self._table.setColumnWidth(5, 100)   # Từ ngày
        self._table.setColumnWidth(6, 100)   # Đến ngày
        self._table.setColumnWidth(7, 100)  # Trạng thái

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
        """Handle row double click - open edit dialog."""
        item = self._table.item(row, 0)
        if item:
            km_id = item.data(Qt.ItemDataRole.UserRole)
            if km_id:
                self.edit_promo_clicked.emit(km_id)

    def _on_add_clicked(self):
        """Handle add promotion button click."""
        self.add_promo_clicked.emit()

    def refresh(self):
        """Refresh the data."""
        self._load_data()
