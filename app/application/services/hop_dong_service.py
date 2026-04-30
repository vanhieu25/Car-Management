"""HopDong service - contract business logic layer.

Implements business rules:
- BR-HD-01 to BR-HD-07: Contract lifecycle management
- TRG-01: Decrease xe.so_luong_ton when contract is paid (will be implemented in G3.5)
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import HopDong
from app.infrastructure.repositories.base_repository import BaseRepository


class HopDongServiceError(Exception):
    """Base exception for HopDong service errors."""
    pass


class HopDongNotFoundError(HopDongServiceError):
    """Raised when contract is not found."""
    pass


class InvalidStateTransitionError(HopDongServiceError):
    """Raised when state transition is not allowed."""
    pass


class HopDongService:
    """Service for contract management operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = BaseRepository(conn, HopDong)

    def get_by_id(self, hop_dong_id: int) -> Optional[HopDong]:
        """Get contract by ID.

        Args:
            hop_dong_id: Contract ID.

        Returns:
            HopDong if found, None otherwise.
        """
        return self._repo.find_by_id(hop_dong_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[HopDong]:
        """Get all contracts with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of HopDong entities.
        """
        return self._repo.find_all(limit, offset)

    def set_paid(self, hop_dong_id: int, nhan_vien_id: int = None) -> HopDong:
        """Mark contract as paid (da_thanh_toan).

        Called when payment is confirmed. Updates ngay_thanh_toan and trang_thai.

        TODO: implement TRG-01
        TRG-01: Decrease xe.so_luong_ton when contract is paid — will be implemented in G3.5
        This trigger should decrement the vehicle's stock when a contract is marked as paid.

        Args:
            hop_dong_id: Contract ID.
            nhan_vien_id: Employee ID processing payment.

        Returns:
            Updated HopDong entity.

        Raises:
            HopDongNotFoundError: If contract not found.
            InvalidStateTransitionError: If contract is not in moi_tao status.
        """
        hop_dong = self._repo.find_by_id(hop_dong_id)
        if not hop_dong:
            raise HopDongNotFoundError(f"Không tìm thấy hợp đồng với ID {hop_dong_id}")

        if hop_dong.trang_thai != "moi_tao":
            raise InvalidStateTransitionError(
                f"Không thể thanh toán hợp đồng ở trạng thái '{hop_dong.trang_thai}'"
            )

        now = datetime.now().isoformat()
        self.conn.execute(
            """UPDATE hop_dong 
               SET trang_thai = 'da_thanh_toan', 
                   ngay_thanh_toan = ?,
                   updated_at = ?
               WHERE id = ?""",
            (now, now, hop_dong_id)
        )
        self.conn.commit()

        return self._repo.find_by_id(hop_dong_id)
