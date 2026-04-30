"""KhachHang service - customer business logic layer.

Implements business rules:
- BR-KH-01: Required fields (ho_ten, so_dien_thoai, email)
- BR-KH-02: so_dien_thoai must be unique
- BR-KH-03: Classification auto-update based on BR-CALC-03
- BR-KH-04: Purchase history includes all contracts including cancelled
- BR-KH-05: Cannot delete customer with contracts → mark inactive
- BR-KH-06: Email valid (BR-DATA-04), SĐT VN (BR-DATA-05)
- BR-CALC-03: Customer classification thresholds
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import KhachHang
from app.infrastructure.repositories.khach_hang_repository import KhachHangRepository, KhachHangSearchFilter
from app.application.validators.khach_hang_validator import KhachHangValidator


class KhachHangServiceError(Exception):
    """Base exception for KhachHang service errors."""
    pass


class ValidationError(KhachHangServiceError):
    """Validation error with field-specific messages."""
    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        super().__init__(message)
        self.field = field
        self.errors = errors or []


class DuplicatePhoneError(KhachHangServiceError):
    """Raised when phone number already exists."""
    pass


class DuplicateEmailError(KhachHangServiceError):
    """Raised when email already exists."""
    pass


class DeleteNotAllowedError(KhachHangServiceError):
    """Raised when deletion is not allowed due to constraints."""
    pass


class KhachHangNotFoundError(KhachHangServiceError):
    """Raised when customer is not found."""
    pass


@dataclass
class KhachHangCreateData:
    """Data for creating a new customer."""
    ho_ten: str
    so_dien_thoai: str
    email: str
    dia_chi: str = ""
    ngay_sinh: str = None
    phan_loai: str = "Thuong"
    created_by: int = None


@dataclass
class KhachHangUpdateData:
    """Data for updating a customer."""
    ho_ten: str = None
    so_dien_thoai: str = None
    email: str = None
    dia_chi: str = None
    ngay_sinh: str = None
    phan_loai: str = None


@dataclass
class KhachHangSearchResult:
    """Search result with metadata."""
    items: List[KhachHang]
    total: int
    page: int
    page_size: int
    total_pages: int


class KhachHangService:
    """Service for customer management operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.
        
        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = KhachHangRepository(conn)
    
    def get_by_id(self, khach_hang_id: int) -> Optional[KhachHang]:
        """Get customer by ID.
        
        Args:
            khach_hang_id: Customer ID.
            
        Returns:
            KhachHang if found, None otherwise.
        """
        return self._repo.find_by_id(khach_hang_id)
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[KhachHang]:
        """Get all customers with pagination.
        
        Args:
            limit: Maximum results.
            offset: Offset for pagination.
            
        Returns:
            List of KhachHang entities.
        """
        return self._repo.find_all(limit, offset)
    
    def get_by_phone(self, phone: str) -> Optional[KhachHang]:
        """Get customer by phone number.
        
        Args:
            phone: Phone number.
            
        Returns:
            KhachHang if found, None otherwise.
        """
        return self._repo.find_by_phone(phone)
    
    def get_by_email(self, email: str) -> Optional[KhachHang]:
        """Get customer by email.
        
        Args:
            email: Email address.
            
        Returns:
            KhachHang if found, None otherwise.
        """
        return self._repo.find_by_email(email)
    
    def create(self, data: KhachHangCreateData, nhan_vien_id: int = None) -> KhachHang:
        """Create a new customer.
        
        Validates:
        - BR-KH-01: Required fields (ho_ten, so_dien_thoai, email)
        - BR-KH-02: so_dien_thoai must be unique
        - BR-KH-06: Email valid, SĐT VN format
        
        Args:
            data: KhachHangCreateData with customer data.
            nhan_vien_id: ID of creating user (for audit).
            
        Returns:
            Created KhachHang entity.
            
        Raises:
            ValidationError: If validation fails.
            DuplicatePhoneError: If phone already exists.
            DuplicateEmailError: If email already exists.
        """
        # Build validation dict
        validation_dict = {
            "ho_ten": data.ho_ten,
            "so_dien_thoai": data.so_dien_thoai,
            "email": data.email,
            "ngay_sinh": data.ngay_sinh,
        }
        
        # Validate
        result = KhachHangValidator.validate_create(validation_dict)
        if not result.is_valid:
            raise ValidationError(
                "; ".join(result.errors),
                errors=result.errors
            )
        
        # Check phone uniqueness (BR-KH-02)
        if self._repo.exists_by_phone(data.so_dien_thoai):
            raise DuplicatePhoneError(
                f"Số điện thoại '{data.so_dien_thoai}' đã được sử dụng bởi khách hàng khác"
            )
        
        # Check email uniqueness (optional - good practice)
        if self._repo.exists_by_email(data.email):
            raise DuplicateEmailError(
                f"Email '{data.email}' đã được sử dụng bởi khách hàng khác"
            )
        
        # Create entity
        kh = KhachHang(
            ho_ten=data.ho_ten,
            so_dien_thoai=data.so_dien_thoai.replace(" ", "").replace("-", ""),  # Normalize
            email=data.email.lower(),
            dia_chi=data.dia_chi or "",
            ngay_sinh=data.ngay_sinh,
            phan_loai=data.phan_loai,
            created_by=data.created_by,
        )
        
        return self._repo.create(kh)
    
    def update(self, khach_hang_id: int, data: KhachHangUpdateData, nhan_vien_id: int = None) -> KhachHang:
        """Update a customer.
        
        Args:
            khach_hang_id: Customer ID to update.
            data: KhachHangUpdateData with fields to update.
            nhan_vien_id: ID of updating user (for audit).
            
        Returns:
            Updated KhachHang entity.
            
        Raises:
            KhachHangNotFoundError: If customer not found.
            ValidationError: If validation fails.
            DuplicatePhoneError: If phone already exists.
        """
        # Get current customer
        kh = self._repo.find_by_id(khach_hang_id)
        if not kh:
            raise KhachHangNotFoundError(f"Không tìm thấy khách hàng với ID {khach_hang_id}")
        
        # Build validation dict
        validation_dict = {}
        if data.ho_ten is not None:
            validation_dict["ho_ten"] = data.ho_ten
        if data.so_dien_thoai is not None:
            validation_dict["so_dien_thoai"] = data.so_dien_thoai
        if data.email is not None:
            validation_dict["email"] = data.email
        if data.ngay_sinh is not None:
            validation_dict["ngay_sinh"] = data.ngay_sinh
        
        # Validate
        result = KhachHangValidator.validate_update(validation_dict)
        if not result.is_valid:
            raise ValidationError(
                "; ".join(result.errors),
                errors=result.errors
            )
        
        # Check phone uniqueness if changing
        if data.so_dien_thoai is not None:
            phone_normalized = data.so_dien_thoai.replace(" ", "").replace("-", "")
            if self._repo.exists_by_phone(phone_normalized, exclude_id=khach_hang_id):
                raise DuplicatePhoneError(
                    f"Số điện thoại '{data.so_dien_thoai}' đã được sử dụng bởi khách hàng khác"
                )
        
        # Check email uniqueness if changing
        if data.email is not None:
            if self._repo.exists_by_email(data.email.lower(), exclude_id=khach_hang_id):
                raise DuplicateEmailError(
                    f"Email '{data.email}' đã được sử dụng bởi khách hàng khác"
                )
        
        # Update fields
        update_data = {}
        if data.ho_ten is not None:
            update_data["ho_ten"] = data.ho_ten
        if data.so_dien_thoai is not None:
            update_data["so_dien_thoai"] = data.so_dien_thoai.replace(" ", "").replace("-", "")
        if data.email is not None:
            update_data["email"] = data.email.lower()
        if data.dia_chi is not None:
            update_data["dia_chi"] = data.dia_chi
        if data.ngay_sinh is not None:
            update_data["ngay_sinh"] = data.ngay_sinh
        if data.phan_loai is not None:
            update_data["phan_loai"] = data.phan_loai
        
        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(khach_hang_id)
            
            self.conn.execute(
                f"UPDATE khach_hang SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()
        
        return self._repo.find_by_id(khach_hang_id)
    
    def delete(self, khach_hang_id: int, nhan_vien_id: int = None) -> bool:
        """Delete a customer.
        
        BR-KH-05: Cannot delete if has active contracts → mark inactive instead.
        
        Args:
            khach_hang_id: Customer ID to delete.
            nhan_vien_id: ID of deleting user (for audit).
            
        Returns:
            True if deleted, False if marked inactive.
            
        Raises:
            KhachHangNotFoundError: If customer not found.
        """
        # Check customer exists
        kh = self._repo.find_by_id(khach_hang_id)
        if not kh:
            raise KhachHangNotFoundError(f"Không tìm thấy khách hàng với ID {khach_hang_id}")
        
        # BR-KH-05: Check for active contracts
        if self._repo.has_active_contracts(khach_hang_id):
            # Mark as inactive instead of deleting
            self.conn.execute(
                """UPDATE khach_hang SET trang_thai = 'inactive', updated_at = ? WHERE id = ?""",
                (datetime.now().isoformat(), khach_hang_id)
            )
            self.conn.commit()
            return False
        
        return self._repo.delete(khach_hang_id)
    
    def search(
        self,
        keyword: str = None,
        phan_loai: str = None,
        birthday_days: int = None,
        page: int = 1,
        page_size: int = 50,
    ) -> KhachHangSearchResult:
        """Search customers with filters.
        
        Args:
            keyword: Keyword search (name, phone, email).
            phan_loai: Filter by classification.
            birthday_days: Find customers with birthday within N days.
            page: Page number (1-indexed).
            page_size: Results per page.
            
        Returns:
            KhachHangSearchResult with items and pagination info.
        """
        filter = KhachHangSearchFilter(
            keyword=keyword,
            phan_loai=phan_loai,
            from_birthday_days=birthday_days,
        )
        
        offset = (page - 1) * page_size
        items = self._repo.search(filter, limit=page_size, offset=offset)
        total = self._repo.count_search(filter)
        total_pages = max(1, (total + page_size - 1) // page_size)
        
        return KhachHangSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    def update_classification(self, khach_hang_id: int) -> KhachHang:
        """Update customer's classification based on purchase value.
        
        BR-CALC-03: Auto-calculate based on tong_gia_tri_mua
        - Thường: < 500 triệu
        - Thân thiết: >= 500 triệu and < 1.5 tỷ
        - VIP: >= 1.5 tỷ
        
        This is called after a contract is completed (da_giao_xe).
        
        Args:
            khach_hang_id: Customer ID.
            
        Returns:
            Updated KhachHang entity.
        """
        kh = self._repo.find_by_id(khach_hang_id)
        if not kh:
            raise KhachHangNotFoundError(f"Không tìm thấy khách hàng với ID {khach_hang_id}")
        
        new_phan_loai = KhachHangValidator.calculate_phan_loai(kh.tong_gia_tri_mua)
        
        if kh.phan_loai != new_phan_loai:
            self._repo.update_classification(khach_hang_id, new_phan_loai)
        
        return self._repo.find_by_id(khach_hang_id)
    
    def get_purchase_history(self, khach_hang_id: int) -> dict:
        """Get customer's complete purchase history.
        
        BR-KH-04: Includes all contracts including cancelled, warranties, complaints.
        
        Args:
            khach_hang_id: Customer ID.
            
        Returns:
            Dict with contracts, warranties, complaints lists.
        """
        kh = self._repo.find_by_id(khach_hang_id)
        if not kh:
            raise KhachHangNotFoundError(f"Không tìm thấy khách hàng với ID {khach_hang_id}")
        
        return self._repo.get_purchase_history(khach_hang_id)
    
    def get_upcoming_birthdays(self, days: int = 7) -> List[KhachHang]:
        """Get customers with upcoming birthdays.
        
        Args:
            days: Number of days to look ahead.
            
        Returns:
            List of KhachHang with birthdays within the window.
        """
        return self._repo.find_birthday_window(days)
    
    def check_phone_exists(self, phone: str, exclude_id: int = None) -> bool:
        """Check if phone already exists.
        
        Args:
            phone: Phone number to check.
            exclude_id: Customer ID to exclude (for updates).
            
        Returns:
            True if exists, False otherwise.
        """
        return self._repo.exists_by_phone(phone, exclude_id)
    
    def check_email_exists(self, email: str, exclude_id: int = None) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check.
            exclude_id: Customer ID to exclude (for updates).
            
        Returns:
            True if exists, False otherwise.
        """
        return self._repo.exists_by_email(email, exclude_id)
    
    def update_purchase_stats_after_contract(
        self,
        khach_hang_id: int,
        contract_total: int,
    ) -> None:
        """Update customer purchase stats after contract completion.
        
        Called when a contract reaches da_giao_xe status.
        Updates tong_gia_tri_mua, so_xe_da_mua, and recalculates classification.
        
        Args:
            khach_hang_id: Customer ID.
            contract_total: Total value of the contract.
        """
        kh = self._repo.find_by_id(khach_hang_id)
        if not kh:
            return
        
        new_tong_gia_tri = kh.tong_gia_tri_mua + contract_total
        new_so_xe = kh.so_xe_da_mua + 1
        
        self._repo.update_purchase_stats(khach_hang_id, new_tong_gia_tri, new_so_xe)
        
        # Recalculate classification
        new_phan_loai = KhachHangValidator.calculate_phan_loai(new_tong_gia_tri)
        self._repo.update_classification(khach_hang_id, new_phan_loai)
