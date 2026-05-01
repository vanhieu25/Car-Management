"""CuuHo service - rescue/cuu_ho business logic layer.

Implements business rules:
- BR-HM-04: Cứu hộ has vi_tri, mo_ta, thoi_gian_yeu_cau
- BR-HM-05: Status flow: tiep_nhan -> dang_xu_ly -> hoan_thanh
- BR-HM-06: Create/Update cuu_ho records
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import sqlite3

from app.domain.entities import CuuHo
from app.infrastructure.repositories.cuu_ho_repository import CuuHoRepository


class CuuHoServiceError(Exception):
    """Base exception for CuuHo service errors."""
    pass


class ValidationError(CuuHoServiceError):
    """Validation error with field-specific messages."""
    pass


class CuuHoNotFoundError(CuuHoServiceError):
    """Raised when CuuHo record is not found."""
    pass


@dataclass
class CuuHoCreateData:
    """Data for creating a new cuu_ho record."""
    khach_hang_id: int
    xe_id: int
    vi_tri: str
    mo_ta: str = ""
    chi_phi: int = 0  # Estimated cost
    thoi_gian_den_du_kien: Optional[str] = None
    nhan_vien_id: Optional[int] = None
    ghi_chu: str = ""
    created_by: Optional[int] = None


@dataclass
class CuuHoUpdateData:
    """Data for updating a cuu_ho record."""
    vi_tri: Optional[str] = None
    mo_ta: Optional[str] = None
    trang_thai: Optional[str] = None
    nhan_vien_id: Optional[int] = None
    thoi_gian_xu_ly: Optional[str] = None
    chi_phi_thuc_te: Optional[int] = None
    ghi_chu: Optional[str] = None


class CuuHoService:
    """Service for rescue/cuu_ho operations."""

    VALID_TRANG_THAI = ['tiep_nhan', 'dang_xu_ly', 'hoan_thanh']
    VALID_TRANG_THAI_TRANSITIONS = {
        'tiep_nhan': ['dang_xu_ly', 'hoan_thanh'],
        'dang_xu_ly': ['hoan_thanh'],
        'hoan_thanh': [],
    }

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = CuuHoRepository(conn)

    def get_by_id(self, id: int) -> Optional[CuuHo]:
        """Get CuuHo by ID.

        Args:
            id: CuuHo ID.

        Returns:
            CuuHo if found, None otherwise.
        """
        return self._repo.find_by_id(id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[CuuHo]:
        """Get all CuuHo records with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of CuuHo entities.
        """
        return self._repo.find_all(limit, offset)

    def find_by_khach_hang(self, khach_hang_id: int) -> List[CuuHo]:
        """Find all CuuHo records for a customer.

        Args:
            khach_hang_id: Customer ID.

        Returns:
            List of CuuHo entities.
        """
        return self._repo.find_by_khach_hang(khach_hang_id)

    def find_by_xe(self, xe_id: int) -> List[CuuHo]:
        """Find all CuuHo records for a vehicle.

        Args:
            xe_id: Vehicle ID.

        Returns:
            List of CuuHo entities.
        """
        return self._repo.find_by_xe(xe_id)

    def find_pending(self) -> List[CuuHo]:
        """Find all pending CuuHo requests.

        Returns:
            List of CuuHo entities with pending status.
        """
        return self._repo.find_pending()

    def create(self, data: CuuHoCreateData) -> CuuHo:
        """Create a new CuuHo record.

        BR-HM-04: Cứu hộ has vi_tri (location), mo_ta, thoi_gian_yeu_cau

        Args:
            data: CuuHoCreateData with rescue data.

        Returns:
            Created CuuHo entity.

        Raises:
            ValidationError: If validation fails.
        """
        # Validate required fields
        if not data.khach_hang_id or data.khach_hang_id <= 0:
            raise ValidationError("Invalid khach_hang_id")

        if not data.xe_id or data.xe_id <= 0:
            raise ValidationError("Invalid xe_id")

        if not data.vi_tri:
            raise ValidationError("vi_tri is required")

        # Validate chi_phi >= 0
        if data.chi_phi < 0:
            raise ValidationError("chi_phi must be >= 0")

        # Create entity with default status 'tiep_nhan'
        ch = CuuHo(
            khach_hang_id=data.khach_hang_id,
            xe_id=data.xe_id,
            nhan_vien_id=data.nhan_vien_id,
            vi_tri=data.vi_tri,
            mo_ta=data.mo_ta or "",
            chi_phi=data.chi_phi,
            trang_thai='tiep_nhan',
            ghi_chu=data.ghi_chu or "",
            created_by=data.created_by,
        )

        return self._repo.create(ch)

    def update(self, id: int, data: CuuHoUpdateData) -> CuuHo:
        """Update a CuuHo record.

        BR-HM-05: Status flow: tiep_nhan -> dang_xu_ly -> hoan_thanh

        Args:
            id: CuuHo ID to update.
            data: CuuHoUpdateData with fields to update.

        Returns:
            Updated CuuHo entity.

        Raises:
            CuuHoNotFoundError: If not found.
            ValidationError: If validation fails.
        """
        # Check exists
        ch = self._repo.find_by_id(id)
        if not ch:
            raise CuuHoNotFoundError(f"Không tìm thấy cứu hộ với ID {id}")

        # Build update dict
        update_data = {}

        if data.vi_tri is not None:
            update_data["vi_tri"] = data.vi_tri

        if data.mo_ta is not None:
            update_data["mo_ta"] = data.mo_ta

        if data.trang_thai is not None:
            # Validate status transition
            if data.trang_thai not in self.VALID_TRANG_THAI:
                raise ValidationError(
                    f"trang_thai must be one of: {', '.join(self.VALID_TRANG_THAI)}"
                )
            
            # Check valid transition
            allowed = self.VALID_TRANG_THAI_TRANSITIONS.get(ch.trang_thai, [])
            if data.trang_thai not in allowed and data.trang_thai != ch.trang_thai:
                raise ValidationError(
                    f"Invalid status transition from '{ch.trang_thai}' to '{data.trang_thai}'"
                )
            
            update_data["trang_thai"] = data.trang_thai

        if data.nhan_vien_id is not None:
            update_data["nhan_vien_id"] = data.nhan_vien_id

        if data.thoi_gian_xu_ly is not None:
            update_data["thoi_gian_xu_ly"] = data.thoi_gian_xu_ly

        if data.chi_phi_thuc_te is not None:
            if data.chi_phi_thuc_te < 0:
                raise ValidationError("chi_phi_thuc_te must be >= 0")
            update_data["chi_phi"] = data.chi_phi_thuc_te

        if data.ghi_chu is not None:
            update_data["ghi_chu"] = data.ghi_chu

        # Execute update
        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()

            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(id)

            self.conn.execute(
                f"UPDATE cuu_ho SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()

        return self._repo.find_by_id(id)