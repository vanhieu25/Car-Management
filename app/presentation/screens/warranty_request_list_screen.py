"""Warranty request list screen - S-BH-01a - Warranty requests listing with filters.

Features:
- Search by request ID, customer name, vehicle
- Filter by status: Tất cả / Mới / Đang xử lý / Hoàn thành / Đóng
- Filter by type: Tất cả / Bảo dưỡng / Sửa chữa / Thay thế
- Table: ID, Ngày yêu cầu, Khách hàng, Xe, Loại, Trạng thái, Chi phí
- Double-click row to open warranty detail
- Pagination

References:
- BR-BH-05: Request status transitions
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor

from app.application.services.bao_hanh_service import BaoHanhService
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


class WarrantyRequestListScreen(QWidget):
    """Warranty request list screen - S-BH-01a.

    Signals:
        view_request_clicked(req_id: int): User wants to view request details.
        view_warranty_clicked(bh_id: int): User wants to view warranty details.
        create_request_clicked(): User wants to create new request.
    """

    view_request_clicked = pyqtSignal(int)
    view_warranty_clicked = pyqtSignal(int)
    create_request_clicked = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize warranty request list screen.

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
        self._current_filter = "tat_ca"
        self._current_type = None
        self._search_keyword = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Yêu cầu bảo hành")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Action buttons for admin/ky_thuat
        if self._session and self._session.vai_tro_ma in ("admin", "ky_thuat"):
            action_layout = QHBoxLayout()

            self._add_btn = QPushButton("➕ Tạo yêu cầu")
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

            self._update_status_btn = QPushButton("🔄 Cập nhật trạng thái")
            self._update_status_btn.setEnabled(False)
            self._update_status_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007aff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #0066cc;
                }
                QPushButton:disabled {
                    background-color: #d2d2d7;
                    color: #86868b;
                }
            """)
            self._update_status_btn.clicked.connect(self._on_update_status_clicked)
            action_layout.addWidget(self._update_status_btn)

            header_layout.addLayout(action_layout)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo mã yêu cầu, tên khách hàng...")
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

        # Filter group
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

        # Status filter
        filter_layout.addWidget(QLabel("Trạng thái:"))

        self._filter_buttons = {}
        filter_tabs = [
            ("tat_ca", "Tất cả"),
            ("moi", "Mới"),
            ("dang_xu_ly", "Đang xử lý"),
            ("da_hoan_thanh", "Hoàn thành"),
            ("da_dong", "Đóng"),
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

        # Type filter
        filter_layout.addWidget(QLabel("Loại:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["Tất cả", "Bảo dưỡng", "Sửa chữa", "Thay thế"])
        self._type_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        filter_layout.addWidget(self._type_combo)

        layout.addWidget(filter_group)

        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Ngày yêu cầu", "Khách hàng", "Xe", "Loại", "Chi phí", "Trạng thái"
        ])

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)

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

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)

        # Connect selection
        self._table.itemSelectionChanged.connect(self._on_selection_changed)

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

        self._total_label = QLabel("Tổng: 0 yêu cầu")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _on_filter_changed(self, filter_key: str):
        """Handle filter tab change."""
        for key, btn in self._filter_buttons.items():
            btn.setChecked(key == filter_key)

        self._current_filter = filter_key
        self._current_page = 1
        self._load_data()

    def _on_type_changed(self, text: str):
        """Handle type filter change."""
        type_map = {
            "Tất cả": None,
            "Bảo dưỡng": "bao_duong",
            "Sửa chữa": "sua_chua",
            "Thay thế": "thay_the",
        }
        self._current_type = type_map.get(text)
        self._current_page = 1
        self._load_data()

    def _on_search(self):
        """Handle search button click."""
        keyword = self._search_input.text().strip()
        self._search_keyword = keyword if keyword else None
        self._current_page = 1
        self._load_data()

    def _on_prev_page(self):
        """Handle previous page button."""
        if self._current_page > 1:
            self._current_page -= 1
            self._load_data()

    def _on_next_page(self):
        """Handle next page button."""
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._load_data()

    def _load_data(self):
        """Load warranty request data."""
        try:
            # Build query for all requests with join to bao_hanh and khach_hang
            query = """
                SELECT yc.id, yc.ngay_yeu_cau, yc.loai_yeu_cau, yc.mo_ta_tinh_trang,
                       yc.chi_phi, yc.trang_thai, yc.bao_hanh_id,
                       kh.ho_ten as kh_ho_ten, kh.so_dien_thoai as kh_sdt,
                       xe.hang as xe_hang, xe.dong_xe as xe_dong_xe
                FROM bao_hanh_yeu_cau yc
                JOIN bao_hanh bh ON yc.bao_hanh_id = bh.id
                JOIN khach_hang kh ON bh.khach_hang_id = kh.id
                JOIN xe ON bh.xe_id = xe.id
                WHERE 1=1
            """
            params = []

            # Status filter
            if self._current_filter != "tat_ca":
                query += " AND yc.trang_thai = ?"
                params.append(self._current_filter)

            # Type filter
            if self._current_type:
                query += " AND yc.loai_yeu_cau = ?"
                params.append(self._current_type)

            # Search keyword
            if self._search_keyword:
                # Try numeric ID first, then fallback to name search
                # Remove commas from keyword for number conversion
                clean_keyword = self._search_keyword.replace(",", "").strip()
                try:
                    req_id = int(clean_keyword)
                    query += " AND yc.id = ?"
                    params.append(req_id)
                except ValueError:
                    query += " AND kh.ho_ten LIKE ?"
                    params.append(f"%{self._search_keyword}%")

            # Count total
            count_query = f"SELECT COUNT(*) FROM ({query})"
            cursor = self._db_conn.execute(count_query, params)
            total = cursor.fetchone()[0]

            self._total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
            offset = (self._current_page - 1) * PAGE_SIZE

            query += f" ORDER BY yc.ngay_yeu_cau DESC LIMIT {PAGE_SIZE} OFFSET {offset}"

            cursor = self._db_conn.execute(query, params)
            rows = cursor.fetchall()

            self._populate_table(rows)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {total} yêu cầu")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, rows: List):
        """Populate table with request data.

        Args:
            rows: List of database rows.
        """
        self._table.setRowCount(len(rows))

        status_colors = {
            "moi": "#007aff",
            "dang_xu_ly": "#ff9500",
            "da_hoan_thanh": "#34c759",
            "da_dong": "#8e8e93",
        }

        status_labels = {
            "moi": "Mới",
            "dang_xu_ly": "Đang xử lý",
            "da_hoan_thanh": "Hoàn thành",
            "da_dong": "Đóng",
        }

        loai_map = {
            "bao_duong": "Bảo dưỡng",
            "sua_chua": "Sửa chữa",
            "thay_the": "Thay thế",
        }

        for row_idx, row in enumerate(rows):
            # ID
            item_id = QTableWidgetItem(str(row[0]))
            item_id.setData(Qt.ItemDataRole.UserRole, row[0])  # Store request ID
            self._table.setItem(row_idx, 0, item_id)

            # Ngày yêu cầu
            ngay_yc = row[1][:10] if row[1] else "-"
            self._table.setItem(row_idx, 1, QTableWidgetItem(ngay_yc))

            # Khách hàng
            self._table.setItem(row_idx, 2, QTableWidgetItem(row[7] or "-"))

            # Xe
            xe_info = f"{row[9] or ''} {row[10] or ''}".strip()
            self._table.setItem(row_idx, 3, QTableWidgetItem(xe_info or "-"))

            # Loại
            loai = loai_map.get(row[2], row[2])
            self._table.setItem(row_idx, 4, QTableWidgetItem(loai))

            # Chi phí
            chi_phi = int(row[4] or 0)
            tien_text = f"{chi_phi:,} đ".replace(",", ".")
            item_tien = QTableWidgetItem(tien_text)
            item_tien.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self._table.setItem(row_idx, 5, item_tien)

            # Trạng thái
            trang_thai = row[5]
            status_text = status_labels.get(trang_thai, trang_thai)
            item_status = QTableWidgetItem(status_text)
            color_hex = status_colors.get(trang_thai, "#8e8e93")
            item_status.setBackground(QColor(color_hex))
            item_status.setForeground(QColor(255, 255, 255))
            self._table.setItem(row_idx, 6, item_status)

    def _on_selection_changed(self):
        """Handle row selection change."""
        if hasattr(self, '_update_status_btn'):
            selected = self._table.selectedItems()
            self._update_status_btn.setEnabled(len(selected) > 0)

    def _on_add_clicked(self):
        """Handle add request button click."""
        self.create_request_clicked.emit()

    def _get_selected_id(self) -> int:
        """Get selected request ID from table.

        Returns:
            Request ID or -1 if none selected.
        """
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return -1
        row = selected_rows[0].row()
        item = self._table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return -1

    def _on_update_status_clicked(self):
        """Handle update status button click."""
        req_id = self._get_selected_id()
        if req_id < 0:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn yêu cầu cần cập nhật.")
            return

        from app.presentation.screens.warranty_request_status_dialog import WarrantyRequestStatusDialog

        # Get current request data
        cursor = self._db_conn.execute(
            "SELECT trang_thai, chi_phi FROM bao_hanh_yeu_cau WHERE id = ?",
            (req_id,)
        )
        row = cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy yêu cầu")
            return

        current_status = row[0]
        current_chi_phi = row[1] or 0

        # Get allowed transitions based on current status
        allowed_transitions = {
            "moi": ["dang_xu_ly"],
            "dang_xu_ly": ["da_hoan_thanh", "moi"],
            "da_hoan_thanh": ["da_dong"],
            "da_dong": [],
        }
        next_statuses = allowed_transitions.get(current_status, [])

        if not next_statuses:
            QMessageBox.information(self, "Thông báo", "Không thể chuyển trạng thái từ trạng thái hiện tại.")
            return

        dialog = WarrantyRequestStatusDialog(
            current_status=current_status,
            allowed_transitions=next_statuses,
            current_chi_phi=current_chi_phi,
            parent=self
        )

        if dialog.exec():
            new_status, chi_phi = dialog.get_values()
            if new_status:
                try:
                    self._bh_service.update_request(
                        req_id=req_id,
                        trang_thai=new_status,
                        chi_phi=chi_phi,
                        nhan_vien_id_current=self._session.nhan_vien_id if self._session else None
                    )
                    QMessageBox.information(self, "Thành công", "Đã cập nhật trạng thái!")
                    self._load_data()
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {str(e)}")

    def _on_row_double_clicked(self, row: int, column: int):
        """Handle row double click."""
        item = self._table.item(row, 0)
        if item:
            req_id = item.data(Qt.ItemDataRole.UserRole)
            if req_id:
                self.view_request_clicked.emit(req_id)

    def refresh(self):
        """Refresh data."""
        self._load_data()