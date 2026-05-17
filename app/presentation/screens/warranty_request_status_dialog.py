"""Warranty request status dialog - Update status of a warranty request.

Features:
- Show current status with color badge
- Dropdown with only allowed next statuses (from state machine)
- When selecting 'da_hoan_thanh', show chi_phi input
- Ok/Cancel buttons

References:
- BR-BH-05: Request status transitions
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt


# Status display names and colors
STATUS_LABELS = {
    'moi':           ('Mới tạo', '#8e8e93'),
    'dang_xu_ly':    ('Đang xử lý', '#ff9500'),
    'da_hoan_thanh': ('Hoàn thành', '#34c759'),
    'da_dong':       ('Đã đóng', '#ff3b30'),
}


class WarrantyRequestStatusDialog(QDialog):
    """Dialog for updating warranty request status."""

    def __init__(
        self,
        current_status: str,
        allowed_transitions: list,
        current_chi_phi: int = 0,
        parent=None
    ):
        """Initialize status dialog.

        Args:
            current_status: Current status code.
            allowed_transitions: List of allowed next status codes.
            current_chi_phi: Current cost (for display when completing).
            parent: Parent widget.
        """
        super().__init__(parent)
        self._current_status = current_status
        self._allowed_transitions = allowed_transitions
        self._current_chi_phi = current_chi_phi

        self.setWindowTitle("Cập nhật trạng thái yêu cầu BH")
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
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        current_layout = QHBoxLayout(current_group)
        status_badge = QLabel(f"<span style='background:{current_color}; color:white; padding:4px 12px; border-radius:4px; font-size:14px;'>{current_label}</span>")
        status_badge.setStyleSheet("padding: 4px;")
        current_layout.addWidget(status_badge)
        current_layout.addStretch()
        layout.addWidget(current_group)

        # New status selection
        new_group = QGroupBox("Chuyển sang trạng thái mới")
        new_group.setStyleSheet("""
            QGroupBox { font-weight: 600; padding: 8px; }
        """)
        new_layout = QVBoxLayout(new_group)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Trạng thái:"))
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

        # chi_phi input (visible only when da_hoan_thanh)
        self._chi_phi_label = QLabel("Chi phí hoàn thành (VNĐ):")
        self._chi_phi_input = QLineEdit()
        self._chi_phi_input.setPlaceholderText("Nhập chi phí...")
        self._chi_phi_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        if self._current_chi_phi > 0:
            self._chi_phi_input.setText(str(self._current_chi_phi))
        chi_phi_row = QHBoxLayout()
        chi_phi_row.addWidget(self._chi_phi_label)
        chi_phi_row.addWidget(self._chi_phi_input)
        chi_phi_row.addStretch()
        new_layout.addLayout(chi_phi_row)

        self._chi_phi_label.setVisible(False)
        self._chi_phi_input.setVisible(False)

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
        is_complete = (st == 'da_hoan_thanh')
        self._chi_phi_label.setVisible(is_complete)
        self._chi_phi_input.setVisible(is_complete)

    def get_values(self):
        """Get selected status and chi_phi.

        Returns:
            Tuple of (new_status: str, chi_phi: int or None)
        """
        st = self._status_combo.currentData()
        chi_phi = None
        if st == 'da_hoan_thanh':
            text = self._chi_phi_input.text().strip()
            if text:
                try:
                    chi_phi = int(text.replace(",", ""))
                except ValueError:
                    chi_phi = 0
        return st, chi_phi