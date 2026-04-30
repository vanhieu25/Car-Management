"""Dialog and notification widgets."""

import time
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGraphicsOpacityEffect,
    QWidget,
)


class ToastDialog(QDialog):
    """Toast notification dialog that auto-dismisses.
    
    Implements BR-UI-05: Show toast notification for 3 seconds on success.
    """
    
    def __init__(self, message: str, parent=None, duration_ms: int = 3000):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._duration_ms = duration_ms
        
        # Main container
        container = QWidget(self)
        container.setStyleSheet("""
            QWidget#toast_container {
                background-color: #2C2C2E;
                border-radius: 12px;
                padding: 12px 20px;
            }
        """)
        container.setObjectName("toast_container")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)
        
        inner_layout = QHBoxLayout(container)
        inner_layout.setSpacing(12)
        
        # Message label
        msg_label = QLabel(message, container)
        msg_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: 500;
        """)
        msg_label.setWordWrap(True)
        inner_layout.addWidget(msg_label, 1)
        
        # Success indicator
        check_label = QLabel("✓", container)
        check_label.setStyleSheet("""
            color: #34C759;
            font-size: 18px;
            font-weight: bold;
        """)
        inner_layout.addWidget(check_label)
        
        # Opacity animation
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)
        
        # Auto dismiss timer
        QTimer.singleShot(100, self._fade_in)
        QTimer.singleShot(duration_ms, self._fade_out)
    
    def _fade_in(self):
        """Fade in animation."""
        self.show()
        for i in range(0, 101, 10):
            self._opacity.setOpacity(i / 100.0)
            QTimer.singleShot(i * 2, lambda: None)
            time.sleep(0.01)
        self._opacity.setOpacity(1.0)
    
    def _fade_out(self):
        """Fade out animation and close."""
        for i in range(100, -1, -10):
            self._opacity.setOpacity(i / 100.0)
            QTimer.singleShot((100 - i) * 2, lambda: None)
            time.sleep(0.01)
        self.close()
    
    @staticmethod
    def show_success(message: str, parent=None, duration_ms: int = 3000):
        """Show a success toast notification."""
        toast = ToastDialog(message, parent, duration_ms)
        toast.exec()


class ConfirmDialog(QDialog):
    """Confirmation dialog with title, message, and action buttons.
    
    Used for destructive actions per BR-UI-04.
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Xác nhận",
        cancel_text: str = "Hủy",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title_label = QLabel(title, self)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #1C1C1E;
        """)
        layout.addWidget(title_label)
        
        # Message
        msg_label = QLabel(message, self)
        msg_label.setStyleSheet("""
            font-size: 14px;
            color: #3C3C43;
        """)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton(cancel_text, self)
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F7;
                color: #007AFF;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E5E5EA;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        confirm_btn = QPushButton(confirm_text, self)
        confirm_btn.setMinimumHeight(44)
        confirm_btn.setStyleSheet("""
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
        confirm_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)
    
    @staticmethod
    def confirm(
        title: str,
        message: str,
        confirm_text: str = "Xác nhận",
        cancel_text: str = "Hủy",
        parent=None,
    ) -> bool:
        """Show confirmation dialog and return True if confirmed."""
        dialog = ConfirmDialog(title, message, confirm_text, cancel_text, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted


class ErrorDialog(QDialog):
    """Error message dialog."""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Error icon and title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("⚠️", self)
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title, self)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #1C1C1E;
        """)
        header_layout.addWidget(title_label, 1)
        layout.addLayout(header_layout)
        
        # Message
        msg_label = QLabel(message, self)
        msg_label.setStyleSheet("""
            font-size: 14px;
            color: #3C3C43;
        """)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label, 1)
        
        # OK button
        ok_btn = QPushButton("Đóng", self)
        ok_btn.setMinimumHeight(44)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
    
    @staticmethod
    def show_error(title: str, message: str, parent=None):
        """Show error dialog."""
        dialog = ErrorDialog(title, message, parent)
        dialog.exec()
