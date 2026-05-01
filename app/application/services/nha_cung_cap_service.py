"""NhaCungCap service - supplier business logic layer.

Implements business rules:
- BR-NCC-01: CRUD operations with validation
- BR-NCC-02: Rating system (3 criteria: chat_luong, thoi_gian_giao, gia_ca)
- BR-NCC-03: avg_rating = (chat_luong + thoi_gian_giao + gia_ca) / 3
- BR-NCC-06: Cannot delete supplier with nhap_kho history

BE Tasks:
- T-G4.4.BE.01: CRUD + validate
- T-G4.4.BE.02: add_rating(ncc_id, ratings)
- T-G4.4.BE.03: calculate_avg_rating(ncc_id)
- T-G4.4.BE.06: Audit + permission @audit('CRUD_NCC')
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.infrastructure.repositories.nha_cung_cap_repository import NhaCungCapRepository
from app.application.services.audit_log_service import AuditLogService


class NhaCungCapServiceError(Exception):
    """Base exception for NhaCungCap service errors."""
    pass


class ValidationError(NhaCungCapServiceError):
    """Raised when validation fails."""
    pass


class DuplicateCodeError(NhaCungCapServiceError):
    """Raised when supplier code already exists."""
    pass


class NotFoundError(NhaCungCapServiceError):
    """Raised when supplier is not found."""
    pass


class DeleteNotAllowedError(NhaCungCapServiceError):
    """Raised when delete is not allowed."""
    pass


@dataclass
class NhaCungCapCreateData:
    """Data for creating a new supplier."""
    ma_ncc: str
    ten_ncc: str
    dia_chi: str = ""
    so_dien_thoai: str = ""
    email: str = ""
    nguoi_lien_he: str = ""
    created_by: int = None


@dataclass
class NhaCungCapUpdateData:
    """Data for updating a supplier."""
    ten_ncc: str = None
    dia_chi: str = None
    so_dien_thoai: str = None
    email: str = None
    nguoi_lien_he: str = None


@dataclass
class NhaCungCapSearchResult:
    """Search result with metadata."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


