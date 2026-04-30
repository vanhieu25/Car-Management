"""NhanVien repository - find by username, update login attempts and lockout."""

from datetime import datetime, timedelta
from typing import Optional

import sqlite3

from app.domain.entities import NhanVien
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.security.password_hasher import MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES


class NhanVienRepository(BaseRepository[NhanVien]):
    """Repository for NhanVien entity with authentication-specific methods."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, NhanVien)

    def find_by_username(self, username: str) -> Optional[NhanVien]:
        """Find a employee by username.
        
        Args:
            username: Username to search for.
            
        Returns:
            NhanVien if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM nhan_vien WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return NhanVien.from_row(row)
        return None

    def is_account_locked(self, username: str) -> tuple[bool, Optional[str]]:
        """Check if account is currently locked.
        
        Args:
            username: Username to check.
            
        Returns:
            Tuple of (is_locked, lock_end_time).
            is_locked is True if account is locked.
            lock_end_time is the ISO timestamp when lock expires, or None if not locked.
        """
        nhan_vien = self.find_by_username(username)
        if not nhan_vien:
            return False, None

        if nhan_vien.khoa_den is None:
            return False, None

        # Parse lock expiration time
        lock_time = datetime.fromisoformat(nhan_vien.khoa_den)
        now = datetime.now()

        if now < lock_time:
            return True, nhan_vien.khoa_den

        # Lock has expired, clear it
        if nhan_vien.khoa_den:
            self.clear_lockout(nhan_vien.id)
        return False, None

    def record_failed_login(self, username: str) -> tuple[int, bool]:
        """Record a failed login attempt.
        
        Increments lan_dang_nhap_sai counter.
        If counter reaches MAX_LOGIN_ATTEMPTS (5), locks the account.
        
        Args:
            username: Username that failed to login.
            
        Returns:
            Tuple of (attempts_count, is_locked).
            attempts_count is the current number of failed attempts.
            is_locked is True if account was just locked.
        """
        nhan_vien = self.find_by_username(username)
        if not nhan_vien:
            return 0, False

        new_count = nhan_vien.lan_dang_nhap_sai + 1
        is_locked = False

        if new_count >= MAX_LOGIN_ATTEMPTS:
            # Lock the account
            lock_end = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            lock_end_str = lock_end.isoformat()
            self.conn.execute(
                """UPDATE nhan_vien 
                   SET lan_dang_nhap_sai = ?, khoa_den = ?, updated_at = ?
                   WHERE id = ?""",
                (new_count, lock_end_str, datetime.now().isoformat(), nhan_vien.id)
            )
            self.conn.commit()
            is_locked = True
        else:
            self.conn.execute(
                """UPDATE nhan_vien 
                   SET lan_dang_nhap_sai = ?, updated_at = ?
                   WHERE id = ?""",
                (new_count, datetime.now().isoformat(), nhan_vien.id)
            )
            self.conn.commit()

        return new_count, is_locked

    def record_successful_login(self, username: str) -> None:
        """Record a successful login - reset failed attempt counter.
        
        Args:
            username: Username that logged in successfully.
        """
        nhan_vien = self.find_by_username(username)
        if not nhan_vien:
            return

        self.conn.execute(
            """UPDATE nhan_vien 
               SET lan_dang_nhap_sai = 0, khoa_den = NULL, updated_at = ?
               WHERE id = ?""",
            (datetime.now().isoformat(), nhan_vien.id)
        )
        self.conn.commit()

    def clear_lockout(self, nhan_vien_id: int) -> None:
        """Clear lockout for an account.
        
        Args:
            nhan_vien_id: ID of the employee to clear lockout for.
        """
        self.conn.execute(
            """UPDATE nhan_vien 
               SET lan_dang_nhap_sai = 0, khoa_den = NULL, updated_at = ?
               WHERE id = ?""",
            (datetime.now().isoformat(), nhan_vien_id)
        )
        self.conn.commit()

    def update_password(self, nhan_vien_id: int, password_hash: str) -> None:
        """Update password for an employee.
        
        Also updates must_change_password flag and last_password_change timestamp.
        
        Args:
            nhan_vien_id: ID of the employee.
            password_hash: New bcrypt password hash.
        """
        now = datetime.now().isoformat()
        self.conn.execute(
            """UPDATE nhan_vien 
               SET mat_khau_hash = ?, 
                   must_change_password = 0, 
                   last_password_change = ?,
                   updated_at = ?
               WHERE id = ?""",
            (password_hash, now, now, nhan_vien_id)
        )
        self.conn.commit()

    def must_change_password(self, username: str) -> bool:
        """Check if user must change password on next login.
        
        Args:
            username: Username to check.
            
        Returns:
            True if user must change password, False otherwise.
        """
        nhan_vien = self.find_by_username(username)
        if not nhan_vien:
            return False
        return bool(nhan_vien.must_change_password)

    def set_must_change_password(self, nhan_vien_id: int, value: bool = True) -> None:
        """Set or clear the must_change_password flag.
        
        Args:
            nhan_vien_id: ID of the employee.
            value: True to force password change, False to clear.
        """
        self.conn.execute(
            """UPDATE nhan_vien 
               SET must_change_password = ?, updated_at = ?
               WHERE id = ?""",
            (1 if value else 0, datetime.now().isoformat(), nhan_vien_id)
        )
        self.conn.commit()

    def get_kpi_by_month(self, nhan_vien_id: int, year: int, month: int) -> dict:
        """Get employee KPI for a specific month.
        
        BR-CALC-05: Số HĐ giao thành công, doanh thu, tỷ lệ chốt
        - so_hop_dong: count of contracts with trang_thai='da_giao_xe'
        - doanh_thu: sum of tong_tien for those contracts
        - ti_le_chot: not available (no lead tracking in current schema)
        
        Args:
            nhan_vien_id: ID of the employee.
            year: Year to query.
            month: Month to query (1-12).
            
        Returns:
            Dict with keys: so_hop_dong, doanh_thu, ti_le_chot (None).
        """
        # Build date range for the month
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"

        cursor = self.conn.execute(
            """SELECT 
                   COUNT(*) as so_hop_dong,
                   COALESCE(SUM(tong_tien), 0) as doanh_thu
               FROM hop_dong 
               WHERE nhan_vien_id = ? 
                 AND trang_thai = 'da_giao_xe'
                 AND ngay_giao_xe >= ? 
                 AND ngay_giao_xe < ?""",
            (nhan_vien_id, start_date, end_date)
        )
        row = cursor.fetchone()
        return {
            'so_hop_dong': row[0] if row else 0,
            'doanh_thu': row[1] if row else 0,
            'ti_le_chot': None  # No lead tracking in current schema
        }
