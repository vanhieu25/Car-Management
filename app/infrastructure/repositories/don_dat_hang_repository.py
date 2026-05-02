"""DonDatHang repository - purchase order data access layer."""
from dataclasses import dataclass

from datetime import datetime
from typing import List, Optional, Any

import sqlite3


@dataclass
class DonDatHangSearchFilter:
    """Filter for order search."""
    trang_thai: Optional[str] = None
    nha_cung_cap_id: Optional[int] = None
    ngay_dat_from: Optional[str] = None
    ngay_dat_to: Optional[str] = None
    keyword: Optional[str] = None


from dataclasses import dataclass


class DonDatHangRepository:
    """Repository for don_dat_hang entity."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn
        self.table_name = "don_dat_hang"

    def find_by_id(self, id: int) -> Optional[Any]:
        """Find order by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM don_dat_hang WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Find all orders with pagination."""
        cursor = self.conn.execute(
            "SELECT * FROM don_dat_hang ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

    def find_by_ncc(self, nha_cung_cap_id: int) -> List[Any]:
        """Find all orders by supplier."""
        cursor = self.conn.execute(
            "SELECT * FROM don_dat_hang WHERE nha_cung_cap_id = ? ORDER BY id DESC",
            (nha_cung_cap_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def search(
        self,
        trang_thai: str = None,
        nha_cung_cap_id: int = None,
        ngay_dat_from: str = None,
        ngay_dat_to: str = None,
        keyword: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[Any], int]:
        """Search orders with filters.

        Returns:
            Tuple of (list of order dicts, total count).
        """
        conditions = []
        params = []

        if trang_thai:
            conditions.append("ddh.trang_thai = ?")
            params.append(trang_thai)

        if nha_cung_cap_id:
            conditions.append("ddh.nha_cung_cap_id = ?")
            params.append(nha_cung_cap_id)

        if ngay_dat_from:
            conditions.append("ddh.ngay_dat >= ?")
            params.append(ngay_dat_from)

        if ngay_dat_to:
            conditions.append("ddh.ngay_dat <= ?")
            params.append(ngay_dat_to)

        if keyword:
            keyword_pattern = f"%{keyword}%"
            conditions.append("(ddh.ma_don LIKE ? OR ncc.ten_ncc LIKE ?)")
            params.extend([keyword_pattern, keyword_pattern])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count query
        count_query = f"""
            SELECT COUNT(*) FROM don_dat_hang ddh
            LEFT JOIN nha_cung_cap ncc ON ddh.nha_cung_cap_id = ncc.id
            WHERE {where_clause}
        """
        count_cursor = self.conn.execute(count_query, params)
        total = count_cursor.fetchone()[0]

        # Data query
        data_query = f"""
            SELECT ddh.*, ncc.ten_ncc as ten_ncc
            FROM don_dat_hang ddh
            LEFT JOIN nha_cung_cap ncc ON ddh.nha_cung_cap_id = ncc.id
            WHERE {where_clause}
            ORDER BY ddh.ngay_dat DESC
            LIMIT ? OFFSET ?
        """
        data_params = params + [limit, offset]
        cursor = self.conn.execute(data_query, data_params)
        items = [dict(row) for row in cursor.fetchall()]

        return items, total

    def next_ma_don(self) -> str:
        """Generate next order code in format DDH<YYYY>-<NNNN>."""
        year = datetime.now().year
        year_str = str(year)

        cursor = self.conn.execute(
            """SELECT ma_don FROM don_dat_hang
               WHERE ma_don LIKE ?
               ORDER BY ma_don DESC LIMIT 1""",
            (f"DDH{year_str}-%",)
        )
        row = cursor.fetchone()

        if row:
            last_code = row[0]
            try:
                seq = int(last_code.split("-")[1]) + 1
            except (IndexError, ValueError):
                seq = 1
        else:
            seq = 1

        return f"DDH{year_str}-{seq:04d}"

    def create(self, data: dict) -> dict:
        """Create a new order."""
        data = data.copy()
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)

        # Auto-generate ma_don if not provided
        if "ma_don" not in data or not data["ma_don"]:
            data["ma_don"] = self.next_ma_don()

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"INSERT INTO don_dat_hang ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor = self.conn.execute(sql, values)
        data["id"] = cursor.lastrowid
        return data

    def update(self, id: int, data: dict) -> None:
        """Update order fields."""
        data = data.copy()
        data.pop("id", None)
        data.pop("created_at", None)

        if not data:
            return

        data["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        values.append(id)

        self.conn.execute(
            f"UPDATE don_dat_hang SET {set_clause} WHERE id = ?",
            values
        )

    def delete(self, id: int) -> bool:
        """Delete order by ID."""
        cursor = self.conn.execute(
            "DELETE FROM don_dat_hang WHERE id = ?", (id,)
        )
        return cursor.rowcount > 0

    # === chi_tiet_don_dat operations ===

    def get_chi_tiet(self, don_dat_hang_id: int) -> List[Any]:
        """Get all chi_tiet_don_dat for an order."""
        cursor = self.conn.execute(
            "SELECT * FROM chi_tiet_don_dat WHERE don_dat_hang_id = ? ORDER BY id",
            (don_dat_hang_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_chi_tiet(
        self,
        don_dat_hang_id: int,
        loai_item: str,
        item_id: int,
        so_luong: int,
        gia_don: int,
    ) -> dict:
        """Add item to order."""
        now = datetime.now().isoformat()
        cursor = self.conn.execute(
            """INSERT INTO chi_tiet_don_dat
               (don_dat_hang_id, loai_item, item_id, so_luong, gia_don, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (don_dat_hang_id, loai_item, item_id, so_luong, gia_don, now)
        )
        return {
            "id": cursor.lastrowid,
            "don_dat_hang_id": don_dat_hang_id,
            "loai_item": loai_item,
            "item_id": item_id,
            "so_luong": so_luong,
            "gia_don": gia_don,
        }

    def delete_chi_tiet(self, don_dat_hang_id: int) -> None:
        """Delete all chi_tiet for an order."""
        self.conn.execute(
            "DELETE FROM chi_tiet_don_dat WHERE don_dat_hang_id = ?",
            (don_dat_hang_id,)
        )

    def calculate_tong_gia(self, don_dat_hang_id: int) -> int:
        """Calculate total price for an order."""
        cursor = self.conn.execute(
            "SELECT SUM(so_luong * gia_don) FROM chi_tiet_don_dat WHERE don_dat_hang_id = ?",
            (don_dat_hang_id,)
        )
        result = cursor.fetchone()[0]
        return result if result else 0

    def count_items(self, don_dat_hang_id: int) -> int:
        """Count total items in an order."""
        cursor = self.conn.execute(
            "SELECT SUM(so_luong) FROM chi_tiet_don_dat WHERE don_dat_hang_id = ?",
            (don_dat_hang_id,)
        )
        result = cursor.fetchone()[0]
        return result if result else 0