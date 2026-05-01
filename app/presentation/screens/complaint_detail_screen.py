"""Complaint detail screen - S-KN-02 - View and process complaint.

Features:
- Tab: Nội dung (view details)
- Tab: Phân công (A-01 only) — assign to NV
- Tab: Cập nhật trạng thái — update status with ly_do (BR-KN-05)
- Tab: Đóng — close with satisfaction rating (BR-KN-04)

References:
- BR-KN-02: Only A-01 can assign
- BR-KN-04: Satisfaction rating 1-5 required before closing
- BR-KN-05: ly_do required when updating status
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QTextEdit, QComboBox,
    QHeaderView, QAbstractItemView, QMessageBox, QGroupBox,
    QTabWidget, QLineEdit, QFormLayout, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QFont

from app.application.services.khieu_nai_service import (
    KhieuNaiService, KhieuNaiUpdateData,
    KhieuNaiNotFoundError, ValidationError
)
from app.application.services.nhan_vien_service import NhanVienService
from app.application.services.session import CurrentSession


MUC_DO_LABELS = {
    "thap": "Thấp",
    "trung_binh": "Trung bình",
    "cao": "Cao",
}
TRANG_THAI_LABELS = {
    "moi": "Mới",
    "dang_xu_ly": "Đang xử lý",
    "da_giai_quyet": "Đã giải quyết",
    "da_dong": "Đã đóng",
}
NGUON_GOC_LABELS = {
    "chat_luong_xe": "Chất lượng xe",
    "dich_vu": "Dịch vụ",
    "bao_hanh": "Bảo hành",
    "khac": "Khác",
}


class ComplaintDetailScreen(QWidget):
    """Complaint detail screen - S-KN-02.

    Signals:
        back_clicked: User wants to go back to list.
        closed: Complaint was closed.
    """

    back_clicked = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, kn_id: int, parent=None):
        """Initialize complaint detail screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            kn_id: Complaint ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._service = KhieuNaiService(db_conn)
        self._nv_service = NhanVienService(db_conn)
        self._kn_id = kn_id

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header with back button
        header_layout = QHBoxLayout()
        self._btn_back = QPushButton("← Quay lại")
        self._btn_back.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #e8e8ed; }
        """)
        self._btn_back.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(self._btn_back)

        self._title_label = QLabel("Chi tiết khiếu nại")
        self._title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                border-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #0071e3;
                color: white;
            }
        """)

        # Tab 1: Nội dung
        self._tab_noi_dung = self._create_content_tab()
        self._tabs.addTab(self._tab_noi_dung, "Nội dung")

        # Tab 2: Phân công (A-01 only)
        self._tab_phan_cong = self._create_assign_tab()
        self._tabs.addTab(self._tab_phan_cong, "Phân công")

        # Tab 3: Cập nhật trạng thái
        self._tab_cap_nhat = self._create_status_tab()
        self._tabs.addTab(self._tab_cap_nhat, "Cập nhật trạng thái")

        # Tab 4: Đóng khiếu nại
        self._tab_dong = self._create_close_tab()
        self._tabs.addTab(self._tab_dong, "Đóng khiếu nại")

        main_layout.addWidget(self._tabs)
        self.setLayout(main_layout)

    def _create_content_tab(self) -> QWidget:
        """Create content tab with complaint details."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # Info grid
        grid = QGridLayout()
        grid.setSpacing(8)

        self._info_labels = {}

        # Row 1: Customer, Contract
        grid.addWidget(QLabel("Khách hàng:"), 0, 0)
        self._info_labels['khach_hang'] = QLabel("-")
        grid.addWidget(self._info_labels['khach_hang'], 0, 1)

        grid.addWidget(QLabel("Hợp đồng:"), 0, 2)
        self._info_labels['hop_dong'] = QLabel("-")
        grid.addWidget(self._info_labels['hop_dong'], 0, 3)

        # Row 2: Priority, Status
        grid.addWidget(QLabel("Mức độ:"), 1, 0)
        self._info_labels['muc_do'] = QLabel("-")
        grid.addWidget(self._info_labels['muc_do'], 1, 1)

        grid.addWidget(QLabel("Trạng thái:"), 1, 2)
        self._info_labels['trang_thai'] = QLabel("-")
        grid.addWidget(self._info_labels['trang_thai'], 1, 3)

        # Row 3: Source, NV
        grid.addWidget(QLabel("Nguồn gốc:"), 2, 0)
        self._info_labels['nguon_goc'] = QLabel("-")
        grid.addWidget(self._info_labels['nguon_goc'], 2, 1)

        grid.addWidget(QLabel("NV xử lý:"), 2, 2)
        self._info_labels['nv_xu_ly'] = QLabel("-")
        grid.addWidget(self._info_labels['nv_xu_ly'], 2, 3)

        # Row 4: Dates
        grid.addWidget(QLabel("Ngày tạo:"), 3, 0)
        self._info_labels['ngay_tao'] = QLabel("-")
        grid.addWidget(self._info_labels['ngay_tao'], 3, 1)

        grid.addWidget(QLabel("Ngày xử lý:"), 3, 2)
        self._info_labels['ngay_xu_ly'] = QLabel("-")
        grid.addWidget(self._info_labels['ngay_xu_ly'], 3, 3)

        grid.addWidget(QLabel("Ngày đóng:"), 4, 0)
        self._info_labels['ngay_dong'] = QLabel("-")
        grid.addWidget(self._info_labels['ngay_dong'], 4, 1)

        grid.addWidget(QLabel("Đánh giá HL:"), 4, 2)
        self._info_labels['danh_gia'] = QLabel("-")
        grid.addWidget(self._info_labels['danh_gia'], 4, 3)

        # Title
        grid.addWidget(QLabel("Tiêu đề:"), 5, 0)
        self._info_labels['tieu_de'] = QLabel("-")
        self._info_labels['tieu_de'].setStyleSheet("font-weight: 600;")
        grid.addWidget(self._info_labels['tieu_de'], 5, 1, 1, 3)

        layout.addLayout(grid)

        # Content
        layout.addWidget(QLabel("Nội dung:"))
        self._content_text = QTextEdit()
        self._content_text.setReadOnly(True)
        self._content_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 12px;
                background-color: #f5f5f7;
            }
        """)
        layout.addWidget(self._content_text)

        # History
        layout.addWidget(QLabel("Lý do cập nhật gần nhất:"))
        self._ly_do_text = QTextEdit()
        self._ly_do_text.setReadOnly(True)
        self._ly_do_text.setMaximumHeight(80)
        self._ly_do_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 8px;
                background-color: #fff3cd;
            }
        """)
        layout.addWidget(self._ly_do_text)

        layout.addStretch()
        return tab

    def _create_assign_tab(self) -> QWidget:
        """Create assignment tab (A-01 only)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        self._assign_note = QLabel("Chỉ quản lý (A-01) mới được phân công nhân viên xử lý.")
        self._assign_note.setStyleSheet("color: #86868b; font-size: 12px;")
        layout.addWidget(self._assign_note)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self._assign_nv_combo = QComboBox()
        self._assign_nv_combo.setMinimumWidth(200)
        form_layout.addRow("Nhân viên xử lý:", self._assign_nv_combo)

        self._btn_assign = QPushButton("Phân công")
        self._btn_assign.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #0077ed; }
        """)
        self._btn_assign.clicked.connect(self._on_assign_clicked)
        form_layout.addRow("", self._btn_assign)

        layout.addLayout(form_layout)
        layout.addStretch()
        return tab

    def _create_status_tab(self) -> QWidget:
        """Create status update tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        self._status_note = QLabel("BR-KN-05: Phải ghi rõ lý do khi cập nhật trạng thái.")
        self._status_note.setStyleSheet("color: #dc3545; font-weight: 500; font-size: 12px;")
        layout.addWidget(self._status_note)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self._status_combo = QComboBox()
        self._status_combo.addItems([
            "Mới", "Đang xử lý", "Đã giải quyết"
        ])
        form_layout.addRow("Chuyển sang:", self._status_combo)

        form_layout.addRow("Lý do *:", None)
        self._ly_do_input = QTextEdit()
        self._ly_do_input.setPlaceholderText("Nhập lý do cập nhật trạng thái...")
        self._ly_do_input.setMaximumHeight(80)
        form_layout.addRow("", self._ly_do_input)

        self._btn_update_status = QPushButton("Cập nhật")
        self._btn_update_status.setStyleSheet("""
            QPushButton {
                background-color: #0071e3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #0077ed; }
        """)
        self._btn_update_status.clicked.connect(self._on_update_status_clicked)
        form_layout.addRow("", self._btn_update_status)

        layout.addLayout(form_layout)
        layout.addStretch()
        return tab

    def _create_close_tab(self) -> QWidget:
        """Create close complaint tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        self._close_note = QLabel("BR-KN-04: Bắt buộc đánh giá hài lòng 1-5 sao trước khi đóng khiếu nại.")
        self._close_note.setStyleSheet("color: #dc3545; font-weight: 500; font-size: 12px;")
        layout.addWidget(self._close_note)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Stars rating
        self._stars_layout = QHBoxLayout()
        self._star_buttons = []
        for i in range(1, 6):
            btn = QPushButton(f"{i}⭐")
            btn.setProperty("rating", i)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f7;
                    border: 1px solid #d2d2d7;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 16px;
                }
                QPushButton:hover { background-color: #fff3cd; }
                QPushButton[selected=true] { background-color: #ffc107; }
            """)
            btn.clicked.connect(lambda checked, x=i: self._on_star_selected(x))
            self._star_buttons.append(btn)
            self._stars_layout.addWidget(btn)
        form_layout.addRow("Đánh giá hài lòng *:", self._stars_layout)

        self._selected_rating = 0
        self._rating_label = QLabel("Chưa chọn")
        form_layout.addRow("", self._rating_label)

        self._btn_close = QPushButton("Đóng khiếu nại")
        self._btn_close.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        self._btn_close.clicked.connect(self._on_close_clicked)
        form_layout.addRow("", self._btn_close)

        layout.addLayout(form_layout)
        layout.addStretch()
        return tab

    def _load_data(self):
        """Load complaint data."""
        try:
            kn = self._service.get_by_id(self._kn_id)

            # Update title
            self._title_label.setText(f"Khiếu nại: {kn.get('tieu_de', '')[:50]}")

            # Content tab
            self._info_labels['khach_hang'].setText(
                f"{kn.get('khach_hang_ten', '-')} ({kn.get('khach_hang_sdt', '')})"
            )
            self._info_labels['hop_dong'].setText(kn.get('ma_hop_dong', '-') or '-')
            self._info_labels['muc_do'].setText(MUC_DO_LABELS.get(kn.get('muc_do', ''), '-'))
            self._info_labels['trang_thai'].setText(TRANG_THAI_LABELS.get(kn.get('trang_thai', ''), '-'))
            self._info_labels['nguon_goc'].setText(NGUON_GOC_LABELS.get(kn.get('nguon_goc', ''), '-') or '-')
            self._info_labels['nv_xu_ly'].setText(kn.get('nhan_vien_xu_ly_ten', '-') or '-')
            self._info_labels['ngay_tao'].setText(kn.get('ngay_tao', '')[:10] if kn.get('ngay_tao') else '-')
            self._info_labels['ngay_xu_ly'].setText(kn.get('ngay_xu_ly', '')[:10] if kn.get('ngay_xu_ly') else '-')
            self._info_labels['ngay_dong'].setText(kn.get('ngay_dong', '')[:10] if kn.get('ngay_dong') else '-')
            
            danh_gia = kn.get('danh_gia_hai_long')
            if danh_gia:
                self._info_labels['danh_gia'].setText(f"{danh_gia} ⭐")
            else:
                self._info_labels['danh_gia'].setText("-")

            self._info_labels['tieu_de'].setText(kn.get('tieu_de', '-'))
            self._content_text.setPlainText(kn.get('noi_dung', ''))
            self._ly_do_text.setPlainText(kn.get('ly_do', 'Chưa có cập nhật') or 'Chưa có cập nhật')

            # Assign tab - load staff list
            self._assign_nv_combo.clear()
            nhan_viens = self._nv_service.get_all()
            self._assign_nv_combo.addItem("-- Chọn nhân viên --", None)
            for nv in nhan_viens:
                if nv.get('trang_thai') == 'dang_lam':
                    self._assign_nv_combo.addItem(nv.get('ho_ten', ''), nv.get('id'))

            # Disable tabs based on status
            status = kn.get('trang_thai', 'moi')
            if status == 'da_dong':
                self._tabs.setTabEnabled(1, False)  # Phân công
                self._tabs.setTabEnabled(2, False)  # Cập nhật
                self._tabs.setTabEnabled(3, False)  # Đóng

        except KhieuNaiNotFoundError:
            QMessageBox.warning(self, "Lỗi", "Khiếu nại không tồn tại")
            self.back_clicked.emit()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thông tin: {e}")

    def _on_star_selected(self, rating: int):
        """Handle star rating selection."""
        self._selected_rating = rating
        self._rating_label.setText(f"Đã chọn: {rating} ⭐")

        # Highlight selected stars
        for i, btn in enumerate(self._star_buttons):
            btn.setProperty("selected", i < rating)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_assign_clicked(self):
        """Handle assign button click."""
        nv_id = self._assign_nv_combo.currentData()
        if not nv_id:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn nhân viên xử lý")
            return

        try:
            self._service.assign(self._kn_id, nv_id)
            QMessageBox.information(self, "Thành công", "Đã phân công nhân viên xử lý")
            self._load_data()
        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể phân công: {e}")

    def _on_update_status_clicked(self):
        """Handle status update button click."""
        ly_do = self._ly_do_input.toPlainText().strip()
        if not ly_do:
            QMessageBox.warning(self, "Cảnh báo", "BR-KN-05: Phải ghi rõ lý do khi cập nhật trạng thái")
            return

        status_map = {
            "Mới": "moi",
            "Đang xử lý": "dang_xu_ly",
            "Đã giải quyết": "da_giai_quyet",
        }
        new_status = status_map.get(self._status_combo.currentText())
        if not new_status:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn trạng thái hợp lệ")
            return

        try:
            self._service.update_status(self._kn_id, new_status, ly_do)
            QMessageBox.information(self, "Thành công", "Đã cập nhật trạng thái")
            self._ly_do_input.clear()
            self._load_data()
        except ValidationError as e:
            QMessageBox.warning(self, "Lỗi", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật: {e}")

    def _on_close_clicked(self):
        """Handle close complaint button click."""
        if self._selected_rating == 0:
            QMessageBox.warning(self, "Cảnh báo", "BR-KN-04: Bắt buộc đánh giá hài lòng 1-5 sao trước khi đóng")
            return

        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Đóng khiếu nại với đánh giá {self._selected_rating} sao?\nHành động này không thể hoàn tác.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._service.close(self._kn_id, self._selected_rating)
                QMessageBox.information(self, "Thành công", "Khiếu nại đã được đóng")
                self.closed.emit()
                self.back_clicked.emit()
            except ValidationError as e:
                QMessageBox.warning(self, "Lỗi", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể đóng: {e}")
