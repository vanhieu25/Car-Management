"""NhapKho repository - inventory receipt data access layer.

Provides database operations for nhap_kho and chi_tiet_nhap_kho tables.
No entity class needed — uses plain dicts.
"""

from typing import List, Optional, Any

import sqlite3

from app.infrastructure.repositories.base_repository import BaseRepository


class NhapKhoRepository(BaseRepository):
    """Repository for nhap_kho entity (dict-based, no entity class)."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        # Use dict for table metadata since we don't have an entity class
        self.conn = conn
        self.table_name = "nhap_kho"

    def find_all(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Find all nhap_kho records with pagination.
        
        Args:
            limit: Maximum results.
            offset: Offset for pagination.
            
        Returns:
            List of nhap_kho dicts.
        """
        cursor = self.conn.execute(
            """SELECT * FROM nhap_kho ORDER BY id DESC LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[dict]:
        """Find nhap_kho record by ID.
        
        Args:
            id: nhap_kho ID.
            
        Returns:
            nhap_kho dict if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM nhap_kho WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_by_ncc(self, nha_cung_cap_id: int) -> List[dict]:
        """Find all nhap_kho records by supplier ID.
        
        Args:
            nha_cung_cap_id: Supplier ID.
            
        Returns:
            List of nhap_kho dicts.
        """
        cursor = self.conn.execute(
            """SELECT * FROM nhap_kho 
               WHERE nha_cung_cap_id = ?
               ORDER BY id DESC""",
            (nha_cung_cap_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def create(self, data: dict) -> dict:
        """Create a new nhap_kho record.
        
        Args:
            data: Dict with nhap_kho fields.
            
        Returns:
            Created nhap_kho dict with id.
        """
        data = data.copy()
        data.pop("id", None)
        data.pop("created_at", None)

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"INSERT INTO nhap_kho ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor = self.conn.execute(sql, values)
        data["id"] = cursor.lastrowid
        return data

    def find_chi_tiet_by_nhap_kho_id(self, nhap_kho_id: int) -> List[dict]:
        """Find all chi_tiet_nhap_kho for a nhap_kho.
        
        Args:
            nhap_kho_id: nhap_kho ID.
            
        Returns:
            List of chi_tiet_nhap_kho dicts.
        """
        cursor = self.conn.execute(
            """SELECT * FROM chi_tiet_nhap_kho 
               WHERE nhap_kho_id = ?
               ORDER BY id""",
            (nhap_kho_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
