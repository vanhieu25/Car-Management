"""Main entry point for Car Management application."""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget


def create_main_window() -> QMainWindow:
    """Create and configure the main application window."""
    window = QMainWindow()
    window.setWindowTitle("Car Management")
    window.resize(1280, 720)

    # Central widget with placeholder content
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    layout.addWidget(
        QLabel("Car Management Application - Ready", alignment=Qt.AlignmentFlag.AlignCenter)
    )
    window.setCentralWidget(central_widget)

    return window


def main() -> int:
    """Application entry point."""
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())