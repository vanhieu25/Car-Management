"""Combo service - combo accessory business logic layer.

Implements business rules:
- BR-PK-04: Combo must have >= 2 accessories
- BR-CALC-07: gia_combo = SUM(gia_pk × so_luong) × he_so_giam
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import ComboPhuKien, PhuKien
from app.application.services.phu_kien_service import PhuKienService, PhuKienNotFoundError


class ComboServiceError(Exception):
    """Base exception for Combo service errors."""
    pass


class ValidationError(ComboServiceError):
    """Validation error with field-specific messages."""
    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        super().__init__(message)
        self.field = field
        self.errors = errors or []


class ComboNotFoundError(ComboServiceError):
    """Raised when combo is not found."""
    pass


class PhuKienNotFoundInComboError(ComboServiceError):
    """Raised when an accessory in combo items is not found."""
    pass


@dataclass
class ComboItemData:
    """An item in a combo."""
    phu_kien_id: int
    so_luong: int = 1


@dataclass
class ComboCreateData:
    """Data for creating a new combo."""
    ten_combo: str
    items: List[ComboItemData]  # List of (phu_kien_id, so_luong)
    he_so_giam: float
    mo_ta: str = ""
    created_by: int = None


@dataclass
class ComboItem:
    """A combo item with accessory details for display."""
    phu_kien_id: int
    ma_pk: str
    ten_pk: str
    gia_ban: int
    so_luong: int


@dataclass
class ComboDetail:
    """Combo with full details including items."""
    id: int
    ma_combo: str
    ten_combo: str
    he_so_giam: float
    mo_ta: str
    items: List[ComboItem]
    gia_goc: int
    gia_combo: int
    tien_tiet_kiem: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ComboSearchResult:
    """Search result with metadata."""
    items: List[ComboDetail]
    total: int
    page: int
    page_size: int
    total_pages: int


class ComboService:
    """Service for combo accessory management operations."""

    def __init__(self, conn: sqlite3.Connection, session=None):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
            session: Current user session (optional, for audit/permission).
        """
        self.conn = conn
        self._pk_service = PhuKienService(conn, session)
        self._session = session

    def _generate_ma_combo(self) -> str:
        """Generate unique ma_combo code.

        Returns:
            New unique ma_combo code (format: CB-XXXXX).
        """
        cursor = self.conn.execute(
            "SELECT MAX(CAST(SUBSTR(ma_combo, 4) AS INTEGER)) FROM combo_phu_kien WHERE ma_combo LIKE 'CB-%'"
        )
        result = cursor.fetchone()[0]
        next_num = (result or 0) + 1
        return f"CB-{next_num:05d}"

    def create(self, data: ComboCreateData) -> ComboDetail:
        """Create a new combo.

        BR-PK-04: Validate items >= 2 PK
        BR-CALC-07: he_so_giam > 0 and <= 1

        Args:
            data: ComboCreateData with combo data.

        Returns:
            Created ComboDetail.

        Raises:
            ValidationError: If validation fails.
        """
        errors = []

        # Validate ten_combo
        if not data.ten_combo or len(data.ten_combo.strip()) < 2:
            errors.append("Tên combo phải có ít nhất 2 ký tự")

        # BR-PK-04: Validate items >= 2 PK
        if not data.items or len(data.items) < 2:
            errors.append("Combo phải chứa ít nhất 2 phụ kiện")

        # Validate he_so_giam > 0 and <= 1
        if data.he_so_giam <= 0 or data.he_so_giam > 1:
            errors.append("Hệ số giảm phải lớn hơn 0 và nhỏ hơn hoặc bằng 1")

        if errors:
            raise ValidationError("; ".join(errors), errors=errors)

        # Validate all phu_kien exist
        for item in data.items:
            pk = self._pk_service.get_by_id(item.phu_kien_id)
            if not pk:
                errors.append(f"Không tìm thấy phụ kiện với ID {item.phu_kien_id}")

        if errors:
            raise ValidationError("; ".join(errors), errors=errors)

        # Insert combo_phu_kien record
        ma_combo = self._generate_ma_combo()
        now = datetime.now().isoformat()

        cursor = self.conn.execute(
            """INSERT INTO combo_phu_kien (ma_combo, ten_combo, he_so_giam, mo_ta, created_at, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ma_combo, data.ten_combo.strip(), data.he_so_giam, data.mo_ta or "", now, data.created_by)
        )
        combo_id = cursor.lastrowid

        # Insert combo_chi_tiet records
        for item in data.items:
            self.conn.execute(
                """INSERT INTO combo_chi_tiet (combo_id, phu_kien_id, so_luong)
                   VALUES (?, ?, ?)""",
                (combo_id, item.phu_kien_id, item.so_luong)
            )

        self.conn.commit()

        # Return full combo detail
        return self.get_by_id(combo_id)

    def get_by_id(self, combo_id: int) -> Optional[ComboDetail]:
        """Get combo by ID with full details.

        Args:
            combo_id: Combo ID.

        Returns:
            ComboDetail if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM combo_phu_kien WHERE id = ?",
            (combo_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        combo = dict(row)

        # Get items
        cursor = self.conn.execute(
            """SELECT cct.*, pk.ma_pk, pk.ten_pk, pk.gia_ban
               FROM combo_chi_tiet cct
               JOIN phu_kien pk ON cct.phu_kien_id = pk.id
               WHERE cct.combo_id = ?""",
            (combo_id,)
        )
        items = []
        gia_goc = 0
        for item_row in cursor.fetchall():
            item_dict = dict(item_row)
            item = ComboItem(
                phu_kien_id=item_dict["phu_kien_id"],
                ma_pk=item_dict["ma_pk"],
                ten_pk=item_dict["ten_pk"],
                gia_ban=item_dict["gia_ban"],
                so_luong=item_dict["so_luong"],
            )
            items.append(item)
            gia_goc += item_dict["gia_ban"] * item_dict["so_luong"]

        # BR-CALC-07: gia_combo = SUM(gia_pk × so_luong) × he_so_giam
        gia_combo = int(gia_goc * combo["he_so_giam"])
        tien_tiet_kiem = gia_goc - gia_combo

        return ComboDetail(
            id=combo["id"],
            ma_combo=combo["ma_combo"],
            ten_combo=combo["ten_combo"],
            he_so_giam=combo["he_so_giam"],
            mo_ta=combo["mo_ta"] or "",
            items=items,
            gia_goc=gia_goc,
            gia_combo=gia_combo,
            tien_tiet_kiem=tien_tiet_kiem,
            created_at=combo.get("created_at"),
            updated_at=combo.get("updated_at"),
        )

    def get_all(self, limit: int = 100, offset: int = 0) -> List[ComboDetail]:
        """Get all combos with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of ComboDetail entities.
        """
        cursor = self.conn.execute(
            "SELECT id FROM combo_phu_kien ORDER BY ten_combo LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [self.get_by_id(row["id"]) for row in cursor.fetchall()]

    def calculate_price(self, combo_id: int) -> Dict[str, Any]:
        """Calculate combo price with breakdown.

        BR-CALC-07: gia_combo = SUM(gia_pk × so_luong) × he_so_giam

        Args:
            combo_id: Combo ID.

        Returns:
            Dict with breakdown: {gia_goc, gia_combo, tien_tiet_kiem, items}

        Raises:
            ComboNotFoundError: If combo not found.
        """
        combo = self.get_by_id(combo_id)
        if not combo:
            raise ComboNotFoundError(f"Không tìm thấy combo với ID {combo_id}")

        return {
            "combo_id": combo_id,
            "ma_combo": combo.ma_combo,
            "ten_combo": combo.ten_combo,
            "he_so_giam": combo.he_so_giam,
            "gia_goc": combo.gia_goc,
            "gia_combo": combo.gia_combo,
            "tien_tiet_kiem": combo.tien_tiet_kiem,
            "items": [
                {
                    "phu_kien_id": item.phu_kien_id,
                    "ma_pk": item.ma_pk,
                    "ten_pk": item.ten_pk,
                    "gia_ban": item.gia_ban,
                    "so_luong": item.so_luong,
                    "thanh_tien": item.gia_ban * item.so_luong,
                }
                for item in combo.items
            ],
        }

    def update(self, combo_id: int, data: ComboCreateData) -> ComboDetail:
        """Update a combo.

        Args:
            combo_id: Combo ID to update.
            data: ComboCreateData with fields to update.

        Returns:
            Updated ComboDetail.

        Raises:
            ComboNotFoundError: If combo not found.
            ValidationError: If validation fails.
        """
        combo = self.get_by_id(combo_id)
        if not combo:
            raise ComboNotFoundError(f"Không tìm thấy combo với ID {combo_id}")

        errors = []

        # Validate ten_combo
        if not data.ten_combo or len(data.ten_combo.strip()) < 2:
            errors.append("Tên combo phải có ít nhất 2 ký tự")

        # BR-PK-04: Validate items >= 2 PK
        if not data.items or len(data.items) < 2:
            errors.append("Combo phải chứa ít nhất 2 phụ kiện")

        # Validate he_so_giam > 0 and <= 1
        if data.he_so_giam <= 0 or data.he_so_giam > 1:
            errors.append("Hệ số giảm phải lớn hơn 0 và nhỏ hơn hoặc bằng 1")

        if errors:
            raise ValidationError("; ".join(errors), errors=errors)

        # Update combo_phu_kien record
        now = datetime.now().isoformat()
        self.conn.execute(
            """UPDATE combo_phu_kien
               SET ten_combo = ?, he_so_giam = ?, mo_ta = ?, updated_at = ?
               WHERE id = ?""",
            (data.ten_combo.strip(), data.he_so_giam, data.mo_ta or "", now, combo_id)
        )

        # Delete old items
        self.conn.execute(
            "DELETE FROM combo_chi_tiet WHERE combo_id = ?",
            (combo_id,)
        )

        # Insert new items
        for item in data.items:
            self.conn.execute(
                """INSERT INTO combo_chi_tiet (combo_id, phu_kien_id, so_luong)
                   VALUES (?, ?, ?)""",
                (combo_id, item.phu_kien_id, item.so_luong)
            )

        self.conn.commit()
        return self.get_by_id(combo_id)

    def delete(self, combo_id: int) -> bool:
        """Delete a combo.

        Args:
            combo_id: Combo ID to delete.

        Returns:
            True if deleted.

        Raises:
            ComboNotFoundError: If combo not found.
        """
        combo = self.get_by_id(combo_id)
        if not combo:
            raise ComboNotFoundError(f"Không tìm thấy combo với ID {combo_id}")

        # Delete combo_chi_tiet records
        self.conn.execute(
            "DELETE FROM combo_chi_tiet WHERE combo_id = ?",
            (combo_id,)
        )

        # Delete combo_phu_kien record
        cursor = self.conn.execute(
            "DELETE FROM combo_phu_kien WHERE id = ?",
            (combo_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def search(
        self,
        keyword: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ComboSearchResult:
        """Search combos with filters.

        Args:
            keyword: Keyword search (ma_combo, ten_combo).
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            ComboSearchResult with items and pagination info.
        """
        conditions = []
        params = []

        if keyword:
            keyword_pattern = f"%{keyword}%"
            conditions.append(
                "(ma_combo LIKE ? OR ten_combo LIKE ?)"
            )
            params.extend([keyword_pattern, keyword_pattern])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count total
        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM combo_phu_kien WHERE {where_clause}",
            params
        )
        total = cursor.fetchone()[0]

        # Get paginated results
        offset = (page - 1) * page_size
        cursor = self.conn.execute(
            f"SELECT id FROM combo_phu_kien WHERE {where_clause} ORDER BY ten_combo LIMIT ? OFFSET ?",
            params + [page_size, offset]
        )

        items = [self.get_by_id(row["id"]) for row in cursor.fetchall()]
        total_pages = max(1, (total + page_size - 1) // page_size)

        return ComboSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_combos_with_price(self, limit: int = 100, offset: int = 0) -> List[ComboDetail]:
        """Get all combos with calculated prices.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of ComboDetail with price breakdown.
        """
        return self.get_all(limit, offset)
