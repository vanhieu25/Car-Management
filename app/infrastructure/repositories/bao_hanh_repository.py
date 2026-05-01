"""BaoHanh repository - warranty data access layer."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import sqlite3

from app.domain.entities import BaoHanh
from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class BaoHanhYeuCau:
    """Yêu cầu bảo hành entity."""
    id: Optional[int] = None
    bao_hanh_id: int = 0
    nhan_vien_id: int = 0
    ngay_yeu_cau: str = ""
    mo_ta_tinh_trang: str = ""
    loai_yeu_cau: str = "sua_chua"
    chi_phi: int = 0
    trang_thai: str = "dang_xu_ly"
    phan_loai: str = "mien_phi"
    ngay_hoan_thanh: Optional[str] = None
    ghi_chu: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[int] = None

    def to_dict(self) -> dict:
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(**dict(row))


class BaoHanhRepository(BaseRepository[BaoHanh]):
    """Repository for BaoHanh entity."""

    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, BaoHanh)

    def find_by_hop_dong_id(self, hop_dong_id: int) -> Optional[BaoHanh]:
        """Find warranty by contract ID.

        Args:
            hop_dong_id: Contract ID.

        Returns:
            BaoHanh if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM bao_hanh WHERE hop_dong_id = ?",
            (hop_dong_id,)
        )
        row = cursor.fetchone()
        if row:
            return BaoHanh.from_row(row)
        return None

    def find_by_id(self, id: int) -> Optional[BaoHanh]:
        """Find warranty by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM bao_hanh WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        if row:
            return BaoHanh.from_row(row)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[BaoHanh]:
        """Find all warranties."""
        cursor = self.conn.execute(
            "SELECT * FROM bao_hanh ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [BaoHanh.from_row(row) for row in cursor.fetchall()]

    def find_expiring_in(self, days: int) -> List[dict]:
        """Find warranties expiring within N days.

        Args:
            days: Number of days from today.

        Returns:
            List of dicts with BH info + khach_hang + xe.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        end_date = datetime.now()
        from datetime import timedelta
        end_date = (end_date + timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
            SELECT bh.*,
                   kh.ho_ten as kh_ho_ten,
                   kh.so_dien_thoai as kh_sdt,
                   xe.hang as xe_hang,
                   xe.dong_xe as xe_dong,
                   xe.mau_sac as xe_mau,
                   hd.ma_hop_dong
            FROM bao_hanh bh
            JOIN khach_hang kh ON bh.khach_hang_id = kh.id
            JOIN xe xe ON bh.xe_id = xe.id
            JOIN hop_dong hd ON bh.hop_dong_id = hd.id
            WHERE bh.ngay_ket_thuc >= ?
              AND bh.ngay_ket_thuc <= ?
              AND bh.trang_thai = 'con_hieu_luc'
            ORDER BY bh.ngay_ket_thuc ASC
        """
        cursor = self.conn.execute(query, (today, end_date))
        return [dict(row) for row in cursor.fetchall()]

    def find_expiring_in_30_days(self) -> List[dict]:
        """Find warranties expiring within 30 days (BR-BH-03)."""
        return self.find_expiring_in(30)

    def find_yeu_cau_by_bao_hanh_id(self, bao_hanh_id: int) -> List[BaoHanhYeuCau]:
        """Find all requests for a warranty.

        Args:
            bao_hanh_id: Warranty ID.

        Returns:
            List of BaoHanhYeuCau entities.
        """
        cursor = self.conn.execute(
            """SELECT * FROM bao_hanh_yeu_cau
               WHERE bao_hanh_id = ?
               ORDER BY ngay_yeu_cau DESC""",
            (bao_hanh_id,)
        )
        return [BaoHanhYeuCau.from_row(row) for row in cursor.fetchall()]

    def find_yeu_cau_by_id(self, req_id: int) -> Optional[BaoHanhYeuCau]:
        """Find a warranty request by ID.

        Args:
            req_id: Request ID.

        Returns:
            BaoHanhYeuCau if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM bao_hanh_yeu_cau WHERE id = ?",
            (req_id,)
        )
        row = cursor.fetchone()
        if row:
            return BaoHanhYeuCau.from_row(row)
        return None

    def create_yeu_cau(self, req: BaoHanhYeuCau) -> BaoHanhYeuCau:
        """Create a new warranty request.

        Args:
            req: BaoHanhYeuCau entity.

        Returns:
            Created BaoHanhYeuCau with id.
        """
        data = req.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"""INSERT INTO bao_hanh_yeu_cau
                  ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"""
        cursor = self.conn.execute(sql, values)
        req.id = cursor.lastrowid
        return req

    def update_yeu_cau(self, req: BaoHanhYeuCau) -> BaoHanhYeuCau:
        """Update a warranty request.

        Args:
            req: BaoHanhYeuCau entity.

        Returns:
            Updated BaoHanhYeuCau.
        """
        if req.id is None:
            raise ValueError("Entity must have an id to update")

        data = req.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)

        if "updated_at" in data:
            data["updated_at"] = datetime.now().isoformat()

        columns = list(data.keys())
        set_clause = ", ".join([f"{col} = ?" for col in columns])
        values = [data[col] for col in columns]
        values.append(req.id)

        sql = f"UPDATE bao_hanh_yeu_cau SET {set_clause} WHERE id = ?"
        self.conn.execute(sql, values)
        return req

    def get_warranty_with_details(self, bh_id: int) -> Optional[dict]:
        """Get warranty with all details (KH, xe, HD, requests).

        Args:
            bh_id: Warranty ID.

        Returns:
            Dict with warranty info and relations.
        """
        cursor = self.conn.execute("SELECT * FROM bao_hanh WHERE id = ?", (bh_id,))
        row = cursor.fetchone()
        if not row:
            return None

        bh = dict(row)

        # KH
        cursor = self.conn.execute("SELECT * FROM khach_hang WHERE id = ?", (bh["khach_hang_id"],))
        kh_row = cursor.fetchone()
        bh["khach_hang"] = dict(kh_row) if kh_row else {}

        # Xe
        cursor = self.conn.execute("SELECT * FROM xe WHERE id = ?", (bh["xe_id"],))
        xe_row = cursor.fetchone()
        bh["xe"] = dict(xe_row) if xe_row else {}

        # Hop dong
        cursor = self.conn.execute("SELECT * FROM hop_dong WHERE id = ?", (bh["hop_dong_id"],))
        hd_row = cursor.fetchone()
        bh["hop_dong"] = dict(hd_row) if hd_row else {}

        # Yeu cau
        cursor = self.conn.execute(
            """SELECT yc.*, nv.ho_ten as nv_ho_ten
               FROM bao_hanh_yeu_cau yc
               LEFT JOIN nhan_vien nv ON yc.nhan_vien_id = nv.id
               WHERE yc.bao_hanh_id = ?
               ORDER BY yc.ngay_yeu_cau DESC""",
            (bh_id,)
        )
        bh["yeu_cau_list"] = [dict(row) for row in cursor.fetchall()]

        return bh

    def get_all_with_filter(
        self,
        trang_thai: str = None,
        search_keyword: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[dict], int]:
        """Get all warranties with filter and count.

        Args:
            trang_thai: Filter by status ('con_hieu_luc', 'het_han', 'sap_het_han').
            search_keyword: Search by ma BH, ten KH.
            limit: Max results.
            offset: Pagination offset.

        Returns:
            Tuple of (list of dicts with BH+KH+Xe info, total count).
        """
        conditions = []
        params = []

        if trang_thai == "con_hieu_luc":
            # Còn hiệu lực: chưa hết hạn
            today = datetime.now().strftime("%Y-%m-%d")
            conditions.append("bh.trang_thai = 'con_hieu_luc' AND bh.ngay_ket_thuc >= ?")
            params.append(today)
        elif trang_thai == "sap_het_han":
            # Sắp hết: trong 30 ngày
            today = datetime.now().strftime("%Y-%m-%d")
            from datetime import timedelta
            future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            conditions.append("bh.trang_thai = 'con_hieu_luc' AND bh.ngay_ket_thuc >= ? AND bh.ngay_ket_thuc <= ?")
            params.extend([today, future])
        elif trang_thai == "het_han":
            conditions.append("(bh.trang_thai = 'het_han' OR bh.ngay_ket_thuc < ?)")
            params.append(datetime.now().strftime("%Y-%m-%d"))
        # else: "tat_ca" - no filter

        if search_keyword:
            keyword = f"%{search_keyword}%"
            conditions.append("(bh.ma_bh LIKE ? OR kh.ho_ten LIKE ?)")
            params.extend([keyword, keyword])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count
        count_query = f"""
            SELECT COUNT(*) FROM bao_hanh bh
            LEFT JOIN khach_hang kh ON bh.khach_hang_id = kh.id
            WHERE {where_clause}
        """
        count_cursor = self.conn.execute(count_query, params)
        total = count_cursor.fetchone()[0]

        # Data
        data_query = f"""
            SELECT bh.*,
                   kh.ho_ten as kh_ho_ten,
                   kh.so_dien_thoai as kh_sdt,
                   xe.hang as xe_hang,
                   xe.dong_xe as xe_dong,
                   xe.mau_sac as xe_mau,
                   hd.ma_hop_dong
            FROM bao_hanh bh
            LEFT JOIN khach_hang kh ON bh.khach_hang_id = kh.id
            LEFT JOIN xe xe ON bh.xe_id = xe.id
            LEFT JOIN hop_dong hd ON bh.hop_dong_id = hd.id
            WHERE {where_clause}
            ORDER BY bh.id DESC
            LIMIT ? OFFSET ?
        """
        data_params = params + [limit, offset]
        cursor = self.conn.execute(data_query, data_params)
        items = [dict(row) for row in cursor.fetchall()]

        return items, total
