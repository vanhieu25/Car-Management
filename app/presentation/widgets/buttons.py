"""Reusable button widgets with consistent styling."""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QPushButton, QWidget


class BaseButton(QPushButton):
    """Base button class with common styling."""
    
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setMinimumSize(QSize(120, 40))
        self.setMaximumSize(QSize(200, 50))
        font = QFont("Segoe UI", 10)
        font.setWeight(QFont.Weight.Medium)
        self.setFont(font)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PrimaryButton(BaseButton):
    """Primary action button - pill shaped, accent color.
    
    Used for main actions like "Đăng nhập", "Lưu", "Xác nhận".
    """
    
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setMinimumSize(QSize(150, 44))
        self.setMaximumSize(QSize(300, 50))
        self._apply_stylesheet()
    
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            PrimaryButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            PrimaryButton:hover {
                background-color: #0056CC;
            }
            PrimaryButton:pressed {
                background-color: #004299;
            }
            PrimaryButton:disabled {
                background-color: #B0B0B0;
                color: #666666;
            }
        """)


class SecondaryButton(BaseButton):
    """Secondary action button - outlined style.
    
    Used for secondary actions like "Hủy", "Quay lại".
    """
    
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self._apply_stylesheet()
    
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            SecondaryButton {
                background-color: transparent;
                color: #007AFF;
                border: 2px solid #007AFF;
                border-radius: 22px;
                padding: 8px 24px;
                font-weight: 500;
                font-size: 14px;
            }
            SecondaryButton:hover {
                background-color: #F0F7FF;
            }
            SecondaryButton:pressed {
                background-color: #E0EEFF;
            }
            SecondaryButton:disabled {
                border-color: #B0B0B0;
                color: #B0B0B0;
            }
        """)


class DangerButton(BaseButton):
    """Danger action button - red accent.
    
    Used for destructive actions like "Xóa", "Hủy HĐ".
    Requires confirmation dialog per BR-UI-04.
    """
    
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self._apply_stylesheet()
    
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            DangerButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: 22px;
                padding: 10px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            DangerButton:hover {
                background-color: #D32F2F;
            }
            DangerButton:pressed {
                background-color: #B71C1C;
            }
            DangerButton:disabled {
                background-color: #B0B0B0;
                color: #666666;
            }
        """)
