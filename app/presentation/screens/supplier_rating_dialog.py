"""Supplier rating dialog - S-NCC-01 - Quick rating popup.

Opens from supplier_list_screen "Đánh giá nhanh" button.
Allows rating supplier on 3 criteria (1-5 stars each):
- chat_luong: Quality
- thoi_gian_giao: Delivery time
- gia_ca: Price

References:
- BR-NCC-02: Rating system (3 criteria, 1-5 each)
- BR-NCC-03: avg = (chat_luong + thoi_gian_giao + gia_ca) / 3

UI Tasks: T-G4.4.UI.01 (part of supplier_list)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QMessageBox, QSpinBox, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.application.services.nha_cung_cap_service import NhaCungCapService


class SupplierRatingDialog(QDialog):
    """Dialog for quick supplier rating.

    Signals:
        rating_updated(ncc_id: int, ratings: dict): Rating was successfully updated.
        cancelled(): User cancelled the operation.
    """

    rating_updated = pyqtSignal(int, dict)
    cancelled = pyqtSignal()

    def __init__(self, db_conn, ncc_id: int, parent=None):
        """Initialize supplier rating dialog.

        Args:
            db_conn: sqlite3 database connection.
            ncc_id: Supplier ID to rate.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Đánh giá nhà cung cấp")
        self.setFixedSize(400, 300)
        self._db_conn = db_conn
        self._ncc_id = ncc_id
        self._ncc_service = NhaCungCapService(db_conn)

        self._setup_ui()
        self._load_current_ratings()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Title
        title = QLabel("Đánh giá nhà cung cấp")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Rating group
        rating_group = QGroupBox("Đánh giá (1-5 sao)")
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
        rating_layout.setLabelWidth(160)
        rating_layout.setHorizontalSpacing(16)
        rating_layout.setVerticalSpacing(12)

        # Chat luong
        cl_layout = QHBoxLayout()
        self._cl_spin = QSpinBox()
        self._cl_spin.setRange(1, 5)
        self._cl_spin.setValue(5)
        self._cl_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 80px;
                background: white;
            }
        """)
        cl_layout.addWidget(self._cl_spin)
        cl_layout.addWidget(QLabel("★ Chất lượng sản phẩm"))
        cl_layout.addStretch()
        rating_layout.addRow("Chất lượng sản phẩm:", self._cl_spin)

        # Thoi gian giao
        self._tg_spin = QSpinBox()
        self._tg_spin.setRange(1, 5)
        self._tg_spin.setValue(5)
        self._tg_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 80px;
                background: white;
            }
        """)
        rating_layout.addRow("Thời gian giao hàng:", self._tg_spin)

        # Gia ca
        self._gc_spin = QSpinBox()
        self._gc_spin.setRange(1, 5)
        self._gc_spin.setValue(5)
        self._gc_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 80px;
                background: white;
            }
        """)
        rating_layout.addRow("Giá cả hợp lý:", self._gc_spin)

        layout.addWidget(rating_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Hủy bỏ")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        cancel_btn.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(cancel_btn)

        submit_btn = QPushButton("💾 Lưu đánh giá")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2db14e;
            }
        """)
        submit_btn.clicked.connect(self._on_submit)
        buttons_layout.addWidget(submit_btn)

        layout.addLayout(buttons_layout)

    def _load_current_ratings(self):
        """Load current ratings for the supplier."""
        try:
            ncc = self._ncc_service.get_by_id(self._ncc_id)
            if ncc:
                self._cl_spin.setValue(ncc.get("diem_chat_luong", 5))
                self._tg_spin.setValue(ncc.get("diem_thoi_gian_giao", 5))
                self._gc_spin.setValue(ncc.get("diem_gia_ca", 5))
        except Exception:
            pass  # Use defaults if error

    def _on_cancel(self):
        """Handle cancel button."""
        self.cancelled.emit()
        self.reject()

    def _on_submit(self):
        """Handle submit button."""
        ratings = {
            "chat_luong": self._cl_spin.value(),
            "thoi_gian_giao": self._tg_spin.value(),
            "gia_ca": self._gc_spin.value(),
        }

        try:
            self._ncc_service.add_rating(self._ncc_id, ratings)

            QMessageBox.information(
                self,
                "Thành công",
                "Đánh giá đã được cập nhật!"
            )

            self.rating_updated.emit(self._ncc_id, ratings)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu đánh giá: {str(e)}")