"""Vehicle delete confirmation dialog - BR-UI-04.

Features:
- Confirm dialog for deleting a vehicle
- Reason input field
- BR-XE-02: Cannot delete if vehicle has active contracts
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class VehicleDeleteDialog(QDialog):
    """Dialog for confirming vehicle deletion.
    
    Signals:
        confirmed: User confirmed deletion with optional reason.
    """
    
    confirmed = pyqtSignal(str)  # reason
    
    def __init__(self, ma_xe: str, can_delete: bool = True, parent=None):
        """Initialize delete confirmation dialog.
        
        Args:
            ma_xe: Vehicle code being deleted.
            can_delete: True if deletion is allowed, False if vehicle has active contracts.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._ma_xe = ma_xe
        self._can_delete = can_delete
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI components."""
        self.setWindowTitle("Xác nhận xóa xe")
        self.setMinimumSize(450, 280)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Warning icon and message
        warning_layout = QHBoxLayout()
        warning_icon = QLabel("⚠️")
        warning_icon.setStyleSheet("font-size: 48px;")
        warning_layout.addWidget(warning_icon)
        
        msg_layout = QVBoxLayout()
        msg_layout.setSpacing(4)
        
        title_label = QLabel("Xác nhận xóa xe")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #1d1d1f;")
        msg_layout.addWidget(title_label)
        
        code_label = QLabel(f"Bạn đang xóa xe: <b>{self._ma_xe}</b>")
        code_label.setStyleSheet("font-size: 14px; color: #1d1d1f;")
        msg_layout.addWidget(code_label)
        
        warning_layout.addLayout(msg_layout)
        warning_layout.addStretch()
        
        layout.addLayout(warning_layout)
        
        # Warning message
        if not self._can_delete:
            warning_label = QLabel(
                "⚠️ Xe này không thể xóa vì đang có hợp đồng chưa hủy. "
                "Vui lòng hủy các hợp đồng liên quan trước."
            )
            warning_label.setStyleSheet("""
                color: #ff3b30;
                font-size: 13px;
                background: #fff4f4;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #ff3b30;
            """)
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)
        else:
            warning_label = QLabel(
                "⚠️ Hành động này không thể hoàn tác. Xe sẽ bị xóa vĩnh viễn khỏi hệ thống."
            )
            warning_label.setStyleSheet("color: #ff3b30; font-size: 13px;")
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)
        
        # Reason input
        reason_label = QLabel("Lý do xóa (tùy chọn):")
        reason_label.setStyleSheet("font-size: 14px; color: #1d1d1f;")
        layout.addWidget(reason_label)
        
        self._reason_input = QLineEdit()
        self._reason_input.setPlaceholderText("Nhập lý do xóa xe (nếu có)...")
        self._reason_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #ff3b30;
            }
        """)
        layout.addWidget(self._reason_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._cancel_btn = QPushButton("Hủy bỏ")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f7;
                color: #1d1d1f;
                border: 1px solid #d2d2d7;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)
        
        self._delete_btn = QPushButton("🗑️ Xóa")
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e0342c;
            }
            QPushButton:disabled {
                background-color: #c7c7cc;
                color: #8e8e93;
            }
        """)
        self._delete_btn.setEnabled(self._can_delete)
        self._delete_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self._delete_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_confirm(self):
        """Handle confirm delete button click."""
        reason = self._reason_input.text().strip()
        self.confirmed.emit(reason)
        self.accept()
