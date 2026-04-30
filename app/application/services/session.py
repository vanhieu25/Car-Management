"""Session management - singleton current user, idle timeout.

Implements BR-SEC-06: Session timeout after 30 minutes of inactivity.
Implements BR-TIME-07: 30-minute idle timeout.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable


# Session timeout in minutes (BR-SEC-06)
SESSION_TIMEOUT_MINUTES = 30


@dataclass
class CurrentSession:
    """Represents the current user session.
    
    This is a singleton-like object that holds the current
    authenticated user's information.
    """
    user_id: int
    username: str
    ho_ten: str
    vai_tro_id: int
    vai_tro_ma: str
    login_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    must_change_password: bool = False  # BR-NV-08: Force password change on first login
    
    def is_expired(self) -> bool:
        """Check if session has expired due to inactivity.
        
        Returns:
            True if idle timeout exceeded.
        """
        idle_time = datetime.now() - self.last_activity
        return idle_time >= timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    def get_idle_minutes(self) -> int:
        """Get number of minutes since last activity.
        
        Returns:
            Minutes since last activity.
        """
        idle_time = datetime.now() - self.last_activity
        return int(idle_time.total_seconds() / 60)
    
    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()


class SessionManager:
    """Manages user sessions with idle timeout.
    
    Implements:
    - BR-SEC-06: 30-minute session timeout
    - BR-TIME-07: Idle timeout countdown
    
    Thread-safe singleton pattern for current session.
    """
    
    _instance: Optional["SessionManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "SessionManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize session manager."""
        if self._initialized:
            return
        
        self._current_session: Optional[CurrentSession] = None
        self._session_lock = threading.Lock()
        self._callbacks: list[Callable[[], None]] = []
        self._initialized = True

    @property
    def current_session(self) -> Optional[CurrentSession]:
        """Get current session if exists.
        
        Returns:
            Current session or None if not logged in.
        """
        with self._session_lock:
            return self._current_session

    @property
    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in.
        
        Returns:
            True if logged in, False otherwise.
        """
        return self._current_session is not None

    def login(
        self,
        user_id: int,
        username: str,
        ho_ten: str,
        vai_tro_id: int,
        vai_tro_ma: str,
        must_change_password: bool = False,
    ) -> CurrentSession:
        """Start a new session for a logged-in user.
        
        Args:
            user_id: User's database ID.
            username: User's username.
            ho_ten: User's full name.
            vai_tro_id: User's role ID.
            vai_tro_ma: User's role code (admin/sales/ky_thuat_bh).
            must_change_password: Force password change on first login (BR-NV-08).
            
        Returns:
            New CurrentSession object.
        """
        with self._session_lock:
            self._current_session = CurrentSession(
                user_id=user_id,
                username=username,
                ho_ten=ho_ten,
                vai_tro_id=vai_tro_id,
                vai_tro_ma=vai_tro_ma,
                login_time=datetime.now(),
                last_activity=datetime.now(),
                must_change_password=must_change_password,
            )
            return self._current_session

    def logout(self) -> None:
        """End the current session."""
        with self._session_lock:
            self._current_session = None

    def touch(self) -> None:
        """Update last activity timestamp.
        
        Call this on every user interaction to reset idle timer.
        """
        with self._session_lock:
            if self._current_session:
                self._current_session.touch()

    def check_session(self) -> tuple[bool, Optional[str]]:
        """Check if current session is valid.
        
        Checks:
        1. Session exists
        2. Session has not expired due to inactivity
        
        Returns:
            Tuple of (is_valid, error_message).
            error_message is None if valid.
        """
        with self._session_lock:
            if self._current_session is None:
                return False, "Chưa đăng nhập"

            if self._current_session.is_expired():
                return False, "Phiên đăng nhập đã hết hạn do không hoạt động. Vui lòng đăng nhập lại."

            return True, None

    def require_session(self) -> CurrentSession:
        """Get current session or raise error.
        
        Returns:
            Current session.
            
        Raises:
            PermissionError: If not logged in or session expired.
        """
        is_valid, error = self.check_session()
        if not is_valid:
            raise PermissionError(error)
        return self._current_session

    def get_time_remaining(self) -> Optional[int]:
        """Get remaining session time in minutes.
        
        Returns:
            Minutes until session expires, or None if not logged in.
        """
        with self._session_lock:
            if self._current_session is None:
                return None
            
            idle = self._current_session.get_idle_minutes()
            return max(0, SESSION_TIMEOUT_MINUTES - idle)

    def register_logout_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called on logout.
        
        Useful for UI to react to logout events.
        
        Args:
            callback: Callable that takes no arguments.
        """
        self._callbacks.append(callback)

    def _notify_logout(self) -> None:
        """Notify all registered callbacks of logout."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                pass  # Don't let callback errors break logout


# Global singleton instance
session_manager = SessionManager()
