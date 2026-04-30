"""StatusBar widget - displays user, time, version, and DB status.

Shows:
- User name and role
- Current time (updated every second)
- Application version
- Database connection status
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QTimer, Qt, QTime
from PyQt6.QtGui import QFont


class StatusBar(QWidget):
    """Status bar widget for the main window.
    
    Displays:
    - User info (left)
    - Current time (center)
    - Version + DB status (right)
    """
    
    def __init__(self, parent=None):
        """Initialize StatusBar widget."""
        super().__init__(parent)
        self._db_connected = True
        self._username = ""
        self._vai_tro = ""
        
        self._setup_ui()
        self._start_timer()
    
    def _setup_ui(self):
        """Set up the UI components."""
        self.setFixedHeight(28)
        self.setStyleSheet(
            "background-color: #f5f5f7; "
            "border-top: 1px solid #e0e0e0; "
            "color: #1d1d1f; "
            "font-size: 12px;"
        )
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)
        
        # Left - User info
        self.user_label = QLabel("")
        self.user_label.setStyleSheet("color: #1d1d1f; font-weight: 500;")
        layout.addWidget(self.user_label, stretch=0)
        
        layout.addStretch()
        
        # Center - Time
        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: #515154;")
        layout.addWidget(self.time_label, stretch=0)
        
        layout.addStretch()
        
        # Right - Version + DB status
        right_layout = QHBoxLayout()
        right_layout.setSpacing(12)
        
        self.version_label = QLabel("v1.0.0")
        self.version_label.setStyleSheet("color: #86868b;")
        right_layout.addWidget(self.version_label)
        
        self.db_status_label = QLabel("● DB")
        self.db_status_label.setStyleSheet("color: #34c759; font-weight: 500;")
        right_layout.addWidget(self.db_status_label)
        
        layout.addLayout(right_layout, stretch=0)
        
        # Update time immediately
        self._update_time()
    
    def _start_timer(self):
        """Start the timer to update time every second."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)  # Every 1 second
    
    def _update_time(self):
        """Update the time display."""
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.time_label.setText(current_time)
    
    def set_user(self, username: str, vai_tro: str = None):
        """Set user information.
        
        Args:
            username: Username.
            vai_tro: Role name (optional).
        """
        self._username = username
        self._vai_tro = vai_tro or ""
        
        display = username
        if vai_tro:
            display = f"{username} · {vai_tro}"
        
        self.user_label.setText(display)
    
    def set_version(self, version: str):
        """Set the version display.
        
        Args:
            version: Version string (e.g., "v1.0.0").
        """
        self.version_label.setText(version)
    
    def set_db_status(self, connected: bool, message: str = None):
        """Set database connection status.
        
        Args:
            connected: True if connected, False otherwise.
            message: Optional status message.
        """
        self._db_connected = connected
        
        if connected:
            self.db_status_label.setText("● DB")
            self.db_status_label.setStyleSheet("color: #34c759; font-weight: 500;")
        else:
            display = message if message else "● DB Offline"
            self.db_status_label.setText(display)
            self.db_status_label.setStyleSheet("color: #ff3b30; font-weight: 500;")
    
    def set_db_status_check(self, check_func):
        """Set a function to check DB status periodically.
        
        Args:
            check_func: Callable that returns (connected: bool, message: str).
        """
        self._db_check_func = check_func
    
    def start_db_monitoring(self, interval_ms: int = 30000):
        """Start periodic DB status checking.
        
        Args:
            interval_ms: Check interval in milliseconds.
        """
        if hasattr(self, '_db_check_func'):
            self._db_timer = QTimer(self)
            self._db_timer.timeout.connect(self._check_db_status)
            self._db_timer.start(interval_ms)
    
    def _check_db_status(self):
        """Check DB status and update display."""
        if hasattr(self, '_db_check_func'):
            connected, message = self._db_check_func()
            self.set_db_status(connected, message)
    
    def stop_timer(self):
        """Stop the timer (call when closing)."""
        if hasattr(self, '_timer'):
            self._timer.stop()
        if hasattr(self, '_db_timer'):
            self._db_timer.stop()