"""Reusable input widgets with validation."""

import re
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLineEdit,
    QWidget,
    QHBoxLayout,
    QLabel,
    QGraphicsOpacityEffect,
)


class PasswordLineEdit(QLineEdit):
    """Password input field with show/hide toggle.
    
    Implements BR-SEC-03: Never show plain text password in UI.
    """
    
    def __init__(self, placeholder: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
            }
            QLineEdit:disabled {
                background-color: #F2F2F7;
                color: #8E8E93;
            }
        """)
        
        # Store for password retrieval
        self._password_text = ""
    
    def setText(self, text: str) -> None:
        """Store password but display dots."""
        self._password_text = text
        super().setText("•" * len(text))
    
    def text(self) -> str:
        """Return actual password text."""
        return self._password_text
    
    def keyPressEvent(self, event):
        """Handle key press to update password."""
        super().keyPressEvent(event)
        # Keep track of actual password
        if event.text() and not self.isEchoing():
            self._password_text = self.text()
        elif event.text():
            # Handle backspace specially
            if event.key() == 0x01000003:  # Backspace
                self._password_text = self._password_text[:-1]


class ValidatedLineEdit(QLineEdit):
    """Text input with real-time validation feedback.
    
    Shows error message below input when validation fails.
    """
    
    validation_changed = pyqtSignal(bool, str)  # is_valid, error_message
    
    def __init__(
        self,
        placeholder: str = "",
        validator=None,  # Callable that returns (is_valid, error_message)
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self._validator = validator
        self._is_valid = True
        self._error_message = ""
        
        self.textChanged.connect(self._on_text_changed)
        self.setStyleSheet("""
            ValidatedLineEdit {
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                background-color: white;
            }
            ValidatedLineEdit:focus {
                border: 2px solid #007AFF;
            }
            ValidatedLineEdit:disabled {
                background-color: #F2F2F7;
                color: #8E8E93;
            }
            ValidatedLineEdit[validationState="valid"] {
                border: 1px solid #34C759;
            }
            ValidatedLineEdit[validationState="invalid"] {
                border: 1px solid #FF3B30;
            }
        """)
    
    def _on_text_changed(self, text: str):
        """Handle text change for validation."""
        if self._validator:
            is_valid, error_msg = self._validator(text)
            self._is_valid = is_valid
            self._error_message = error_msg or ""
            
            # Update stylesheet using property
            if is_valid:
                self.setProperty("validationState", "valid")
            else:
                self.setProperty("validationState", "invalid")
            self.style().unpolish(self)
            self.style().polish(self)
            
            self.validation_changed.emit(is_valid, self._error_message)
    
    def is_valid(self) -> bool:
        """Return current validation state."""
        return self._is_valid
    
    def error_message(self) -> str:
        """Return current error message."""
        return self._error_message


class StrengthIndicator(QWidget):
    """Password strength indicator widget.
    
    Shows visual feedback on password strength (0-100 score).
    Used in change password dialog per BR-SEC-02.
    """
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._score = 0
        self.setMinimumHeight(8)
        self.setMaximumHeight(12)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F2F2F7;
                border-radius: 4px;
            }
        """)
    
    def set_score(self, score: int):
        """Update strength score (0-100).
        
        Args:
            score: Password strength score.
        """
        self._score = max(0, min(100, score))
        self.update()
    
    def paintEvent(self, event):
        """Paint the strength bar."""
        from PyQt6.QtWidgets import QStylePainter
        from PyQt6.QtGui import QColor, QBrush, QPainter, QRect
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#F2F2F7"))
        
        # Calculate width based on score
        fill_width = int(self.width() * self._score / 100)
        if fill_width > 0:
            # Color based on score
            if self._score < 40:
                color = QColor("#FF3B30")  # Red - weak
            elif self._score < 70:
                color = QColor("#FF9500")  # Orange - medium
            else:
                color = QColor("#34C759")  # Green - strong
            
            painter.fillRect(0, 0, fill_width, self.height(), color)
        
        painter.end()
