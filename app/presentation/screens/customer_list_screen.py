"""Customer list screen - S-KH-01 - Customer listing with search and filters.

Features:
- SearchBar with keyword search (name, phone, email)
- Filter by classification (Thuong/Than_thiet/VIP)
- Badge colors: Thường=gray, Thân thiết=blue, VIP=yellow
- Pagination: 50 rows/page (default)
- Sort by column
- Empty/Loading/Error states
- Add/Edit/Delete buttons (permission-based)

References:
- BR-KH-01..07: Customer management rules
- BR-CALC-03: Customer classification
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.application.services.khach_hang_service import KhachHangService, KhachHangSearchResult
from app.application.services.session import CurrentSession
from app.domain.entities import KhachHang


PAGE_SIZE = 50


class CustomerListScreen(QWidget):
    """Customer list screen - S-KH-01.
    
    Signals:
        add_customer_clicked: User clicked add customer button.
        edit_customer_clicked(khach_hang_id: int): User wants to edit a customer.
        view_customer_clicked(khach_hang_id: int): User wants to view customer details.
    """
    
    add_customer_clicked = pyqtSignal()
    edit_customer_clicked = pyqtSignal(int)
    view_customer_clicked = pyqtSignal(int)
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize customer list screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._kh_service = KhachHangService(db_conn)
        
        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[KhachHangSearchResult] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Quản lý khách hàng")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add customer button (only for A-01, A-02)
        if self._session and self._session.vai_tro_ma in ("A-01", "A-02"):
            self._add_btn = QPushButton("➕ Thêm khách hàng")
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
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo tên, SĐT, email...")
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
        
        # Classification filter
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
        self._phan_loai_combo.addItems(["Tất cả", "Thường", "Thân thiết", "VIP"])
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
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        
        legend_layout.addWidget(self._create_badge("Thường", "#8e8e93"))
        legend_layout.addWidget(self._create_badge("Thân thiết", "#007aff"))
        legend_layout.addWidget(self._create_badge("VIP", "#ffcc00"))
        
        filter_layout.addLayout(legend_layout)
        
        layout.addWidget(filter_group)
        
        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Họ tên", "Số điện thoại", "Email", "Phân loại", "Tổng giá trị mua"
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
        
        self._total_label = QLabel("Tổng: 0 khách hàng")
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
    
    def _load_data(self):
        """Load customer data based on filters."""
        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None
        
        phan_loai_map = {"Thường": "Thuong", "Thân thiết": "Than_thiet", "VIP": "VIP"}
        phan_loai = None
        if self._phan_loai_combo.currentText() != "Tất cả":
            phan_loai = phan_loai_map.get(self._phan_loai_combo.currentText())
        
        try:
            result = self._kh_service.search(
                keyword=keyword,
                phan_loai=phan_loai,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )
            
            self._current_result = result
            self._total_pages = result.total_pages
            
            self._populate_table(result.items)
            
            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} khách hàng")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _populate_table(self, items: List[KhachHang]):
        """Populate table with customer data.
        
        Args:
            items: List of KhachHang entities.
        """
        self._table.setRowCount(len(items))
        
        # Classification colors (BR-CALC-03)
        phan_loai_colors = {
            "Thuong": "#8e8e93",   # Gray
            "Than_thiet": "#007aff",  # Blue
            "VIP": "#ffcc00",     # Yellow/Gold
        }
        
        phan_loai_labels = {
            "Thuong": "Thường",
            "Than_thiet": "Thân thiết",
            "VIP": "VIP",
        }
        
        for row, kh in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(kh.id))
            self._table.setItem(row, 0, item_id)
            
            # Họ tên
            self._table.setItem(row, 1, QTableWidgetItem(kh.ho_ten))
            
            # SĐT
            self._table.setItem(row, 2, QTableWidgetItem(kh.so_dien_thoai))
            
            # Email
            self._table.setItem(row, 3, QTableWidgetItem(kh.email or "-"))
            
            # Phân loại (with color)
            phan_loai_text = phan_loai_labels.get(kh.phan_loai, kh.phan_loai)
            item_phan_loai = QTableWidgetItem(phan_loai_text)
            color = phan_loai_colors.get(kh.phan_loai, "#8e8e93")
            item_phan_loai.setBackground(QColor(color))
            item_phan_loai.setForeground(QColor(255, 255, 255))
            self._table.setItem(row, 4, item_phan_loai)
            
            # Tổng giá trị mua
            gia_tri_text = f"{kh.tong_gia_tri_mua:,.0f} đ".replace(",", ".")
            item_gia_tri = QTableWidgetItem(gia_tri_text)
            item_gia_tri.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 5, item_gia_tri)
            
            # Store ID for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, kh.id)
        
        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(2, 120)  # SĐT
        self._table.setColumnWidth(3, 180)  # Email
        self._table.setColumnWidth(4, 100)  # Phân loại
    
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
            khach_hang_id = item.data(Qt.ItemDataRole.UserRole)
            if khach_hang_id:
                self.view_customer_clicked.emit(khach_hang_id)
    
    def _on_add_clicked(self):
        """Handle add customer button click."""
        self.add_customer_clicked.emit()
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
