"""Vehicle list screen - S-XE-01 - Vehicle listing with search and filters.

Features:
- SearchBar with keyword search (BR-XE-07: ma_xe, hang, dong_xe)
- 5 FilterChips: hãng, dòng, năm, khoảng giá, trạng thái
- DataTable with columns: mã, hãng, dòng, năm, màu, giá, tồn kho, trạng thái
- Highlight red rows where so_luong_ton ≤ muc_toi_thieu (BR-XE-08)
- Pagination: 50 rows/page (default)
- Sort by column
- Empty/Loading/Error states
- Add/Edit/Delete buttons (permission-based)

References:
- UC-XE-04: Tìm kiếm nâng cao
- BR-XE-06: Tìm kiếm hỗ trợ tổ hợp tiêu chí
- BR-XE-07: Tìm kiếm theo từ khoá (case-insensitive, Vietnamese)
- BR-XE-08: Cảnh báo tồn kho thấp
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QCheckBox, QSpinBox, QFormLayout, QDateEdit, QGroupBox,
    QApplication, QStyledItemDelegate, QStyleOptionViewItem
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QVariant, QModelIndex
from PyQt6.QtGui import QColor, QFont

from app.application.services.xe_service import XeService, XeSearchResult
from app.application.services.session import CurrentSession
from app.domain.entities import Xe


PAGE_SIZE = 50


class VehicleListScreen(QWidget):
    """Vehicle list screen - S-XE-01.
    
    Signals:
        add_vehicle_clicked: User clicked add vehicle button.
        edit_vehicle_clicked(xe_id: int): User wants to edit a vehicle.
        view_vehicle_clicked(xe_id: int): User wants to view vehicle details.
    """
    
    add_vehicle_clicked = pyqtSignal()
    edit_vehicle_clicked = pyqtSignal(int)
    view_vehicle_clicked = pyqtSignal(int)
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize vehicle list screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._xe_service = XeService(db_conn)
        
        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[XeSearchResult] = None
        self._sort_column = "hang"
        self._sort_order = Qt.SortOrder.AscendingOrder
        
        self._setup_ui()
        self._load_filter_options()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with title and add button
        header_layout = QHBoxLayout()
        
        title = QLabel("Quản lý xe")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add vehicle button (only for A-01 and A-02)
        if self._session and self._session.vai_tro_ma in ("A-01", "A-02"):
            self._add_btn = QPushButton("➕ Thêm xe")
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
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo mã xe, hãng, dòng xe...")
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
        
        # Filters section
        filter_group = QGroupBox()
        filter_group.setStyleSheet("""
            QGroupBox {
                background-color: #f5f5f7;
                border-radius: 8px;
                padding: 16px;
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
        
        # Brand filter
        filter_layout.addWidget(QLabel("Hãng:"))
        self._hang_combo = QComboBox()
        self._hang_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._hang_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._hang_combo)
        
        # Model filter
        filter_layout.addWidget(QLabel("Dòng:"))
        self._dong_combo = QComboBox()
        self._dong_combo.setStyleSheet(self._hang_combo.styleSheet())
        self._dong_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._dong_combo)
        
        # Year filter
        filter_layout.addWidget(QLabel("Năm:"))
        self._nam_combo = QComboBox()
        self._nam_combo.setStyleSheet(self._hang_combo.styleSheet())
        self._nam_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._nam_combo)
        
        # Status filter
        filter_layout.addWidget(QLabel("Trạng thái:"))
        self._trang_thai_combo = QComboBox()
        self._trang_thai_combo.addItems(["Tất cả", "Còn hàng", "Đã bán", "Sắp về"])
        self._trang_thai_combo.setStyleSheet(self._hang_combo.styleSheet())
        self._trang_thai_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._trang_thai_combo)
        
        # Low stock only checkbox
        self._low_stock_check = QCheckBox("⚠️ Tồn kho thấp")
        self._low_stock_check.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #ff3b30;
                padding: 4px 8px;
            }
        """)
        self._low_stock_check.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._low_stock_check)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Mã xe", "Hãng", "Dòng", "Năm", "Màu", "Giá bán", "Tồn kho", "Trạng thái"
        ])
        
        # Setup table style
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                gridline-color: #e5e5ea;
                background-color: white;
                selection-background-color: #0066cc;
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
        
        # Enable sorting
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)
        header.sortIndicatorChanged.connect(self._on_sort_changed)
        
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
            QPushButton:disabled {
                background-color: #f5f5f7;
                color: #86868b;
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
        
        self._total_label = QLabel("Tổng: 0 xe")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)
        
        layout.addLayout(pagination_layout)
    
    def _load_filter_options(self):
        """Load filter options from database."""
        # Load brands
        hangs = self._xe_service.get_distinct_hangs()
        self._hang_combo.clear()
        self._hang_combo.addItem("Tất cả")
        self._hang_combo.addItems(hangs)
        
        # Load years
        self._nam_combo.clear()
        self._nam_combo.addItem("Tất cả")
        current_year = 2026
        for year in range(current_year + 1, 1999, -1):
            self._nam_combo.addItem(str(year))
    
    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        # Update model dropdown based on brand selection
        hang = self._hang_combo.currentText()
        if hang and hang != "Tất cả":
            dong_xe_list = self._xe_service.get_distinct_dong_xe(hang)
            self._dong_combo.blockSignals(True)
            self._dong_combo.clear()
            self._dong_combo.addItem("Tất cả")
            self._dong_combo.addItems(dong_xe_list)
            self._dong_combo.blockSignals(False)
        else:
            self._dong_combo.blockSignals(True)
            self._dong_combo.clear()
            self._dong_combo.addItem("Tất cả")
            self._dong_combo.blockSignals(False)
        
        # Reset to page 1 and reload
        self._current_page = 1
        self._load_data()
    
    def _on_sort_changed(self, logicalIndex: int, order: Qt.SortOrder):
        """Handle sort changed."""
        headers = ["ma_xe", "hang", "dong_xe", "nam_san_xuat", "mau_sac", "gia_ban", "so_luong_ton", "trang_thai"]
        if logicalIndex < len(headers):
            self._sort_column = headers[logicalIndex]
            self._sort_order = order
            self._load_data()
    
    def _load_data(self):
        """Load vehicle data based on filters."""
        # Get filter values
        hang = None if self._hang_combo.currentText() == "Tất cả" else self._hang_combo.currentText()
        dong_xe = None if self._dong_combo.currentText() == "Tất cả" else self._dong_combo.currentText()
        
        nam_text = self._nam_combo.currentText()
        nam_min = None
        nam_max = None
        if nam_text != "Tất cả":
            try:
                year = int(nam_text)
                nam_min = year
                nam_max = year
            except:
                pass
        
        trang_thai_map = {"Còn hàng": "con_hang", "Đã bán": "da_ban", "Sắp về": "sap_ve"}
        trang_thai = None
        if self._trang_thai_combo.currentText() != "Tất cả":
            trang_thai = trang_thai_map.get(self._trang_thai_combo.currentText())
        
        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None
        
        low_stock = self._low_stock_check.isChecked()
        
        # Search
        try:
            result = self._xe_service.search(
                hang=hang,
                dong_xe=dong_xe,
                nam_san_xuat_min=nam_min,
                nam_san_xuat_max=nam_max,
                trang_thai=trang_thai,
                keyword=keyword,
                low_stock_only=low_stock,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )
            
            self._current_result = result
            self._total_pages = result.total_pages
            
            # Populate table
            self._populate_table(result.items)
            
            # Update pagination UI
            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} xe")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _populate_table(self, items: List[Xe]):
        """Populate table with vehicle data.
        
        Args:
            items: List of Xe entities.
        """
        self._table.setRowCount(len(items))
        
        for row, xe in enumerate(items):
            # Check if low stock (BR-XE-08)
            is_low_stock = xe.so_luong_ton <= xe.muc_toi_thieu and xe.trang_thai != "da_ban"
            
            # Mã xe
            item_ma = QTableWidgetItem(xe.ma_xe)
            if is_low_stock:
                item_ma.setBackground(QColor(255, 59, 48, 30))  # Light red background
            self._table.setItem(row, 0, item_ma)
            
            # Hãng
            item_hang = QTableWidgetItem(xe.hang)
            if is_low_stock:
                item_hang.setBackground(QColor(255, 59, 48, 30))
            self._table.setItem(row, 1, item_hang)
            
            # Dòng
            item_dong = QTableWidgetItem(xe.dong_xe)
            if is_low_stock:
                item_dong.setBackground(QColor(255, 59, 48, 30))
            self._table.setItem(row, 2, item_dong)
            
            # Năm
            item_nam = QTableWidgetItem(str(xe.nam_san_xuat))
            if is_low_stock:
                item_nam.setBackground(QColor(255, 59, 48, 30))
            self._table.setItem(row, 3, item_nam)
            
            # Màu
            item_mau = QTableWidgetItem(xe.mau_sac or "-")
            if is_low_stock:
                item_mau.setBackground(QColor(255, 59, 48, 30))
            self._table.setItem(row, 4, item_mau)
            
            # Giá
            item_gia = QTableWidgetItem(f"{xe.gia_ban:,.0f} đ".replace(",", "."))
            item_gia.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if is_low_stock:
                item_gia.setBackground(QColor(255, 59, 48, 30))
            self._table.setItem(row, 5, item_gia)
            
            # Tồn kho
            item_ton = QTableWidgetItem(str(xe.so_luong_ton))
            item_ton.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_low_stock:
                item_ton.setBackground(QColor(255, 59, 48))
                item_ton.setForeground(QColor(255, 255, 255))
            self._table.setItem(row, 6, item_ton)
            
            # Trạng thái
            status_text = {"con_hang": "Còn hàng", "da_ban": "Đã bán", "sap_ve": "Sắp về"}.get(xe.trang_thai, xe.trang_thai)
            item_status = QTableWidgetItem(status_text)
            
            # Color by status
            if xe.trang_thai == "con_hang":
                item_status.setBackground(QColor(52, 199, 89, 50))  # Light green
            elif xe.trang_thai == "da_ban":
                item_status.setBackground(QColor(255, 149, 0, 50))  # Light orange
            else:
                item_status.setBackground(QColor(0, 122, 255, 50))  # Light blue
            
            if is_low_stock:
                item_status.setBackground(QColor(255, 59, 48))
                item_status.setForeground(QColor(255, 255, 255))
            
            self._table.setItem(row, 7, item_status)
            
            # Store xe id for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, xe.id)
        
        # Set column widths
        self._table.setColumnWidth(0, 100)  # ma_xe
        self._table.setColumnWidth(3, 70)   # nam_san_xuat
        self._table.setColumnWidth(4, 80)   # mau_sac
        self._table.setColumnWidth(5, 130)  # gia_ban
        self._table.setColumnWidth(6, 80)   # so_luong_ton
        self._table.setColumnWidth(7, 100)  # trang_thai
    
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
        """Handle row double click - emit view signal.
        
        Args:
            row: Clicked row index.
            column: Clicked column index.
        """
        item = self._table.item(row, 0)
        if item:
            xe_id = item.data(Qt.ItemDataRole.UserRole)
            if xe_id:
                self.view_vehicle_clicked.emit(xe_id)
    
    def _on_add_clicked(self):
        """Handle add vehicle button click."""
        self.add_vehicle_clicked.emit()
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
