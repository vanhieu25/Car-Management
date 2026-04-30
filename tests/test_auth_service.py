"""Unit tests for AuthService - T-G2.2.TEST.01, TEST.02, TEST.03.

Tests:
- TEST.01: login success / wrong password / locked / unlocked → AC-SEC-01
- TEST.02: Account lockout after 5 failed attempts → AC-SEC-02
- TEST.03: change_password validation (length >= 8) → AC-SEC-03
"""

import pytest
import sqlite3
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def fresh_db():
    """Create a fresh database with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(db_path)
    runner.run_pending()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def seeded_db(fresh_db):
    """Create database with seed data applied."""
    from app.infrastructure.database.seeds.dev_seed import seed_all
    seed_all(fresh_db)
    return fresh_db


import tempfile


class TestAuthServiceLogin:
    """Test AuthService.login() - AC-SEC-01."""

    def test_login_success(self, seeded_db):
        """Test successful login with correct credentials."""
        from app.application.services.auth_service import AuthService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)
        result = auth.login("admin", "Admin@123")

        assert result.success is True, "Login should succeed with correct credentials"
        assert result.user is not None, "User object should be returned"
        assert result.user.username == "admin"
        assert result.must_change_password is True, "First login should require password change"

        conn.close()

    def test_login_wrong_password(self, seeded_db):
        """Test login fails with wrong password."""
        from app.application.services.auth_service import AuthService, LoginError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)
        result = auth.login("admin", "wrongpassword")

        assert result.success is False, "Login should fail with wrong password"
        assert result.error == LoginError.WRONG_PASSWORD

        conn.close()

    def test_login_nonexistent_user(self, seeded_db):
        """Test login fails for non-existent user."""
        from app.application.services.auth_service import AuthService, LoginError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)
        result = auth.login("nonexistent", "anypassword")

        assert result.success is False, "Login should fail for non-existent user"
        assert result.error == LoginError.USER_NOT_FOUND

        conn.close()

    def test_login_inactive_account(self, seeded_db):
        """Test login fails for inactive account."""
        from app.application.services.auth_service import AuthService, LoginError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Set admin to inactive
        conn.execute(
            "UPDATE nhan_vien SET trang_thai = 'inactive' WHERE username = 'admin'"
        )
        conn.commit()

        auth = AuthService(conn)
        result = auth.login("admin", "Admin@123")

        assert result.success is False, "Login should fail for inactive account"
        assert result.error == LoginError.ACCOUNT_INACTIVE

        # Reset for other tests
        conn.execute(
            "UPDATE nhan_vien SET trang_thai = 'active' WHERE username = 'admin'"
        )
        conn.commit()
        conn.close()

    def test_login_locked_account(self, seeded_db):
        """Test login fails when account is locked."""
        from app.application.services.auth_service import AuthService, LoginError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Lock the account manually
        lock_time = (datetime.now() + timedelta(minutes=15)).isoformat()
        conn.execute(
            "UPDATE nhan_vien SET khoa_den = ? WHERE username = 'admin'",
            (lock_time,)
        )
        conn.commit()

        auth = AuthService(conn)
        result = auth.login("admin", "Admin@123")

        assert result.success is False, "Login should fail for locked account"
        assert result.error == LoginError.ACCOUNT_LOCKED

        conn.close()

    def test_login_unlocked_after_timeout(self, seeded_db):
        """Test locked account unlocks after lockout period expires."""
        from app.application.services.auth_service import AuthService, LoginError

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Set lock to expire in the past
        expired_lock = (datetime.now() - timedelta(minutes=1)).isoformat()
        conn.execute(
            "UPDATE nhan_vien SET khoa_den = ?, lan_dang_nhap_sai = 5 WHERE username = 'admin'",
            (expired_lock,)
        )
        conn.commit()

        auth = AuthService(conn)
        result = auth.login("admin", "Admin@123")

        # Should succeed because lock has expired
        assert result.success is True, "Login should succeed after lockout expires"
        assert result.user.username == "admin"

        conn.close()


class TestAccountLockout:
    """Test account lockout after 5 failed attempts - AC-SEC-02 / BR-SEC-05."""

    def test_lockout_after_5_failed_attempts(self, fresh_db):
        """Test that account gets locked after 5 failed login attempts."""
        from app.application.services.auth_service import AuthService, LoginError

        # Setup: create admin user
        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert vai_tro
        conn.execute(
            "INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('admin', 'Admin')"
        )

        # Insert admin user with known password hash
        # Hash of "Admin@123" with bcrypt cost 12
        password_hash = "$2b$12$LQv3c1yqBwEbKrB3qVLZjeqMWrT6Gv.rJr7.N1VxVYqPZrA.1wXq"
        conn.execute(
            """INSERT INTO nhan_vien 
               (username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai) 
               VALUES ('testuser', ?, 'Test User', 'test@test.com', 1, 'active')""",
            (password_hash,)
        )
        conn.commit()

        auth = AuthService(conn)

        # Try 4 wrong passwords - should still be able to try
        for i in range(4):
            result = auth.login("testuser", f"wrongpassword{i}")
            assert result.success is False
            assert result.error == LoginError.WRONG_PASSWORD

        # 5th wrong password should lock the account
        result = auth.login("testuser", "wrongpassword5")
        assert result.success is False
        assert result.error == LoginError.ACCOUNT_LOCKED

        # Verify in database
        cursor = conn.execute(
            "SELECT khoa_den, lan_dang_nhap_sai FROM nhan_vien WHERE username = 'testuser'"
        )
        row = cursor.fetchone()
        assert row[0] is not None, "khoa_den should be set"
        assert row[1] == 5, "lan_dang_nhap_sai should be 5"

        conn.close()

    def test_successful_login_resets_counter(self, fresh_db):
        """Test that successful login resets failed attempt counter."""
        from app.application.services.auth_service import AuthService, LoginError

        conn = sqlite3.connect(fresh_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert vai_tro
        conn.execute(
            "INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('admin', 'Admin')"
        )

        # Insert admin user
        password_hash = "$2b$12$LQv3c1yqBwEbKrB3qVLZjeqMWrT6Gv.rJr7.N1VxVYqPZrA.1wXq"
        conn.execute(
            """INSERT INTO nhan_vien 
               (username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai, lan_dang_nhap_sai) 
               VALUES ('testuser', ?, 'Test User', 'test@test.com', 1, 'active', 3)""",
            (password_hash,)
        )
        conn.commit()

        auth = AuthService(conn)

        # Successful login
        result = auth.login("testuser", "Admin@123")
        assert result.success is True

        # Verify counter was reset
        cursor = conn.execute(
            "SELECT lan_dang_nhap_sai FROM nhan_vien WHERE username = 'testuser'"
        )
        row = cursor.fetchone()
        assert row[0] == 0, "lan_dang_nhap_sai should be reset to 0"

        conn.close()


class TestChangePassword:
    """Test change_password validation - AC-SEC-03 / BR-SEC-02."""

    def test_change_password_success(self, seeded_db):
        """Test successful password change."""
        from app.application.services.auth_service import AuthService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)

        # Get admin's id
        cursor = conn.execute("SELECT id FROM nhan_vien WHERE username = 'admin'")
        admin_id = cursor.fetchone()[0]

        result = auth.change_password(
            admin_id,
            old_password="Admin@123",
            new_password="NewPass@123",
        )

        assert result.success is True, f"Password change should succeed: {result.error_message}"

        # Verify new password works
        result2 = auth.login("admin", "NewPass@123")
        assert result2.success is True, "New password should work for login"

        conn.close()

    def test_change_password_wrong_old(self, seeded_db):
        """Test password change fails with wrong old password."""
        from app.application.services.auth_service import AuthService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)

        cursor = conn.execute("SELECT id FROM nhan_vien WHERE username = 'admin'")
        admin_id = cursor.fetchone()[0]

        result = auth.change_password(
            admin_id,
            old_password="WrongOldPass",
            new_password="NewPass@123",
        )

        assert result.success is False, "Password change should fail with wrong old password"
        assert "cũ" in result.error_message or "wrong" in result.error_message.lower()

        conn.close()

    def test_change_password_too_short(self, seeded_db):
        """Test password change fails when new password is too short (less than 8 chars)."""
        from app.application.services.auth_service import AuthService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)

        cursor = conn.execute("SELECT id FROM nhan_vien WHERE username = 'admin'")
        admin_id = cursor.fetchone()[0]

        result = auth.change_password(
            admin_id,
            old_password="Admin@123",
            new_password="Short1",  # Only 6 chars
        )

        assert result.success is False, "Password change should fail for short password"
        assert "8" in result.error_message, "Error should mention minimum 8 characters"

        conn.close()

    def test_change_password_no_letter(self, seeded_db):
        """Test password change fails when new password has no letter."""
        from app.application.services.auth_service import AuthService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)

        cursor = conn.execute("SELECT id FROM nhan_vien WHERE username = 'admin'")
        admin_id = cursor.fetchone()[0]

        result = auth.change_password(
            admin_id,
            old_password="Admin@123",
            new_password="12345678",  # No letters
        )

        assert result.success is False, "Password change should fail without letters"
        assert "chữ" in result.error_message.lower(), "Error should mention letters"

        conn.close()

    def test_change_password_no_number(self, seeded_db):
        """Test password change fails when new password has no number."""
        from app.application.services.auth_service import AuthService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)

        cursor = conn.execute("SELECT id FROM nhan_vien WHERE username = 'admin'")
        admin_id = cursor.fetchone()[0]

        result = auth.change_password(
            admin_id,
            old_password="Admin@123",
            new_password="PasswordX",  # No numbers
        )

        assert result.success is False, "Password change should fail without numbers"
        assert "số" in result.error_message.lower(), "Error should mention numbers"

        conn.close()

    def test_force_change_password_no_old_required(self, seeded_db):
        """Test force_change_password works without old password."""
        from app.application.services.auth_service import AuthService

        conn = sqlite3.connect(seeded_db)
        conn.execute("PRAGMA foreign_keys = ON")

        auth = AuthService(conn)

        cursor = conn.execute("SELECT id FROM nhan_vien WHERE username = 'sales01'")
        sales_id = cursor.fetchone()[0]

        result = auth.force_change_password(
            sales_id,
            new_password="NewPass@123",
        )

        assert result.success is True, "Force password change should succeed"

        conn.close()
