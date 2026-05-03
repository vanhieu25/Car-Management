"""Supplier list screen - S-NCC-01 - Supplier listing with search and filters.

Features:
- Table: ma_ncc, ten_ncc, so_dien_thoai, email, diem_tong, avg_rating (star display)
- Filter by avg_rating range
- "Đánh giá nhanh" button → opens rating dialog
- Search by ten_ncc/ma_ncc
- Add/Edit/Delete buttons (permission-based)

References:
- BR-NCC-01..06: Supplier management rules
- BR-NCC-02: Rating system (3 criteria)
- BR-NCC-03: avg_rating calculation

UI Tasks: T-G4.4.UI.01
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QDoubleSpinBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.nha_cung_cap_service import (
    NhaCungCapService,
    NhaCungCapSearchResult,
    NhaCungCapServiceError,
)
from app.application.services.session import CurrentSession

PAGE_SIZE = 50


class SupplierListScreen(QWidget):
    """Supplier list screen - S-NCC-01.

    Signals:
        add_supplier_clicked: User clicked add supplier button.
        edit_supplier_clicked(ncc_id: int): User wants to edit a supplier.
        view_supplier_clicked(ncc_id: int): User wants to view supplier details.
        rate_supplier_clicked(ncc_id: int): User wants to rate a supplier.
    """

    add_supplier_clicked = pyqtSignal()
    edit_supplier_clicked = pyqtSignal(int)
    view_supplier_clicked = pyqtSignal(int)
    rate_supplier_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize supplier list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._ncc_service = NhaCungCapService(db_conn)

        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[NhaCungCapSearchResult] = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Quản lý nhà cung cấp")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add supplier button (only for admin and sales roles)
        if self._session and self._session.vai_tro_ma in ("admin", "sales"):
            action_layout = QHBoxLayout()
            
            self._add_btn = QPushButton("➕ Thêm nhà cung cấp")
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
            action_layout.addWidget(self._add_btn)
            
            self._delete_btn = QPushButton("🗑️ Xoá")
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
                    background-color: #cc2f26;
                }
            """)
            self._delete_btn.clicked.connect(self._on_delete_clicked)
            action_layout.addWidget(self._delete_btn)
            
            action_layout.addStretch()
            
            layout.addLayout(action_layout)
        
        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo mã, tên nhà cung cấp...")
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

        # Rating filter
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

        filter_layout.addWidget(QLabel("Điểm đánh giá:"))

        filter_layout.addWidget(QLabel("Từ"))

        self._min_rating_spin = QDoubleSpinBox()
        self._min_rating_spin.setRange(0, 5)
        self._min_rating_spin.setSingleStep(0.5)
        self._min_rating_spin.setValue(0)
        self._min_rating_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 6px 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 70px;
                background: white;
            }
        """)
        self._min_rating_spin.valueChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._min_rating_spin)

        filter_layout.addWidget(QLabel("đến"))

        self._max_rating_spin = QDoubleSpinBox()
        self._max_rating_spin.setRange(0, 5)
        self._max_rating_spin.setSingleStep(0.5)
        self._max_rating_spin.setValue(5)
        self._max_rating_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 6px 10px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 70px;
                background: white;
            }
        """)
        self._max_rating_spin.valueChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._max_rating_spin)

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Mã NCC", "Tên nhà cung cấp", "SĐT", "Email", "Điểm tổng", "Đánh giá"
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

        self._total_label = QLabel("Tổng: 0 nhà cung cấp")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        self._current_page = 1
        self._load_data()

    def _load_data(self):
        """Load supplier data based on filters."""
        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None

        min_rating = self._min_rating_spin.value() if self._min_rating_spin.value() > 0 else None
        max_rating = self._max_rating_spin.value() if self._max_rating_spin.value() < 5 else None

        try:
            result = self._ncc_service.search(
                keyword=keyword,
                min_rating=min_rating,
                max_rating=max_rating,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )

            self._current_result = result
            self._total_pages = result.total_pages

            self._populate_table(result.items)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} nhà cung cấp")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, items: List[dict]):
        """Populate table with supplier data.

        Args:
            items: List of supplier dicts.
        """
        self._table.setRowCount(len(items))

        for row, ncc in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(ncc["id"]))
            self._table.setItem(row, 0, item_id)

            # Mã NCC
            self._table.setItem(row, 1, QTableWidgetItem(ncc.get("ma_ncc", "")))

            # Tên NCC
            self._table.setItem(row, 2, QTableWidgetItem(ncc.get("ten_ncc", "")))

            # SĐT
            self._table.setItem(row, 3, QTableWidgetItem(ncc.get("so_dien_thoai", "-")))

            # Email
            self._table.setItem(row, 4, QTableWidgetItem(ncc.get("email", "-")))

            # Điểm tổng
            diem_tong = ncc.get("diem_tong", 0)
            item_diem = QTableWidgetItem(str(diem_tong))
            item_diem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, item_diem)

            # Avg rating (stars)
            avg_rating = round(diem_tong / 3, 1) if diem_tong > 0 else 0
            stars = self._render_stars(avg_rating)
            item_stars = QTableWidgetItem(stars)
            item_stars.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 6, item_stars)

            # Store ID for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, ncc["id"])

        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(1, 100)  # Mã NCC
        self._table.setColumnWidth(3, 120)  # SĐT
        self._table.setColumnWidth(4, 180)  # Email
        self._table.setColumnWidth(5, 80)   # Điểm tổng

    def _render_stars(self, rating: float) -> str:
        """Render star display for rating.

        Args:
            rating: Rating value (0-5).

        Returns:
            String with filled and empty stars.
        """
        full_stars = int(rating)
        half_star = (rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        result = "★" * full_stars
        if half_star:
            result += "1⁄2"
        result += "☆" * empty_stars

        return result

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
            ncc_id = item.data(Qt.ItemDataRole.UserRole)
            if ncc_id:
                self.view_supplier_clicked.emit(ncc_id)

    def _on_add_clicked(self):
        """Handle add supplier button click."""
        self.add_supplier_clicked.emit()
    
    def _get_selected_id(self) -> int:
        """Get selected supplier ID from table.
        
        Returns:
            Supplier ID or -1 if none selected.
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
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn nhà cung cấp cần xoá.")
            return
        
        reply = QMessageBox.question(
            self,
            "Xác nhận xoá",
            "Bạn có chắc muốn xoá nhà cung cấp này?\n\nHành động này không thể hoàn tác.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self._ncc_service.delete(item_id)
            QMessageBox.information(self, "Thành công", "Đã xoá thành công")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xoá: {str(e)}")

    def refresh(self):
        """Refresh the data."""
        self._load_data()