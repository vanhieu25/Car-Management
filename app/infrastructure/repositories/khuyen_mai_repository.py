"""KhuyenMai repository - promotion data access layer."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import KhuyenMai
from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class KhuyenMaiPhamVi:
    """Phạm vi áp dụng khuyến mãi."""
    id: int
    khuyen_mai_id: int
    loai_ap_dung: str  # 'all', 'hang', 'dong_xe', 'xe'
    gia_tri_ap_dung: str = None


class KhuyenMaiRepository(BaseRepository[KhuyenMai]):
    """Repository for KhuyenMai entity."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, KhuyenMai)

    def find_by_id(self, km_id: int) -> Optional[KhuyenMai]:
        """Find promotion by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM khuyen_mai WHERE id = ?", (km_id,)
        )
        row = cursor.fetchone()
        if row:
            return KhuyenMai.from_row(row)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[KhuyenMai]:
        """Find all promotions with pagination."""
        cursor = self.conn.execute(
            "SELECT * FROM khuyen_mai ORDER BY id LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [KhuyenMai.from_row(row) for row in cursor.fetchall()]

    def find_active(self) -> List[KhuyenMai]:
        """Find all active promotions (dang_chay)."""
        cursor = self.conn.execute(
            "SELECT * FROM khuyen_mai WHERE trang_thai = 'dang_chay' ORDER BY id"
        )
        return [KhuyenMai.from_row(row) for row in cursor.fetchall()]

    def find_by_trang_thai(self, trang_thai: str) -> List[KhuyenMai]:
        """Find promotions by status."""
        cursor = self.conn.execute(
            "SELECT * FROM khuyen_mai WHERE trang_thai = ? ORDER BY id",
            (trang_thai,)
        )
        return [KhuyenMai.from_row(row) for row in cursor.fetchall()]

    def find_expired(self, current_date: str) -> List[KhuyenMai]:
        """Find promotions where den_ngay < current_date and status is dang_chong.

        Args:
            current_date: ISO date string (YYYY-MM-DD).

        Returns:
            List of expired promotions.
        """
        cursor = self.conn.execute(
            """SELECT * FROM khuyen_mai
               WHERE den_ngay < ? AND trang_thai = 'dang_chay'""",
            (current_date,)
        )
        return [KhuyenMai.from_row(row) for row in cursor.fetchall()]

    def create(self, km: KhuyenMai) -> KhuyenMai:
        """Create a new promotion."""
        now = km.created_at or ""
        cursor = self.conn.execute(
            """INSERT INTO khuyen_mai
               (ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri,
                tu_ngay, den_ngay, trang_thai, so_luong_cho_phep,
                so_luong_da_su_dung, created_at, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                km.ten_km,
                km.mo_ta or "",
                km.loai_km,
                km.gia_tri,
                km.kieu_gia_tri,
                km.tu_ngay,
                km.den_ngay,
                km.trang_thai,
                km.so_luong_cho_phep,
                km.so_luong_da_su_dung,
                now,
                km.created_by,
            )
        )
        km.id = cursor.lastrowid
        return km

    def update_status(self, km_id: int, new_status: str) -> None:
        """Update promotion status.

        Args:
            km_id: Promotion ID.
            new_status: New status value.
        """
        from datetime import datetime
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE khuyen_mai SET trang_thai = ?, updated_at = ? WHERE id = ?",
            (new_status, now, km_id)
        )
        self.conn.commit()

    # === km_pham_vi methods ===

    def get_pham_vi(self, km_id: int) -> List[KhuyenMaiPhamVi]:
        """Get all phạm vi for a promotion.

        Args:
            km_id: Promotion ID.

        Returns:
            List of KhuyenMaiPhamVi.
        """
        cursor = self.conn.execute(
            "SELECT * FROM km_pham_vi WHERE khuyen_mai_id = ?",
            (km_id,)
        )
        return [KhuyenMaiPhamVi(**dict(row)) for row in cursor.fetchall()]

    def create_pham_vi(self, km_id: int, loai_ap_dung: str, gia_tri_ap_dung: str = None) -> None:
        """Create a phạm vi record for a promotion.

        Args:
            km_id: Promotion ID.
            loai_ap_dung: Type of scope ('all', 'hang', 'dong_xe', 'xe').
            gia_tri_ap_dung: Value for the scope (e.g., hang name, xe_id).
        """
        cursor = self.conn.execute(
            """INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
               VALUES (?, ?, ?)""",
            (km_id, loai_ap_dung, gia_tri_ap_dung)
        )

    def delete_pham_vi(self, km_id: int) -> None:
        """Delete all phạm vi for a promotion.

        Args:
            km_id: Promotion ID.
        """
        self.conn.execute(
            "DELETE FROM km_pham_vi WHERE khuyen_mai_id = ?",
            (km_id,)
        )

    def check_applicable_to_xe(self, km_id: int, xe_id: int) -> bool:
        """Check if promotion is applicable to a specific vehicle.

        Args:
            km_id: Promotion ID.
            xe_id: Vehicle ID.

        Returns:
            True if applicable, False otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM km_pham_vi WHERE khuyen_mai_id = ?",
            (km_id,)
        )
        pham_vi_list = [dict(row) for row in cursor.fetchall()]

        # If no pham_vi defined, apply to all
        if not pham_vi_list:
            return True

        # Get vehicle info
        cursor = self.conn.execute(
            "SELECT * FROM xe WHERE id = ?", (xe_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False
        xe = dict(row)

        for pv in pham_vi_list:
            loai = pv["loai_ap_dung"]
            gia_tri = pv["gia_tri_ap_dung"]

            if loai == "all":
                return True
            elif loai == "hang" and xe["hang"] == gia_tri:
                return True
            elif loai == "dong_xe" and xe["dong_xe"] == gia_tri:
                return True
            elif loai == "xe" and str(xe_id) == str(gia_tri):
                return True

        return False

    # === Contract statistics for effectiveness report ===

    def count_contracts(self, km_id: int) -> int:
        """Count contracts using this promotion.

        Args:
            km_id: Promotion ID.

        Returns:
            Number of contracts.
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM hop_dong WHERE khuyen_mai_id = ?",
            (km_id,)
        )
        return cursor.fetchone()[0]

    def sum_contract_total(self, km_id: int) -> int:
        """Sum of tong_tien for contracts using this promotion.

        Args:
            km_id: Promotion ID.

        Returns:
            Total revenue.
        """
        cursor = self.conn.execute(
            "SELECT SUM(tong_tien) FROM hop_dong WHERE khuyen_mai_id = ?",
            (km_id,)
        )
        result = cursor.fetchone()[0]
        return result if result else 0

    def sum_discount(self, km_id: int) -> int:
        """Sum of tien_giam_km for contracts using this promotion.

        Args:
            km_id: Promotion ID.

        Returns:
            Total discount given.
        """
        cursor = self.conn.execute(
            "SELECT SUM(tien_giam_km) FROM hop_dong WHERE khuyen_mai_id = ?",
            (km_id,)
        )
        result = cursor.fetchone()[0]
        return result if result else 0

    def get_contract_stats(self, km_id: int) -> Dict[str, Any]:
        """Get contract statistics for a promotion.

        Args:
            km_id: Promotion ID.

        Returns:
            Dict with so_hop_dong, doanh_thu, tong_giam.
        """
        return {
            "so_hop_dong": self.count_contracts(km_id),
            "doanh_thu": self.sum_contract_total(km_id),
            "tong_giam": self.sum_discount(km_id),
        }