"""BaoDuong repository - maintenance/bao_duong data access layer."""

from typing import List, Optional

import sqlite3

from app.domain.entities import BaoDuong, KhachHang, Xe
from app.infrastructure.repositories.base_repository import BaseRepository


class BaoDuongRepository(BaseRepository[BaoDuong]):
    """Repository for BaoDuong entity."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, BaoDuong)

    def find_by_khach_hang(self, khach_hang_id: int) -> List[BaoDuong]:
        """Find all bao_duong records by customer ID.
        
        Args:
            khach_hang_id: Customer ID.
            
        Returns:
            List of BaoDuong entities.
        """
        cursor = self.conn.execute(
            """SELECT * FROM bao_duong 
               WHERE khach_hang_id = ?
               ORDER BY ngay_du_kien DESC""",
            (khach_hang_id,)
        )
        return [BaoDuong.from_row(row) for row in cursor.fetchall()]

    def find_by_xe(self, xe_id: int) -> List[BaoDuong]:
        """Find all bao_duong records by vehicle ID.
        
        Args:
            xe_id: Vehicle ID.
            
        Returns:
            List of BaoDuong entities.
        """
        cursor = self.conn.execute(
            """SELECT * FROM bao_duong 
               WHERE xe_id = ?
               ORDER BY ngay_du_kien DESC""",
            (xe_id,)
        )
        return [BaoDuong.from_row(row) for row in cursor.fetchall()]

    def find_upcoming(self, days: int = 7) -> List[dict]:
        """Find bao_duong appointments within N days.
        
        Args:
            days: Number of days to look ahead.
            
        Returns:
            List of dicts with bao_duong, khach_hang, and xe info.
        """
        cursor = self.conn.execute(
            """SELECT bd.*, 
                      kh.ho_ten as kh_ho_ten, kh.so_dien_thoai as kh_sdt,
                      xe.ma_xe, xe.hang, xe.dong_xe, xe.mau_sac
               FROM bao_duong bd
               JOIN khach_hang kh ON bd.khach_hang_id = kh.id
               JOIN xe ON bd.xe_id = xe.id
               WHERE bd.ngay_du_kien >= date('now')
                 AND bd.ngay_du_kien <= date('now', '+' || ? || ' days')
                 AND bd.trang_thai NOT IN ('hoan_thanh', 'huy')
               ORDER BY bd.ngay_du_kien ASC""",
            (days,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def soft_delete(self, id: int) -> bool:
        """Soft delete bao_duong by setting trang_thai to 'huy'.
        
        Args:
            id: BaoDuong ID.
            
        Returns:
            True if updated, False otherwise.
        """
        from datetime import datetime
        cursor = self.conn.execute(
            """UPDATE bao_duong 
               SET trang_thai = 'huy', updated_at = ?
               WHERE id = ?""",
            (datetime.now().isoformat(), id)
        )
        return cursor.rowcount > 0

    def has_active_records(self, id: int) -> bool:
        """Check if bao_duong has active (non-cancelled) records.
        
        Args:
            id: BaoDuong ID.
            
        Returns:
            True if has active records, False otherwise.
        """
        cursor = self.conn.execute(
            """SELECT 1 FROM bao_duong 
               WHERE id = ? AND trang_thai NOT IN ('hoan_thanh', 'huy')
               LIMIT 1""",
            (id,)
        )
        return cursor.fetchone() is not None