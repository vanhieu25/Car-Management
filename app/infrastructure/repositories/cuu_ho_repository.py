"""CuuHo repository - rescue/cuu_ho data access layer."""

from typing import List, Optional

import sqlite3

from app.domain.entities import CuuHo
from app.infrastructure.repositories.base_repository import BaseRepository


class CuuHoRepository(BaseRepository[CuuHo]):
    """Repository for CuuHo entity."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, CuuHo)

    def find_by_khach_hang(self, khach_hang_id: int) -> List[CuuHo]:
        """Find all cuu_ho records by customer ID.
        
        Args:
            khach_hang_id: Customer ID.
            
        Returns:
            List of CuuHo entities.
        """
        cursor = self.conn.execute(
            """SELECT * FROM cuu_ho 
               WHERE khach_hang_id = ?
               ORDER BY thoi_gian_yeu_cau DESC""",
            (khach_hang_id,)
        )
        return [CuuHo.from_row(row) for row in cursor.fetchall()]

    def find_pending(self) -> List[CuuHo]:
        """Find all pending cuu_ho requests (tiep_nhan or dang_xu_ly).
        
        Returns:
            List of CuuHo entities with pending status.
        """
        cursor = self.conn.execute(
            """SELECT * FROM cuu_ho 
               WHERE trang_thai IN ('tiep_nhan', 'dang_xu_ly')
               ORDER BY thoi_gian_yeu_cau ASC"""
        )
        return [CuuHo.from_row(row) for row in cursor.fetchall()]

    def find_by_xe(self, xe_id: int) -> List[CuuHo]:
        """Find all cuu_ho records by vehicle ID.
        
        Args:
            xe_id: Vehicle ID.
            
        Returns:
            List of CuuHo entities.
        """
        cursor = self.conn.execute(
            """SELECT * FROM cuu_ho 
               WHERE xe_id = ?
               ORDER BY thoi_gian_yeu_cau DESC""",
            (xe_id,)
        )
        return [CuuHo.from_row(row) for row in cursor.fetchall()]