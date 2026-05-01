"""BaoDuong service - maintenance business logic layer.

Implements business rules:
- BR-TIME-02: Find BD appointments within N days (find_upcoming)
- BR-HM-01: Create/Update/Delete bao duong records
- BR-HM-02: Status flow for bao duong
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import BaoDuong
from app.infrastructure.repositories.bao_duong_repository import BaoDuongRepository


class BaoDuongServiceError(Exception):
    """Base exception for BaoDuong service errors."""
    pass


class ValidationError(BaoDuongServiceError):
    """Validation error with field-specific messages."""
    pass


class BaoDuongNotFoundError(BaoDuongServiceError):
    """Raised when BaoDuong record is not found."""
    pass


class DeleteNotAllowedError(BaoDuongServiceError):
    """Raised when deletion is not allowed."""
    pass


@dataclass
class BaoDuongCreateData:
    """Data for creating a new bao_duong record."""
    khach_hang_id: int
    xe_id: int
    ngay_du_kien: str
    chi_phi: int = 0
    km_xe: int = 0
    noi_dung: str = ""
    nhan_vien_id: Optional[int] = None
    ghi_chu: str = ""
    created_by: Optional[int] = None


@dataclass
class BaoDuongUpdateData:
    """Data for updating a bao_duong record."""
    ngay_du_kien: Optional[str] = None
    ngay_thuc_te: Optional[str] = None
    km_xe: Optional[int] = None
    noi_dung: Optional[str] = None
    chi_phi: Optional[int] = None
    trang_thai: Optional[str] = None
    nhan_vien_id: Optional[int] = None
    ghi_chu: Optional[str] = None


class BaoDuongService:
    """Service for maintenance/bao_duong operations."""

    VALID_TRANG_THAI = ['cho_xac_nhan', 'da_xac_nhan', 'dang_thuc_hien', 'hoan_thanh', 'huy']
    VALID_TRANG_THAI_UPDATE = ['da_xac_nhan', 'dang_thuc_hien', 'hoan_thanh', 'huy']

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = BaoDuongRepository(conn)

    def get_by_id(self, id: int) -> Optional[BaoDuong]:
        """Get BaoDuong by ID.

        Args:
            id: BaoDuong ID.

        Returns:
            BaoDuong if found, None otherwise.
        """
        return self._repo.find_by_id(id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[BaoDuong]:
        """Get all BaoDuong records with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of BaoDuong entities.
        """
        return self._repo.find_all(limit, offset)

    def find_by_khach_hang(self, khach_hang_id: int) -> List[BaoDuong]:
        """Find all BaoDuong records for a customer.

        Args:
            khach_hang_id: Customer ID.

        Returns:
            List of BaoDuong entities.
        """
        return self._repo.find_by_khach_hang(khach_hang_id)

    def find_by_xe(self, xe_id: int) -> List[BaoDuong]:
        """Find all BaoDuong records for a vehicle.

        Args:
            xe_id: Vehicle ID.

        Returns:
            List of BaoDuong entities.
        """
        return self._repo.find_by_xe(xe_id)

    def find_upcoming(self, days: int = 7) -> List[dict]:
        """Find BaoDuong appointments within N days.

        BR-TIME-02: Returns list with khach_hang and xe info
        for dashboard warning.

        Args:
            days: Number of days to look ahead (default 7).

        Returns:
            List of dicts with bao_duong, khach_hang, and xe info.
        """
        return self._repo.find_upcoming(days)

    def create(self, data: BaoDuongCreateData) -> BaoDuong:
        """Create a new BaoDuong record.

        Args:
            data: BaoDuongCreateData with maintenance data.

        Returns:
            Created BaoDuong entity.

        Raises:
            ValidationError: If validation fails.
        """
        # Validate required fields
        if not data.khach_hang_id or data.khach_hang_id <= 0:
            raise ValidationError("Invalid khach_hang_id")

        if not data.xe_id or data.xe_id <= 0:
            raise ValidationError("Invalid xe_id")

        if not data.ngay_du_kien:
            raise ValidationError("ngay_du_kien is required")

        # Validate chi_phi >= 0
        if data.chi_phi < 0:
            raise ValidationError("chi_phi must be >= 0")

        # Validate km_xe >= 0
        if data.km_xe < 0:
            raise ValidationError("km_xe must be >= 0")

        # Create entity with default status 'cho_xac_nhan'
        bd = BaoDuong(
            khach_hang_id=data.khach_hang_id,
            xe_id=data.xe_id,
            nhan_vien_id=data.nhan_vien_id,
            ngay_du_kien=data.ngay_du_kien,
            km_xe=data.km_xe,
            noi_dung=data.noi_dung or "",
            chi_phi=data.chi_phi,
            trang_thai='cho_xac_nhan',
            ghi_chu=data.ghi_chu or "",
            created_by=data.created_by,
        )

        return self._repo.create(bd)

    def update(self, id: int, data: BaoDuongUpdateData) -> BaoDuong:
        """Update a BaoDuong record.

        Args:
            id: BaoDuong ID to update.
            data: BaoDuongUpdateData with fields to update.

        Returns:
            Updated BaoDuong entity.

        Raises:
            BaoDuongNotFoundError: If not found.
            ValidationError: If validation fails.
        """
        # Check exists
        bd = self._repo.find_by_id(id)
        if not bd:
            raise BaoDuongNotFoundError(f"Không tìm thấy bảo dưỡng với ID {id}")

        # Build update dict
        update_data = {}

        if data.ngay_du_kien is not None:
            update_data["ngay_du_kien"] = data.ngay_du_kien

        if data.ngay_thuc_te is not None:
            update_data["ngay_thuc_te"] = data.ngay_thuc_te

        if data.km_xe is not None:
            if data.km_xe < 0:
                raise ValidationError("km_xe must be >= 0")
            update_data["km_xe"] = data.km_xe

        if data.noi_dung is not None:
            update_data["noi_dung"] = data.noi_dung

        if data.chi_phi is not None:
            if data.chi_phi < 0:
                raise ValidationError("chi_phi must be >= 0")
            update_data["chi_phi"] = data.chi_phi

        if data.trang_thai is not None:
            if data.trang_thai not in self.VALID_TRANG_THAI_UPDATE:
                raise ValidationError(
                    f"trang_thai must be one of: {', '.join(self.VALID_TRANG_THAI_UPDATE)}"
                )
            update_data["trang_thai"] = data.trang_thai

        if data.nhan_vien_id is not None:
            update_data["nhan_vien_id"] = data.nhan_vien_id

        if data.ghi_chu is not None:
            update_data["ghi_chu"] = data.ghi_chu

        # Execute update
        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()

            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(id)

            self.conn.execute(
                f"UPDATE bao_duong SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()

        return self._repo.find_by_id(id)

    def delete(self, id: int) -> bool:
        """Delete (soft delete) a BaoDuong record.

        Args:
            id: BaoDuong ID to delete.

        Returns:
            True if deleted.

        Raises:
            BaoDuongNotFoundError: If not found.
            DeleteNotAllowedError: If has active records.
        """
        # Check exists
        bd = self._repo.find_by_id(id)
        if not bd:
            raise BaoDuongNotFoundError(f"Không tìm thấy bảo dưỡng với ID {id}")

        # Soft delete by setting trang_thai to 'huy'
        return self._repo.soft_delete(id)