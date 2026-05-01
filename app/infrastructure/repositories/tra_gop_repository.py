"""TraGop repository - installment data access layer."""

from dataclasses import dataclass
from typing import Optional, List, Any

import sqlite3

from app.domain.entities import TraGop
from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class TraGopLichSu:
    """Lịch sử trả góp (installment payment history)."""
    id: Optional[int] = None
    tra_gop_id: int = 0
    ky_thu: int = 0
    ngay_den_han: str = ""
    so_tien_phai_tra: int = 0
    ngay_thuc_te: Optional[str] = None
    trang_thai: str = "chua_tra"
    ghi_chu: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(**dict(row))


class TraGopRepository(BaseRepository[TraGop]):
    """Repository for TraGop entity with specific queries."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, TraGop)

    def find_by_hop_dong_id(self, hop_dong_id: int) -> Optional[TraGop]:
        """Find installment by contract ID.

        Args:
            hop_dong_id: Contract ID.

        Returns:
            TraGop if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM tra_gop WHERE hop_dong_id = ?",
            (hop_dong_id,)
        )
        row = cursor.fetchone()
        if row:
            return TraGop.from_row(row)
        return None

    def find_overdue(self) -> List[dict]:
        """Find all overdue installment records.

        Returns all tra_gop records that have any 'qua_han' kỳ.
        Each record includes hop_dong info (KH, xe, so_tien).

        Returns:
            List of dicts with tra_gop and hop_dong info.
        """
        cursor = self.conn.execute("""
            SELECT DISTINCT tg.*,
                   kh.ho_ten as khach_hang_ten,
                   kh.so_dien_thoai as khach_hang_sdt,
                   xe.hang, xe.dong_xe, xe bien_so,
                   hd.tong_tien as hop_dong_tong_tien,
                   hd.ma_hop_dong
            FROM tra_gop tg
            JOIN hop_dong hd ON tg.hop_dong_id = hd.id
            JOIN khach_hang kh ON hd.khach_hang_id = kh.id
            JOIN xe ON hd.xe_id = xe.id
            JOIN tra_gop_lich_su tgls ON tgls.tra_gop_id = tg.id
            WHERE tgls.trang_thai = 'qua_han'
            ORDER BY tg.id
        """)
        return [dict(row) for row in cursor.fetchall()]

    def find_all_lich_su(self, tra_gop_id: int) -> List[TraGopLichSu]:
        """Get all payment history for an installment.

        Args:
            tra_gop_id: TraGop ID.

        Returns:
            List of TraGopLichSu ordered by ky_thu.
        """
        cursor = self.conn.execute(
            """SELECT * FROM tra_gop_lich_su
               WHERE tra_gop_id = ?
               ORDER BY ky_thu""",
            (tra_gop_id,)
        )
        return [TraGopLichSu.from_row(row) for row in cursor.fetchall()]

    def find_lich_su_by_id(self, lich_su_id: int) -> Optional[TraGopLichSu]:
        """Find a specific lich_su record by ID.

        Args:
            lich_su_id: tra_gop_lich_su ID.

        Returns:
            TraGopLichSu if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM tra_gop_lich_su WHERE id = ?",
            (lich_su_id,)
        )
        row = cursor.fetchone()
        if row:
            return TraGopLichSu.from_row(row)
        return None

    def create(self, tra_gop: TraGop) -> TraGop:
        """Create a new installment record."""
        data = tra_gop.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"INSERT INTO tra_gop ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor = self.conn.execute(sql, values)
        tra_gop.id = cursor.lastrowid
        return tra_gop

    def create_lich_su(self, lich_su: TraGopLichSu) -> TraGopLichSu:
        """Create a new lich_su record.

        Args:
            lich_su: TraGopLichSu entity.

        Returns:
            Created TraGopLichSu with id.
        """
        cursor = self.conn.execute(
            """INSERT INTO tra_gop_lich_su
               (tra_gop_id, ky_thu, ngay_den_han, so_tien_phai_tra, trang_thai)
               VALUES (?, ?, ?, ?, ?)""",
            (
                lich_su.tra_gop_id,
                lich_su.ky_thu,
                lich_su.ngay_den_han,
                lich_su.so_tien_phai_tra,
                lich_su.trang_thai,
            )
        )
        lich_su.id = cursor.lastrowid
        return lich_su

    def update_lich_su(self, lich_su: TraGopLichSu) -> TraGopLichSu:
        """Update a lich_su record.

        Args:
            lich_su: TraGopLichSu entity.

        Returns:
            Updated TraGopLichSu.
        """
        cursor = self.conn.execute(
            """UPDATE tra_gop_lich_su
               SET ngay_thuc_te = ?, trang_thai = ?, ghi_chu = ?
               WHERE id = ?""",
            (lich_su.ngay_thuc_te, lich_su.trang_thai, lich_su.ghi_chu, lich_su.id)
        )
        return lich_su

    def update(self, tra_gop: TraGop) -> TraGop:
        """Update an existing installment record."""
        if tra_gop.id is None:
            raise ValueError("Entity must have an id to update")

        data = tra_gop.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)

        if "updated_at" in data:
            from datetime import datetime
            data["updated_at"] = datetime.now().isoformat()

        columns = list(data.keys())
        set_clause = ", ".join([f"{col} = ?" for col in columns])
        values = [data[col] for col in columns]
        values.append(tra_gop.id)

        sql = f"UPDATE tra_gop SET {set_clause} WHERE id = ?"
        self.conn.execute(sql, values)
        return tra_gop

    def count_da_tra(self, tra_gop_id: int) -> int:
        """Count how many kỳ have been paid.

        Args:
            tra_gop_id: TraGop ID.

        Returns:
            Count of kỳ with status 'da_tra'.
        """
        cursor = self.conn.execute(
            """SELECT COUNT(*) FROM tra_gop_lich_su
               WHERE tra_gop_id = ? AND trang_thai = 'da_tra'""",
            (tra_gop_id,)
        )
        return cursor.fetchone()[0]

    def count_total(self, tra_gop_id: int) -> int:
        """Count total kỳ for an installment.

        Args:
            tra_gop_id: TraGop ID.

        Returns:
            Total count of kỳ.
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM tra_gop_lich_su WHERE tra_gop_id = ?",
            (tra_gop_id,)
        )
        return cursor.fetchone()[0]

    def has_qua_han(self, tra_gop_id: int) -> bool:
        """Check if installment has any qua_han kỳ.

        Args:
            tra_gop_id: TraGop ID.

        Returns:
            True if any kỳ is 'qua_han'.
        """
        cursor = self.conn.execute(
            """SELECT 1 FROM tra_gop_lich_su
               WHERE tra_gop_id = ? AND trang_thai = 'qua_han' LIMIT 1""",
            (tra_gop_id,)
        )
        return cursor.fetchone() is not None
