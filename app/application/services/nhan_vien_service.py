"""NhanVien service - employee business logic layer.

Implements business rules:
- BR-NV-01..08: Employee management
- BR-SEC-01..09: Security (password hashing, account lockout)
- BR-CALC-05: Employee KPI calculation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

import sqlite3
import re

from app.domain.entities import NhanVien
from app.infrastructure.repositories.nhan_vien_repository import NhanVienRepository
from app.infrastructure.security.password_hasher import PasswordHasher, password_hasher
from app.application.services.audit_decorator import audit
from app.application.services.audit_log_service import AuditAction
from app.application.services.decorators import require_permission


class NhanVienServiceError(Exception):
    """Base exception for NhanVien service errors."""
    pass


class ValidationError(NhanVienServiceError):
    """Validation error with field-specific messages."""
    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        super().__init__(message)
        self.field = field
        self.errors = errors or []


class DuplicateUsernameError(NhanVienServiceError):
    """Raised when username already exists."""
    pass


class DuplicateEmailError(NhanVienServiceError):
    """Raised when email already exists."""
    pass


class CannotLockAdminError(NhanVienServiceError):
    """Raised when trying to lock the admin account."""
    pass


class NhanVienNotFoundError(NhanVienServiceError):
    """Raised when employee is not found."""
    pass


@dataclass
class NhanVienCreateData:
    """Data for creating a new employee."""
    username: str
    ho_ten: str
    email: str
    so_dien_thoai: str = ""
    vai_tro_id: int = 2  # Default to sales role
    dia_chi: str = ""


@dataclass
class NhanVienUpdateData:
    """Data for updating an employee."""
    ho_ten: str = None
    email: str = None
    so_dien_thoai: str = None
    dia_chi: str = None
    vai_tro_id: int = None
    trang_thai: str = None


@dataclass
class NhanVienSearchResult:
    """Search result with metadata."""
    items: List[NhanVien]
    total: int
    page: int
    page_size: int
    total_pages: int


class NhanVienService:
    """Service for employee management operations."""
    
    def __init__(self, conn: sqlite3.Connection, session=None):
        """Initialize with database connection.
        
        Args:
            conn: sqlite3.Connection instance.
            session: Current user session (optional).
        """
        self.conn = conn
        self._session = session
        self._repo = NhanVienRepository(conn)
        self._hasher = password_hasher
    
    def get_by_id(self, nhan_vien_id: int) -> Optional[NhanVien]:
        """Get employee by ID.
        
        Args:
            nhan_vien_id: Employee ID.
            
        Returns:
            NhanVien if found, None otherwise.
        """
        return self._repo.find_by_id(nhan_vien_id)
    
    def get_by_username(self, username: str) -> Optional[NhanVien]:
        """Get employee by username.
        
        Args:
            username: Username.
            
        Returns:
            NhanVien if found, None otherwise.
        """
        return self._repo.find_by_username(username)
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[NhanVien]:
        """Get all employees with pagination.
        
        Args:
            limit: Maximum results.
            offset: Offset for pagination.
            
        Returns:
            List of NhanVien entities.
        """
        return self._repo.find_all(limit, offset)
    
    def search(
        self,
        keyword: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> NhanVienSearchResult:
        """Search employees with filters.
        
        Args:
            keyword: Keyword search (username, ho_ten).
            page: Page number (1-indexed).
            page_size: Results per page.
            
        Returns:
            NhanVienSearchResult with items and pagination info.
        """
        offset = (page - 1) * page_size
        
        # Build query
        conditions = []
        params = []
        
        if keyword:
            conditions.append("(username LIKE ? OR ho_ten LIKE ?)")
            params.append(f"%{keyword}%")
            params.append(f"%{keyword}%")
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Count total
        count_sql = f"SELECT COUNT(*) FROM nhan_vien {where_clause}"
        cursor = self.conn.execute(count_sql, params)
        total = cursor.fetchone()[0]
        
        # Get items
        sql = f"""
            SELECT * FROM nhan_vien 
            {where_clause}
            ORDER BY id
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        cursor = self.conn.execute(sql, params)
        items = [NhanVien.from_row(row) for row in cursor.fetchall()]
        
        total_pages = max(1, (total + page_size - 1) // page_size)
        
        return NhanVienSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format.
        
        Args:
            email: Email address.
            
        Returns:
            True if valid, False otherwise.
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))
    
    def _validate_create_data(self, data: NhanVienCreateData) -> List[str]:
        """Validate create data.
        
        Args:
            data: NhanVienCreateData to validate.
            
        Returns:
            List of error messages (empty if valid).
        """
        errors = []
        
        # Required fields
        if not data.username or not data.username.strip():
            errors.append("Username là bắt buộc")
        elif len(data.username) < 3:
            errors.append("Username phải có ít nhất 3 ký tự")
        
        if not data.ho_ten or not data.ho_ten.strip():
            errors.append("Họ tên là bắt buộc")
        
        if not data.email or not data.email.strip():
            errors.append("Email là bắt buộc")
        elif not self._validate_email(data.email):
            errors.append("Email không hợp lệ")
        
        return errors
    
    @audit(action="CREATE_NHAN_VIEN", table="nhan_vien")
    def create(self, data: NhanVienCreateData) -> Tuple[NhanVien, str]:
        """Create a new employee.
        
        Validates:
        - Username is unique
        - Email format is valid
        - Required fields present
        
        Generates random password, hashes it with bcrypt.
        Sets must_change_password=True so user must change on first login.
        
        Args:
            data: NhanVienCreateData with employee data.
            
        Returns:
            Tuple of (created NhanVien, raw_password).
            Raw password is returned ONCE for display to admin.
            
        Raises:
            ValidationError: If validation fails.
            DuplicateUsernameError: If username already exists.
            DuplicateEmailError: If email already exists.
        """
        # Validate
        errors = self._validate_create_data(data)
        if errors:
            raise ValidationError("; ".join(errors), errors=errors)
        
        # Check username uniqueness
        if self._repo.find_by_username(data.username):
            raise DuplicateUsernameError(
                f"Username '{data.username}' đã được sử dụng bởi nhân viên khác"
            )
        
        # Check email uniqueness
        cursor = self.conn.execute(
            "SELECT id FROM nhan_vien WHERE email = ?",
            (data.email.lower(),)
        )
        if cursor.fetchone():
            raise DuplicateEmailError(
                f"Email '{data.email}' đã được sử dụng bởi nhân viên khác"
            )
        
        # Generate random password (12 chars with upper+lower+digit)
        raw_password = self._hasher.generate_random_password(12)
        password_hash = self._hasher.hash_password(raw_password)
        
        # Create entity
        now = datetime.now().isoformat()
        nhan_vien = NhanVien(
            username=data.username.strip(),
            mat_khau_hash=password_hash,
            ho_ten=data.ho_ten.strip(),
            email=data.email.lower().strip(),
            so_dien_thoai=data.so_dien_thoai.strip() if data.so_dien_thoai else "",
            vai_tro_id=data.vai_tro_id,
            trang_thai="active",
            lan_dang_nhap_sai=0,
            khoa_den=None,
            must_change_password=1,
            created_at=now,
            updated_at=now,
        )
        
        created = self._repo.create(nhan_vien)
        
        return created, raw_password
    
    @audit(action="UPDATE_NHAN_VIEN", table="nhan_vien")
    def update(self, nhan_vien_id: int, data: NhanVienUpdateData) -> NhanVien:
        """Update an employee (admin only).
        
        Args:
            nhan_vien_id: Employee ID to update.
            data: NhanVienUpdateData with fields to update.
            
        Returns:
            Updated NhanVien entity.
            
        Raises:
            NhanVienNotFoundError: If employee not found.
            ValidationError: If validation fails.
        """
        # Get current employee
        nv = self._repo.find_by_id(nhan_vien_id)
        if not nv:
            raise NhanVienNotFoundError(f"Không tìm thấy nhân viên với ID {nhan_vien_id}")
        
        # Build update data
        update_data = {}
        
        if data.ho_ten is not None:
            update_data["ho_ten"] = data.ho_ten.strip()
        
        if data.email is not None:
            email = data.email.lower().strip()
            if not self._validate_email(email):
                raise ValidationError("Email không hợp lệ", field="email")
            # Check uniqueness
            cursor = self.conn.execute(
                "SELECT id FROM nhan_vien WHERE email = ? AND id != ?",
                (email, nhan_vien_id)
            )
            if cursor.fetchone():
                raise DuplicateEmailError(f"Email '{email}' đã được sử dụng")
            update_data["email"] = email
        
        if data.so_dien_thoai is not None:
            update_data["so_dien_thoai"] = data.so_dien_thoai.strip()
        
        if data.dia_chi is not None:
            update_data["dia_chi"] = data.dia_chi.strip()
        
        if data.vai_tro_id is not None:
            update_data["vai_tro_id"] = data.vai_tro_id
        
        if data.trang_thai is not None:
            if data.trang_thai not in ("active", "inactive"):
                raise ValidationError("Trạng thái không hợp lệ")
            update_data["trang_thai"] = data.trang_thai
        
        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(nhan_vien_id)
            
            self.conn.execute(
                f"UPDATE nhan_vien SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()
        
        return self._repo.find_by_id(nhan_vien_id)
    
    @audit(action="UPDATE_NHAN_VIEN", table="nhan_vien")
    def lock(self, nhan_vien_id: int, ly_do: str = None) -> NhanVien:
        """Lock an employee account.
        
        Cannot lock the admin account (username == 'admin').
        Sets trang_thai = 'inactive' and records lockout info.
        
        Args:
            nhan_vien_id: Employee ID to lock.
            ly_do: Reason for locking (optional, stored in audit).
            
        Returns:
            Updated NhanVien entity.
            
        Raises:
            NhanVienNotFoundError: If employee not found.
            CannotLockAdminError: If trying to lock admin account.
        """
        nv = self._repo.find_by_id(nhan_vien_id)
        if not nv:
            raise NhanVienNotFoundError(f"Không tìm thấy nhân viên với ID {nhan_vien_id}")
        
        # Cannot lock admin
        if nv.username == "admin":
            raise CannotLockAdminError("Không thể khóa tài khoản admin")
        
        now = datetime.now().isoformat()
        self.conn.execute(
            """UPDATE nhan_vien 
               SET trang_thai = 'inactive', 
                   khoa_den = ?,
                   updated_at = ?
               WHERE id = ?""",
            (now, now, nhan_vien_id)
        )
        self.conn.commit()
        
        return self._repo.find_by_id(nhan_vien_id)
    
    @audit(action="UPDATE_NHAN_VIEN", table="nhan_vien")
    def unlock(self, nhan_vien_id: int) -> NhanVien:
        """Unlock an employee account.
        
        Resets trang_thai = 'active' and clears lockout counters.
        
        Args:
            nhan_vien_id: Employee ID to unlock.
            
        Returns:
            Updated NhanVien entity.
            
        Raises:
            NhanVienNotFoundError: If employee not found.
        """
        nv = self._repo.find_by_id(nhan_vien_id)
        if not nv:
            raise NhanVienNotFoundError(f"Không tìm thấy nhân viên với ID {nhan_vien_id}")
        
        self._repo.clear_lockout(nhan_vien_id)
        
        self.conn.execute(
            """UPDATE nhan_vien 
               SET trang_thai = 'active', 
                   updated_at = ?
               WHERE id = ?""",
            (datetime.now().isoformat(), nhan_vien_id)
        )
        self.conn.commit()
        
        return self._repo.find_by_id(nhan_vien_id)
    
    def calc_kpi(
        self,
        nhan_vien_id: int,
        from_date: str,
        to_date: str,
    ) -> Dict[str, Any]:
        """Calculate employee KPI for a date range.
        
        Queries hop_dong where:
        - nhan_vien_id matches
        - trang_thai = 'da_giao_xe'
        - ngay_giao_xe within date range
        
        Returns:
            Dict with keys:
            - so_hop_dong: number of successfully delivered contracts
            - doanh_thu: total revenue from those contracts
            - ti_le_chot: None (no lead tracking in current schema)
        
        Args:
            nhan_vien_id: Employee ID.
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).
            
        Returns:
            KPI dictionary.
        """
        cursor = self.conn.execute(
            """SELECT 
                   COUNT(*) as so_hop_dong,
                   COALESCE(SUM(tong_tien), 0) as doanh_thu
               FROM hop_dong 
               WHERE nhan_vien_id = ? 
                 AND trang_thai = 'da_giao_xe'
                 AND date(ngay_giao_xe) >= date(?)
                 AND date(ngay_giao_xe) <= date(?)""",
            (nhan_vien_id, from_date, to_date)
        )
        row = cursor.fetchone()
        
        return {
            'so_hop_dong': row[0] if row else 0,
            'doanh_thu': row[1] if row else 0,
            'ti_le_chot': None  # No lead tracking in current schema
        }
    
    def update_self(self, nhan_vien_id: int, data: Dict[str, str]) -> NhanVien:
        """Update own profile (A-02/A-03 can only update their own profile).
        
        Only allows updating: ho_ten, email, so_dien_thoai, dia_chi.
        Cannot change vai_tro or trang_thai.
        
        Args:
            nhan_vien_id: Employee ID.
            data: Dict with fields to update.
            
        Returns:
            Updated NhanVien entity.
            
        Raises:
            NhanVienNotFoundError: If employee not found.
            ValidationError: If trying to change restricted fields.
        """
        nv = self._repo.find_by_id(nhan_vien_id)
        if not nv:
            raise NhanVienNotFoundError(f"Không tìm thấy nhân viên với ID {nhan_vien_id}")
        
        # Check for restricted fields
        restricted = {'vai_tro_id', 'trang_thai', 'username', 'mat_khau_hash'}
        requested = set(data.keys())
        if requested & restricted:
            raise ValidationError(
                "Không thể thay đổi các trường: vai_tro_id, trang_thai, username, mat_khau_hash"
            )
        
        # Build update data (only allowed fields)
        allowed = {'ho_ten', 'email', 'so_dien_thoai', 'dia_chi'}
        update_data = {}
        
        for field in allowed & requested:
            value = data[field]
            if field == 'email':
                value = value.lower().strip()
                if not self._validate_email(value):
                    raise ValidationError("Email không hợp lệ", field="email")
                # Check uniqueness
                cursor = self.conn.execute(
                    "SELECT id FROM nhan_vien WHERE email = ? AND id != ?",
                    (value, nhan_vien_id)
                )
                if cursor.fetchone():
                    raise DuplicateEmailError(f"Email '{value}' đã được sử dụng")
            update_data[field] = value.strip() if isinstance(value, str) else value
        
        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(nhan_vien_id)
            
            self.conn.execute(
                f"UPDATE nhan_vien SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()
        
        return self._repo.find_by_id(nhan_vien_id)
    
    def get_current_month_kpi(self, nhan_vien_id: int) -> Dict[str, Any]:
        """Get employee KPI for current month.
        
        Args:
            nhan_vien_id: Employee ID.
            
        Returns:
            KPI dictionary.
        """
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Build date range for the month
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"
        
        return self.calc_kpi(nhan_vien_id, start_date, end_date)
