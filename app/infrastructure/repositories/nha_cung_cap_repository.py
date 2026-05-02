"""NhaCungCap repository - supplier data access layer."""
from dataclasses import dataclass

from typing import List, Optional, Any

import sqlite3

from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class NhaCungCapSearchFilter:
    """Filter for supplier search."""
    keyword: Optional[str] = None  # Search in ma_ncc, ten_ncc
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None


from dataclasses import dataclass


class NhaCungCapRepository(BaseRepository):
    """Repository for NhaCungCap entity."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn
        self.table_name = "nha_cung_cap"

    def find_by_id(self, id: int) -> Optional[Any]:
        """Find supplier by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM nha_cung_cap WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def find_by_ma_ncc(self, ma_ncc: str) -> Optional[Any]:
        """Find supplier by code."""
        cursor = self.conn.execute(
            "SELECT * FROM nha_cung_cap WHERE ma_ncc = ?", (ma_ncc,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Find all suppliers with pagination."""
        cursor = self.conn.execute(
            "SELECT * FROM nha_cung_cap ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

    def search(
        self,
        keyword: str = None,
        min_rating: float = None,
        max_rating: float = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """Search suppliers with filters."""
        conditions = []
        params = []

        if keyword:
            keyword_pattern = f"%{keyword}%"
            conditions.append("(ma_ncc LIKE ? OR ten_ncc LIKE ?)")
            params.extend([keyword_pattern, keyword_pattern])

        # avg_rating = diem_tong / 3
        if min_rating is not None:
            # diem_tong / 3 >= min_rating => diem_tong >= min_rating * 3
            conditions.append("diem_tong >= ?")
            params.append(int(min_rating * 3))

        if max_rating is not None:
            conditions.append("diem_tong <= ?")
            params.append(int(max_rating * 3))

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM nha_cung_cap
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def count_search(
        self,
        keyword: str = None,
        min_rating: float = None,
        max_rating: float = None,
    ) -> int:
        """Count suppliers matching filter."""
        conditions = []
        params = []

        if keyword:
            keyword_pattern = f"%{keyword}%"
            conditions.append("(ma_ncc LIKE ? OR ten_ncc LIKE ?)")
            params.extend([keyword_pattern, keyword_pattern])

        if min_rating is not None:
            conditions.append("diem_tong >= ?")
            params.append(int(min_rating * 3))

        if max_rating is not None:
            conditions.append("diem_tong <= ?")
            params.append(int(max_rating * 3))

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM nha_cung_cap WHERE {where_clause}",
            params
        )
        return cursor.fetchone()[0]

    def exists_by_ma_ncc(self, ma_ncc: str, exclude_id: int = None) -> bool:
        """Check if ma_ncc already exists."""
        if exclude_id:
            cursor = self.conn.execute(
                "SELECT 1 FROM nha_cung_cap WHERE ma_ncc = ? AND id != ?",
                (ma_ncc, exclude_id)
            )
        else:
            cursor = self.conn.execute(
                "SELECT 1 FROM nha_cung_cap WHERE ma_ncc = ?",
                (ma_ncc,)
            )
        return cursor.fetchone() is not None

    def has_nhap_kho_history(self, ncc_id: int) -> bool:
        """Check if supplier has nhap_kho history (BR-NCC-06)."""
        cursor = self.conn.execute(
            "SELECT 1 FROM nhap_kho WHERE nha_cung_cap_id = ? LIMIT 1",
            (ncc_id,)
        )
        return cursor.fetchone() is not None

    def create(self, data: dict) -> dict:
        """Create a new supplier."""
        data = data.copy()
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"INSERT INTO nha_cung_cap ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor = self.conn.execute(sql, values)
        data["id"] = cursor.lastrowid
        return data

    def update(self, id: int, data: dict) -> None:
        """Update supplier fields."""
        data = data.copy()
        data.pop("id", None)
        data.pop("created_at", None)

        if not data:
            return

        from datetime import datetime
        data["updated_at"] = datetime.now().isoformat()

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        values.append(id)

        self.conn.execute(
            f"UPDATE nha_cung_cap SET {set_clause} WHERE id = ?",
            values
        )

    def delete(self, id: int) -> bool:
        """Delete supplier by ID."""
        cursor = self.conn.execute(
            "DELETE FROM nha_cung_cap WHERE id = ?", (id,)
        )
        return cursor.rowcount > 0

    def update_ratings(self, id: int, chat_luong: int, thoi_gian_giao: int, gia_ca: int) -> None:
        """Update supplier ratings.

        BR-NCC-02: Store 3 ratings (1-5 each)
        diem_tong = sum of 3 ratings
        avg = diem_tong / 3
        """
        from datetime import datetime

        diem_tong = chat_luong + thoi_gian_giao + gia_ca

        self.conn.execute(
            """UPDATE nha_cung_cap
               SET diem_chat_luong = ?,
                   diem_thoi_gian_giao = ?,
                   diem_gia_ca = ?,
                   diem_tong = ?,
                   updated_at = ?
               WHERE id = ?""",
            (chat_luong, thoi_gian_giao, gia_ca, diem_tong, datetime.now().isoformat(), id)
        )

    def count_all(self) -> int:
        """Count total suppliers."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM nha_cung_cap")
        return cursor.fetchone()[0]