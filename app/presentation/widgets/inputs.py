"""Custom input widgets with inline editing support."""

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
                background-color: transparent;
            }
            QLabel:hover {
                background-color: #f0f0f5;
                border: 1px solid #d2d2d7;
            }
        """)
        self._display.setCursor(Qt.CursorShape.PointingHandCursor)

        # Edit line edit (hidden initially)
        self._editor = QLineEdit()
        self._editor.setMinimumHeight(36)
        self._editor.setMinimumWidth(100)
        self._editor.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._editor.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #0066cc;
                border-radius: 6px;
                font-size: 14px;
                color: #1d1d1f;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #0066cc;
            }
        """)
        self._editor.setVisible(False)

        # Validator for editor
        if self._is_float:
            self._validator = QDoubleValidator(self._minimum, self._maximum, self._decimals)
        else:
            self._validator = QIntValidator(int(self._minimum), int(self._maximum))
        self._editor.setValidator(self._validator)

        layout.addWidget(self._display)
        layout.addWidget(self._editor)

        # Connections
        self._display.mousePressEvent = lambda e: self._start_edit()
        self._editor.editingFinished.connect(self._finish_edit)
        self._editor.keyPressEvent = self._handle_key

        # Wheel event on display
        self._display.wheelEvent = self._handle_wheel

    def _handle_key(self, event):
        """Handle key press in editor."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finish_edit()
        elif event.key() == Qt.Key.Key_Escape:
            self._cancel_edit()
        else:
            self._editor.QLineEdit.keyPressEvent(self._editor, event)

    def _handle_wheel(self, event):
        """Handle mouse wheel scroll to increment/decrement."""
        if self._editing:
            return  # Don't wheel while editing

        # Accept the wheel event
        event.accept()
        delta = event.angleDelta().y()
        if delta > 0:
            self._increment()
        elif delta < 0:
            self._decrement()

    def _increment(self):
        """Increment value by step."""
        new_value = min(self._value + self._step, self._maximum)
        if new_value != self._value:
            self._set_value(new_value)
            self.valueChanged.emit(int(new_value) if not self._is_float else new_value)

    def _decrement(self):
        """Decrement value by step."""
        new_value = max(self._value - self._step, self._minimum)
        if new_value != self._value:
            self._set_value(new_value)
            self.valueChanged.emit(int(new_value) if not self._is_float else new_value)

    def _start_edit(self):
        """Enter edit mode."""
        if self._editing:
            return
        self._editing = True
        self._original_value = self._value

        # Set editor text (raw, no formatting)
        if self._is_float:
            editor_text = f"{self._value:.{self._decimals}f}"
        else:
            editor_text = str(int(self._value))

        self._editor.setText(editor_text)
        self._editor.setVisible(True)
        self._display.setVisible(False)
        self._editor.setFocus()
        self._editor.selectAll()

    def _finish_edit(self):
        """Finish editing and save value."""
        if not self._editing:
            return
        self._editing = False

        text = self._editor.text().strip()
        if not text:
            text = str(self._original_value)

        try:
            if self._is_float:
                val = float(text)
            else:
                val = int(text)

            # Clamp to range
            val = max(self._minimum, min(val, self._maximum))
            self._set_value(val)
            self.valueChanged.emit(int(val) if not self._is_float else val)
        except ValueError:
            pass

        self._editor.setVisible(False)
        self._display.setVisible(True)
        self._update_display()

    def _cancel_edit(self):
        """Cancel editing and revert to original value."""
        if not self._editing:
            return
        self._editing = False
        self._value = self._original_value
        self._editor.setVisible(False)
        self._display.setVisible(True)
        self._update_display()

    def _set_value(self, value: float):
        """Set the value internally and update display."""
        self._value = float(value)
        self._update_display()

    def _update_display(self):
        """Update the display label with formatted value and suffix."""
        if self._is_float:
            formatted = f"{self._value:,.{self._decimals}f}"
        else:
            formatted = f"{int(self._value):,}"

        # Remove trailing zeros for floats
        if self._is_float and self._decimals > 0:
            formatted = formatted.rstrip('0').rstrip('.')

        # Add suffix if any
        if self._suffix:
            text = f"{formatted} {self._suffix}"
        else:
            text = formatted

        self._display.setText(text)

    def value(self) -> float:
        """Return the current numeric value."""
        if self._is_float:
            return float(self._value)
        return int(self._value)

    def setValue(self, value: float):
        """Set the numeric value."""
        self._set_value(max(self._minimum, min(float(value), self._maximum)))

    def setRange(self, minimum: float, maximum: float):
        """Set the min/max range."""
        self._minimum = float(minimum)
        self._maximum = float(maximum)
        self._validator.setBottom(self._minimum)
        self._validator.setTop(self._maximum)
        # Clamp current value
        self._set_value(max(self._minimum, min(self._value, self._maximum)))

    def setReadOnly(self, read_only: bool):
        """Set read-only state (disables editing)."""
        self._display.setEnabled(not read_only)
        if read_only and self._editing:
            self._cancel_edit()

    def setEnabled(self, enabled: bool):
        """Set enabled state."""
        super().setEnabled(enabled)
        self._display.setEnabled(enabled)
        if not enabled:
            self._display.setStyleSheet("""
                QLabel {
                    padding: 8px 12px;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    font-size: 14px;
                    color: #8e8e93;
                    background-color: #f2f2f7;
                }
            """)
        else:
            self._display.setStyleSheet("""
                QLabel {
                    padding: 8px 12px;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    font-size: 14px;
                    color: #1d1d1f;
                    background-color: transparent;
                }
                QLabel:hover {
                    background-color: #f0f0f5;
                    border: 1px solid #d2d2d7;
                }
            """)

    def event(self, event):
        """Handle events for child widget focus."""
        if event.type() == QEvent.Type.FocusOut and self._editing:
            # Finish edit when clicking outside
            self._finish_edit()
        return super().event(event)
