"""Customer care screen - S-HM-04 - Show customers with upcoming birthdays.

Features:
- Show list of customers with birthday within ±7 days from today
- Each row: KH name, phone, birthday, vehicle count
- "Gửi thiệp" button (mock — just log message, don't actually send)
- Calls KhachHangService.find_birthday_window(7) to get data

References:
- BR-HM-07: Customer care (birthday reminder)
"""

import logging
from typing import List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QGroupBox,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.khach_hang_service import KhachHangService
from app.application.services.session import CurrentSession
from app.domain.entities import KhachHang


# Configure logging for the mock "send card" action
logger = logging.getLogger(__name__)


class CustomerCareScreen(QWidget):
    """Customer care screen - S-HM-04.
    
    Shows customers with upcoming birthdays (±7 days).
    
    Signals:
        view_customer_clicked(khach_hang_id: int): User wants to view customer details.
    """
    
    view_customer_clicked = pyqtSignal(int)
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize customer care screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._kh_service = KhachHangService(db_conn)
        
        self._birthday_customers: List[KhachHang] = []
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Chăm sóc khách hàng")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        self._refresh_btn = QPushButton("🔄 Làm mới")
        self._refresh_btn.setStyleSheet("""
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
        self._refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(self._refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Info group
        info_group = QGroupBox()
        info_group.setStyleSheet("""
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
        info_layout = QHBoxLayout(info_group)
        info_layout.setSpacing(24)
        
        # Icon
        info_icon = QLabel("🎂")
        info_icon.setStyleSheet("font-size: 32px;")
        info_layout.addWidget(info_icon)
        
        # Info text
        info_text = QLabel()
        info_text.setStyleSheet("font-size: 15px; color: #1d1d1f;")
        self._info_label = info_text
        info_layout.addWidget(info_text, stretch=1)
        
        layout.addWidget(info_group)
        
        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "STT", "Họ tên", "Số điện thoại", "Ngày sinh", "Số xe đã mua"
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
        
        # Empty state label
        self._empty_label = QLabel("🎉 Không có khách hàng nào có sinh nhật trong tuần này!")
        self._empty_label.setStyleSheet("""
            font-size: 16px;
            color: #86868b;
            padding: 40px;
            qproperty-alignment: 'AlignCenter';
        """)
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)
    
    def _load_data(self):
        """Load customers with upcoming birthdays."""
        try:
            # Get customers with birthday within ±7 days
            self._birthday_customers = self._kh_service.get_upcoming_birthdays(days=7)
            
            # Update info label
            count = len(self._birthday_customers)
            if count > 0:
                self._info_label.setText(
                    f"Có <b>{count}</b> khách hàng có sinh nhật trong tuần này!"
                )
                self._info_label.setStyleSheet("font-size: 15px; color: #1d1d1f;")
            else:
                self._info_label.setText(
                    "Không có khách hàng nào có sinh nhật trong tuần này."
                )
            
            self._populate_table()
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _populate_table(self):
        """Populate table with birthday customers."""
        self._table.setRowCount(0)
        
        if not self._birthday_customers:
            self._table.setVisible(False)
            self._empty_label.setVisible(True)
            return
        
        self._table.setVisible(True)
        self._empty_label.setVisible(False)
        
        self._table.setRowCount(len(self._birthday_customers))
        
        for row_idx, kh in enumerate(self._birthday_customers):
            # STT
            item_stt = QTableWidgetItem(str(row_idx + 1))
            item_stt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row_idx, 0, item_stt)
            
            # Họ tên
            item_ten = QTableWidgetItem(kh.ho_ten)
            item_ten.setData(Qt.ItemDataRole.UserRole, kh.id)
            self._table.setItem(row_idx, 1, item_ten)
            
            # SĐT
            self._table.setItem(row_idx, 2, QTableWidgetItem(kh.so_dien_thoai))
            
            # Ngày sinh
            birthday = kh.ngay_sinh or "N/A"
            item_ns = QTableWidgetItem(birthday)
            item_ns.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row_idx, 3, item_ns)
            
            # Số xe đã mua
            so_xe = kh.so_xe_da_mua or 0
            item_xe = QTableWidgetItem(str(so_xe))
            item_xe.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row_idx, 4, item_xe)
            
            # Highlight birthday rows with light yellow
            for col in range(5):
                self._table.item(row_idx, col).setBackground(QColor(255, 255, 230))
        
        # Set column widths
        self._table.setColumnWidth(0, 50)   # STT
        self._table.setColumnWidth(2, 120)  # SĐT
        self._table.setColumnWidth(3, 120)  # Ngày sinh
        self._table.setColumnWidth(4, 100)  # Số xe
    
    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click."""
        item = self._table.item(row, 1)  # Column 1 = Họ tên (has UserRole)
        if item:
            kh_id = item.data(Qt.ItemDataRole.UserRole)
            if kh_id:
                self.view_customer_clicked.emit(kh_id)
    
    def _on_send_card(self, row: int):
        """Handle 'Gửi thiệp' button click (mock).
        
        Args:
            row: Table row index.
        """
        item = self._table.item(row, 1)  # Họ tên column
        if not item:
            return
        
        kh_id = item.data(Qt.ItemDataRole.UserRole)
        kh_name = item.text()
        
        # Mock send - just log the action
        logger.info(f"[CUSTOMER CARE] Mock send birthday card to: {kh_name} (ID: {kh_id})")
        
        QMessageBox.information(
            self,
            "Gửi thiệp",
            f"Đã gửi thiệp chúc mừng sinh nhật đến: {kh_name}\n"
            f"(Mock action - không có email thực sự được gửi)"
        )
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()