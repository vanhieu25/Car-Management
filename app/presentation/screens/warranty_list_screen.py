"""Warranty list screen - S-BH-01 - Warranty listing with filters and search.

Features:
- SearchBar with keyword search (ma_bh, ten_khach_hang)
- Filter tabs: Tất cả / Còn HL / Sắp hết (≤30 ngày) / Hết hạn
- Table: ma_bh, xe (hang+dong), khach_hang, ngay_bat_dau, ngay_ket_thuc, trang_thai
- Highlight row yellow when expiring within 30 days (BR-BH-03)
- Highlight row red when expired
- Pagination
- Double-click row to open warranty detail

References:
- BR-BH-01..10: Warranty management
- BR-BH-03: Warning 30 days before expiry
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor

from app.application.services.bao_hanh_service import BaoHanhService, YeuCauSearchResult
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


class WarrantyListScreen(QWidget):
    """Warranty list screen - S-BH-01.
    
    Signals:
        view_warranty_clicked(bh_id: int): User wants to view warranty details.
    """
    
    view_warranty_clicked = pyqtSignal(int)
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize warranty list screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bh_service = BaoHanhService(db_conn)
        
        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[YeuCauSearchResult] = None
        self._current_filter = "tat_ca"
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Quản lý bảo hành")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo mã BH, tên khách hàng...")
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
        
        # Filter tabs
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
        
        filter_layout.addWidget(QLabel("Lọc theo trạng thái:"))
        
        # Filter tabs as toggle buttons
        self._filter_buttons = {}
        filter_tabs = [
            ("tat_ca", "Tất cả"),
            ("con_hieu_luc", "Còn hiệu lực"),
            ("sap_het_han", "Sắp hết (≤30 ngày)"),
            ("het_han", "Hết hạn"),
        ]
        
        for filter_key, filter_label in filter_tabs:
            btn = QPushButton(filter_label)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    border: 1px solid #d2d2d7;
                    border-radius: 6px;
                    font-size: 13px;
                    background: white;
                }
                QPushButton:checked {
                    background-color: #0066cc;
                    color: white;
                    border: 1px solid #0066cc;
                }
                QPushButton:hover:not(:checked) {
                    background-color: #e5e5ea;
                }
            """)
            btn.clicked.connect(lambda checked, f=filter_key: self._on_filter_changed(f) if checked else None)
            filter_layout.addWidget(btn)
            self._filter_buttons[filter_key] = btn
        
        # Default: select "Tất cả"
        self._filter_buttons["tat_ca"].setChecked(True)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Mã BH", "Xe", "Khách hàng", "Ngày bắt đầu", "Ngày kết thúc", "Trạng thái"
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
        
        self._total_label = QLabel("Tổng: 0 bảo hành")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)
        
        layout.addLayout(pagination_layout)
    
    def _on_filter_changed(self, filter_key: str):
        """Handle filter tab change."""
        # Uncheck all buttons
        for key, btn in self._filter_buttons.items():
            btn.setChecked(key == filter_key)
        
        self._current_filter = filter_key
        self._current_page = 1
        self._load_data()
    
    def _on_search(self):
        """Handle search button click."""
        self._current_page = 1
        self._load_data()
    
    def _load_data(self):
        """Load warranty data based on filters."""
        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None
        
        try:
            result = self._bh_service.get_all(
                trang_thai=self._current_filter,
                search_keyword=keyword,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )
            
            self._current_result = result
            self._total_pages = result.total_pages
            
            self._populate_table(result.items)
            
            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} bảo hành")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _populate_table(self, items: List[dict]):
        """Populate table with warranty data.
        
        Args:
            items: List of warranty dicts.
        """
        self._table.setRowCount(len(items))
        
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        
        for row, item in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(item.get("id", "")))
            self._table.setItem(row, 0, item_id)
            
            # Ma BH
            ma_bh = f"BH{item.get('id', '')}"
            self._table.setItem(row, 1, QTableWidgetItem(ma_bh))
            
            # Xe (hang + dong)
            xe_info = f"{item.get('xe_hang', '')} {item.get('xe_dong', '')}"
            self._table.setItem(row, 2, QTableWidgetItem(xe_info))
            
            # Khach hang
            self._table.setItem(row, 3, QTableWidgetItem(item.get("kh_ho_ten", "")))
            
            # Ngay bat dau
            self._table.setItem(row, 4, QTableWidgetItem(item.get("ngay_bat_dau", "")[:10] if item.get("ngay_bat_dau") else ""))
            
            # Ngay ket thuc
            ngay_ket_thuc = item.get("ngay_ket_thuc", "")[:10] if item.get("ngay_ket_thuc") else ""
            self._table.setItem(row, 5, QTableWidgetItem(ngay_ket_thuc))
            
            # Trang thai
            trang_thai = item.get("trang_thai", "")
            status_item = QTableWidgetItem()
            
            # Determine status and color
            if trang_thai == "het_han":
                status_text = "Hết hạn"
                bg_color = QColor("#ff3b30")  # Red
                fg_color = QColor(255, 255, 255)
            else:
                # Check if expiring within 30 days
                try:
                    ket_thuc_date = datetime.strptime(ngay_ket_thuc, "%Y-%m-%d").date()
                    days_left = (ket_thuc_date - today).days
                    if days_left <= 0:
                        status_text = "Hết hạn"
                        bg_color = QColor("#ff3b30")
                        fg_color = QColor(255, 255, 255)
                    elif days_left <= 30:
                        status_text = f"Sắp hết ({days_left} ngày)"
                        bg_color = QColor("#ffcc00")  # Yellow
                        fg_color = QColor(0, 0, 0)
                    else:
                        status_text = "Còn hiệu lực"
                        bg_color = QColor("#34c759")  # Green
                        fg_color = QColor(255, 255, 255)
                except:
                    status_text = "Còn hiệu lực"
                    bg_color = QColor("#34c759")
                    fg_color = QColor(255, 255, 255)
            
            status_item.setText(status_text)
            status_item.setBackground(bg_color)
            status_item.setForeground(fg_color)
            self._table.setItem(row, 6, status_item)
            
            # Store ID for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item.get("id"))
        
        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(1, 100)  # Ma BH
        self._table.setColumnWidth(2, 200)  # Xe
        self._table.setColumnWidth(3, 180)  # KH
        self._table.setColumnWidth(4, 120)  # Ngay BD
        self._table.setColumnWidth(5, 120)  # Ngay KT
        self._table.setColumnWidth(6, 140)  # Trang thai
    
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
                self.view_warranty_clicked.emit(bh_id)
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
