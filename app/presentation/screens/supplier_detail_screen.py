"""Supplier detail screen - S-NCC-02 - Supplier details with tabs.

Tabs:
- Thông tin: NCC details (ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email, nguoi_lien_he)
- Lịch sử nhập: table of nhap_kho records
- Đánh giá: form with 3 star inputs (chat_luong, giao_hang, gia)

References:
- BR-NCC-01..06: Supplier management rules
- BR-NCC-02: Rating system

UI Task: T-G4.4.UI.02
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QTabWidget, QMessageBox,
    QFormLayout, QLineEdit, QTextEdit, QGroupBox, QFrame,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.presentation.widgets.inputs import InlineNumericEdit

from app.application.services.nha_cung_cap_service import NhaCungCapService, NotFoundError
from app.application.services.nhap_kho_service import NhapKhoService
from app.application.services.session import CurrentSession


class SupplierDetailScreen(QWidget):
    """Supplier detail screen - S-NCC-02.

    Signals:
        edit_clicked(ncc_id: int): User wants to edit supplier.
        back_clicked(): User wants to go back.
    """

    edit_clicked = pyqtSignal(int)
    back_clicked = pyqtSignal()

    def __init__(self, db_conn, session: CurrentSession, ncc_id: int, parent=None):
        """Initialize supplier detail screen.

        Args:
            db_conn: sqlite3 database connection.
            session: Current user session.
            ncc_id: Supplier ID to display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._db_conn = db_conn
        self._session = session
        self._ncc_id = ncc_id
        self._ncc_service = NhaCungCapService(db_conn)
        self._nhap_kho_service = NhapKhoService(db_conn)

        self._ncc_data = None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with back button
        header_layout = QHBoxLayout()

        self._back_btn = QPushButton("← Quay lại")
        self._back_btn.setStyleSheet("""
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
        self._back_btn.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self._back_btn)

        self._title = QLabel("Chi tiết nhà cung cấp")
        self._title.setStyleSheet("font-size: 24px; font-weight: 600; color: #1d1d1f;")
        header_layout.addWidget(self._title)

        header_layout.addStretch()

        # Edit button (only for A-01, A-02)
        if self._session and self._session.vai_tro_ma in ("admin", "sales"):
            self._edit_btn = QPushButton("✏️ Sửa")
            self._edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #0055aa;
                }
            """)
            self._edit_btn.clicked.connect(self._on_edit_clicked)
            header_layout.addWidget(self._edit_btn)

        layout.addLayout(header_layout)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #0066cc;
                border-bottom: 2px solid #0066cc;
            }
        """)

        # Tab 1: Thông tin
        self._info_tab = self._create_info_tab()
        self._tabs.addTab(self._info_tab, "📋 Thông tin")

        # Tab 2: Lịch sử nhập
        self._history_tab = self._create_history_tab()
        self._tabs.addTab(self._history_tab, "📦 Lịch sử nhập")

        # Tab 3: Đánh giá
        self._rating_tab = self._create_rating_tab()
        self._tabs.addTab(self._rating_tab, "⭐ Đánh giá")

        layout.addWidget(self._tabs)

    def _create_info_tab(self) -> QWidget:
        """Create the info tab widget."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Use a form layout directly as the main layout
        info_form = QFormLayout()
        info_form.setHorizontalSpacing(20)
        info_form.setVerticalSpacing(10)

        # Labels for info fields
        self._info_labels = {
            "ma_ncc": QLabel(),
            "ten_ncc": QLabel(),
            "dia_chi": QLabel(),
            "so_dien_thoai": QLabel(),
            "email": QLabel(),
            "nguoi_lien_he": QLabel(),
            "diem_tong": QLabel(),
            "avg_rating": QLabel(),
        }

        for field, label in self._info_labels.items():
            label.setStyleSheet("font-size: 14px; color: #1d1d1f;")

        rows = [
            ("Mã NCC:", self._info_labels["ma_ncc"]),
            ("Tên NCC:", self._info_labels["ten_ncc"]),
            ("Địa chỉ:", self._info_labels["dia_chi"]),
            ("SĐT:", self._info_labels["so_dien_thoai"]),
            ("Email:", self._info_labels["email"]),
            ("Người liên hệ:", self._info_labels["nguoi_lien_he"]),
            ("Điểm tổng:", self._info_labels["diem_tong"]),
            ("Đánh giá TB:", self._info_labels["avg_rating"]),
        ]

        for label_text, lbl in rows:
            info_form.addRow(label_text, lbl)

        main_layout.addLayout(info_form)
        main_layout.addStretch()

        return widget

    def _create_history_tab(self) -> QWidget:
        """Create the import history tab widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Info label
        info_label = QLabel("Lịch sử nhập kho từ nhà cung cấp này:")
        info_label.setStyleSheet("font-size: 14px; color: #86868b;")
        layout.addWidget(info_label)

        # Table
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels([
            "ID", "Ngày nhập", "NV nhập", "Số items", "Ghi chú"
        ])

        self._history_table.setStyleSheet("""
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
        """)

        self._history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        layout.addWidget(self._history_table)

        return widget

    def _create_rating_tab(self) -> QWidget:
        """Create the rating tab widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Rating display
        rating_group = QGroupBox("Đánh giá hiện tại")
        rating_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }
        """)
        rating_layout = QFormLayout(rating_group)

        self._rating_labels = {
            "chat_luong": QLabel("0 / 5"),
            "thoi_gian_giao": QLabel("0 / 5"),
            "gia_ca": QLabel("0 / 5"),
        }

        rating_rows = [
            ("Chất lượng sản phẩm:", self._rating_labels["chat_luong"]),
            ("Thời gian giao hàng:", self._rating_labels["thoi_gian_giao"]),
            ("Giá cả hợp lý:", self._rating_labels["gia_ca"]),
        ]

        for label_text, label in rating_rows:
            label.setStyleSheet("font-size: 14px; color: #0066cc; font-weight: 500;")
            rating_layout.addRow(label_text, label)

        layout.addWidget(rating_group)

        # Add rating section (for A-01, A-02)
        if self._session and self._session.vai_tro_ma in ("admin", "sales"):
            add_rating_group = QGroupBox("Thêm đánh giá mới")
            add_rating_group.setStyleSheet("""
                QGroupBox {
                    font-weight: 600;
                    font-size: 14px;
                    border: 1px solid #d2d2d7;
                    border-radius: 8px;
                    padding: 16px;
                    margin-top: 8px;
                }
            """)
            add_layout = QVBoxLayout(add_rating_group)

            # Rating buttons row
            rating_btn_layout = QHBoxLayout()
            rating_btn_layout.setSpacing(12)

            # Chat luong
            cl_layout = QHBoxLayout()
            cl_layout.addWidget(QLabel("Chất lượng:"))
            self._cl_spin = InlineNumericEdit(
                value=5,
                minimum=1,
                maximum=5,
                step=1,
                is_float=False,
            )
            cl_layout.addWidget(self._cl_spin)
            cl_layout.addStretch()
            rating_btn_layout.addLayout(cl_layout)

            # Thoi gian giao
            tg_layout = QHBoxLayout()
            tg_layout.addWidget(QLabel("Giao hàng:"))
            self._tg_spin = InlineNumericEdit(
                value=5,
                minimum=1,
                maximum=5,
                step=1,
                is_float=False,
            )
            tg_layout.addWidget(self._tg_spin)
            tg_layout.addStretch()
            rating_btn_layout.addLayout(tg_layout)

            # Gia ca
            gc_layout = QHBoxLayout()
            gc_layout.addWidget(QLabel("Giá cả:"))
            self._gc_spin = InlineNumericEdit(
                value=5,
                minimum=1,
                maximum=5,
                step=1,
                is_float=False,
            )
            gc_layout.addWidget(self._gc_spin)
            gc_layout.addStretch()
            rating_btn_layout.addLayout(gc_layout)

            add_layout.addLayout(rating_btn_layout)

            # Submit button
            self._submit_rating_btn = QPushButton("💾 Cập nhật đánh giá")
            self._submit_rating_btn.setStyleSheet("""
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
            self._submit_rating_btn.clicked.connect(self._on_submit_rating)
            add_layout.addWidget(self._submit_rating_btn, alignment=Qt.AlignmentFlag.AlignRight)

            layout.addWidget(add_rating_group)

        layout.addStretch()

        return widget

    def _load_data(self):
        """Load supplier data."""
        # Add mode - no data to load
        if self._ncc_id is None:
            self._ncc_data = None
            return

        try:
            self._ncc_data = self._ncc_service.get_by_id(self._ncc_id)
            if not self._ncc_data:
                QMessageBox.warning(self, "Lỗi", "Không tìm thấy nhà cung cấp")
                self._on_back_clicked()
                return

            self._update_info_tab()
            self._update_history_tab()
            self._update_rating_tab()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải dữ liệu: {str(e)}")

    def _update_info_tab(self):
        """Update info tab with supplier data."""
        ncc = self._ncc_data

        self._info_labels["ma_ncc"].setText(ncc.get("ma_ncc", "-"))
        self._info_labels["ten_ncc"].setText(ncc.get("ten_ncc", "-"))
        self._info_labels["dia_chi"].setText(ncc.get("dia_chi", "-") or "-")
        self._info_labels["so_dien_thoai"].setText(ncc.get("so_dien_thoai", "-") or "-")
        self._info_labels["email"].setText(ncc.get("email", "-") or "-")
        self._info_labels["nguoi_lien_he"].setText(ncc.get("nguoi_lien_he", "-") or "-")

        diem_tong = ncc.get("diem_tong", 0)
        self._info_labels["diem_tong"].setText(str(diem_tong))

        avg_rating = round(diem_tong / 3, 1) if diem_tong > 0 else 0
        stars = self._render_stars(avg_rating)
        self._info_labels["avg_rating"].setText(stars)

    def _update_history_tab(self):
        """Update history tab with import records."""
        history = self._nhap_kho_service.get_by_ncc(self._ncc_id)

        self._history_table.setRowCount(len(history))

        for row, record in enumerate(history):
            # ID
            self._history_table.setItem(row, 0, QTableWidgetItem(str(record.get("id", ""))))

            # Ngày nhập
            ngay_nhap = record.get("ngay_nhap", "")
            if ngay_nhap:
                ngay_nhap = ngay_nhap[:10]
            self._history_table.setItem(row, 1, QTableWidgetItem(ngay_nhap))

            # NV nhập (we need to lookup)
            self._history_table.setItem(row, 2, QTableWidgetItem(str(record.get("nhan_vien_id", "-"))))

            # Số items
            items = record.get("items", [])
            self._history_table.setItem(row, 3, QTableWidgetItem(str(len(items))))

            # Ghi chú
            self._history_table.setItem(row, 4, QTableWidgetItem(record.get("ghi_chu", "") or ""))

        # Set column widths
        from PyQt6.QtWidgets import QAbstractItemView
        self._history_table.setColumnWidth(0, 50)
        self._history_table.setColumnWidth(1, 120)
        self._history_table.setColumnWidth(3, 80)

    def _update_rating_tab(self):
        """Update rating tab with current ratings."""
        ncc = self._ncc_data

        self._rating_labels["chat_luong"].setText(f"{ncc.get('diem_chat_luong', 0)} / 5")
        self._rating_labels["thoi_gian_giao"].setText(f"{ncc.get('diem_thoi_gian_giao', 0)} / 5")
        self._rating_labels["gia_ca"].setText(f"{ncc.get('diem_gia_ca', 0)} / 5")

    def _render_stars(self, rating: float) -> str:
        """Render star display for rating."""
        full_stars = int(rating)
        half_star = (rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        result = "★" * full_stars
        if half_star:
            result += "½"
        result += "☆" * empty_stars

        return result

    def _on_submit_rating(self):
        """Handle submit rating button click."""
        try:
            ratings = {
                "chat_luong": self._cl_spin.value(),
                "thoi_gian_giao": self._tg_spin.value(),
                "gia_ca": self._gc_spin.value(),
            }

            self._ncc_service.add_rating(self._ncc_id, ratings)

            QMessageBox.information(self, "Thành công", "Đánh giá đã được cập nhật!")

            # Reload data
            self._ncc_data = self._ncc_service.get_by_id(self._ncc_id)
            self._update_rating_tab()
            self._update_info_tab()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật đánh giá: {str(e)}")

    def _on_edit_clicked(self):
        """Handle edit button click."""
        self.edit_clicked.emit(self._ncc_id)

    def _on_back_clicked(self):
        """Handle back button click."""
        self.back_clicked.emit()

    def refresh(self):
        """Refresh the data."""
        self._load_data()