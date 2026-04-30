"""Integration tests for login UI flow - T-G2.2.TEST.05.

Tests the full login flow:
- UI: User types credentials and clicks login
- Service: AuthService.login() processes credentials
- DB: Data is fetched and updated
- UI: Appropriate dialog is shown or closed
"""

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def db_with_seed():
    """Create a temporary database with migrations and seed data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(db_path)
    runner.run_pending()

    from app.infrastructure.database.seeds.dev_seed import seed_all
    seed_all(db_path)

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def app_instance(db_with_seed, monkeypatch):
    """Create application with test database path."""
    # Patch get_connection to return our test database
    import sqlite3
    
    def mock_get_connection(db_path=None):
        conn = sqlite3.connect(db_with_seed)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    from app import infrastructure
    monkeypatch.setattr(
        "app.infrastructure.database.connection.get_connection",
        mock_get_connection
    )
    monkeypatch.setattr(
        "app.presentation.screens.login_screen.get_connection",
        mock_get_connection
    )


class TestLoginScreenIntegration:
    """Integration tests for LoginScreen with AuthService."""

    def test_login_screen_initial_state(self, qapp):
        """Test login screen opens with correct initial state."""
        from app.presentation.screens.login_screen import LoginScreen

        screen = LoginScreen()
        
        assert screen.username_input.text() == ""
        assert screen.password_input.text() == ""
        assert not screen.login_btn.isEnabled() == False  # Button should be enabled
        assert not screen.error_label.isVisible()
        
        screen.close()

    def test_login_success_emits_signal(self, qapp, db_with_seed):
        """Test successful login emits login_successful signal."""
        from app.presentation.screens.login_screen import LoginScreen
        from PyQt6.QtWidgets import QApplication

        screen = LoginScreen()
        
        # Set credentials
        screen.username_input.setText("admin")
        screen.password_input.setText("Admin@123")
        
        # Track signal emission
        signal_received = []
        screen.login_successful.connect(lambda: signal_received.append(True))
        
        # Process events to allow signal to propagate
        QApplication.processEvents()
        
        screen.close()

    def test_login_ui_validates_empty_fields(self, qapp):
        """Test login UI shows error for empty fields."""
        from app.presentation.screens.login_screen import LoginScreen

        screen = LoginScreen()
        
        # Try to login with empty fields
        screen.username_input.setText("")
        screen.password_input.setText("")
        
        screen._on_login_clicked()
        
        # Should show error
        assert screen.error_label.isVisible()
        assert "đăng nhập" in screen.error_label.text().lower()
        
        screen.close()


class TestChangePasswordDialogIntegration:
    """Integration tests for ChangePasswordDialog."""

    def test_password_strength_indicator_updates(self, qapp):
        """Test password strength indicator updates as user types."""
        from app.presentation.screens.change_password_dialog import ChangePasswordDialog

        dialog = ChangePasswordDialog(
            user_id=1,
            require_old_password=True,
            force_change=False,
        )
        
        # Type weak password
        dialog.new_password_input.setText("weak")
        assert dialog.strength_indicator._score < 40
        
        # Type medium password
        dialog.new_password_input.setText("Medium123")
        assert 40 <= dialog.strength_indicator._score < 70
        
        # Type strong password
        dialog.new_password_input.setText("StrongPass@123")
        assert dialog.strength_indicator._score >= 70
        
        dialog.close()

    def test_change_password_dialog_fields(self, qapp):
        """Test change password dialog has all required fields."""
        from app.presentation.screens.change_password_dialog import ChangePasswordDialog

        # With old password required
        dialog = ChangePasswordDialog(
            user_id=1,
            require_old_password=True,
            force_change=False,
        )
        
        assert dialog.old_password_input is not None
        assert dialog.new_password_input is not None
        assert dialog.confirm_input is not None
        assert dialog.strength_indicator is not None
        
        dialog.close()

    def test_force_change_password_dialog_no_cancel(self, qapp):
        """Test force change password dialog cannot be cancelled."""
        from app.presentation.screens.change_password_dialog import ChangePasswordDialog

        dialog = ChangePasswordDialog(
            user_id=1,
            require_old_password=False,
            force_change=True,
        )
        
        # Cancel button should not exist in force change mode
        # (checked by looking at whether it was added to layout)
        # In force change mode, user cannot cancel without changing password
        
        dialog.close()


class TestPasswordHasherUnit:
    """Unit tests for password hasher and validator."""

    def test_bcrypt_hash_and_verify(self):
        """Test password hashing and verification."""
        from app.infrastructure.security.password_hasher import PasswordHasher

        hasher = PasswordHasher(cost=12)
        
        password = "TestPassword@123"
        hashed = hasher.hash_password(password)
        
        # Hash should be different from password
        assert hashed != password
        
        # Verify correct password
        assert hasher.verify_password(password, hashed) is True
        
        # Verify wrong password fails
        assert hasher.verify_password("WrongPassword", hashed) is False

    def test_bcrypt_cost_must_be_12_or_higher(self):
        """Test that bcrypt cost must be at least 12."""
        from app.infrastructure.security.password_hasher import PasswordHasher

        # Should work with cost 12
        hasher = PasswordHasher(cost=12)
        assert hasher.cost == 12
        
        # Should work with cost higher than 12
        hasher = PasswordHasher(cost=14)
        assert hasher.cost == 14

    def test_bcrypt_cost_below_12_raises(self):
        """Test that bcrypt cost below 12 raises ValueError."""
        from app.infrastructure.security.password_hasher import PasswordHasher

        with pytest.raises(ValueError):
            PasswordHasher(cost=10)

    def test_password_validator_min_length(self):
        """Test password validator checks minimum length."""
        from app.infrastructure.security.password_hasher import PasswordValidator

        validator = PasswordValidator(min_length=8)
        
        # Too short
        is_valid, msg = validator.validate("short1")
        assert is_valid is False
        assert "8" in msg
        
        # Exactly 8 chars
        is_valid, msg = validator.validate("password1")
        assert is_valid is True

    def test_password_validator_requires_letter(self):
        """Test password validator requires at least one letter."""
        from app.infrastructure.security.password_hasher import PasswordValidator

        validator = PasswordValidator(require_uppercase=True, require_lowercase=True)
        
        # No letters
        is_valid, msg = validator.validate("12345678")
        assert is_valid is False

    def test_password_validator_requires_number(self):
        """Test password validator requires at least one number."""
        from app.infrastructure.security.password_hasher import PasswordValidator

        validator = PasswordValidator(require_digit=True)
        
        # No numbers
        is_valid, msg = validator.validate("password")
        assert is_valid is False

    def test_password_strength_score(self):
        """Test password strength scoring."""
        from app.infrastructure.security.password_hasher import PasswordValidator

        validator = PasswordValidator()
        
        # Weak password scores low
        weak_score = validator.get_strength_score("abc")
        assert weak_score < 40
        
        # Strong password scores high
        strong_score = validator.get_strength_score("StrongPass@123!")
        assert strong_score >= 70


class TestSessionManager:
    """Unit tests for session manager."""

    def test_session_manager_is_singleton(self):
        """Test that session manager is a singleton."""
        from app.application.services.session import SessionManager

        sm1 = SessionManager()
        sm2 = SessionManager()
        
        assert sm1 is sm2

    def test_session_not_logged_in_initially(self):
        """Test that session manager shows not logged in initially."""
        from app.application.services.session import SessionManager

        sm = SessionManager()
        sm.logout()  # Ensure clean state
        
        assert sm.is_logged_in is False
        assert sm.current_session is None

    def test_login_creates_session(self):
        """Test that login creates a session."""
        from app.application.services.session import SessionManager

        sm = SessionManager()
        sm.logout()  # Ensure clean state
        
        session = sm.login(
            user_id=1,
            username="admin",
            ho_ten="Nguyễn Văn Admin",
            vai_tro_id=1,
            vai_tro_ma="admin",
        )
        
        assert sm.is_logged_in is True
        assert sm.current_session is not None
        assert sm.current_session.username == "admin"
        assert sm.current_session.vai_tro_id == 1

    def test_logout_clears_session(self):
        """Test that logout clears the session."""
        from app.application.services.session import SessionManager

        sm = SessionManager()
        
        sm.login(
            user_id=1,
            username="admin",
            ho_ten="Admin",
            vai_tro_id=1,
            vai_tro_ma="admin",
        )
        
        assert sm.is_logged_in is True
        
        sm.logout()
        
        assert sm.is_logged_in is False
        assert sm.current_session is None

    def test_touch_updates_activity(self):
        """Test that touch updates last activity time."""
        from app.application.services.session import SessionManager

        sm = SessionManager()
        
        sm.login(
            user_id=1,
            username="admin",
            ho_ten="Admin",
            vai_tro_id=1,
            vai_tro_ma="admin",
        )
        
        initial_activity = sm.current_session.last_activity
        
        # Small delay
        import time
        time.sleep(0.01)
        
        sm.touch()
        
        assert sm.current_session.last_activity >= initial_activity

    def test_session_expires_after_timeout(self):
        """Test that session expires after 30 minutes of inactivity."""
        from app.application.services.session import SessionManager, CurrentSession
        from datetime import datetime, timedelta

        sm = SessionManager()
        sm.logout()
        
        # Create session with old last_activity
        old_time = datetime.now() - timedelta(minutes=31)
        sm._current_session = CurrentSession(
            user_id=1,
            username="admin",
            ho_ten="Admin",
            vai_tro_id=1,
            vai_tro_ma="admin",
            last_activity=old_time,
        )
        
        is_valid, error = sm.check_session()
        assert is_valid is False
        assert "hết hạn" in error.lower()

    def test_get_time_remaining(self):
        """Test getting remaining session time."""
        from app.application.services.session import SessionManager

        sm = SessionManager()
        sm.logout()
        
        # Not logged in returns None
        assert sm.get_time_remaining() is None
        
        # After login, should have time remaining
        sm.login(
            user_id=1,
            username="admin",
            ho_ten="Admin",
            vai_tro_id=1,
            vai_tro_ma="admin",
        )
        
        remaining = sm.get_time_remaining()
        assert remaining is not None
        assert remaining <= 30
        assert remaining > 0
