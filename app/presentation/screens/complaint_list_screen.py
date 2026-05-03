"""Complaint list screen - S-KN-01 - Complaint listing with priority sorting.

Features:
- Table: tieu_de, khach_hang, muc_do, trang_thai, ngay_tao, nv_xu_ly
- Badge colors: 'thap'=green, 'trung_binh'=orange, 'cao'=red (BR-KN-03)
- Status badges: 'moi'=blue, 'dang_xu_ly'=orange, 'da_giai_quyet'=green, 'da_dong'=gray
- KN cấp 'cao' displayed first (BR-KN-03)
- Filter by muc_do, trang_thai
- Search by tieu_de/khach_hang

References:
- BR-KN-03: Priority 'cao' should be displayed first
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor

from app.application.services.khieu_nai_service import (
    KhieuNaiService, KhieuNaiCreateData, KhieuNaiUpdateData,
    KhieuNaiNotFoundError, ValidationError
)
from app.application.services.session import CurrentSession


PAGE_SIZE = 50

MUC_DO_LABELS = {
    "thap": "Thấp",
    "trung_binh": "Trung bình",
    "cao": "Cao",
}
MUC_DO_COLORS = {
    "thap": "#4caf50",
    "trung_binh": "#ff9800",
    "cao": "#f44336",
}

TRANG_THAI_LABELS = {
    "moi": "Mới",
    "dang_xu_ly": "Đang xử lý",
    "da_giai_quyet": "Đã giải quyết",
    "da_dong": "Đã đóng",
}
TRANG_THAI_COLORS = {
    "moi": "#2196f3",
    "dang_xu_ly": "#ff9800",
    "da_giai_quyet": "#4caf50",
    "da_dong": "#9e9e9e",
}

MUC_DO_OPTIONS = ["Tất cả", "Cao", "Trung bình", "Thấp"]
MUC_DO_VALUE_MAP = {
    "Cao": "cao",
    "Trung bình": "trung_binh",
    "Thấp": "thap",
}
TRANG_THAI_OPTIONS = ["Tất cả", "Mới", "Đang xử lý", "Đã giải quyết", "Đã đóng"]
TRANG_THAI_VALUE_MAP = {
    "Mới": "moi",
    "Đang xử lý": "dang_xu_ly",
    "Đã giải quyết": "da_giai_quyet",
    "Đã đóng": "da_dong",
}


class ComplaintListScreen(QWidget):
    """Complaint list screen - S-KN-01.

    Signals:
        add_complaint_clicked: User clicked add complaint button.
        view_complaint_clicked(kn_id: int): User wants to view complaint.
    """

    add_complaint_clicked = pyqtSignal()
    view_complaint_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize complaint list screen."""
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = KhieuNaiService(db_conn)

        self._current_page = 0
        self._muc_do_filter = None
        self._status_filter = None
        self._search_keyword = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # Title
        title_label = QLabel("Khiếu nại")
        title_label.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f;")
        main_layout.addWidget(title_label)

        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self._stats_labels = {}
        stats_items = [
            ("tong_khieu_nai", "Tổng KN"),
            ("chua_xu_ly", "Chưa xử lý"),
            ("cao", "Cao"),
            ("trung_binh", "Trung bình"),
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

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Tìm kiếm (tiêu đề, khách hàng)...")
        self._search_edit.textChanged.connect(self._on_search_changed)
        self._search_edit.setStyleSheet("padding: 6px 12px; border-radius: 6px;")
        filter_layout.addWidget(self._search_edit)

        self._muc_do_combo = QComboBox()
        self._muc_do_combo.addItems(MUC_DO_OPTIONS)
        self._muc_do_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Mức độ:"))
        filter_layout.addWidget(self._muc_do_combo)

        self._status_combo = QComboBox()
        self._status_combo.addItems(TRANG_THAI_OPTIONS)
        self._status_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Trạng thái:"))
        filter_layout.addWidget(self._status_combo)

        filter_layout.addStretch()

        self._btn_add = QPushButton("+ Tạo khiếu nại")
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

        if self._session and self._session.vai_tro_ma in ("admin",):
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
            "Tiêu đề", "Khách hàng", "Mức độ", "Trạng thái", "Ngày tạo", "NV xử lý", "HĐ"
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
        """Create a stat card."""
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
        """Load complaints data."""
        try:
            # Get stats
            stats = self._service.get_stats_summary()
            self._stats_labels["tong_khieu_nai"].findChild(QLabel).setText(str(stats.get("tong_khieu_nai", 0)))
            self._stats_labels["chua_xu_ly"].findChild(QLabel).setText(str(stats.get("chua_xu_ly", 0)))
            self._stats_labels["cao"].findChild(QLabel).setText(str(stats.get("cao", 0)))
            self._stats_labels["trung_binh"].findChild(QLabel).setText(str(stats.get("trung_binh", 0)))

            # Get complaints
            if self._muc_do_filter:
                kns = self._service.get_by_muc_do(self._muc_do_filter)
            elif self._status_filter:
                kns = self._service.get_by_status(self._status_filter)
            else:
                kns = self._service.get_all(limit=PAGE_SIZE, offset=self._current_page * PAGE_SIZE)

            self._populate_table(kns)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {e}")

    def _populate_table(self, kns: List[dict]):
        """Populate table with complaint data."""
        self._table.setRowCount(len(kns))

        for row, kn in enumerate(kns):
            # Title
            title_item = QTableWidgetItem(kn.get('tieu_de', ''))
            title_item.setData(Qt.ItemDataRole.UserRole, kn['id'])
            self._table.setItem(row, 0, title_item)

            # Customer
            self._table.setItem(row, 1, QTableWidgetItem(kn.get('khach_hang_ten', '-') or '-'))

            # Priority badge (BR-KN-03: cao = red, displayed first)
            muc_do = kn.get('muc_do', 'trung_binh')
            muc_do_text = MUC_DO_LABELS.get(muc_do, muc_do)
            muc_item = QTableWidgetItem(muc_do_text)
            muc_item.setBackground(QColor(MUC_DO_COLORS.get(muc_do, "#9e9e9e")))
            muc_item.setForeground(QColor("white"))
            muc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 2, muc_item)

            # Status badge
            status = kn.get('trang_thai', 'moi')
            status_text = TRANG_THAI_LABELS.get(status, status)
            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(QColor(TRANG_THAI_COLORS.get(status, "#9e9e9e")))
            status_item.setForeground(QColor("white"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, status_item)

            # Date created
            ngay_tao = kn.get('ngay_tao', '')[:10] if kn.get('ngay_tao') else '-'
            self._table.setItem(row, 4, QTableWidgetItem(ngay_tao))

            # Assigned NV
            nv_ten = kn.get('nhan_vien_xu_ly_ten', '') or '-'
            self._table.setItem(row, 5, QTableWidgetItem(nv_ten))

            # Contract
            ma_hd = kn.get('ma_hop_dong', '') or '-'
            self._table.setItem(row, 6, QTableWidgetItem(ma_hd))

        # Resize columns
        self._table.resizeColumnsToContents()
        # RESIZED via horizontalHeader instead: self._table.setColumnWidth(0, 200)

        # Update pagination
        self._page_label.setText(f"Trang {self._current_page + 1}")
        self._btn_prev.setEnabled(self._current_page > 0)
        self._btn_next.setEnabled(len(kns) == PAGE_SIZE)

    def _on_filter_changed(self):
        """Handle filter change."""
        self._current_page = 0
        muc_do_text = self._muc_do_combo.currentText()
        self._muc_do_filter = MUC_DO_VALUE_MAP.get(muc_do_text)
        status_text = self._status_combo.currentText()
        self._status_filter = TRANG_THAI_VALUE_MAP.get(status_text)
        self._load_data()

    def _on_search_changed(self, text):
        """Handle search text change."""
        self._search_keyword = text if text.strip() else None
        self._current_page = 0
        self._load_data()

    def _on_add_clicked(self):
        """Handle add complaint button click."""
        self.add_complaint_clicked.emit()
    
    def _get_selected_id(self) -> int:
        """Get selected complaint ID from table.
        
        Returns:
            Complaint ID or -1 if none selected.
        """
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return -1
        row = selected_rows[0].row()
        item = self._table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return -1
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        item_id = self._get_selected_id()
        if item_id < 0:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn khiếu nại cần xoá.")
            return
        
        reply = QMessageBox.question(
            self,
            "Xác nhận xoá",
            "Bạn có chắc muốn xoá khiếu nại này?\n\nHành động này không thể hoàn tác.",
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
            kn_id = item.data(Qt.ItemDataRole.UserRole)
            self.view_complaint_clicked.emit(kn_id)

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
