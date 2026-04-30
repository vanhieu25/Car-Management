"""NhapKho service - inventory receipt business logic layer.

Implements business rules:
- BR-KHO-01: Import inventory from supplier
- TRG-04: If xe was da_ban and stock becomes > 0, set trang_thai = 'con_hang'
"""

from datetime import datetime
from typing import List, Dict, Any

import sqlite3


class NhapKhoServiceError(Exception):
    """Base exception for NhapKho service errors."""
    pass


class ValidationError(NhapKhoServiceError):
    """Raised when validation fails."""
    pass


class NhapKhoService:
    """Service for inventory receipt operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = None  # Lazy init

    def _get_repo(self):
        """Lazy-load repo to avoid circular import."""
        if self._repo is None:
            from app.infrastructure.repositories.nhap_kho_repository import NhapKhoRepository
            self._repo = NhapKhoRepository(self.conn)
        return self._repo

    def get_by_id(self, nhap_kho_id: int) -> Dict:
        """Get nhap_kho by ID.

        Args:
            nhap_kho_id: nhap_kho ID.

        Returns:
            nhap_kho dict with chi_tiet list.
        """
        repo = self._get_repo()
        nhap_kho = repo.find_by_id(nhap_kho_id)
        if not nhap_kho:
            return None

        chi_tiet = repo.find_chi_tiet_by_nhap_kho_id(nhap_kho_id)
        nhap_kho["items"] = chi_tiet
        return nhap_kho

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all nhap_kho records.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of nhap_kho dicts.
        """
        repo = self._get_repo()
        return repo.find_all(limit, offset)

    def get_by_ncc(self, nha_cung_cap_id: int) -> List[Dict]:
        """Get all nhap_kho records by supplier.

        Args:
            nha_cung_cap_id: Supplier ID.

        Returns:
            List of nhap_kho dicts.
        """
        repo = self._get_repo()
        return repo.find_by_ncc(nha_cung_cap_id)

    def create(
        self,
        nha_cung_cap_id: int,
        items: List[Dict],
        nhan_vien_id: int,
        ngay_nhap: str = None,
        ghi_chu: str = "",
    ) -> Dict:
        """Create a new inventory receipt (nhap_kho).

        For each item dict with loai_item ('xe'/'phu_kien'), item_id, so_luong, gia_nhap:
        1. Insert nhap_kho record (first item only creates the header)
        2. Insert chi_tiet_nhap_kho record
        3. If loai_item='xe': UPDATE xe SET so_luong_ton = so_luong_ton + so_luong
        4. If loai_item='phu_kien': UPDATE phu_kien SET ton_kho = ton_kho + so_luong
        5. TRG-04: If xe was da_ban and stock becomes > 0, set trang_thai = 'con_hang'

        Args:
            nha_cung_cap_id: Supplier ID.
            items: List of item dicts with loai_item, item_id, so_luong, gia_nhap.
            nhan_vien_id: Employee ID creating this receipt.
            ngay_nhap: Date string (YYYY-MM-DD) for the receipt.
            ghi_chu: Note/remark.

        Returns:
            Dict with nhap_kho record and items list.
        """
        if not items:
            raise ValidationError("Danh sách items không được rỗng")

        now = datetime.now().isoformat()
        # Use provided ngay_nhap or current date
        receipt_date = ngay_nhap if ngay_nhap else now[:10]

        # First item creates the nhap_kho header
        first_item = items[0]

        # Create nhap_kho header
        nhap_kho_data = {
            "nha_cung_cap_id": nha_cung_cap_id,
            "nhan_vien_id": nhan_vien_id,
            "ngay_nhap": receipt_date,
            "ghi_chu": ghi_chu,
            "created_by": nhan_vien_id,
        }

        repo = self._get_repo()
        nhap_kho = repo.create(nhap_kho_data)
        nhap_kho_id = nhap_kho["id"]

        inserted_items = []

        for item in items:
            # Normalize loai -> loai_item for BE compatibility
            loai_item = item.get("loai_item") or item.get("loai")
            item_id = item.get("item_id")
            so_luong = item.get("so_luong")
            gia_nhap = item.get("gia_nhap", 0)

            if loai_item not in ("xe", "phu_kien", "Xe", "PhuKien"):
                raise ValidationError(f"loai_item '{loai_item}' không hợp lệ")
            # Normalize loai values to BE format
            if loai_item == "Xe":
                loai_item = "xe"
            elif loai_item == "PhuKien":
                loai_item = "phu_kien"
            if not item_id:
                raise ValidationError("item_id is required")
            if not so_luong or so_luong <= 0:
                raise ValidationError("so_luong must be positive")

            # Insert chi_tiet_nhap_kho
            cursor = self.conn.execute(
                """INSERT INTO chi_tiet_nhap_kho 
                   (nhap_kho_id, loai_item, item_id, so_luong, gia_nhap, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (nhap_kho_id, loai_item, item_id, so_luong, gia_nhap, now)
            )
            chi_tiet_id = cursor.lastrowid

            # Update stock based on item type
            if loai_item == "xe":
                # Get current xe state before update (for TRG-04)
                cursor = self.conn.execute(
                    "SELECT id, so_luong_ton, trang_thai FROM xe WHERE id = ?",
                    (item_id,)
                )
                xe_row = cursor.fetchone()
                if not xe_row:
                    raise ValidationError(f"Không tìm thấy xe với ID {item_id}")

                old_stock = xe_row["so_luong_ton"]
                old_status = xe_row["trang_thai"]

                # Update stock
                new_stock = old_stock + so_luong
                self.conn.execute(
                    """UPDATE xe SET so_luong_ton = ?, updated_at = ? WHERE id = ?""",
                    (new_stock, now, item_id)
                )

                # TRG-04: If xe was da_ban and stock becomes > 0, set con_hang
                if old_status == "da_ban" and new_stock > 0:
                    self.conn.execute(
                        """UPDATE xe SET trang_thai = 'con_hang', updated_at = ? WHERE id = ?""",
                        (now, item_id)
                    )

            elif loai_item == "phu_kien":
                # Get current phu_kien state
                cursor = self.conn.execute(
                    "SELECT id, ton_kho FROM phu_kien WHERE id = ?",
                    (item_id,)
                )
                pk_row = cursor.fetchone()
                if not pk_row:
                    raise ValidationError(f"Không tìm thấy phụ kiện với ID {item_id}")

                new_stock = pk_row["ton_kho"] + so_luong
                self.conn.execute(
                    """UPDATE phu_kien SET ton_kho = ?, updated_at = ? WHERE id = ?""",
                    (new_stock, now, item_id)
                )

            inserted_items.append({
                "id": chi_tiet_id,
                "nhap_kho_id": nhap_kho_id,
                "loai_item": loai_item,
                "item_id": item_id,
                "so_luong": so_luong,
                "gia_nhap": gia_nhap,
            })

        self.conn.commit()

        nhap_kho["items"] = inserted_items
        return nhap_kho

    def get_nha_cung_cap_list(self) -> List[Dict]:
        """Get list of all suppliers (nha cung cap).

        Returns:
            List of dicts with id, ma_ncc, ten_ncc.
        """
        cursor = self.conn.execute(
            "SELECT id, ma_ncc, ten_ncc FROM nha_cung_cap ORDER BY ten_ncc"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """Get recent stock-in history.

        Args:
            limit: Number of records to return.

        Returns:
            List of dicts with ngay_nhap, ten_ncc, so_items, tong_gia_tri.
        """
        cursor = self.conn.execute(
            """SELECT 
                   nk.ngay_nhap,
                   ncc.ten_ncc,
                   COUNT(ctnk.id) AS so_items,
                   SUM(ctnk.so_luong * ctnk.gia_nhap) AS tong_gia_tri
               FROM nhap_kho nk
               LEFT JOIN nha_cung_cap ncc ON nk.nha_cung_cap_id = ncc.id
               LEFT JOIN chi_tiet_nhap_kho ctnk ON nk.id = ctnk.nhap_kho_id
               GROUP BY nk.id
               ORDER BY nk.ngay_nhap DESC
               LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
