"""Rescue request list screen - S-CH-01 - Rescue request listing with filters.

Features:
- Table: khach_hang, xe, vi_tri, trang_thai, thoi_gian_yeu_cau, nhan_vien, chi_phi
- Status badges: 'tiep_nhan'=yellow, 'dang_xu_ly'=blue, 'hoan_thanh'=green
- Filter by trang_thai
- Search by khach_hang/xe
- Pagination
- Add/Edit buttons (permission-based)
- Double-click row to view details

References:
- BR-HM-04: Cứu hộ has vi_tri, mo_ta, thoi_gian_yeu_cau
- BR-HM-05: Status flow: tiep_nhan -> dang_xu_ly -> hoan_thanh
- BR-HM-06: Create/Update cuu_ho records
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.cuu_ho_service import (
    CuuHoService, CuuHoCreateData, CuuHoUpdateData,
    ValidationError, CuuHoNotFoundError
)
from app.application.services.session import CurrentSession
from app.domain.entities import CuuHo


PAGE_SIZE = 50

TRANG_THAI_LABELS = {
    "tiep_nhan": "Tiếp nhận",
    "dang_xu_ly": "Đang xử lý",
    "hoan_thanh": "Hoàn thành",
}
TRANG_THAI_COLORS = {
    "tiep_nhan": "#ffc107",
    "dang_xu_ly": "#2196f3",
    "hoan_thanh": "#4caf50",
}

TRANG_THAI_OPTIONS = ["Tất cả", "Tiếp nhận", "Đang xử lý", "Hoàn thành"]
TRANG_THAI_VALUE_MAP = {
    "Tiếp nhận": "tiep_nhan",
    "Đang xử lý": "dang_xu_ly",
    "Hoàn thành": "hoan_thanh",
}


class RescueRequestListScreen(QWidget):
    """Rescue request list screen - S-CH-01.

    Signals:
        add_rescue_clicked: User clicked add rescue button.
        edit_rescue_clicked(cuu_ho_id: int): User wants to edit a rescue request.
    """

    add_rescue_clicked = pyqtSignal()
    edit_rescue_clicked = pyqtSignal(int)
    delete_rescue_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize rescue request list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._ch_service = CuuHoService(db_conn)

        self._current_page = 1
        self._total_pages = 1
        self._current_data: List[CuuHo] = []
        self._filter_status = ""
        self._search_keyword = ""

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Yêu cầu cứu hộ")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add button (only for admin/A-02)
        if self._session and self._session.vai_tro_ma in ("A-01", "A-02"):
            self._add_btn = QPushButton("➕ Thêm yêu cầu")
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
            # Delete button (only for admin)
            if self._session and self._session.vai_tro_ma == "A-01":
                self._delete_btn = QPushButton("🗑️ Xóa")
                self._delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff3b30;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 10px 20px;
                        font-size: 14px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #d63030;
                    }
                """)
                self._delete_btn.clicked.connect(self._on_delete_clicked)
                header_layout.addWidget(self._delete_btn)
            header_layout.addWidget(self._add_btn)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo khách hàng, xe, vị trí...")
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
                padding: 12px;
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
        filter_layout.setSpacing(16)

        # Status filter
        status_label = QLabel("Trạng thái:")
        status_label.setStyleSheet("font-weight: 500;")
        filter_layout.addWidget(status_label)

        self._status_filter = QComboBox()
        self._status_filter.addItems(TRANG_THAI_OPTIONS)
        self._status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
                background: white;
                min-width: 140px;
            }
            QComboBox:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._status_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._status_filter)

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Khách hàng",
            "Xe",
            "Vị trí",
            "Trạng thái",
            "Thời gian yêu cầu",
            "Nhân viên phụ trách",
            "Chi phí ước tính"
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
        self._table.doubleClicked.connect(self._on_row_double_clicked)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

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
                color: #d2d2d7;
            }
        """)
        self._prev_btn.clicked.connect(self._on_prev_page)
        pagination_layout.addWidget(self._prev_btn)

        self._page_label = QLabel("Trang 1 / 1")
        self._page_label.setStyleSheet("font-size: 14px; color: #86868b;")
        pagination_layout.addWidget(self._page_label)

        self._next_btn = QPushButton("Sau ▶")
        self._next_btn.setStyleSheet("""
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
                color: #d2d2d7;
            }
        """)
        self._next_btn.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(self._next_btn)

        layout.addLayout(pagination_layout)

    def _load_data(self):
        """Load rescue request data from database."""
        try:
            # Get total count
            all_data = self._ch_service.get_all(limit=10000, offset=0)
            total = len(all_data)
            self._total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

            if self._current_page > self._total_pages:
                self._current_page = self._total_pages

            offset = (self._current_page - 1) * PAGE_SIZE
            self._current_data = all_data[offset:offset + PAGE_SIZE]

            self._populate_table()
            self._update_pagination()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self):
        """Populate table with rescue request data."""
        self._table.setRowCount(0)

        # Apply filters
        filtered_data = self._current_data

        if self._filter_status:
            filtered_data = [r for r in filtered_data if r.trang_thai == self._filter_status]

        if self._search_keyword:
            kw = self._search_keyword.lower()
            filtered_data = [
                r for r in filtered_data
                if kw in (r.vi_tri or "").lower()
                or kw in (r.mo_ta or "").lower()
            ]

        self._table.setRowCount(len(filtered_data))

        for row, ch in enumerate(filtered_data):
            # Khách hàng (placeholder - would need join)
            self._table.setItem(row, 0, QTableWidgetItem(f"KH-{ch.khach_hang_id}"))

            # Xe (placeholder - would need join)
            self._table.setItem(row, 1, QTableWidgetItem(f"Xe-{ch.xe_id}"))

            # Vị trí
            self._table.setItem(row, 2, QTableWidgetItem(ch.vi_tri or "-"))

            # Trạng thái badge
            status_item = QTableWidgetItem(TRANG_THAI_LABELS.get(ch.trang_thai, ch.trang_thai or "-"))
            status_item.setBackground(QColor(TRANG_THAI_COLORS.get(ch.trang_thai, "#e5e5ea")))
            status_item.setForeground(QColor("#ffffff" if ch.trang_thai in TRANG_THAI_COLORS else "#1d1d1f"))
            self._table.setItem(row, 3, status_item)

            # Thời gian yêu cầu
            thoi_gian = ch.thoi_gian_yeu_cau or "-"
            self._table.setItem(row, 4, QTableWidgetItem(thoi_gian))

            # Nhân viên phụ trách
            nv_text = f"NV-{ch.nhan_vien_id}" if ch.nhan_vien_id else "Chưa phân công"
            self._table.setItem(row, 5, QTableWidgetItem(nv_text))

            # Chi phí ước tính
            chi_phi_text = f"{ch.chi_phi:,.0f} đ".replace(",", ".") if ch.chi_phi else "0 đ"
            self._table.setItem(row, 6, QTableWidgetItem(chi_phi_text))

            # Store ID for double-click
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, ch.id)

        self._table.resizeColumnsToContents()

    def _update_pagination(self):
        """Update pagination controls."""
        self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
        self._prev_btn.setEnabled(self._current_page > 1)
        self._next_btn.setEnabled(self._current_page < self._total_pages)

    def _on_search(self):
        """Handle search button click."""
        self._search_keyword = self._search_input.text().strip()
        self._current_page = 1
        self._load_data()

    def _on_filter_changed(self):
        """Handle status filter change."""
        status_text = self._status_filter.currentText()
        self._filter_status = TRANG_THAI_VALUE_MAP.get(status_text, "")
        self._current_page = 1
        self._load_data()

    def _on_prev_page(self):
        """Handle previous page button click."""
        if self._current_page > 1:
            self._current_page -= 1
            self._load_data()

    def _on_next_page(self):
        """Handle next page button click."""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_data()

    def _on_delete_clicked(self):
        """Handle delete button click."""
        selected = self._table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một dòng để xóa!")
            return
        row = selected[0].row()
        item = self._table.item(row, 0)
        if not item:
            return
        cuu_ho_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Xác nhận", "Bạn có chắc muốn xóa yêu cầu cứu hộ này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._ch_service.delete(cuu_ho_id)
                QMessageBox.information(self, "Thành công", "Đã xóa yêu cầu cứu hộ!")
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa: {e}")

    def _on_add_clicked(self):
        """Handle add button click."""
        self.add_rescue_clicked.emit()

    def _on_row_double_clicked(self, index):
        """Handle row double-click to edit."""
        row = index.row()
        item = self._table.item(row, 0)
        if item:
            cuu_ho_id = item.data(Qt.ItemDataRole.UserRole)
            if cuu_ho_id:
                self.edit_rescue_clicked.emit(cuu_ho_id)

    def refresh(self):
        """Refresh the data."""
        self._load_data()
