"""Employee list screen - S-NV-01 - Employee listing with search and filters.

Features:
- SearchBar with keyword search (username, ho_ten)
- Table with columns: username, ho_ten, email, vai_tro, trang_thai, created_at
- Only visible to A-01 (admin role)
- Buttons: Thêm, Khoá, Mở khoá
- Pagination: 50 rows/page (default)
- Lock/Unlock confirmation dialog with reason field

References:
- BR-NV-01..08: Employee management rules
- BR-SEC-05: Account lockout
"""

from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QDialog, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.application.services.nhan_vien_service import (
    NhanVienService, NhanVienSearchResult, NhanVienNotFoundError,
    CannotLockAdminError, DuplicateUsernameError, DuplicateEmailError,
    ValidationError as NVValidationError
)
from app.application.services.session import CurrentSession
from app.domain.entities import NhanVien, VaiTro


PAGE_SIZE = 50


class LockConfirmDialog(QDialog):
    """Dialog for confirming employee lock with reason field."""
    
    def __init__(self, nhan_vien: NhanVien, parent=None):
        """Initialize lock confirm dialog.
        
        Args:
            nhan_vien: NhanVien to lock.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._nhan_vien = nhan_vien
        self.setWindowTitle(f"Khoá tài khoản - {nhan_vien.ho_ten}")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog {
                background-color: #F2F2F7;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header warning
        warning_label = QLabel(
            f"⚠️ Bạn có chắc muốn khoá nhân viên này?\n\n"
            f"Tài khoản: {self._nhan_vien.username}\n"
            f"Họ tên: {self._nhan_vien.ho_ten}",
            self
        )
        warning_label.setStyleSheet("""
            font-size: 14px;
            color: #1C1C1E;
            padding: 12px;
            background-color: #FFF9E6;
            border-radius: 8px;
        """)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Reason field
        reason_label = QLabel("Lý do khoá (*):", self)
        reason_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #3C3C43;")
        layout.addWidget(reason_label)
        
        self._reason_input = QTextEdit(self)
        self._reason_input.setPlaceholderText("Nhập lý do khoá tài khoản...")
        self._reason_input.setMinimumHeight(100)
        self._reason_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #D1D1D6;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #007AFF;
            }
        """)
        layout.addWidget(self._reason_input)
        
        # Note
        note_label = QLabel(
            "Tài khoản bị khoá sẽ không thể đăng nhập vào hệ thống.",
            self
        )
        note_label.setStyleSheet("font-size: 12px; color: #8E8E93;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Huỷ bỏ", self)
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F7;
                color: #1C1C1E;
                border: 1px solid #D1D1D6;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E5E5EA;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self._confirm_btn = QPushButton("🔒 Khoá tài khoản", self)
        self._confirm_btn.setMinimumHeight(44)
        self._confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        self._confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self._confirm_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_confirm(self):
        """Handle confirm button click."""
        reason = self._reason_input.toPlainText().strip()
        if not reason:
            QMessageBox.warning(
                self,
                "Thiếu lý do",
                "Vui lòng nhập lý do khoá tài khoản."
            )
            return
        self.accept()
    
    def get_reason(self) -> str:
        """Get entered reason."""
        return self._reason_input.toPlainText().strip()


