"""Kho service - inventory management business logic layer.

Provides inventory overview and low-stock reporting.
"""

from typing import List, Dict, Any

import sqlite3


class KhoService:
    """Service for inventory management operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn

    def get_inventory_overview(self) -> List[Dict]:
        """Get inventory overview grouped by category.

        Groups xe by hang || ' ' || dong_xe with:
        - count of vehicles
        - sum of so_luong_ton
        - sum of (so_luong_ton * gia_ban) as gia_tri

        Groups all phu_kien with:
        - total count
        - sum of ton_kho
        - sum of (ton_kho * gia_ban) as gia_tri

        Returns:
            List of dicts with keys: loai, nhom, so_luong_ton, gia_tri
        """
        result = []

        # Query xe grouped by hang || ' ' || dong_xe
        cursor = self.conn.execute(
            """SELECT 
                   hang || ' ' || dong_xe AS nhom,
                   COUNT(*) AS so_luong_ton,
                   SUM(xe.so_luong_ton) AS tong_ton,
                   SUM(xe.so_luong_ton * xe.gia_ban) AS gia_tri
               FROM xe
               WHERE xe.trang_thai != 'da_ban'
               GROUP BY hang, dong_xe
               HAVING tong_ton > 0
               ORDER BY hang, dong_xe"""
        )
        for row in cursor.fetchall():
            result.append({
                "loai": "xe",
                "nhom": row["nhom"],
                "so_luong_ton": row["tong_ton"] or 0,
                "gia_tri": row["gia_tri"] or 0,
            })

        # Query phu_kien summary
        cursor = self.conn.execute(
            """SELECT 
                   COUNT(*) AS so_luong_ton,
                   SUM(ton_kho) AS tong_ton,
                   SUM(ton_kho * gia_ban) AS gia_tri
               FROM phu_kien
               WHERE ton_kho > 0"""
        )
        row = cursor.fetchone()
        if row and row["tong_ton"] and row["tong_ton"] > 0:
            result.append({
                "loai": "phu_kien",
                "nhom": "Phụ kiện",
                "so_luong_ton": row["tong_ton"] or 0,
                "gia_tri": row["gia_tri"] or 0,
            })

        return result

    def get_low_stock_items(self, threshold_pk: int = 2) -> List[Dict]:
        """Get items with low stock.

        Queries:
        - xe WHERE so_luong_ton <= muc_toi_thieu
        - phu_kien WHERE ton_kho <= threshold_pk (default 2)

        Returns:
            Combined list with loai, ten, ton_kho, muc_toi_thieu.
        """
        result = []

        # Low stock xe
        cursor = self.conn.execute(
            """SELECT id, hang, dong_xe, so_luong_ton, muc_toi_thieu
               FROM xe
               WHERE so_luong_ton <= muc_toi_thieu
               ORDER BY so_luong_ton ASC"""
        )
        for row in cursor.fetchall():
            result.append({
                "loai": "xe",
                "ten": f"{row['hang']} {row['dong_xe']}",
                "ton_kho": row["so_luong_ton"],
                "muc_toi_thieu": row["muc_toi_thieu"],
            })

        # Low stock phu_kien
        cursor = self.conn.execute(
            """SELECT id, ten_pk, ton_kho
               FROM phu_kien
               WHERE ton_kho <= ?
               ORDER BY ton_kho ASC""",
            (threshold_pk,)
        )
        for row in cursor.fetchall():
            result.append({
                "loai": "phu_kien",
                "ten": row["ten_pk"],
                "ton_kho": row["ton_kho"],
                "muc_toi_thieu": threshold_pk,
            })

        return result

    def get_items_by_loai(self, loai: str) -> List[Dict]:
        """Get items by loai (Xe or PhuKien).

        Args:
            loai: Item type ('Xe' or 'PhuKien').

        Returns:
            List of dicts with id, ma, ten.
        """
        result = []
        if loai == "Xe":
            cursor = self.conn.execute(
                """SELECT id, ma_xe AS ma, hang || ' ' || dong_xe AS ten
                   FROM xe
                   WHERE trang_thai != 'da_ban'
                   ORDER BY hang, dong_xe"""
            )
            for row in cursor.fetchall():
                result.append({"id": row["id"], "ma": row["ma"], "ten": row["ten"]})
        elif loai == "PhuKien":
            cursor = self.conn.execute(
                """SELECT id, ma_pk AS ma, ten_pk AS ten
                   FROM phu_kien
                   ORDER BY ten_pk"""
            )
            for row in cursor.fetchall():
                result.append({"id": row["id"], "ma": row["ma"], "ten": row["ten"]})
        return result
