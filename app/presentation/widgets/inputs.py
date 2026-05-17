"""Reusable input widgets with validation."""

import re
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QIntValidator, QDoubleValidator
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
        from PyQt6.QtGui import QColor, QBrush, QPainter
        from PyQt6.QtCore import QRect
        
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


class InlineNumericEdit(QWidget):
    """Inline numeric editor that looks like text but edits on click.
    
    Features:
    - Displays as plain text (no border/spinners visible)
    - Single click enters edit mode (shows QLineEdit)
    - Mouse wheel scroll increments/decrements value
    - Enter saves, Escape cancels
    - Comma formatting for thousands
    - Optional suffix label (e.g. "đ", "%", "km")
    """

    valueChanged = pyqtSignal((int,), (float,))

    def __init__(
        self,
        value: float = 0,
        minimum: float = 0,
        maximum: float = 9999999999,
        step: float = 1,
        suffix: str = "",
        is_float: bool = False,
        decimals: int = 0,
        parent: QWidget = None,
    ):
        """Initialize inline numeric editor.
        
        Args:
            value: Initial value.
            minimum: Minimum allowed value.
            maximum: Maximum allowed value.
            step: Increment/decrement step for wheel/buttons.
            suffix: Optional suffix displayed after value (e.g. "đ", "%").
            is_float: If True, treat values as floats; otherwise ints.
            decimals: Number of decimal places for float display.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._value = float(value)
        self._minimum = float(minimum)
        self._maximum = float(maximum)
        self._step = float(step)
        self._suffix = suffix
        self._is_float = is_float
        self._decimals = decimals
        self._original_value = self._value
        self._editing = False

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        """Set up the widget layout and style."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Display label (looks like plain text)
        self._display = QLabel()
        self._display.setMinimumHeight(36)
        self._display.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._display.setStyleSheet("""
            QLabel {
                padding: 8px 12px;
                border: 1px solid transparent;
                border-radius: 6px;
                font-size: 14px;
                color: #1d1d1f;
                background: transparent;
            }
            QLabel:hover {
                background: #f5f5f7;
                cursor: text;
            }
        """)
        layout.addWidget(self._display)

        # Edit input (hidden by default)
        self._edit = QLineEdit()
        self._edit.setMinimumHeight(36)
        self._edit.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._edit.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #0066cc;
                border-radius: 6px;
                font-size: 14px;
                color: #1d1d1f;
                background: white;
            }
        """)
        self._edit.setVisible(False)
        layout.addWidget(self._edit)

        # Set up validators
        if self._is_float:
            self._edit.setValidator(QDoubleValidator())
        else:
            self._edit.setValidator(QIntValidator())

        # Event handlers
        self._display.mousePressEvent = self._on_display_clicked
        self._display.wheelEvent = self._on_wheel
        self._edit.keyPressEvent = self._on_edit_keypress
        self._edit.focusOutEvent = self._on_focus_out

    def _on_display_clicked(self, event):
        """Enter edit mode on single click."""
        if not self.isEnabled():
            return
        self._start_edit()

    def _on_wheel(self, event):
        """Increment/decrement value on wheel scroll (when not editing)."""
        if self._editing or not self.isEnabled():
            return
        
        delta = event.angleDelta().y()
        if delta > 0:
            self._increment()
        else:
            self._decrement()
        
        event.accept()

    def _on_edit_keypress(self, event):
        """Handle key presses in edit mode."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._accept_edit()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self._cancel_edit()
            event.accept()
        else:
            QLineEdit.keyPressEvent(self._edit, event)

    def _on_focus_out(self, event):
        """Accept edit when focus is lost."""
        self._accept_edit()
        event.accept()

    def _start_edit(self):
        """Enter edit mode."""
        self._editing = True
        self._original_value = self._value
        
        # Set edit text (no formatting in edit mode)
        if self._is_float:
            self._edit.setText(f"{self._value:.{self._decimals}f}")
        else:
            self._edit.setText(str(int(self._value)))
        
        self._display.setVisible(False)
        self._edit.setVisible(True)
        self._edit.setFocus()
        self._edit.selectAll()

    def _accept_edit(self):
        """Accept the current edit value."""
        if not self._editing:
            return
        
        text = self._edit.text().strip()
        try:
            if self._is_float:
                new_value = float(text)
            else:
                new_value = int(text)
            
            # Clamp to range
            new_value = max(self._minimum, min(self._maximum, new_value))
            
            if self._is_float:
                self._value = float(new_value)
                self.valueChanged.emit(float(new_value))
            else:
                self._value = int(new_value)
                self.valueChanged.emit(int(new_value))
            
            self._update_display()
        except ValueError:
            # Revert on invalid input
            pass
        
        self._editing = False
        self._edit.setVisible(False)
        self._display.setVisible(True)

    def _cancel_edit(self):
        """Cancel edit and revert to original value."""
        if not self._editing:
            return
        
        self._value = self._original_value
        self._update_display()
        self._editing = False
        self._edit.setVisible(False)
        self._display.setVisible(True)

    def _increment(self):
        """Increment value by step."""
        new_value = self._value + self._step
        new_value = max(self._minimum, min(self._maximum, new_value))
        
        if self._is_float:
            self._value = float(new_value)
            self.valueChanged.emit(float(new_value))
        else:
            self._value = int(new_value)
            self.valueChanged.emit(int(new_value))
        
        self._update_display()

    def _decrement(self):
        """Decrement value by step."""
        new_value = self._value - self._step
        new_value = max(self._minimum, min(self._maximum, new_value))
        
        if self._is_float:
            self._value = float(new_value)
            self.valueChanged.emit(float(new_value))
        else:
            self._value = int(new_value)
            self.valueChanged.emit(int(new_value))
        
        self._update_display()

    def _update_display(self):
        """Update the display label with formatted value."""
        if self._is_float:
            formatted = f"{self._value:,.{self._decimals}f}".replace(",", ".")
        else:
            formatted = f"{int(self._value):,}".replace(",", ".")
        
        # Remove trailing zeros after decimal for floats
        if self._is_float and self._decimals > 0:
            formatted = formatted.rstrip("0").rstrip(".")
        
        text = f"{formatted} {self._suffix}".strip()
        self._display.setText(text)

    def value(self):
        """Return current value."""
        if self._is_float:
            return float(self._value)
        return int(self._value)

    def setEnabled(self, enabled: bool):
        """Disable editing when widget is disabled."""
        if not enabled and self._editing:
            self._value = self._original_value
            self._editing = False
            self._edit.setVisible(False)
            self._display.setVisible(True)
        super().setEnabled(enabled)
        self._display.setEnabled(enabled)
        self._edit.setEnabled(enabled)

    def setDisabled(self, disabled: bool):
        """Disable editing when widget is disabled (convenience method)."""
        self.setEnabled(not disabled)

    def event(self, event):
        """Handle focus events - ignore when disabled."""
        if event.type() == QEvent.Type.FocusIn and not self.isEnabled():
            return False
        return super().event(event)

    def setValue(self, value):
        """Set the current value.
        
        Args:
            value: New value to set.
        """
        new_value = max(self._minimum, min(self._maximum, float(value)))
        self._value = new_value
        self._update_display()

    def setRange(self, minimum, maximum):
        """Set the minimum and maximum values.
        
        Args:
            minimum: Minimum allowed value.
            maximum: Maximum allowed value.
        """
        self._minimum = float(minimum)
        self._maximum = float(maximum)
        # Clamp current value to new range
        self._value = max(self._minimum, min(self._maximum, self._value))
        self._update_display()

    def setSuffix(self, suffix: str):
        """Set the suffix label.
        
        Args:
            suffix: Suffix string (e.g. "đ", "%", "km").
        """
        self._suffix = suffix
        self._update_display()

    def setStep(self, step: float):
        """Set the increment/decrement step.
        
        Args:
            step: Step value for wheel changes.
        """
        self._step = float(step)

    def setDecimals(self, decimals: int):
        """Set the number of decimal places.
        
        Args:
            decimals: Number of decimal places.
        """
        self._decimals = decimals
        self._update_display()

    def setReadOnly(self, read_only: bool):
        """Set read-only mode (wheel still works).
        
        Args:
            read_only: If True, disable editing.
        """
        if read_only:
            self._display.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self._display.setCursor(Qt.CursorShape.IBeamCursor)
