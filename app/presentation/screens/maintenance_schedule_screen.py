"""Maintenance schedule screen - S-HM-01 - Calendar view of maintenance appointments.

Features:
- QCalendarWidget for calendar view
- Toggle between calendar view and list view
- Click date → show maintenance schedule for that day
- Show customer name, vehicle, time, status
- Filter by status, search by customer name

References:
- BR-TIME-02: Find BD appointments within N days
- BR-HM-01..02: Maintenance management
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QCalendarWidget, QStackedWidget, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont

from app.application.services.bao_duong_service import BaoDuongService, BaoDuongCreateData, BaoDuongUpdateData
from app.application.services.session import CurrentSession


class MaintenanceScheduleScreen(QWidget):
    """Maintenance schedule screen - S-HM-01.
    
    Signals:
        add_maintenance_clicked: User clicked add maintenance button.
        edit_maintenance_clicked(bao_duong_id: int): User wants to edit maintenance record.
    """
    
    add_maintenance_clicked = pyqtSignal()
    edit_maintenance_clicked = pyqtSignal(int)
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize maintenance schedule screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._bd_service = BaoDuongService(db_conn)
        
        self._current_view = "calendar"  # "calendar" or "list"
        self._selected_date = QDate.currentDate()
        self._status_filter = None
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
        
        title = QLabel("Lịch bảo dưỡng")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add maintenance button (permission-based)
        if self._session and self._session.vai_tro_ma in ("admin", "sales", "A-04"):
            self._add_btn = QPushButton("➕ Thêm lịch bảo dưỡng")
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
            header_layout.addWidget(self._add_btn)
        
        layout.addLayout(header_layout)
        
        # View toggle and filters
        controls_group = QGroupBox()
        controls_group.setStyleSheet("""
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
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setSpacing(16)
        
        # View toggle buttons
        self._calendar_view_btn = QPushButton("📅 Lịch")
        self._calendar_view_btn.setCheckable(True)
        self._calendar_view_btn.setChecked(True)
        self._calendar_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #0066cc;
            }
            QPushButton:!checked {
                background-color: #f5f5f7;
                color: #1d1d1f;
            }
        """)
        self._calendar_view_btn.clicked.connect(lambda: self._set_view("calendar"))
        controls_layout.addWidget(self._calendar_view_btn)
        
        self._list_view_btn = QPushButton("📋 Danh sách")
        self._list_view_btn.setCheckable(True)
        self._list_view_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #0066cc;
                color: white;
            }
        """)
        self._list_view_btn.clicked.connect(lambda: self._set_view("list"))
        controls_layout.addWidget(self._list_view_btn)
        
        controls_layout.addSpacing(24)
        
        # Status filter
        controls_layout.addWidget(QLabel("Trạng thái:"))
        self._status_combo = QComboBox()
        self._status_combo.addItems(["Tất cả", "Chờ xác nhận", "Đã xác nhận", "Đang thực hiện", "Hoàn thành", "Đã hủy"])
        self._status_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 140px;
                background: white;
            }
        """)
        self._status_combo.currentTextChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(self._status_combo)
        
        # Search by customer name
        controls_layout.addWidget(QLabel("Tìm KH:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Tên khách hàng...")
        self._search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 150px;
                background: white;
            }
        """)
        self._search_input.returnPressed.connect(self._on_search)
        controls_layout.addWidget(self._search_input)
        
        self._search_btn = QPushButton("Tìm")
        self._search_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
        """)
        self._search_btn.clicked.connect(self._on_search)
        controls_layout.addWidget(self._search_btn)
        
        controls_layout.addStretch()
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)
        legend_layout.addWidget(self._create_badge("Chờ xác nhận", "#8e8e93"))
        legend_layout.addWidget(self._create_badge("Đã xác nhận", "#007aff"))
        legend_layout.addWidget(self._create_badge("Đang thực hiện", "#ff9500"))
        legend_layout.addWidget(self._create_badge("Hoàn thành", "#34c759"))
        legend_layout.addWidget(self._create_badge("Đã hủy", "#ff3b30"))
        
        controls_layout.addLayout(legend_layout)
        
        layout.addWidget(controls_group)
        
        # Stacked widget for calendar/list views
        self._view_stack = QStackedWidget()
        
        # Calendar view
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        calendar_layout.setContentsMargins(0, 0, 0, 0)
        
        self._calendar = QCalendarWidget()
        self._calendar.setStyleSheet("""
            QCalendarWidget {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                background-color: white;
            }
            QCalendarWidget QToolButton {
                color: #1d1d1f;
            }
            QCalendarWidget QMenu {
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
            }
            QCalendarWidget QAbstractItemView {
                selection-background-color: #0066cc;
            }
        """)
        self._calendar.clicked.connect(self._on_date_selected)
        calendar_layout.addWidget(self._calendar)
        
        # Selected date schedule table
        self._date_schedule_label = QLabel("Lịch ngày: " + QDate.currentDate().toString("dd/MM/yyyy"))
        self._date_schedule_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1d1d1f; margin-top: 16px;")
        calendar_layout.addWidget(self._date_schedule_label)
        
        self._schedule_table = QTableWidget()
        self._schedule_table.setColumnCount(5)
        self._schedule_table.setHorizontalHeaderLabels(["Giờ", "Khách hàng", "Xe", "Nội dung", "Trạng thái"])
        self._schedule_table.setStyleSheet("""
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
        self._schedule_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._schedule_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._schedule_table.cellDoubleClicked.connect(self._on_schedule_row_double_clicked)
        self._schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        calendar_layout.addWidget(self._schedule_table)
        
        self._view_stack.addWidget(calendar_widget)
        
        # List view (upcoming appointments)
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        self._list_table = QTableWidget()
        self._list_table.setColumnCount(6)
        self._list_table.setHorizontalHeaderLabels(["Ngày", "Giờ", "Khách hàng", "Xe", "Nội dung", "Trạng thái"])
        self._list_table.setStyleSheet("""
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
        self._list_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._list_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._list_table.setSortingEnabled(True)
        self._list_table.cellDoubleClicked.connect(self._on_list_row_double_clicked)
        self._list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_layout.addWidget(self._list_table)
        
        self._view_stack.addWidget(list_widget)
        
        layout.addWidget(self._view_stack)
    
    def _create_badge(self, text: str, color: str) -> QLabel:
        """Create a badge label with colored background."""
        label = QLabel(f"<span style='background:{color}; color:white; padding:2px 8px; border-radius:4px; font-size:12px;'>{text}</span>")
        label.setStyleSheet("padding: 0 4px;")
        return label
    
    def _set_view(self, view: str):
        """Switch between calendar and list view."""
        self._current_view = view
        if view == "calendar":
            self._calendar_view_btn.setChecked(True)
            self._list_view_btn.setChecked(False)
            self._calendar_view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
            """)
            self._list_view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f7;
                    color: #1d1d1f;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
            """)
            self._view_stack.setCurrentIndex(0)
        else:
            self._list_view_btn.setChecked(True)
            self._calendar_view_btn.setChecked(False)
            self._list_view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
            """)
            self._calendar_view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f7;
                    color: #1d1d1f;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 14px;
                }
            """)
            self._view_stack.setCurrentIndex(1)
        
        self._load_data()
    
    def _on_filter_changed(self):
        """Handle filter change - reload data."""
        self._load_data()
    
    def _on_search(self):
        """Handle search button click."""
        self._search_keyword = self._search_input.text().strip() if self._search_input.text().strip() else None
        self._load_data()
    
    def _on_date_selected(self, date: QDate):
        """Handle calendar date selection."""
        self._selected_date = date
        self._date_schedule_label.setText("Lịch ngày: " + date.toString("dd/MM/yyyy"))
        self._load_schedule_for_date(date)
    
    def _load_schedule_for_date(self, date: QDate):
        """Load maintenance schedule for specific date."""
        date_str = date.toString("yyyy-MM-dd")
        
        # Status mapping
        status_map = {
            "Chờ xác nhận": "cho_xac_nhan",
            "Đã xác nhận": "da_xac_nhan",
            "Đang thực hiện": "dang_thuc_hien",
            "Hoàn thành": "hoan_thanh",
            "Đã hủy": "huy",
        }
        
        # Build query
        query = """
            SELECT bd.id, bd.ngay_du_kien, bd.noi_dung, bd.trang_thai, bd.chi_phi,
                   kh.ho_ten, kh.so_dien_thoai,
                   xe.hang, xe.dong_xe, xe.mau_sac,
                   nv.ho_ten as nv_ten
            FROM bao_duong bd
            LEFT JOIN khach_hang kh ON bd.khach_hang_id = kh.id
            LEFT JOIN xe ON bd.xe_id = xe.id
            LEFT JOIN nhan_vien nv ON bd.nhan_vien_id = nv.id
            WHERE date(bd.ngay_du_kien) = ?
        """
        params = [date_str]
        
        status_text = self._status_combo.currentText()
        if status_text != "Tất cả":
            status_code = status_map.get(status_text)
            if status_code:
                query += " AND bd.trang_thai = ?"
                params.append(status_code)
        
        if self._search_keyword:
            query += " AND kh.ho_ten LIKE ?"
            params.append(f"%{self._search_keyword}%")
        
        query += " ORDER BY bd.ngay_du_kien"
        
        try:
            cursor = self._db_conn.execute(query, params)
            rows = cursor.fetchall()
            
            self._schedule_table.setRowCount(len(rows))
            
            # Status colors
            status_colors = {
                "cho_xac_nhan": "#8e8e93",
                "da_xac_nhan": "#007aff",
                "dang_thuc_hien": "#ff9500",
                "hoan_thanh": "#34c759",
                "huy": "#ff3b30",
            }
            
            status_labels = {
                "cho_xac_nhan": "Chờ xác nhận",
                "da_xac_nhan": "Đã xác nhận",
                "dang_thuc_hien": "Đang thực hiện",
                "hoan_thanh": "Hoàn thành",
                "huy": "Đã hủy",
            }
            
            for row_idx, row in enumerate(rows):
                # Giờ (extracted from datetime)
                ngay_du_kien = row[1] or ""
                gio = ngay_du_kien[11:16] if len(ngay_du_kien) > 16 else "08:00"
                
                item_gio = QTableWidgetItem(gio)
                item_gio.setData(Qt.ItemDataRole.UserRole, row[0])
                self._schedule_table.setItem(row_idx, 0, item_gio)
                
                # Khách hàng
                self._schedule_table.setItem(row_idx, 1, QTableWidgetItem(row[5] or "N/A"))
                
                # Xe
                xe_info = f"{row[7]} {row[8]} - {row[9]}" if row[7] else "N/A"
                self._schedule_table.setItem(row_idx, 2, QTableWidgetItem(xe_info))
                
                # Nội dung
                self._schedule_table.setItem(row_idx, 3, QTableWidgetItem(row[2] or "-"))
                
                # Trạng thái
                status = row[3]
                status_text_label = status_labels.get(status, status)
                item_status = QTableWidgetItem(status_text_label)
                color_hex = status_colors.get(status, "#8e8e93")
                item_status.setBackground(QColor(color_hex))
                item_status.setForeground(QColor(255, 255, 255))
                self._schedule_table.setItem(row_idx, 4, item_status)
        
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải lịch bảo dưỡng: {str(e)}")
    
    def _load_list_view(self):
        """Load all upcoming maintenance appointments in list view."""
        # Status mapping
        status_map = {
            "Chờ xác nhận": "cho_xac_nhan",
            "Đã xác nhận": "da_xac_nhan",
            "Đang thực hiện": "dang_thuc_hien",
            "Hoàn thành": "hoan_thanh",
            "Đã hủy": "huy",
        }
        
        # Build query
        query = """
            SELECT bd.id, bd.ngay_du_kien, bd.noi_dung, bd.trang_thai, bd.chi_phi,
                   kh.ho_ten, kh.so_dien_thoai,
                   xe.hang, xe.dong_xe, xe.mau_sac,
                   nv.ho_ten as nv_ten
            FROM bao_duong bd
            LEFT JOIN khach_hang kh ON bd.khach_hang_id = kh.id
            LEFT JOIN xe ON bd.xe_id = xe.id
            LEFT JOIN nhan_vien nv ON bd.nhan_vien_id = nv.id
            WHERE 1=1
        """
        params = []
        
        status_text = self._status_combo.currentText()
        if status_text != "Tất cả":
            status_code = status_map.get(status_text)
            if status_code:
                query += " AND bd.trang_thai = ?"
                params.append(status_code)
        
        if self._search_keyword:
            query += " AND kh.ho_ten LIKE ?"
            params.append(f"%{self._search_keyword}%")
        
        query += " ORDER BY bd.ngay_du_kien"
        
        try:
            cursor = self._db_conn.execute(query, params)
            rows = cursor.fetchall()
            
            self._list_table.setRowCount(len(rows))
            
            # Status colors
            status_colors = {
                "cho_xac_nhan": "#8e8e93",
                "da_xac_nhan": "#007aff",
                "dang_thuc_hien": "#ff9500",
                "hoan_thanh": "#34c759",
                "huy": "#ff3b30",
            }
            
            status_labels = {
                "cho_xac_nhan": "Chờ xác nhận",
                "da_xac_nhan": "Đã xác nhận",
                "dang_thuc_hien": "Đang thực hiện",
                "hoan_thanh": "Hoàn thành",
                "huy": "Đã hủy",
            }
            
            for row_idx, row in enumerate(rows):
                # Store ID
                item_id = QTableWidgetItem(str(row[0]))
                item_id.setData(Qt.ItemDataRole.UserRole, row[0])
                
                # Ngày
                ngay_du_kien = row[1] or ""
                ngay_formatted = ngay_du_kien[:10] if ngay_du_kien else "N/A"
                item_ngay = QTableWidgetItem(ngay_formatted)
                
                # Giờ
                gio = ngay_du_kien[11:16] if len(ngay_du_kien) > 16 else "08:00"
                item_gio = QTableWidgetItem(gio)
                
                # Khách hàng
                self._list_table.setItem(row_idx, 0, item_ngay)
                self._list_table.setItem(row_idx, 1, item_gio)
                self._list_table.setItem(row_idx, 2, QTableWidgetItem(row[5] or "N/A"))
                
                # Xe
                xe_info = f"{row[7]} {row[8]} - {row[9]}" if row[7] else "N/A"
                self._list_table.setItem(row_idx, 3, QTableWidgetItem(xe_info))
                
                # Nội dung
                self._list_table.setItem(row_idx, 4, QTableWidgetItem(row[2] or "-"))
                
                # Trạng thái
                status = row[3]
                status_text_label = status_labels.get(status, status)
                item_status = QTableWidgetItem(status_text_label)
                color_hex = status_colors.get(status, "#8e8e93")
                item_status.setBackground(QColor(color_hex))
                item_status.setForeground(QColor(255, 255, 255))
                self._list_table.setItem(row_idx, 5, item_status)
        
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách bảo dưỡng: {str(e)}")
    
    def _load_data(self):
        """Load data based on current view."""
        if self._current_view == "calendar":
            self._load_schedule_for_date(self._selected_date)
        else:
            self._load_list_view()
    
    def _on_schedule_row_double_clicked(self, row: int, column: int):
        """Handle schedule table row double click."""
        item = self._schedule_table.item(row, 0)
        if item:
            bd_id = item.data(Qt.ItemDataRole.UserRole)
            if bd_id:
                self.edit_maintenance_clicked.emit(bd_id)
    
    def _on_list_row_double_clicked(self, row: int, column: int):
        """Handle list table row double click."""
        item = self._list_table.item(row, 0)
        if item:
            bd_id = item.data(Qt.ItemDataRole.UserRole)
            if bd_id:
                self.edit_maintenance_clicked.emit(bd_id)
    
    def _on_add_clicked(self):
        """Handle add maintenance button click."""
        self.add_maintenance_clicked.emit()
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()