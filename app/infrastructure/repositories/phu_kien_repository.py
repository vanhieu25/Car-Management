"""PhuKien repository - accessory data access layer."""

from dataclasses import dataclass
from typing import Optional, List, Any

import sqlite3

from app.domain.entities import PhuKien
from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class PhuKienSearchFilter:
    """Filter for accessory search."""
    keyword: Optional[str] = None  # Search in ma_pk, ten_pk
    phan_loai: Optional[str] = None  # noi_that, ngoai_that, dien_tu, bao_ve, trang_tri
    het_hang: Optional[bool] = None  # ton_kho <= 0


class PhuKienRepository(BaseRepository[PhuKien]):
    """Repository for PhuKien entity with search capabilities."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, PhuKien)

    def find_by_ma(self, ma_pk: str) -> Optional[PhuKien]:
        """Find an accessory by ma_pk code.

        Args:
            ma_pk: Accessory code.

        Returns:
            PhuKien if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM phu_kien WHERE ma_pk = ?",
            (ma_pk,)
        )
        row = cursor.fetchone()
        if row:
            return PhuKien.from_row(row)
        return None

    def exists_by_ma(self, ma_pk: str, exclude_id: int = None) -> bool:
        """Check if ma_pk already exists.

        Args:
            ma_pk: Accessory code to check.
            exclude_id: ID to exclude from check (for updates).

        Returns:
            True if exists, False otherwise.
        """
        if exclude_id:
            cursor = self.conn.execute(
                "SELECT 1 FROM phu_kien WHERE ma_pk = ? AND id != ?",
                (ma_pk, exclude_id)
            )
        else:
            cursor = self.conn.execute(
                "SELECT 1 FROM phu_kien WHERE ma_pk = ?",
                (ma_pk,)
            )
        return cursor.fetchone() is not None

    def search(
        self,
        filter: PhuKienSearchFilter,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PhuKien]:
        """Search accessories with dynamic filters.

        Args:
            filter: PhuKienSearchFilter with filter criteria.
            limit: Maximum results to return.
            offset: Offset for pagination.

        Returns:
            List of matching PhuKien entities.
        """
        conditions = []
        params = []

        if filter.keyword:
            keyword_pattern = f"%{filter.keyword}%"
            conditions.append(
                "(ma_pk LIKE ? OR ten_pk LIKE ?)"
            )
            params.extend([keyword_pattern, keyword_pattern])

        if filter.phan_loai:
            conditions.append("phan_loai = ?")
            params.append(filter.phan_loai)

        if filter.het_hang is True:
            conditions.append("ton_kho <= 0")
        elif filter.het_hang is False:
            conditions.append("ton_kho > 0")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM phu_kien
            WHERE {where_clause}
            ORDER BY ten_pk
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        return [PhuKien.from_row(row) for row in cursor.fetchall()]

    def count_search(self, filter: PhuKienSearchFilter) -> int:
        """Count accessories matching filter.

        Args:
            filter: PhuKienSearchFilter with filter criteria.

        Returns:
            Count of matching accessories.
        """
        conditions = []
        params = []

        if filter.keyword:
            keyword_pattern = f"%{filter.keyword}%"
            conditions.append(
                "(ma_pk LIKE ? OR ten_pk LIKE ?)"
            )
            params.extend([keyword_pattern, keyword_pattern])

        if filter.phan_loai:
            conditions.append("phan_loai = ?")
            params.append(filter.phan_loai)

        if filter.het_hang is True:
            conditions.append("ton_kho <= 0")
        elif filter.het_hang is False:
            conditions.append("ton_kho > 0")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM phu_kien WHERE {where_clause}",
            params
        )
        return cursor.fetchone()[0]

    def has_active_contracts(self, pk_id: int) -> bool:
        """Check if accessory is referenced by any active contracts.

        BR-PK-06: Cannot delete if referenced by active contracts.

        Args:
            pk_id: Accessory ID to check.

        Returns:
            True if referenced by active contracts, False otherwise.
        """
        cursor = self.conn.execute(
            """SELECT 1 FROM hop_dong_phu_kien hdpk
               JOIN hop_dong hd ON hdpk.hop_dong_id = hd.id
               WHERE hdpk.phu_kien_id = ? AND hd.trang_thai != 'huy'
               LIMIT 1""",
            (pk_id,)
        )
        return cursor.fetchone() is not None

    def update_inventory(self, pk_id: int, new_ton_kho: int) -> None:
        """Update accessory inventory.

        Args:
            pk_id: Accessory ID.
            new_ton_kho: New inventory value.
        """
        from datetime import datetime

        self.conn.execute(
            """UPDATE phu_kien SET ton_kho = ?, updated_at = ? WHERE id = ?""",
            (new_ton_kho, datetime.now().isoformat(), pk_id)
        )
        self.conn.commit()

    def get_all_by_phan_loai(self, phan_loai: str) -> List[PhuKien]:
        """Get all accessories by category.

        Args:
            phan_loai: Category (noi_that, ngoai_that, dien_tu, bao_ve, trang_tri).

        Returns:
            List of PhuKien entities.
        """
        cursor = self.conn.execute(
            "SELECT * FROM phu_kien WHERE phan_loai = ? AND ton_kho > 0 ORDER BY ten_pk",
            (phan_loai,)
        )
        return [PhuKien.from_row(row) for row in cursor.fetchall()]

    def get_available(self) -> List[PhuKien]:
        """Get all accessories with stock > 0.

        Returns:
            List of available PhuKien entities.
        """
        cursor = self.conn.execute(
            "SELECT * FROM phu_kien WHERE ton_kho > 0 ORDER BY ten_pk"
        )
        return [PhuKien.from_row(row) for row in cursor.fetchall()]
