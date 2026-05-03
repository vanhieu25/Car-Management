"""Campaign list screen - S-MK-01 - Marketing campaign listing with stats.

Features:
- Table: ten_chien_dich, kenh_tiep_thi, ngay_bat_dau, ngay_ket_thuc, ngan_sach, trang_thai
- Badge colors: 'nhap'=gray, 'dang_chay'=green, 'ket_thuc'=red
- Filter by trang_thai, date range
- KpiCard row: total campaigns / active / leads
- Buttons: Create campaign, View details

References:
- BR-MK-01: Campaign lifecycle
- BR-CALC-06: Conversion rate
"""

from typing import Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont

from app.application.services.chien_dich_mk_service import (
    ChienDichMkService, ChienDichMkCreateData, ChienDichMkNotFoundError
)
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


TRANG_THAI_LABELS = {
    "nhap": "Nháp",
    "dang_chay": "Đang chạy",
    "ket_thuc": "Kết thúc",
}

TRANG_THAI_COLORS = {
    "nhap": "#9e9e9e",
    "dang_chay": "#4caf50",
    "ket_thuc": "#f44336",
}

KENH_LABELS = {
    "facebook": "Facebook",
    "google_ads": "Google Ads",
    "youtube": "YouTube",
    "truyen_hinh": "Truyền hình",
    "bao_chi": "Báo chí",
    "truyen_mieng": "Truyền miệng",
    "khac": "Khác",
}


