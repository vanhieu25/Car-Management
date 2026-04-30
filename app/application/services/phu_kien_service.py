"""PhuKien service - accessory business logic layer.

Implements business rules:
- BR-PK-01: Phan loai (noi_that, ngoai_that, dien_tu, bao_ve, trang_tri)
- BR-PK-04: Combo must have >= 2 accessories
- BR-PK-05: ton_kho >= 0, gia_ban >= 0; highlight red when out of stock
- BR-PK-06: Cannot delete if referenced by active contracts
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import PhuKien
from app.infrastructure.repositories.phu_kien_repository import PhuKienRepository, PhuKienSearchFilter
from app.application.services.audit_decorator import audit
from app.application.services.decorators import require_permission


class PhuKienServiceError(Exception):
    """Base exception for PhuKien service errors."""
    pass


class ValidationError(PhuKienServiceError):
    """Validation error with field-specific messages."""
    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        super().__init__(message)
        self.field = field
        self.errors = errors or []


class DuplicateMaPkError(PhuKienServiceError):
    """Raised when ma_pk already exists."""
    pass


class DeleteNotAllowedError(PhuKienServiceError):
    """Raised when deletion is not allowed due to constraints."""
    pass


class PhuKienNotFoundError(PhuKienServiceError):
    """Raised when accessory is not found."""
    pass


class InventoryError(PhuKienServiceError):
    """Raised when inventory operation would result in negative stock."""
    pass


VALID_PHAN_LOAI = ["noi_that", "ngoai_that", "dien_tu", "bao_ve", "trang_tri"]


@dataclass
class PhuKienCreateData:
    """Data for creating a new accessory."""
    ten_pk: str
    phan_loai: str
    gia_ban: int
    ton_kho: int = 0
    mo_ta: str = ""
    created_by: int = None


@dataclass
class PhuKienUpdateData:
    """Data for updating an accessory."""
    ten_pk: str = None
    phan_loai: str = None
    gia_ban: int = None
    ton_kho: int = None
    mo_ta: str = None


@dataclass
class PhuKienSearchResult:
    """Search result with metadata."""
    items: List[PhuKien]
    total: int
    page: int
    page_size: int
    total_pages: int


class PhuKienService:
    """Service for accessory management operations."""

    def __init__(self, conn: sqlite3.Connection, session=None):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
            session: Current user session (optional, for audit/permission).
        """
        self.conn = conn
        self._repo = PhuKienRepository(conn)
        self._session = session

    def get_by_id(self, pk_id: int) -> Optional[PhuKien]:
        """Get accessory by ID.

        Args:
            pk_id: Accessory ID.

        Returns:
            PhuKien if found, None otherwise.
        """
        return self._repo.find_by_id(pk_id)

    def get_by_ma(self, ma_pk: str) -> Optional[PhuKien]:
        """Get accessory by ma_pk code.

        Args:
            ma_pk: Accessory code.

        Returns:
            PhuKien if found, None otherwise.
        """
        return self._repo.find_by_ma(ma_pk)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[PhuKien]:
        """Get all accessories with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of PhuKien entities.
        """
        return self._repo.find_all(limit, offset)

    def get_available(self) -> List[PhuKien]:
        """Get all accessories with stock > 0.

        Returns:
            List of available PhuKien entities.
        """
        return self._repo.get_available()

    @audit("CRUD_PK", table="phu_kien")
    @require_permission("phu_kien", "create")
    def create(self, data: PhuKienCreateData) -> PhuKien:
        """Create a new accessory.

        Validates:
        - BR-PK-05: ten_pk >= 3 chars, gia_ban >= 0, ton_kho >= 0

        Args:
            data: PhuKienCreateData with accessory data.

        Returns:
            Created PhuKien entity.

        Raises:
            ValidationError: If validation fails.
            DuplicateMaPkError: If ma_pk already exists.
        """
        errors = []

        # Validate ten_pk >= 3 chars (BR-PK-05)
        if not data.ten_pk or len(data.ten_pk.strip()) < 3:
            errors.append("Tên phụ kiện phải có ít nhất 3 ký tự")

        # Validate phan_loai
        if data.phan_loai not in VALID_PHAN_LOAI:
            errors.append(f"Phân loại không hợp lệ. Các loại hợp lệ: {', '.join(VALID_PHAN_LOAI)}")

        # Validate gia_ban >= 0 (BR-PK-05)
        if data.gia_ban < 0:
            errors.append("Giá bán không được nhỏ hơn 0")

        # Validate ton_kho >= 0 (BR-PK-05)
        if data.ton_kho < 0:
            errors.append("Tồn kho không được nhỏ hơn 0")

        if errors:
            raise ValidationError("; ".join(errors), errors=errors)

        # Generate ma_pk
        ma_pk = self._generate_ma_pk()

        # Create entity
        pk = PhuKien(
            ma_pk=ma_pk,
            ten_pk=data.ten_pk.strip(),
            phan_loai=data.phan_loai,
            gia_ban=data.gia_ban,
            ton_kho=data.ton_kho,
            mo_ta=data.mo_ta or "",
            created_by=data.created_by,
        )

        return self._repo.create(pk)

    def _generate_ma_pk(self) -> str:
        """Generate unique ma_pk code.

        Returns:
            New unique ma_pk code (format: PK-XXXXX).
        """
        cursor = self.conn.execute(
            "SELECT MAX(CAST(SUBSTR(ma_pk, 4) AS INTEGER)) FROM phu_kien WHERE ma_pk LIKE 'PK-%'"
        )
        result = cursor.fetchone()[0]
        next_num = (result or 0) + 1
        return f"PK-{next_num:05d}"

    @audit("UPDATE_PK", table="phu_kien", id_param=0)
    @require_permission("phu_kien", "update")
    def update(self, pk_id: int, data: PhuKienUpdateData) -> PhuKien:
        """Update an accessory.

        Args:
            pk_id: Accessory ID to update.
            data: PhuKienUpdateData with fields to update.

        Returns:
            Updated PhuKien entity.

        Raises:
            PhuKienNotFoundError: If accessory not found.
            ValidationError: If validation fails.
        """
        # Get current accessory
        pk = self._repo.find_by_id(pk_id)
        if not pk:
            raise PhuKienNotFoundError(f"Không tìm thấy phụ kiện với ID {pk_id}")

        errors = []

        # Validate ten_pk >= 3 chars if provided
        if data.ten_pk is not None:
            if len(data.ten_pk.strip()) < 3:
                errors.append("Tên phụ kiện phải có ít nhất 3 ký tự")

        # Validate phan_loai if provided
        if data.phan_loai is not None and data.phan_loai not in VALID_PHAN_LOAI:
            errors.append(f"Phân loại không hợp lệ. Các loại hợp lệ: {', '.join(VALID_PHAN_LOAI)}")

        # Validate gia_ban >= 0 if provided
        if data.gia_ban is not None and data.gia_ban < 0:
            errors.append("Giá bán không được nhỏ hơn 0")

        # Validate ton_kho >= 0 if provided
        if data.ton_kho is not None and data.ton_kho < 0:
            errors.append("Tồn kho không được nhỏ hơn 0")

        if errors:
            raise ValidationError("; ".join(errors), errors=errors)

        # Update fields
        update_data = {}
        if data.ten_pk is not None:
            update_data["ten_pk"] = data.ten_pk.strip()
        if data.phan_loai is not None:
            update_data["phan_loai"] = data.phan_loai
        if data.gia_ban is not None:
            update_data["gia_ban"] = data.gia_ban
        if data.ton_kho is not None:
            update_data["ton_kho"] = data.ton_kho
        if data.mo_ta is not None:
            update_data["mo_ta"] = data.mo_ta

        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()

            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(pk_id)

            self.conn.execute(
                f"UPDATE phu_kien SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()

        return self._repo.find_by_id(pk_id)

    @audit("DELETE_PK", table="phu_kien", id_param=0)
    @require_permission("phu_kien", "delete")
    def delete(self, pk_id: int) -> bool:
        """Delete an accessory.

        BR-PK-06: Cannot delete if referenced by active contracts.

        Args:
            pk_id: Accessory ID to delete.

        Returns:
            True if deleted.

        Raises:
            PhuKienNotFoundError: If accessory not found.
            DeleteNotAllowedError: If referenced by active contracts.
        """
        # Check accessory exists
        pk = self._repo.find_by_id(pk_id)
        if not pk:
            raise PhuKienNotFoundError(f"Không tìm thấy phụ kiện với ID {pk_id}")

        # BR-PK-06: Check for active contracts
        if self._repo.has_active_contracts(pk_id):
            raise DeleteNotAllowedError(
                f"Không thể xóa phụ kiện '{pk.ten_pk}' vì đang được tham chiếu bởi hợp đồng đang hoạt động"
            )

        return self._repo.delete(pk_id)

    def adjust_inventory(self, pk_id: int, delta: int) -> PhuKien:
        """Adjust accessory inventory by delta.

        BR-PK-05: Cannot go negative - raise error if result < 0.
        Used when contracts are paid (add stock) or cancelled (remove stock).

        Args:
            pk_id: Accessory ID.
            delta: Change in inventory (positive = add, negative = remove).

        Returns:
            Updated PhuKien entity.

        Raises:
            PhuKienNotFoundError: If accessory not found.
            InventoryError: If result would be negative.
        """
        pk = self._repo.find_by_id(pk_id)
        if not pk:
            raise PhuKienNotFoundError(f"Không tìm thấy phụ kiện với ID {pk_id}")

        new_ton_kho = pk.ton_kho + delta

        # BR-PK-05: Cannot go negative
        if new_ton_kho < 0:
            raise InventoryError(
                f"Không thể điều chỉnh tồn kho: sẽ âm ({new_ton_kho}). "
                f"Tồn kho hiện tại: {pk.ton_kho}, yêu cầu: {delta}"
            )

        self._repo.update_inventory(pk_id, new_ton_kho)
        return self._repo.find_by_id(pk_id)

    def search(
        self,
        keyword: str = None,
        phan_loai: str = None,
        het_hang: bool = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PhuKienSearchResult:
        """Search accessories with filters.

        Args:
            keyword: Keyword search (ma_pk, ten_pk).
            phan_loai: Filter by category.
            het_hang: Filter by out-of-stock status.
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            PhuKienSearchResult with items and pagination info.
        """
        filter = PhuKienSearchFilter(
            keyword=keyword,
            phan_loai=phan_loai,
            het_hang=het_hang,
        )

        offset = (page - 1) * page_size
        items = self._repo.search(filter, limit=page_size, offset=offset)
        total = self._repo.count_search(filter)
        total_pages = max(1, (total + page_size - 1) // page_size)

        return PhuKienSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_by_phan_loai(self, phan_loai: str) -> List[PhuKien]:
        """Get all accessories by category.

        Args:
            phan_loai: Category (noi_that, ngoai_that, dien_tu, bao_ve, trang_tri).

        Returns:
            List of PhuKien entities.
        """
        return self._repo.get_all_by_phan_loai(phan_loai)
