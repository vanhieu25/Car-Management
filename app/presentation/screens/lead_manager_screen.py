"""Lead manager screen - S-MK-03 - Lead listing with status management.

Features:
- Table: ho_ten, so_dien_thoai, chien_dich, nhan_vien, trang_thai, ngay_tao
- Badge colors: 'moi'=blue, 'dang_cham_soc'=orange, 'chuyen_doi'=green, 'tu_choi'=red
- Filter by trang_thai, campaign, date range
- Search by keyword
- Buttons: Update status, Convert to customer, Assign staff
- Convert button disabled if status != 'dang_cham_soc' or has khach_hang_id

References:
- BR-MK-02: Lead status flow (moi → dang_cham_soc → chuyen_doi/tu_choi)
- BR-MK-03: Convert lead to customer
"""

from typing import Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QApplication, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont

from app.application.services.lead_service import (
    LeadService, LeadCreateData, LeadUpdateData,
    LeadNotFoundError, ValidationError, LeadConvertError
)
from app.application.services.session import CurrentSession


PAGE_SIZE = 50


TRANG_THAI_LABELS = {
    "moi": "Mới",
    "dang_cham_soc": "Đang chăm sóc",
    "chuyen_doi": "Chuyển đổi",
    "tu_choi": "Từ chối",
}

TRANG_THAI_COLORS = {
    "moi": "#2196f3",
    "dang_cham_soc": "#ff9800",
    "chuyen_doi": "#4caf50",
    "tu_choi": "#f44336",
}


