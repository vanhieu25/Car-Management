"""Inventory overview screen - S-KHO-01 - Kho inventory overview.

Features:
- KPI cards: Total cars in stock, Total car value, Total accessories in stock, Total accessory value
- Table grouped by hang+dong_xe showing stock quantity and value
- Red highlight when so_luong_ton <= muc_toi_thieu
- Footer row with totals
- Refresh button

References:
- UC-KHO-01: Xem tổng quan tồn kho
"""

from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QGroupBox, QHeaderView,
    QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush

from app.application.services.kho_service import KhoService
from app.application.services.session import CurrentSession


class InventoryOverviewScreen(QWidget):
    """Inventory overview screen - S-KHO-01.
    
    Signals:
        stock_in_clicked: User clicked stock-in button.
    """
    
    stock_in_clicked = pyqtSignal()
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize inventory overview screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._kho_service = KhoService(db_conn)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Tổng quan tồn kho")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        self._refresh_btn = QPushButton("🔄 Tải lại")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self._refresh_btn)
        
        # Stock-in button (permission-based)
        if self._session and self._session.vai_tro_ma in ("A-01", "A-02", "A-03"):
            self._stock_in_btn = QPushButton("📥 Nhập kho")
            self._stock_in_btn.setStyleSheet("""
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
            self._stock_in_btn.clicked.connect(self._on_stock_in_clicked)
            header_layout.addWidget(self._stock_in_btn)
        
        layout.addLayout(header_layout)
        
        # KPI Cards
        kpi_group = QGroupBox()
        kpi_group.setStyleSheet("""
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
        kpi_layout = QHBoxLayout(kpi_group)
        kpi_layout.setSpacing(24)
        
        # Tong so xe ton
        self._kpi_tong_xe = self._create_kpi_card(
            "Tổng số xe tồn",
            "0",
            "#007aff"
        )
        kpi_layout.addWidget(self._kpi_tong_xe)
        
        # Tong gia tri xe
        self._kpi_gia_tri_xe = self._create_kpi_card(
            "Tổng giá trị tồn (xe)",
            "0 đ",
            "#34c759"
        )
        kpi_layout.addWidget(self._kpi_gia_tri_xe)
        
        # Tong so phu kien ton
        self._kpi_tong_pk = self._create_kpi_card(
            "Tổng số phụ kiện tồn",
            "0",
            "#ff9500"
        )
        kpi_layout.addWidget(self._kpi_tong_pk)
        
        # Tong gia tri phu kien
        self._kpi_gia_tri_pk = self._create_kpi_card(
            "Tổng giá trị tồn (PK)",
            "0 đ",
            "#af52de"
        )
        kpi_layout.addWidget(self._kpi_gia_tri_pk)
        
        layout.addWidget(kpi_group)
        
        # Data table - grouped by hang+dong_xe
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels([
            "Nhóm xe (Hãng + Dòng xe)",
            "Số lượng tồn",
            "Giá trị tồn"
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
        
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._table)
    
    def _create_kpi_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a KPI card widget.
        
        Args:
            title: KPI title.
            value: KPI value.
            color: Hex color for value text.
            
        Returns:
            QGroupBox with KPI card styling.
        """
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
                min-width: 150px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                font-size: 12px;
                font-weight: 500;
                color: #86868b;
            }
        """)
        card.setTitle(title)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 20, 8, 8)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {color};
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        return card
    
    def _update_kpi_value(self, card: QGroupBox, value: str):
        """Update the value label of a KPI card.
        
        Args:
            card: KPI card group box.
            value: New value string.
        """
        card_layout = card.layout()
        if card_layout and card_layout.count() > 0:
            value_widget = card_layout.itemAt(0).widget()
            if value_widget and isinstance(value_widget, QLabel):
                value_widget.setText(value)
    
    def _load_data(self):
        """Load inventory data from database."""
        try:
            inventory_list = self._kho_service.get_inventory_overview()
            
            # Separate xe and phu_kien data
            xe_items = [r for r in inventory_list if r.get("loai") == "xe"]
            pk_items = [r for r in inventory_list if r.get("loai") == "phu_kien"]
            
            # Calculate totals for xe
            tong_so_xe = sum(r.get("so_luong_ton", 0) for r in xe_items)
            tong_gia_tri_xe = sum(r.get("gia_tri", 0) for r in xe_items)
            
            # Calculate totals for phu_kien
            tong_so_pk = sum(r.get("so_luong_ton", 0) for r in pk_items)
            tong_gia_tri_pk = sum(r.get("gia_tri", 0) for r in pk_items)
            
            # Update KPI cards
            self._update_kpi_value(self._kpi_tong_xe, str(tong_so_xe))
            self._update_kpi_value(self._kpi_gia_tri_xe, f"{tong_gia_tri_xe:,.0f} đ".replace(",", "."))
            self._update_kpi_value(self._kpi_tong_pk, str(tong_so_pk))
            self._update_kpi_value(self._kpi_gia_tri_pk, f"{tong_gia_tri_pk:,.0f} đ".replace(",", "."))
            
            # Populate table with xe data grouped by nhom
            self._populate_table(xe_items)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu tồn kho: {str(e)}")
    
    def _populate_table(self, nhom_xe_list: List[Dict[str, Any]]):
        """Populate table with inventory data.
        
        Args:
            nhom_xe_list: List of inventory groups from KhoService.
        """
        # Filter out rows with zero data for cleaner display
        rows = [r for r in nhom_xe_list if r.get("so_luong_ton", 0) > 0 or r.get("gia_tri", 0) > 0]
        
        self._table.setRowCount(len(rows) + 1)  # +1 for footer
        
        total_quantity = 0
        total_value = 0
        
        for row, nhom in enumerate(rows):
            nhom_xe = nhom.get("nhom", "-")
            so_luong_ton = nhom.get("so_luong_ton", 0)
            gia_tri = nhom.get("gia_tri", 0)
            # muc_toi_thieu is not in the current KhoService response,
            # so we use a default of 0 (no red highlight unless configured)
            muc_toi_thieu = 0
            
            total_quantity += so_luong_ton
            total_value += gia_tri
            
            # Nhom xe column
            self._table.setItem(row, 0, QTableWidgetItem(nhom_xe))
            
            # So luong ton column
            item_quantity = QTableWidgetItem(str(so_luong_ton))
            item_quantity.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 1, item_quantity)
            
            # Gia tri ton column
            item_value = QTableWidgetItem(f"{gia_tri:,.0f} đ".replace(",", "."))
            item_value.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, item_value)
            
            # Highlight red if below minimum threshold
            if so_luong_ton <= muc_toi_thieu:
                red_brush = QBrush(QColor("#ffebee"))
                for col in range(3):
                    if self._table.item(row, col):
                        self._table.item(row, col).setBackground(red_brush)
        
        # Footer row - "Tổng cộng"
        footer_row = len(rows)
        footer_font = self._table.font()
        footer_font.setBold(True)
        
        item_nhom = QTableWidgetItem("Tổng cộng")
        item_nhom.setFont(footer_font)
        item_nhom.setBackground(QColor("#e5e5ea"))
        self._table.setItem(footer_row, 0, item_nhom)
        
        item_quantity = QTableWidgetItem(str(total_quantity))
        item_quantity.setFont(footer_font)
        item_quantity.setBackground(QColor("#e5e5ea"))
        item_quantity.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(footer_row, 1, item_quantity)
        
        item_value = QTableWidgetItem(f"{total_value:,.0f} đ".replace(",", "."))
        item_value.setFont(footer_font)
        item_value.setBackground(QColor("#e5e5ea"))
        item_value.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._table.setItem(footer_row, 2, item_value)
    
    def _on_stock_in_clicked(self):
        """Handle stock-in button click."""
        self.stock_in_clicked.emit()
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