class EmployeeListScreen(QWidget):
    """Employee list screen - S-NV-01.
    
    Signals:
        add_employee_clicked: User clicked add employee button.
        view_employee_clicked(nhan_vien_id: int): User wants to view employee details.
    """
    
    add_employee_clicked = pyqtSignal()
    view_employee_clicked = pyqtSignal(int)
    
    def __init__(self, db_conn, session: CurrentSession, parent=None):
        """Initialize employee list screen.
        
        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._nv_service = NhanVienService(db_conn, session)
        
        self._current_page = 1
        self._total_pages = 1
        self._current_result: Optional[NhanVienSearchResult] = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Quản lý nhân viên")
        title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add employee button (only for A-01)
        if self._session and self._session.vai_tro_ma == "A-01":
            self._add_btn = QPushButton("➕ Thêm nhân viên")
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
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo username, họ tên...")
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
        
        # Data table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Username", "Họ tên", "Email", "Vai trò", "Trạng thái"
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
        
        # Action buttons (only for A-01)
        if self._session and self._session.vai_tro_ma == "A-01":
            action_layout = QHBoxLayout()
            
            self._lock_btn = QPushButton("🔒 Khoá")
            self._lock_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff9500;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #cc7700;
                }
            """)
            self._lock_btn.clicked.connect(self._on_lock_clicked)
            action_layout.addWidget(self._lock_btn)
            
            self._unlock_btn = QPushButton("🔓 Mở khoá")
            self._unlock_btn.setStyleSheet("""
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
                    background-color: #0055bb;
                }
            """)
            self._unlock_btn.clicked.connect(self._on_unlock_clicked)
            action_layout.addWidget(self._unlock_btn)
            
            action_layout.addStretch()
            
            layout.addLayout(action_layout)
        
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
        
        self._total_label = QLabel("Tổng: 0 nhân viên")
        self._total_label.setStyleSheet("font-size: 14px; color: #86868b; margin-left: 16px;")
        pagination_layout.addWidget(self._total_label)
        
        layout.addLayout(pagination_layout)
    
    def _load_data(self):
        """Load employee data based on filters."""
        keyword = self._search_input.text().strip() if self._search_input.text().strip() else None
        
        try:
            result = self._nv_service.search(
                keyword=keyword,
                page=self._current_page,
                page_size=PAGE_SIZE,
            )
            
            self._current_result = result
            self._total_pages = result.total_pages
            
            self._populate_table(result.items)
            
            self._page_label.setText(f"Trang {self._current_page} / {self._total_pages}")
            self._total_label.setText(f"Tổng: {result.total} nhân viên")
            self._prev_btn.setEnabled(self._current_page > 1)
            self._next_btn.setEnabled(self._current_page < self._total_pages)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")
    
    def _populate_table(self, items: List[NhanVien]):
        """Populate table with employee data.
        
        Args:
            items: List of NhanVien entities.
        """
        self._table.setRowCount(len(items))
        
        # Role labels
        role_labels = {
            1: ("Admin", "#FF3B30"),
            2: ("Sales", "#007aff"),
            3: ("Kỹ thuật BH", "#34c759"),
        }
        
        for row, nv in enumerate(items):
            # ID
            item_id = QTableWidgetItem(str(nv.id))
            self._table.setItem(row, 0, item_id)
            
            # Username
            self._table.setItem(row, 1, QTableWidgetItem(nv.username))
            
            # Họ tên
            self._table.setItem(row, 2, QTableWidgetItem(nv.ho_ten))
            
            # Email
            self._table.setItem(row, 3, QTableWidgetItem(nv.email or "-"))
            
            # Vai trò
            role_text, role_color = role_labels.get(nv.vai_tro_id, ("N/A", "#8e8e93"))
            item_role = QTableWidgetItem(role_text)
            item_role.setBackground(QColor(role_color))
            item_role.setForeground(QColor(255, 255, 255))
            self._table.setItem(row, 4, item_role)
            
            # Trạng thái
            if nv.trang_thai == "active":
                status_text = "Hoạt động"
                status_color = "#34c759"
            else:
                status_text = "Bị khoá"
                status_color = "#ff3b30"
            
            item_status = QTableWidgetItem(status_text)
            item_status.setBackground(QColor(status_color))
            item_status.setForeground(QColor(255, 255, 255))
            self._table.setItem(row, 5, item_status)
            
            # Store ID for later use
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, nv.id)
        
        # Set column widths
        self._table.setColumnWidth(0, 50)   # ID
        self._table.setColumnWidth(1, 120)  # Username
        self._table.setColumnWidth(3, 200)  # Email
        self._table.setColumnWidth(4, 100)  # Vai trò
        self._table.setColumnWidth(5, 100)  # Trạng thái
    
    def _get_selected_id(self) -> int:
        """Get selected employee ID from table.
        
        Returns:
            Employee ID or -1 if none selected.
        """
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return -1
        row = selected_rows[0].row()
        item = self._table.item(row, 0)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return -1
    
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
            nhan_vien_id = item.data(Qt.ItemDataRole.UserRole)
            if nhan_vien_id:
                self.view_employee_clicked.emit(nhan_vien_id)
    
    def _on_add_clicked(self):
        """Handle add employee button click."""
        self.add_employee_clicked.emit()
    
    def _on_lock_clicked(self):
        """Handle lock button click."""
        nhan_vien_id = self._get_selected_id()
        if nhan_vien_id < 0:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn nhân viên cần khoá.")
            return
        
        nv = self._nv_service.get_by_id(nhan_vien_id)
        if not nv:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy nhân viên.")
            return
        
        # Show confirm dialog
        dialog = LockConfirmDialog(nv, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        reason = dialog.get_reason()
        
        try:
            self._nv_service.lock(nhan_vien_id, reason)
            QMessageBox.information(
                self,
                "Thành công",
                f"Đã khoá tài khoản nhân viên {nv.ho_ten}"
            )
            self._load_data()
        except CannotLockAdminError as e:
            QMessageBox.warning(self, "Không thể khoá", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể khoá: {str(e)}")
    
    def _on_unlock_clicked(self):
        """Handle unlock button click."""
        nhan_vien_id = self._get_selected_id()
        if nhan_vien_id < 0:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn nhân viên cần mở khoá.")
            return
        
        nv = self._nv_service.get_by_id(nhan_vien_id)
        if not nv:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy nhân viên.")
            return
        
        reply = QMessageBox.question(
            self,
            "Xác nhận mở khoá",
            f"Bạn có chắc muốn mở khoá tài khoản của {nv.ho_ten}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self._nv_service.unlock(nhan_vien_id)
            QMessageBox.information(
                self,
                "Thành công",
                f"Đã mở khoá tài khoản nhân viên {nv.ho_ten}"
            )
            self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể mở khoá: {str(e)}")
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