class LeadManagerScreen(QWidget):
    """Lead manager screen - S-MK-03.

    Signals:
        add_lead_clicked: User clicked add lead button.
        edit_lead_clicked(lead_id: int): User wants to edit a lead.
    """

    add_lead_clicked = pyqtSignal()
    edit_lead_clicked = pyqtSignal(int)

    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize lead manager screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = LeadService(db_conn)

        self._current_page = 0
        self._status_filter = None
        self._campaign_filter = None
        self._search_keyword = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # Title
        title_label = QLabel("Quản lý Lead")
        title_label.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f;")
        main_layout.addWidget(title_label)

        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self._stats_labels = {}
        stats_items = [
            ("tong_lead", "Tổng lead"),
            ("moi", "Mới"),
            ("dang_cham_soc", "Đang chăm sóc"),
            ("chuyen_doi", "Chuyển đổi"),
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
        self._search_edit.setPlaceholderText("Tìm kiếm (tên, SĐT, email)...")
        self._search_edit.textChanged.connect(self._on_search_changed)
        self._search_edit.setStyleSheet("padding: 6px 12px; border-radius: 6px;")
        filter_layout.addWidget(self._search_edit)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["Tất cả", "Mới", "Đang chăm sóc", "Chuyển đổi", "Từ chối"])
        self._status_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("Trạng thái:"))
        filter_layout.addWidget(self._status_combo)

        filter_layout.addStretch()

        self._btn_add = QPushButton("+ Thêm Lead")
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

        main_layout.addLayout(filter_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self._btn_update_status = QPushButton("Cập nhật trạng thái")
        self._btn_update_status.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #e8e8ed; }
        """)
        self._btn_update_status.clicked.connect(self._on_update_status_clicked)
        action_layout.addWidget(self._btn_update_status)

        self._btn_convert = QPushButton("Chuyển thành KH")
        self._btn_convert.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #2db84d; }
        """)
        self._btn_convert.clicked.connect(self._on_convert_clicked)
        action_layout.addWidget(self._btn_convert)

        self._btn_assign = QPushButton("Gán nhân viên")
        self._btn_assign.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #e8e8ed; }
        """)
        self._btn_assign.clicked.connect(self._on_assign_clicked)
        action_layout.addWidget(self._btn_assign)

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
            action_layout.addWidget(self._btn_delete)

        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Họ tên", "SĐT", "Email", "Chiến dịch", "NV phụ trách", "Trạng thái", "Ngày tạo"
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
        """Load leads data."""
        try:
            # Get stats
            stats = self._service.get_lead_stats()
            self._stats_labels["tong_lead"].findChild(QLabel).setText(str(stats.get("tong_lead", 0)))
            self._stats_labels["moi"].findChild(QLabel).setText(str(stats.get("moi", 0)))
            self._stats_labels["dang_cham_soc"].findChild(QLabel).setText(str(stats.get("dang_cham_soc", 0)))
            self._stats_labels["chuyen_doi"].findChild(QLabel).setText(str(stats.get("chuyen_doi", 0)))

            # Get leads
            status_map = {
                "Mới": "moi",
                "Đang chăm sóc": "dang_cham_soc",
                "Chuyển đổi": "chuyen_doi",
                "Từ chối": "tu_choi"
            }
            status_filter = status_map.get(self._status_combo.currentText())

            if self._search_keyword:
                leads = self._service.search(self._search_keyword)
            elif status_filter:
                leads = self._service.get_by_status(status_filter)
            else:
                leads = self._service.get_all(limit=PAGE_SIZE, offset=self._current_page * PAGE_SIZE)

            self._populate_table(leads)
            self._update_action_buttons()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {e}")

    def _populate_table(self, leads: List[dict]):
        """Populate table with lead data."""
        self._table.setRowCount(len(leads))

        for row, lead in enumerate(leads):
            # Name
            name_item = QTableWidgetItem(lead.get('ho_ten', ''))
            name_item.setData(Qt.UserRole, lead['id'])
            self._table.setItem(row, 0, name_item)

            # Phone
            self._table.setItem(row, 1, QTableWidgetItem(lead.get('so_dien_thoai', '')))

            # Email
            self._table.setItem(row, 2, QTableWidgetItem(lead.get('email', '')))

            # Campaign
            campaign_name = lead.get('ten_chien_dich', '') or '-'
            self._table.setItem(row, 3, QTableWidgetItem(campaign_name))

            # Assigned NV
            nv_ten = lead.get('nhan_vien_ten', '') or '-'
            self._table.setItem(row, 4, QTableWidgetItem(nv_ten))

            # Status badge
            status = lead.get('trang_thai', 'moi')
            status_text = TRANG_THAI_LABELS.get(status, status)
            status_item = QTableWidgetItem(status_text)
            status_item.setBackground(QColor(TRANG_THAI_COLORS.get(status, "#9e9e9e")))
            status_item.setForeground(QColor("white"))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, status_item)

            # Created date
            created_at = lead.get('created_at', '')[:10] if lead.get('created_at') else '-'
            self._table.setItem(row, 6, QTableWidgetItem(created_at))

        # Resize columns
        self._table.resizeColumnsToContents()
        self._table.column(0).setWidth(150)

        # Update pagination
        self._page_label.setText(f"Trang {self._current_page + 1}")
        self._btn_prev.setEnabled(self._current_page > 0)
        self._btn_next.setEnabled(len(leads) == PAGE_SIZE)

    def _update_action_buttons(self):
        """Update action button states based on selection."""
        selected_rows = self._table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        self._btn_update_status.setEnabled(has_selection)
        self._btn_assign.setEnabled(has_selection)

        # Convert button: only enabled if selected row has trang_thai='dang_cham_soc' and no khach_hang_id
        if has_selection:
            row = selected_rows[0].row()
            status_item = self._table.item(row, 5)
            if status_item:
                status = status_item.text()
                is_dang_cham_soc = status == "Đang chăm sóc"
                self._btn_convert.setEnabled(is_dang_cham_soc)
        else:
            self._btn_convert.setEnabled(False)

    def _on_filter_changed(self):
        """Handle filter change."""
        self._current_page = 0
        self._load_data()

    def _on_search_changed(self, text):
        """Handle search text change."""
        self._search_keyword = text if text.strip() else None
        self._current_page = 0
        self._load_data()

    def _on_add_clicked(self):
        """Handle add lead button click."""
        self.add_lead_clicked.emit()

    def _on_row_double_clicked(self, row, column):
        """Handle table row double click."""
        item = self._table.item(row, 0)
        if item:
            lead_id = item.data(Qt.UserRole)
            self.edit_lead_clicked.emit(lead_id)

    def _on_update_status_clicked(self):
        """Handle update status button click."""
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chọn lead", "Vui lòng chọn một lead để cập nhật trạng thái")
            return

        row = selected_rows[0].row()
        lead_id = self._table.item(row, 0).data(Qt.UserRole)

        from app.presentation.screens.lead_status_dialog import LeadStatusDialog
        dialog = LeadStatusDialog(self._db_conn, self._session, lead_id, self)
        dialog.saved.connect(self._load_data)
        dialog.exec()

    def _on_convert_clicked(self):
        """Handle convert to customer button click."""
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chọn lead", "Vui lòng chọn một lead để chuyển đổi")
            return

        row = selected_rows[0].row()
        lead_id = self._table.item(row, 0).data(Qt.UserRole)
        lead_name = self._table.item(row, 0).text()

        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Chuyển lead '{lead_name}' thành khách hàng?\n\nHành động này sẽ tạo khách hàng mới từ thông tin lead.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._service.convert_to_customer(lead_id)
                QMessageBox.information(self, "Thành công", f"Lead '{lead_name}' đã được chuyển thành khách hàng")
                self._load_data()
            except LeadConvertError as e:
                QMessageBox.warning(self, "Lỗi", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể chuyển đổi: {e}")

    def _on_assign_clicked(self):
        """Handle assign staff button click."""
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chọn lead", "Vui lòng chọn một lead để gán nhân viên")
            return

        row = selected_rows[0].row()
        lead_id = self._table.item(row, 0).data(Qt.UserRole)

        from app.presentation.screens.lead_assign_dialog import LeadAssignDialog
        dialog = LeadAssignDialog(self._db_conn, self._session, lead_id, self)
        dialog.saved.connect(self._load_data)
        dialog.exec()
    
    def _on_delete_clicked(self):
        """Handle delete button click."""
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn lead cần xoá.")
            return
        
        row = selected_rows[0].row()
        lead_id = self._table.item(row, 0).data(Qt.UserRole)
        lead_name = self._table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Xác nhận xoá",
            f"Bạn có chắc muốn xoá lead '{lead_name}'?\n\nHành động này không thể hoàn tác.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self._service.delete(lead_id)
            QMessageBox.information(self, "Thành công", "Đã xoá thành công")
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể xoá: {str(e)}")

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
