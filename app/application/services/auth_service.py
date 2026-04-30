"""Authentication service - login, logout, password change.

Implements BR-SEC-01..09, BR-SEC-09 (audit logging), TRG-08.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import sqlite3

from app.domain.entities import NhanVien
from app.infrastructure.repositories.nhan_vien_repository import NhanVienRepository
from app.infrastructure.security.password_hasher import (
    PasswordHasher,
    PasswordValidator,
    password_hasher,
    password_validator,
)
from app.application.services.audit_log_service import AuditLogService, AuditAction


class LoginError(Enum):
    """Possible login error reasons."""
    USER_NOT_FOUND = "Tài khoản không tồn tại"
    WRONG_PASSWORD = "Mật khẩu không đúng"
    ACCOUNT_INACTIVE = "Tài khoản đã bị vô hiệu hóa"
    ACCOUNT_LOCKED = "Tài khoản bị khóa đến {lock_time}"
    SESSION_TIMEOUT = "Phiên đăng nhập đã hết hạn"


@dataclass
class LoginResult:
    """Result of a login attempt."""
    success: bool
    error: Optional[LoginError] = None
    error_params: Optional[dict] = None
    user: Optional[NhanVien] = None
    must_change_password: bool = False


@dataclass
class ChangePasswordResult:
    """Result of a password change attempt."""
    success: bool
    error_message: Optional[str] = None


class AuthService:
    """Authentication service handling login, logout, and password changes.
    
    Implements BR-SEC-01..09:
    - BR-SEC-01: Passwords stored as bcrypt hash with cost >= 12
    - BR-SEC-02: New passwords must be >= 8 characters with at least 1 letter and 1 number
    - BR-SEC-03: No plain text passwords in UI, log, or files
    - BR-SEC-05: 5 failed logins -> 15 minute lockout
    - BR-SEC-06: Session timeout after 30 minutes
    - BR-SEC-07: Password change requires old password verification
    
    Audit (BR-SEC-09, TRG-08):
    - LOGIN action logged on successful login
    - LOGOUT action logged on logout
    - CHANGE_PASSWORD action logged on password change
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        hasher: PasswordHasher = password_hasher,
        validator: PasswordValidator = password_validator,
        audit_service: AuditLogService = None,
    ):
        """Initialize with database connection.
        
        Args:
            conn: SQLite database connection.
            hasher: Password hasher instance (default: bcrypt cost 12).
            validator: Password validator instance (default: BR-SEC-02 rules).
            audit_service: Optional AuditLogService instance for logging.
        """
        self.conn = conn
        self.hasher = hasher
        self.validator = validator
        self.repo = NhanVienRepository(conn)
        self._audit_service = audit_service

    def _get_audit_service(self) -> AuditLogService:
        """Get or create audit service."""
        if self._audit_service is None:
            self._audit_service = AuditLogService(self.conn)
        return self._audit_service

    def login(self, username: str, password: str) -> LoginResult:
        """Attempt to log in a user.
        
        Flow (UC-SEC-01):
        1. Check if user exists
        2. Check if account is locked
        3. Verify password
        4. Check if account is active
        5. Reset failed login counter on success
        6. Return must_change_password flag for first-time login
        
        Args:
            username: Username to login.
            password: Plain text password.
            
        Returns:
            LoginResult with success=True and user if successful,
            or success=False with error reason.
        """
        # Step 1: Find user
        user = self.repo.find_by_username(username)
        if not user:
            return LoginResult(success=False, error=LoginError.USER_NOT_FOUND)

        # Step 2: Check if account is locked
        is_locked, lock_end_time = self.repo.is_account_locked(username)
        if is_locked:
            return LoginResult(
                success=False,
                error=LoginError.ACCOUNT_LOCKED,
                error_params={"lock_time": lock_end_time}
            )

        # Step 3: Verify password
        if not self.hasher.verify_password(password, user.mat_khau_hash):
            # Record failed attempt
            attempts, just_locked = self.repo.record_failed_login(username)
            if just_locked:
                lock_time = self.repo.find_by_username(username).khoa_den
                return LoginResult(
                    success=False,
                    error=LoginError.ACCOUNT_LOCKED,
                    error_params={"lock_time": lock_time}
                )
            return LoginResult(
                success=False,
                error=LoginError.WRONG_PASSWORD,
                error_params={"attempts_remaining": 5 - attempts}
            )

        # Step 4: Check if account is active
        if user.trang_thai != "active":
            return LoginResult(success=False, error=LoginError.ACCOUNT_INACTIVE)

        # Step 5: Reset failed login counter
        self.repo.record_successful_login(username)

        # Step 6: Check if must change password (first login or forced)
        must_change = bool(user.must_change_password)

        # Log successful login (BR-SEC-09, TRG-08)
        try:
            audit = self._get_audit_service()
            audit.log_login(user.id, user.username)
        except Exception:
            pass  # Don't fail login if audit fails

        return LoginResult(
            success=True,
            user=user,
            must_change_password=must_change
        )

    def logout(self, username: str, nhan_vien_id: int = None) -> None:
        """Record a logout.
        
        Args:
            username: Username that is logging out.
            nhan_vien_id: User ID for audit log (optional).
        """
        # Log logout (BR-SEC-09, TRG-08)
        if nhan_vien_id:
            try:
                audit = self._get_audit_service()
                audit.log_logout(nhan_vien_id)
            except Exception:
                pass  # Don't fail logout if audit fails

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> ChangePasswordResult:
        """Change a user's password.
        
        Implements BR-SEC-02, BR-SEC-07:
        - Requires old password verification
        - Validates new password strength (>= 8 chars, 1 letter, 1 number)
        - Hashes and stores new password
        
        Args:
            user_id: ID of the user changing password.
            old_password: Current password for verification.
            new_password: New password to set.
            
        Returns:
            ChangePasswordResult with success=True if successful,
            or success=False with error message.
        """
        # Find the user
        cursor = self.conn.execute(
            "SELECT * FROM nhan_vien WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return ChangePasswordResult(
                success=False,
                error_message="Người dùng không tồn tại"
            )

        user = NhanVien.from_row(row)

        # Verify old password
        if not self.hasher.verify_password(old_password, user.mat_khau_hash):
            return ChangePasswordResult(
                success=False,
                error_message="Mật khẩu cũ không đúng"
            )

        # Validate new password strength
        is_valid, error_msg = self.validator.validate(new_password)
        if not is_valid:
            return ChangePasswordResult(
                success=False,
                error_message=error_msg
            )

        # Hash and store new password
        new_hash = self.hasher.hash_password(new_password)
        self.repo.update_password(user_id, new_hash)

        # Log password change (BR-SEC-09)
        try:
            audit = self._get_audit_service()
            audit.log_password_change(user_id)
        except Exception:
            pass

        return ChangePasswordResult(success=True)

    def force_change_password(
        self,
        user_id: int,
        new_password: str,
    ) -> ChangePasswordResult:
        """Force change password (no old password required).
        
        Used when:
        - User must change password on first login (BR-NV-08)
        - Admin resets password
        
        Args:
            user_id: ID of the user changing password.
            new_password: New password to set.
            
        Returns:
            ChangePasswordResult with success=True if successful.
        """
        # Find the user
        cursor = self.conn.execute(
            "SELECT * FROM nhan_vien WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return ChangePasswordResult(
                success=False,
                error_message="Người dùng không tồn tại"
            )

        # Validate new password strength
        is_valid, error_msg = self.validator.validate(new_password)
        if not is_valid:
            return ChangePasswordResult(
                success=False,
                error_message=error_msg
            )

        # Hash and store new password
        new_hash = self.hasher.hash_password(new_password)
        self.repo.update_password(user_id, new_hash)

        # Log password change (BR-SEC-09)
        try:
            audit = self._get_audit_service()
            audit.log_password_change(user_id)
        except Exception:
            pass

        return ChangePasswordResult(success=True)

    def get_lock_time_remaining(self, username: str) -> Optional[int]:
        """Get remaining lock time in minutes for a locked account.
        
        Args:
            username: Username to check.
            
        Returns:
            Number of minutes remaining, or None if not locked.
        """
        is_locked, lock_end_time = self.repo.is_account_locked(username)
        if not is_locked or not lock_end_time:
            return None

        lock_time = datetime.fromisoformat(lock_end_time)
        remaining = lock_time - datetime.now()
        return max(0, int(remaining.total_seconds() / 60))