def audit(action: str):
    """Decorator for audit logging on service methods."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            # Log audit after method execution
            nhan_vien_id = getattr(self, '_nhan_vien_id', None)
            if result and hasattr(result, 'id'):
                self._audit_log(action, result, nhan_vien_id)
            elif result and isinstance(result, dict) and result.get('id'):
                self._audit_log_dict(action, result, nhan_vien_id)
            return result
        return wrapper
    return decorator


def require_permission(resource: str, actions: str):
    """Decorator for permission checking."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # For now, allow all - actual permission check would need session context
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class NhaCungCapService:
    """Service for supplier management operations."""

    def __init__(self, conn: sqlite3.Connection, nhan_vien_id: int = None):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
            nhan_vien_id: ID of current user for audit logging.
        """
        self.conn = conn
        self._repo = NhaCungCapRepository(conn)
        self._audit_service = AuditLogService(conn)
        self._nhan_vien_id = nhan_vien_id

    def _validate_email(self, email: str) -> bool:
        """Validate email format (BR-DATA-04)."""
        if not email:
            return True  # Email can be empty
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        """Validate Vietnamese phone format (BR-DATA-05)."""
        if not phone:
            return True  # Phone can be empty
        # Remove spaces and dashes
        phone_clean = phone.replace(" ", "").replace("-", "")
        # VN phone: 10-11 digits starting with 0
        pattern = r"^0[0-9]{9,10}$"
        return bool(re.match(pattern, phone_clean))

    def _audit_log(self, action: str, entity, nhan_vien_id: int):
        """Log audit for entity operations."""
        if hasattr(entity, 'to_dict'):
            data = entity.to_dict() if hasattr(entity, 'to_dict') else dict(entity)
        else:
            data = dict(entity) if entity else {}
        self._audit_service.log_create(
            action=action,
            nhan_vien_id=nhan_vien_id,
            table="nha_cung_cap",
            record_id=data.get("id"),
            record_data=data,
        )

    def _audit_log_dict(self, action: str, data: dict, nhan_vien_id: int):
        """Log audit for dict-based operations."""
        self._audit_service.log_create(
            action=action,
            nhan_vien_id=nhan_vien_id,
            table="nha_cung_cap",
            record_id=data.get("id"),
            record_data=data,
        )

    # === T-G4.4.BE.01: CRUD + validate ===

    def create(self, data: NhaCungCapCreateData) -> Dict[str, Any]:
        """Create a new supplier.

        Validates:
        - ma_ncc: unique, not empty
        - ten_ncc: not empty
        - email: valid format (BR-DATA-04)
        - so_dien_thoai: VN format (BR-DATA-05)

        Args:
            data: NhaCungCapCreateData with supplier data.

        Returns:
            Created supplier dict.

        Raises:
            ValidationError: If validation fails.
            DuplicateCodeError: If ma_ncc already exists.
        """
        # Validate required fields
        if not data.ten_ncc or not data.ten_ncc.strip():
            raise ValidationError("Tên nhà cung cấp không được trống", field="ten_ncc")

        # Validate email
        if data.email and not self._validate_email(data.email):
            raise ValidationError("Email không hợp lệ", field="email")

        # Validate phone
        if data.so_dien_thoai and not self._validate_phone(data.so_dien_thoai):
            raise ValidationError("Số điện thoại không hợp lệ (cần 10-11 số bắt đầu bằng 0)", field="so_dien_thoai")

        # Check ma_ncc uniqueness
        if self._repo.exists_by_ma_ncc(data.ma_ncc):
            raise DuplicateCodeError(f"Mã nhà cung cấp '{data.ma_ncc}' đã tồn tại")

        # Prepare data
        now = datetime.now().isoformat()
        ncc_data = {
            "ma_ncc": data.ma_ncc.strip(),
            "ten_ncc": data.ten_ncc.strip(),
            "dia_chi": data.dia_chi or "",
            "so_dien_thoai": data.so_dien_thoai or "",
            "email": data.email or "",
            "nguoi_lien_he": data.nguoi_lien_he or "",
            "diem_chat_luong": 0,
            "diem_thoi_gian_giao": 0,
            "diem_gia_ca": 0,
            "diem_tong": 0,
            "created_by": data.created_by or self._nhan_vien_id,
        }

        created = self._repo.create(ncc_data)

        # Audit log
        self._audit_service.log_create(
            action="CRUD_NCC",
            nhan_vien_id=self._nhan_vien_id,
            table="nha_cung_cap",
            record_id=created["id"],
            record_data=created,
        )

        return created

    def update(self, id: int, data: NhaCungCapUpdateData) -> Dict[str, Any]:
        """Update a supplier.

        Args:
            id: Supplier ID.
            data: NhaCungCapUpdateData with fields to update.

        Returns:
            Updated supplier dict.

        Raises:
            NotFoundError: If supplier not found.
            ValidationError: If validation fails.
        """
        # Check exists
        existing = self._repo.find_by_id(id)
        if not existing:
            raise NotFoundError(f"Không tìm thấy nhà cung cấp với ID {id}")

        # Validate email if provided
        if data.email is not None and data.email and not self._validate_email(data.email):
            raise ValidationError("Email không hợp lệ", field="email")

        # Validate phone if provided
        if data.so_dien_thoai is not None and data.so_dien_thoai and not self._validate_phone(data.so_dien_thoai):
            raise ValidationError("Số điện thoại không hợp lệ", field="so_dien_thoai")

        # Build update dict
        update_data = {}
        if data.ten_ncc is not None:
            update_data["ten_ncc"] = data.ten_ncc.strip()
        if data.dia_chi is not None:
            update_data["dia_chi"] = data.dia_chi
        if data.so_dien_thoai is not None:
            update_data["so_dien_thoai"] = data.so_dien_thoai
        if data.email is not None:
            update_data["email"] = data.email
        if data.nguoi_lien_he is not None:
            update_data["nguoi_lien_he"] = data.nguoi_lien_he

        if update_data:
            self._repo.update(id, update_data)

        # Audit log
        after = self._repo.find_by_id(id)
        self._audit_service.log_update(
            action="CRUD_NCC",
            nhan_vien_id=self._nhan_vien_id,
            table="nha_cung_cap",
            record_id=id,
            before=existing,
            after=after,
        )

        return after

    def delete(self, id: int) -> bool:
        """Delete a supplier.

        BR-NCC-06: Cannot delete if has nhap_kho history.

        Args:
            id: Supplier ID.

        Returns:
            True if deleted.

        Raises:
            NotFoundError: If supplier not found.
            DeleteNotAllowedError: If supplier has nhap_kho history.
        """
        # Check exists
        existing = self._repo.find_by_id(id)
        if not existing:
            raise NotFoundError(f"Không tìm thấy nhà cung cấp với ID {id}")

        # BR-NCC-06: Check nhap_kho history
        if self._repo.has_nhap_kho_history(id):
            raise DeleteNotAllowedError(
                "Không thể xóa nhà cung cấp đã có lịch sử nhập kho"
            )

        result = self._repo.delete(id)

        # Audit log
        self._audit_service.log_delete(
            action="CRUD_NCC",
            nhan_vien_id=self._nhan_vien_id,
            table="nha_cung_cap",
            record_id=id,
            before=existing,
        )

        return result

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Get supplier by ID.

        Args:
            id: Supplier ID.

        Returns:
            Supplier dict if found, None otherwise.
        """
        return self._repo.find_by_id(id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all suppliers.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of supplier dicts.
        """
        return self._repo.find_all(limit, offset)

    def search(
        self,
        keyword: str = None,
        min_rating: float = None,
        max_rating: float = None,
        page: int = 1,
        page_size: int = 50,
    ) -> NhaCungCapSearchResult:
        """Search suppliers with filters.

        Args:
            keyword: Search in ma_ncc, ten_ncc.
            min_rating: Minimum avg rating (1-5).
            max_rating: Maximum avg rating (1-5).
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            NhaCungCapSearchResult with items and pagination.
        """
        offset = (page - 1) * page_size
        items = self._repo.search(keyword, min_rating, max_rating, page_size, offset)
        total = self._repo.count_search(keyword, min_rating, max_rating)
        total_pages = max(1, (total + page_size - 1) // page_size)

        return NhaCungCapSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # === T-G4.4.BE.02: add_rating ===

    def add_rating(self, ncc_id: int, ratings: Dict[str, int]) -> Dict[str, Any]:
        """Add/update supplier ratings.

        BR-NCC-02: Store 3 ratings (1-5 each):
        - chat_luong: Quality rating
        - thoi_gian_giao: Delivery time rating
        - gia_ca: Price rating

        diem_tong = sum of 3 ratings
        avg_rating = diem_tong / 3

        Args:
            ncc_id: Supplier ID.
            ratings: Dict with chat_luong, thoi_gian_giao, gia_ca (each 1-5).

        Returns:
            Updated supplier dict with new ratings.

        Raises:
            NotFoundError: If supplier not found.
            ValidationError: If ratings invalid.
        """
        existing = self._repo.find_by_id(ncc_id)
        if not existing:
            raise NotFoundError(f"Không tìm thấy nhà cung cấp với ID {ncc_id}")

        # Validate ratings
        chat_luong = ratings.get("chat_luong", 0)
        thoi_gian_giao = ratings.get("thoi_gian_giao", 0)
        gia_ca = ratings.get("gia_ca", 0)

        for name, value in [("chat_luong", chat_luong), ("thoi_gian_giao", thoi_gian_giao), ("gia_ca", gia_ca)]:
            if not isinstance(value, int) or value < 1 or value > 5:
                raise ValidationError(f"Điểm {name} phải từ 1 đến 5", field=name)

        # Update ratings
        self._repo.update_ratings(ncc_id, chat_luong, thoi_gian_giao, gia_ca)

        # Audit log
        after = self._repo.find_by_id(ncc_id)
        self._audit_service.log_update(
            action="CRUD_NCC",
            nhan_vien_id=self._nhan_vien_id,
            table="nha_cung_cap",
            record_id=ncc_id,
            before=existing,
            after=after,
        )

        return after

    # === T-G4.4.BE.03: calculate_avg_rating ===

    def calculate_avg_rating(self, ncc_id: int) -> float:
        """Calculate average rating for a supplier.

        BR-NCC-03: avg = (chat_luong + thoi_gian_giao + gia_ca) / 3

        Args:
            ncc_id: Supplier ID.

        Returns:
            Average rating (0-5).

        Raises:
            NotFoundError: If supplier not found.
        """
        ncc = self._repo.find_by_id(ncc_id)
        if not ncc:
            raise NotFoundError(f"Không tìm thấy nhà cung cấp với ID {ncc_id}")

        if ncc["diem_tong"] == 0:
            return 0.0

        return round(ncc["diem_tong"] / 3, 2)