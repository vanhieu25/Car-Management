"""Contract list screen - S-HD-01 - Contract listing with search and filters.

Features:
- Table with columns: Mã HĐ, KH, Xe, Ngày tạo, Tổng tiền, Trạng thái, NV
- Filter bar: trạng thái dropdown, ngày range, KH search, NV dropdown
- Status badges: moi_tao=gray, da_thanh_toan=blue, da_giao_xe=green, huy=red
- Click row → open Contract Detail (S-HD-03)

References:
- BR-HD-01..12: Contract lifecycle management
- BR-CALC-01: Total calculation
"""

from typing import Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont

from app.application.services.hop_dong_service import HopDongService, HopDongSearchResult
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


class ContractListScreen(QWidget):
    """Contract list screen - S-HD-01.
    
    Signals:
        create_contract_clicked: User clicked create contract button.
        view_contract_clicked(hop_dong_id: int): User wants to view contract details.
    """
    
    create_contract_clicked = pyqtSignal()
    view_contract_clicked = pyqtSignal(int)
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize contract list screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._hd_service = HopDongService(db_conn)
        
        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[HopDongSearchResult] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Quản lý hợp đồng")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Create contract button (only for A-01, A-02)
        if self._session and self._session.vai_tro_ma in ("A-01", "A-02"):
            self._create_btn = QPushButton("➕ Tạo hợp đồng mới")
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
        filter_layout.setContentsMargins(8, 16, 8, 8)
        
        # Status filter
        filter_layout.addWidget(QLabel("Trạng thái:"))
        self._status_combo = QComboBox()
        self._status_combo.addItems(["Tất cả", "Mới tạo", "Đã thanh toán", "Đã giao xe", "Đã hủy"])
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
        
        # Date range - from
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
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
        self._date_to.setDate(QDate.currentDate())
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
        
        # Customer search
        filter_layout.addWidget(QLabel("KH:"))
        self._kh_search = QLineEdit()
        self._kh_search.setPlaceholderText("Tên KH...")
        self._kh_search.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
                min-width: 120px;
            }
        """)
        self._kh_search.returnPressed.connect(self._on_filter_changed)
        filter_layout.addWidget(self._kh_search)
        
        # NV filter (dropdown populated from DB)
        filter_layout.addWidget(QLabel("NV:"))
        self._nv_combo = QComboBox()
        self._nv_combo.addItem("Tất cả", None)
        self._load_nv_list()
        self._nv_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._nv_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._nv_combo)
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        legend_layout.addWidget(self._create_badge("Mới tạo", "#8e8e93"))
        legend_layout.addWidget(self._create_badge("Đã thanh toán", "#007aff"))
        legend_layout.addWidget(self._create_badge("Đã giao xe", "#34c759"))
        legend_layout.addWidget(self._create_badge("Đã hủy", "#ff3b30"))
        
        filter_layout.addLayout(legend_layout)
        
        layout.addWidget(filter_group)
        
        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Mã HĐ", "Khách hàng", "Xe", "Ngày tạo", "Tổng tiền", "Trạng thái", "NV phụ trách"
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
        
        self._total_label = QLabel("Tổng: 0 hợp đồng")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)
        
        layout.addLayout(pagination_layout)
    
    def _load_nv_list(self):
        """Load employee list into NV dropdown."""
        try:
            cursor = self._db_conn.execute(
                """SELECT id, ho_ten FROM nhan_vien WHERE trang_thai = 'active' ORDER BY ho_ten"""
            )
            for row in cursor.fetchall():
                self._nv_combo.addItem(row[1], row[0])
        except Exception:
            pass
    
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
        status_map = {
            "Mới tạo": "moi_tao",
            "Đã thanh toán": "da_thanh_toan",
            "Đã giao xe": "da_giao_xe",
            "Đã hủy": "huy",
        }
        
        params = {}
        
        # Status filter
        if self._status_combo.currentText() != "Tất cả":
            params["trang_thai"] = status_map.get(self._status_combo.currentText())
        
        # Date range
        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")
        params["ngay_tao_from"] = date_from
        params["ngay_tao_to"] = date_to
        
        # Customer keyword
        kh_keyword = self._kh_search.text().strip()
        if kh_keyword:
            params["keyword"] = kh_keyword
        
        # NV filter
        nv_id = self._nv_combo.currentData()
        if nv_id is not None:
            params["nhan_vien_id"] = nv_id
        
        return params
    
    def _load_data(self):
        """Load contract data based on filters."""
        params = self._get_filter_params()
        
        try:
            result = self._hd_service.search(
                trang_thai=params.get("trang_thai"),
                ngay_tao_from=params.get("ngay_tao_from"),
                ngay_tao_to=params.get("ngay_tao_to"),
                nhan_vien_id=params.get("nhan_vien_id"),
                keyword=params.get("keyword"),
                page=self._current_page,
                page_size=PAGE_SIZE,
            )
            
            self._current_result = result
            self._total_pages = result.total_pages
            
            self._populate_table(result.items)
            
            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} hợp đồng")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _populate_table(self, items: List):
        """Populate table with contract data.
        
        Args:
            items: List of HopDong entities.
        """
        self._table.setRowCount(len(items))
        
        # Status colors
        status_colors = {
            "moi_tao": "#8e8e93",    # Gray
            "da_thanh_toan": "#007aff",  # Blue
            "da_giao_xe": "#34c759",  # Green
            "huy": "#ff3b30",        # Red
        }
        
        status_labels = {
            "moi_tao": "Mới tạo",
            "da_thanh_toan": "Đã thanh toán",
            "da_giao_xe": "Đã giao xe",
            "huy": "Đã hủy",
        }
        
        for row, hd in enumerate(items):
            # Get related data for display
            cursor = self._db_conn.execute(
                """SELECT kh.ho_ten, xe.hang, xe.dong_xe, nv.ho_ten as nv_ten
                   FROM hop_dong hd
                   LEFT JOIN khach_hang kh ON hd.khach_hang_id = kh.id
                   LEFT JOIN xe ON hd.xe_id = xe.id
                   LEFT JOIN nhan_vien nv ON hd.nhan_vien_id = nv.id
                   WHERE hd.id = ?""",
                (hd.id,)
            )
            rel = cursor.fetchone()
            
            # Mã HĐ
            item_ma = QTableWidgetItem(hd.ma_hop_dong)
            item_ma.setData(Qt.ItemDataRole.UserRole, hd.id)
            self._table.setItem(row, 0, item_ma)
            
            # Khách hàng
            khach_hang = rel[0] if rel else "N/A"
            self._table.setItem(row, 1, QTableWidgetItem(khach_hang or "N/A"))
            
            # Xe
            xe_info = f"{rel[1]} {rel[2]}" if rel and rel[1] else "N/A"
            self._table.setItem(row, 2, QTableWidgetItem(xe_info))
            
            # Ngày tạo
            ngay_tao = hd.ngay_tao[:10] if hd.ngay_tao else "N/A"
            self._table.setItem(row, 3, QTableWidgetItem(ngay_tao))
            
            # Tổng tiền
            tong_tien_text = f"{hd.tong_tien:,.0f} đ".replace(",", ".")
            item_tien = QTableWidgetItem(tong_tien_text)
            item_tien.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_tien)
            
            # Trạng thái (with color)
            status_text = status_labels.get(hd.trang_thai, hd.trang_thai)
            item_status = QTableWidgetItem(status_text)
            color_hex = status_colors.get(hd.trang_thai, "#8e8e93")
            color = QColor(color_hex)
            item_status.setBackground(color)
            item_status.setForeground(QColor(255, 255, 255))
            self._table.setItem(row, 5, item_status)
            
            # NV phụ trách
            nv_ten = rel[3] if rel else "N/A"
            self._table.setItem(row, 6, QTableWidgetItem(nv_ten or "N/A"))
        
        # Set column widths
        self._table.setColumnWidth(0, 120)  # Mã HĐ
        self._table.setColumnWidth(1, 150)  # KH
        self._table.setColumnWidth(2, 150)  # Xe
        self._table.setColumnWidth(3, 100)  # Ngày tạo
        self._table.setColumnWidth(4, 130)  # Tổng tiền
        self._table.setColumnWidth(5, 120)  # Trạng thái
        self._table.setColumnWidth(6, 120)  # NV
    
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
            hop_dong_id = item.data(Qt.ItemDataRole.UserRole)
            if hop_dong_id:
                self.view_contract_clicked.emit(hop_dong_id)
    
    def _on_create_clicked(self):
        """Handle create contract button click."""
        self.create_contract_clicked.emit()
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
