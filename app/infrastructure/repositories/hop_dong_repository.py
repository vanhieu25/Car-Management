"""HopDong repository - contract data access layer."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Any

import sqlite3

from app.domain.entities import HopDong
from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class HopDongSearchFilter:
    """Filter for contract search."""
    trang_thai: Optional[str] = None
    ngay_tao_from: Optional[str] = None
    ngay_tao_to: Optional[str] = None
    khach_hang_id: Optional[int] = None
    nhan_vien_id: Optional[int] = None
    keyword: Optional[str] = None


class HopDongRepository(BaseRepository[HopDong]):
    """Repository for HopDong entity with search and specific queries."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, HopDong)

    def find_by_ma_hop_dong(self, ma_hop_dong: str) -> Optional[HopDong]:
        """Find a contract by its code.

        Args:
            ma_hop_dong: Contract code to search for.

        Returns:
            HopDong if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM hop_dong WHERE ma_hop_dong = ?",
            (ma_hop_dong,)
        )
        row = cursor.fetchone()
        if row:
            return HopDong.from_row(row)
        return None

    def next_ma_hop_dong(self) -> str:
        """Generate next contract code in format HD<YYYY>-<NNNN>.

        Queries MAX(ma_hop_dong) for current year and returns next sequence.

        Returns:
            Next contract code like "HD2026-0001".
        """
        year = datetime.now().year
        year_str = str(year)

        cursor = self.conn.execute(
            """SELECT ma_hop_dong FROM hop_dong
               WHERE ma_hop_dong LIKE ?
               ORDER BY ma_hop_dong DESC LIMIT 1""",
            (f"HD{year_str}-%",)
        )
        row = cursor.fetchone()

        if row:
            last_code = row[0]
            # Parse sequence: "HD2026-0001" -> 0001
            try:
                seq = int(last_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                seq = 1
        else:
            seq = 1

        return f"HD{year_str}-{seq:04d}"

    def create(self, hop_dong: HopDong) -> HopDong:
        """Create a new contract with auto-generated ma_hop_dong.

        Args:
            hop_dong: HopDong entity to create.

        Returns:
            Created HopDong entity with id and ma_hop_dong.
        """
        if not hop_dong.ma_hop_dong:
            hop_dong.ma_hop_dong = self.next_ma_hop_dong()

        data = hop_dong.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"INSERT INTO hop_dong ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor = self.conn.execute(sql, values)
        hop_dong.id = cursor.lastrowid
        return hop_dong

    def update(self, hop_dong: HopDong) -> HopDong:
        """Update an existing contract."""
        if hop_dong.id is None:
            raise ValueError("Entity must have an id to update")

        data = hop_dong.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)

        if "updated_at" in data:
            data["updated_at"] = datetime.now().isoformat()

        columns = list(data.keys())
        set_clause = ", ".join([f"{col} = ?" for col in columns])
        values = [data[col] for col in columns]
        values.append(hop_dong.id)

        sql = f"UPDATE hop_dong SET {set_clause} WHERE id = ?"
        self.conn.execute(sql, values)
        return hop_dong

    def find_all(self, filter: HopDongSearchFilter = None, limit: int = 100, offset: int = 0) -> List[HopDong]:
        """Find all contracts with optional filter.

        Args:
            filter: HopDongSearchFilter with filter criteria.
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of HopDong entities.
        """
        if filter is None:
            filter = HopDongSearchFilter()

        conditions = []
        params = []

        if filter.trang_thai:
            conditions.append("trang_thai = ?")
            params.append(filter.trang_thai)

        if filter.ngay_tao_from:
            conditions.append("ngay_tao >= ?")
            params.append(filter.ngay_tao_from)

        if filter.ngay_tao_to:
            conditions.append("ngay_tao <= ?")
            params.append(filter.ngay_tao_to)

        if filter.khach_hang_id:
            conditions.append("khach_hang_id = ?")
            params.append(filter.khach_hang_id)

        if filter.nhan_vien_id:
            conditions.append("nhan_vien_id = ?")
            params.append(filter.nhan_vien_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM hop_dong
            WHERE {where_clause}
            ORDER BY ngay_tao DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        return [HopDong.from_row(row) for row in cursor.fetchall()]

    def search(
        self,
        filter: HopDongSearchFilter,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[HopDong], int]:
        """Search contracts with filters and pagination.

        Args:
            filter: HopDongSearchFilter with filter criteria.
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            Tuple of (list of HopDong, total count).
        """
        conditions = []
        params = []

        if filter.trang_thai:
            conditions.append("hd.trang_thai = ?")
            params.append(filter.trang_thai)

        if filter.ngay_tao_from:
            conditions.append("hd.ngay_tao >= ?")
            params.append(filter.ngay_tao_from)

        if filter.ngay_tao_to:
            conditions.append("hd.ngay_tao <= ?")
            params.append(filter.ngay_tao_to)

        if filter.khach_hang_id:
            conditions.append("hd.khach_hang_id = ?")
            params.append(filter.khach_hang_id)

        if filter.nhan_vien_id:
            conditions.append("hd.nhan_vien_id = ?")
            params.append(filter.nhan_vien_id)

        if filter.keyword:
            keyword_pattern = f"%{filter.keyword}%"
            conditions.append("(hd.ma_hop_dong LIKE ? OR kh.ho_ten LIKE ?)")
            params.extend([keyword_pattern, keyword_pattern])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count query
        count_query = f"""
            SELECT COUNT(*) FROM hop_dong hd
            LEFT JOIN khach_hang kh ON hd.khach_hang_id = kh.id
            WHERE {where_clause}
        """
        count_cursor = self.conn.execute(count_query, params)
        total = count_cursor.fetchone()[0]

        # Data query
        offset = (page - 1) * page_size
        data_query = f"""
            SELECT hd.* FROM hop_dong hd
            LEFT JOIN khach_hang kh ON hd.khach_hang_id = kh.id
            WHERE {where_clause}
            ORDER BY hd.ngay_tao DESC
            LIMIT ? OFFSET ?
        """
        data_params = params + [page_size, offset]
        cursor = self.conn.execute(data_query, data_params)
        items = [HopDong.from_row(row) for row in cursor.fetchall()]

        return items, total

    def get_full_contract(self, hop_dong_id: int) -> dict:
        """Get contract with all relations (KH, xe, pk list, km).

        Args:
            hop_dong_id: Contract ID.

        Returns:
            Dict with hop_dong, khach_hang, xe, phu_kien list, khuyen_mai.
        """
        # Get contract
        cursor = self.conn.execute("SELECT * FROM hop_dong WHERE id = ?", (hop_dong_id,))
        row = cursor.fetchone()
        if not row:
            return None

        hop_dong = dict(row)

        # Get customer
        kh_cursor = self.conn.execute(
            "SELECT * FROM khach_hang WHERE id = ?",
            (hop_dong["khach_hang_id"],)
        )
        kh_row = kh_cursor.fetchone()
        hop_dong["khach_hang"] = dict(kh_row) if kh_row else None

        # Get vehicle
        xe_cursor = self.conn.execute(
            "SELECT * FROM xe WHERE id = ?",
            (hop_dong["xe_id"],)
        )
        xe_row = xe_cursor.fetchone()
        hop_dong["xe"] = dict(xe_row) if xe_row else None

        # Get employee
        nv_cursor = self.conn.execute(
            "SELECT * FROM nhan_vien WHERE id = ?",
            (hop_dong["nhan_vien_id"],)
        )
        nv_row = nv_cursor.fetchone()
        hop_dong["nhan_vien"] = dict(nv_row) if nv_row else None

        # Get accessories
        pk_cursor = self.conn.execute(
            """SELECT pk.*, hdpk.so_luong as so_luong_mua, hdpk.gia_ban as gia_ban_snapshot
               FROM hop_dong_phu_kien hdpk
               JOIN phu_kien pk ON hdpk.phu_kien_id = pk.id
               WHERE hdpk.hop_dong_id = ?""",
            (hop_dong_id,)
        )
        hop_dong["phu_kien_list"] = [dict(row) for row in pk_cursor.fetchall()]

        # Get promotion if exists
        if hop_dong.get("khuyen_mai_id"):
            km_cursor = self.conn.execute(
                "SELECT * FROM khuyen_mai WHERE id = ?",
                (hop_dong["khuyen_mai_id"],)
            )
            km_row = km_cursor.fetchone()
            hop_dong["khuyen_mai"] = dict(km_row) if km_row else None
        else:
            hop_dong["khuyen_mai"] = None

        return hop_dong

    def add_phu_kien(self, hop_dong_id: int, phu_kien_id: int, so_luong: int, gia_ban: int) -> None:
        """Add an accessory to a contract.

        Args:
            hop_dong_id: Contract ID.
            phu_kien_id: Accessory ID.
            so_luong: Quantity.
            gia_ban: Snapshot price at time of contract.
        """
        self.conn.execute(
            """INSERT OR REPLACE INTO hop_dong_phu_kien
               (hop_dong_id, phu_kien_id, so_luong, gia_ban)
               VALUES (?, ?, ?, ?)""",
            (hop_dong_id, phu_kien_id, so_luong, gia_ban)
        )

    def remove_phu_kien(self, hop_dong_id: int, phu_kien_id: int) -> None:
        """Remove an accessory from a contract.

        Args:
            hop_dong_id: Contract ID.
            phu_kien_id: Accessory ID.
        """
        self.conn.execute(
            """DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ? AND phu_kien_id = ?""",
            (hop_dong_id, phu_kien_id)
        )

    def clear_phu_kien(self, hop_dong_id: int) -> None:
        """Clear all accessories from a contract.

        Args:
            hop_dong_id: Contract ID.
        """
        self.conn.execute(
            "DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?",
            (hop_dong_id,)
        )

    def delete(self, id: int) -> bool:
        """Delete contract and related records.

        Args:
            id: Contract ID.

        Returns:
            True if deleted.
        """
        # Delete related hop_dong_phu_kien records
        self.conn.execute("DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?", (id,))
        # Delete the contract
        cursor = self.conn.execute("DELETE FROM hop_dong WHERE id = ?", (id,))
        return cursor.rowcount > 0
