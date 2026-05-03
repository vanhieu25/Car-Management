"""Installment list screen - S-TG-01 - Installment listing with filters.

Features:
- Overdue warning banner (S-TG-04): shows red "X kỳ quá hạn" when overdue exist
- Table: ma_hd, khach_hang, ngan_hang, so_tien_vay, lai_suat, so_ky, tien_thang, trang_thai
- Filter by ngan_hang, trang_thai (đang trả / hoàn thành / có quá hạn)
- Red highlight for records with any 'qua_han' kỳ
- Search by ma_hd, ten_khach_hang
- Pagination
- Click row → open installment progress (S-TG-03)

References:
- BR-TG-01..05: Installment management
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from app.application.services.tra_gop_service import TraGopService, TraGopListItem
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


class InstallmentListScreen(QWidget):
    """Installment list screen - S-TG-01.

    Signals:
        view_installment_clicked(tra_gop_id: int): User wants to view installment details.
        create_installment_clicked(): User wants to create new installment.
    """

    view_installment_clicked = pyqtSignal(int)
    create_installment_clicked = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize installment list screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = TraGopService(db_conn)

        self._current_page = 1
        self._total_pages = 1
        self._overdue_count = 0

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Quản lý trả góp")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Create button (only for A-01, A-02)
        if self._session and self._session.vai_tro_ma in ("admin", "sales"):
            self._create_btn = QPushButton("➕ Tạo phương án trả góp")
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

        # Overdue warning banner (S-TG-04)
        self._overdue_banner = QPushButton()
        self._overdue_banner.setVisible(False)
        self._overdue_banner.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 15px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e6392a;
            }
        """)
        self._overdue_banner.clicked.connect(self._on_overdue_banner_clicked)
        layout.addWidget(self._overdue_banner)

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

        # Search
        filter_layout.addWidget(QLabel("Tìm kiếm:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Mã HĐ, tên KH...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                background: white;
                min-width: 150px;
            }
        """)
        self._search_input.returnPressed.connect(self._on_filter_changed)
        filter_layout.addWidget(self._search_input)

        # Bank filter
        filter_layout.addWidget(QLabel("Ngân hàng:"))
        self._bank_combo = QComboBox()
        self._bank_combo.addItem("Tất cả", None)
        self._load_bank_list()
        self._bank_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._bank_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._bank_combo)

        # Status filter
        filter_layout.addWidget(QLabel("Trạng thái:"))
        self._status_combo = QComboBox()
        self._status_combo.addItems(["Tất cả", "Đang trả", "Hoàn thành", "Có quá hạn"])
        self._status_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 120px;
                background: white;
            }
        """)
        self._status_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._status_combo)

        filter_layout.addStretch()

        layout.addWidget(filter_group)

        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Mã HĐ", "Khách hàng", "Ngân hàng", "Số tiền vay", "Lãi suất", "Số kỳ", "Tiền tháng", "Trạng thái"
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

        self._total_label = QLabel("Tổng: 0 bản ghi")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)

        layout.addLayout(pagination_layout)

    def _load_bank_list(self):
        """Load distinct bank list from database."""
        try:
            cursor = self._db_conn.execute(
                """SELECT DISTINCT ngan_hang FROM tra_gop ORDER BY ngan_hang"""
            )
            for row in cursor.fetchall():
                self._bank_combo.addItem(row[0], row[0])
        except Exception:
            pass

    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        self._current_page = 1
        self._load_data()

    def _on_overdue_banner_clicked(self):
        """Handle overdue banner click - filter to show only overdue."""
        self._status_combo.setCurrentText("Có quá hạn")
        self._current_page = 1
        self._load_data()

    def _get_filter_params(self) -> dict:
        """Get current filter parameters."""
        params = {}

        keyword = self._search_input.text().strip()
        if keyword:
            params["keyword"] = keyword

        bank = self._bank_combo.currentData()
        if bank:
            params["ngan_hang"] = bank

        status_text = self._status_combo.currentText()
        if status_text == "Đang trả":
            params["trang_thai"] = "dang_tra"
        elif status_text == "Hoàn thành":
            params["trang_thai"] = "hoan_thanh"
        elif status_text == "Có quá hạn":
            params["has_qua_han"] = True

        return params

    def _load_data(self):
        """Load installment data based on filters."""
        params = self._get_filter_params()

        try:
            # Update overdue banner
            self._overdue_count = self._service.count_overdue()
            if self._overdue_count > 0:
                self._overdue_banner.setText(
                    f"⚠️  Có {self._overdue_count} kỳ quá hạn - Click để xem chi tiết"
                )
                self._overdue_banner.setVisible(True)
            else:
                self._overdue_banner.setVisible(False)

            # Load data
            items, total = self._service.get_all(
                ngan_hang=params.get("ngan_hang"),
                trang_thai=params.get("trang_thai"),
                has_qua_han=params.get("has_qua_han"),
                keyword=params.get("keyword"),
                limit=PAGE_SIZE,
                offset=(self._current_page - 1) * PAGE_SIZE,
            )

            self._total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE) if total > 0 else 1

            self._populate_table(items)

            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {total} bản ghi")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _populate_table(self, items: List[TraGopListItem]):
        """Populate table with installment data.

        Args:
            items: List of TraGopListItem entities.
        """
        self._table.setRowCount(len(items))

        # Status colors
        status_colors = {
            "dang_tra": "#007aff",    # Blue
            "hoan_thanh": "#34c759",  # Green
        }

        status_labels = {
            "dang_tra": "Đang trả",
            "hoan_thanh": "Hoàn thành",
        }

        for row, item in enumerate(items):
            # Mã HĐ
            item_ma = QTableWidgetItem(item.ma_hop_dong)
            item_ma.setData(Qt.ItemDataRole.UserRole, item.id)
            self._table.setItem(row, 0, item_ma)

            # Khách hàng
            self._table.setItem(row, 1, QTableWidgetItem(item.khach_hang_ten or "N/A"))

            # Ngân hàng
            self._table.setItem(row, 2, QTableWidgetItem(item.ngan_hang))

            # Số tiền vay
            tien_vay_text = f"{item.so_tien_vay:,.0f} đ".replace(",", ".")
            item_tien = QTableWidgetItem(tien_vay_text)
            item_tien.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 3, item_tien)

            # Lãi suất
            lai_text = f"{item.lai_suat_nam:.2f}%"
            item_lai = QTableWidgetItem(lai_text)
            item_lai.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, item_lai)

            # Số kỳ
            item_ky = QTableWidgetItem(f"{item.so_ky} tháng")
            item_ky.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, item_ky)

            # Tiền tháng
            tien_thang_text = f"{item.so_tien_tra_thang:,.0f} đ".replace(",", ".")
            item_thang = QTableWidgetItem(tien_thang_text)
            item_thang.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 6, item_thang)

            # Trạng thái
            status_text = status_labels.get(item.trang_thai, item.trang_thai)
            item_status = QTableWidgetItem(status_text)

            if item.has_qua_han:
                # Red highlight for overdue
                item_status.setBackground(QColor("#ff3b30"))
                item_status.setForeground(QColor(255, 255, 255))
            else:
                color_hex = status_colors.get(item.trang_thai, "#8e8e93")
                item_status.setBackground(QColor(color_hex))
                item_status.setForeground(QColor(255, 255, 255))

            self._table.setItem(row, 7, item_status)

        # Set column widths
        self._table.setColumnWidth(0, 120)  # Mã HĐ
        self._table.setColumnWidth(1, 150)  # KH
        self._table.setColumnWidth(2, 120)  # Ngân hàng
        self._table.setColumnWidth(3, 130)  # Số tiền vay
        self._table.setColumnWidth(4, 80)   # Lãi suất
        self._table.setColumnWidth(5, 80)    # Số kỳ
        self._table.setColumnWidth(6, 130)  # Tiền tháng
        self._table.setColumnWidth(7, 110)  # Trạng thái

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
            tra_gop_id = item.data(Qt.ItemDataRole.UserRole)
            if tra_gop_id:
                self.view_installment_clicked.emit(tra_gop_id)

    def _on_create_clicked(self):
        """Handle create installment button click."""
        self.create_installment_clicked.emit()

    def refresh(self):
        """Refresh the data."""
        self._load_data()