class CampaignListScreen(QWidget):
    """Campaign list screen - S-MK-01.

    Signals:
        add_campaign_clicked: User clicked add campaign button.
        edit_campaign_clicked(campaign_id: int): User wants to edit a campaign.
    """

    add_campaign_clicked = pyqtSignal()
    edit_campaign_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize campaign list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = ChienDichMkService(db_conn)

        self._current_page = 0
        self._status_filter = None
        self._date_from = None
        self._date_to = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # Title
        title_label = QLabel("Chiến dịch Marketing")
        title_label.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f;")
        main_layout.addWidget(title_label)

        # Stats row (KpiCards)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self._stats_labels = {}
        stats_items = [
            ("tong_chien_dich", "Tổng chiến dịch"),
            ("dang_chay", "Đang chạy"),
            ("ket_thuc", "Kết thúc"),
            ("nhap", "Nháp"),
        ]

        for key, label_text in stats_items:
            card = self._create_stat_card("0", label_text)
            self._stats_labels[key] = card
            stats_layout.addWidget(card)

        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        # Filter row
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["Tất cả", "Nháp", "Đang chạy", "Kết thúc"])
        self._status_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Trạng thái:"))
        filter_layout.addWidget(self._status_combo)

        self._date_from_edit = QDateEdit()
        self._date_from_edit.setCalendarPopup(True)
        self._date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self._date_from_edit.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Từ ngày:"))
        filter_layout.addWidget(self._date_from_edit)

        self._date_to_edit = QDateEdit()
        self._date_to_edit.setCalendarPopup(True)
        self._date_to_edit.setDate(QDate.currentDate())
        self._date_to_edit.dateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Đến ngày:"))
        filter_layout.addWidget(self._date_to_edit)

        filter_layout.addStretch()

        self._btn_add = QPushButton("+ Tạo chiến dịch")
        self._btn_add.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #0077ed; }
        """)
        self._btn_add.clicked.connect(self._on_add_clicked)
        filter_layout.addWidget(self._btn_add)

        if self._session and self._session.vai_tro_ma in ("A-01",):
            self._btn_delete = QPushButton("🗑️ Xoá")
            self._btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #ff3b30;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-weight: 500;
                }
                QPushButton:hover { background-color: #e0342c; }
            """)
            self._btn_delete.clicked.connect(self._on_delete_clicked)
            filter_layout.addWidget(self._btn_delete)

        main_layout.addLayout(filter_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Tên chiến dịch", "Kênh", "Ngày bắt đầu", "Ngày kết thúc",
            "Ngân sách", "Trạng thái", "Tỷ lệ chuyển đổi"
        ])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: #e8f0fe; }
        """)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)
        main_layout.addWidget(self._table)

        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self._btn_prev = QPushButton("← Trước")
        self._btn_prev.clicked.connect(self._on_prev_page)
        pagination_layout.addWidget(self._btn_prev)

        self._page_label = QLabel("Trang 1")
        pagination_layout.addWidget(self._page_label)

        self._btn_next = QPushButton("Sau →")
        self._btn_next.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(self._btn_next)

        main_layout.addLayout(pagination_layout)

        self.setLayout(main_layout)

    def _create_stat_card(self, value: str, label: str) -> QGroupBox:
        """Create a stat card (KpiCard style)."""
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 8px;
                background-color: #f5f5f7;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(2)
        layout.setContentsMargins(8, 8, 8, 8)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        title_label = QLabel(label)
        title_label.setStyleSheet("font-size: 12px; color: #86868b;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        return card

    def _load_data(self):
        """Load campaigns data."""
        try:
            # Get stats
            stats = self._service.get_stats_summary()
            self._stats_labels["tong_chien_dich"].findChild(QLabel).setText(str(stats.get("tong_chien_dich", 0)))
            self._stats_labels["dang_chay"].findChild(QLabel).setText(str(stats.get("dang_chay", 0)))
            self._stats_labels["ket_thuc"].findChild(QLabel).setText(str(stats.get("ket_thuc", 0)))
            self._stats_labels["nhap"].findChild(QLabel).setText(str(stats.get("nhap", 0)))

            # Get campaigns
            status_map = {"Nháp": "nhap", "Đang chạy": "dang_chay", "Kết thúc": "ket_thuc"}
            status_filter = status_map.get(self._status_combo.currentText())

            if status_filter:
                campaigns = self._service.get_by_status(status_filter)
            else:
                campaigns = self._service.get_all(limit=PAGE_SIZE, offset=self._current_page * PAGE_SIZE)

            self._populate_table(campaigns)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {e}")

    def _populate_table(self, campaigns: List[dict]):
        """Populate table with campaign data."""
        self._table.setRowCount(len(campaigns))

        for row, campaign in enumerate(campaigns):
            # Campaign name
            name_item = QTableWidgetItem(campaign['ten_chien_dich'])
            name_item.setData(Qt.UserRole, campaign['id'])
            self._table.setItem(row, 0, name_item)

            # Channel
            kenh = KENH_LABELS.get(campaign['kenh_tiep_thi'], campaign['kenh_tiep_thi'])
            self._table.setItem(row, 1, QTableWidgetItem(kenh))

            # Dates
            self._table.setItem(row, 2, QTableWidgetItem(campaign['ngay_bat_dau']))
            self._table.setItem(row, 3, QTableWidgetItem(campaign['ngay_ket_thuc']))

            # Budget
            ngan_sach = campaign.get('ngan_sach', 0)
            self._table.setItem(row, 4, QTableWidgetItem(f"{ngan_sach:,.0f} VNĐ"))

            # Status badge
            status = campaign['trang_thai']
            status_text = TRANG_THAI_LABELS.get(status, status)
            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(QColor(TRANG_THAI_COLORS.get(status, "#9e9e9e")))
            status_item.setForeground(QColor("white"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, status_item)

            # Conversion rate
            ty_le = self._service.calculate_conversion_rate(campaign['id'])
            rate_item = QTableWidgetItem(f"{ty_le:.1f}%")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 6, rate_item)

        # Resize columns
        self._table.resizeColumnsToContents()
        self._table.column(0).setWidth(200)

        # Update pagination
        total = len(campaigns)
        self._page_label.setText(f"Trang {self._current_page + 1}")
        self._btn_prev.setEnabled(self._current_page > 0)
        self._btn_next.setEnabled(total == PAGE_SIZE)

    def _on_filter_changed(self):
        """Handle filter change."""
        self._current_page = 0
        self._load_data()

    def _on_add_clicked(self):
        """Handle add campaign button click."""
        self.add_campaign_clicked.emit()
    
    def _get_selected_id(self) -> int:
        """Get selected campaign ID from table.
        
        Returns:
            Campaign ID or -1 if none selected.
        """
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return -1
        row = selected_rows[0].row()
        item = self._table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return -1
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        item_id = self._get_selected_id()
        if item_id < 0:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn chiến dịch cần xoá.")
            return
        
        reply = QMessageBox.question(
            self,
            "Xác nhận xoá",
            "Bạn có chắc muốn xoá chiến dịch này?\n\nHành động này không thể hoàn tác.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self._service.delete(item_id)
            QMessageBox.information(self, "Thành công", "Đã xoá thành công")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xoá: {str(e)}")

    def _on_row_double_clicked(self, row, column):
        """Handle table row double click."""
        item = self._table.item(row, 0)
        if item:
            campaign_id = item.data(Qt.UserRole)
            self.edit_campaign_clicked.emit(campaign_id)

    def _on_prev_page(self):
        """Go to previous page."""
        if self._current_page > 0:
            self._current_page -= 1
            self._load_data()

    def _on_next_page(self):
        """Go to next page."""
        self._current_page += 1
        self._load_data()

    def refresh(self):
        """Refresh data."""
        self._load_data()
