"""Maintenance status dialog - Update status of a maintenance appointment.

Features:
- Show current status with color badge
- Dropdown with only allowed next statuses (from state machine)
- When selecting 'hoan_thanh', show date picker for ngay_thuc_te
- Ok/Cancel buttons

References:
- BR-HM-02: Status flow for bao duong
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QDateEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont


# Status display names and colors
STATUS_LABELS = {
    'cho_xac_nhan':  ('Chờ xác nhận', '#8e8e93'),
    'da_xac_nhan':   ('Đã xác nhận', '#007aff'),
    'dang_thuc_hien': ('Đang thực hiện', '#ff9500'),
    'hoan_thanh':    ('Hoàn thành', '#34c759'),
    'huy':           ('Đã hủy', '#ff3b30'),
}


class MaintenanceStatusDialog(QDialog):
    """Dialog for updating maintenance status."""

    def __init__(
        self,
        current_status: str,
        allowed_transitions: list,
        parent=None
    ):
        """Initialize status dialog.

        Args:
            current_status: Current status code.
            allowed_transitions: List of allowed next status codes.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._current_status = current_status
        self._allowed_transitions = allowed_transitions

        self.setWindowTitle("Cập nhật trạng thái")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { font-size: 14px; color: #1d1d1f; }
        """)

        self._setup_ui()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Current status display
        current_label, current_color = STATUS_LABELS.get(
            self._current_status, (self._current_status, '#8e8e93')
        )

        current_group = QGroupBox("Trạng thái hiện tại")
        current_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                padding: 8px;
            }
        """)
        current_layout = QHBoxLayout(current_group)
        status_badge = QLabel(f"<span style='background:{current_color}; color:white; padding:4px 12px; border-radius:4px; font-size:14px;'>{current_label}</span>")
        status_badge.setStyleSheet("padding: 4px;")
        current_layout.addWidget(status_badge)
        current_layout.addStretch()
        layout.addWidget(current_group)

        # New status selection
        new_label, new_color = STATUS_LABELS.get(
            self._allowed_transitions[0] if self._allowed_transitions else '',
            ('', '#8e8e93')
        )

        new_group = QGroupBox("Trạng thái mới")
        new_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                padding: 8px;
            }
        """)
        new_layout = QVBoxLayout(new_group)

        # Status dropdown
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Chuyển sang:"))
        self._status_combo = QComboBox()
        self._status_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 180px;
                background: white;
                font-size: 14px;
            }
        """)
        for st in self._allowed_transitions:
            label, color = STATUS_LABELS.get(st, (st, '#8e8e93'))
            self._status_combo.addItem(label, st)
        self._status_combo.currentIndexChanged.connect(self._on_status_changed)
        status_row.addWidget(self._status_combo)
        status_row.addStretch()
        new_layout.addLayout(status_row)

        # ngay_thuc_te (completion date) - only visible when hoan_thanh selected
        self._date_label = QLabel("Ngày hoàn thành thực tế:")
        self._date_edit = QDateEdit()
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setStyleSheet("""
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                min-width: 140px;
                background: white;
            }
        """)
        date_row = QHBoxLayout()
        date_row.addWidget(self._date_label)
        date_row.addWidget(self._date_edit)
        date_row.addStretch()
        new_layout.addLayout(date_row)

        self._date_label.setVisible(False)
        self._date_edit.setVisible(False)

        layout.addWidget(new_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._ok_btn = QPushButton("Xác nhận")
        self._ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #0055aa; }
        """)
        self._ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._ok_btn)

        self._cancel_btn = QPushButton("Huỷ")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 10px 24px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #e5e5ea; }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        layout.addLayout(btn_layout)

    def _on_status_changed(self):
        """Handle status combo change."""
        st = self._status_combo.currentData()
        is_complete = (st == 'hoan_thanh')
        self._date_label.setVisible(is_complete)
        self._date_edit.setVisible(is_complete)

    def get_values(self):
        """Get selected status and completion date.

        Returns:
            Tuple of (new_status: str, ngay_thuc_te: str or None)
        """
        st = self._status_combo.currentData()
        ngay_thuc_te = None
        if st == 'hoan_thanh':
            ngay_thuc_te = self._date_edit.date().toString("yyyy-MM-dd")
        return st, ngay_thuc_te