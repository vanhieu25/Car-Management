"""BaoHiem repository - insurance data access layer."""

from typing import List, Optional

import sqlite3

from app.domain.entities import BaoHiem
from app.infrastructure.repositories.base_repository import BaseRepository


class BaoHiemRepository(BaseRepository[BaoHiem]):
    """Repository for BaoHiem entity."""

    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, BaoHiem)

    def find_by_bao_hanh_id(self, bao_hanh_id: int) -> List[BaoHiem]:
        """Find all insurance records for a warranty."""
        cursor = self.conn.execute(
            "SELECT * FROM bao_hiem WHERE bao_hanh_id = ? ORDER BY id DESC",
            (bao_hanh_id,)
        )
        return [BaoHiem.from_row(row) for row in cursor.fetchall()]

    def find_by_so_policy(self, so_policy: str) -> Optional[BaoHiem]:
        """Find insurance by policy number."""
        cursor = self.conn.execute(
            "SELECT * FROM bao_hiem WHERE so_policy = ?",
            (so_policy,)
        )
        row = cursor.fetchone()
        return BaoHiem.from_row(row) if row else None

    def find_by_dai_ly_ban_id(self, dai_ly_ban_id: int) -> List[BaoHiem]:
        """Find all insurance sold by a specific dealership."""
        cursor = self.conn.execute(
            "SELECT * FROM bao_hiem WHERE dai_ly_ban_id = ? ORDER BY id DESC",
            (dai_ly_ban_id,)
        )
        return [BaoHiem.from_row(row) for row in cursor.fetchall()]

    def find_expiring(self, days: int = 30, dai_ly_ban_id: int = None) -> List[dict]:
        """Find insurance expiring within N days.

        Args:
            days: Number of days from today.
            dai_ly_ban_id: Optional dealership filter.

        Returns:
            List of dicts with insurance + warranty + customer info.
        """
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        query = """
            SELECT bh.*,
                   kh.ho_ten as kh_ho_ten,
                   kh.so_dien_thoai as kh_sdt
            FROM bao_hiem bh
            JOIN bao_hanh bhhh ON bh.bao_hanh_id = bhhh.id
            JOIN khach_hang kh ON bhhh.khach_hang_id = kh.id
            WHERE bh.trang_thai = 'con_hieu_luc'
              AND bh.ngay_het_han >= ?
              AND bh.ngay_het_han <= ?
        """
        params = [today, end_date]

        if dai_ly_ban_id is not None:
            query += " AND bh.dai_ly_ban_id = ?"
            params.append(dai_ly_ban_id)

        query += " ORDER BY bh.ngay_het_han ASC"

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_all_with_filter(
        self,
        loai_bh: str = None,
        trang_thai: str = None,
        search_keyword: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[dict], int]:
        """Get all insurance with filter and count.

        Args:
            loai_bh: Filter by insurance type.
            trang_thai: Filter by status.
            search_keyword: Search by so_policy, khach_hang name, xe bien_so.
            limit: Max results.
            offset: Pagination offset.

        Returns:
            Tuple of (list of dicts, total count).
        """
        conditions = []
        params = []

        if loai_bh:
            conditions.append("bh.loai_bh = ?")
            params.append(loai_bh)

        if trang_thai:
            conditions.append("bh.trang_thai = ?")
            params.append(trang_thai)

        if search_keyword:
            keyword = f"%{search_keyword}%"
            conditions.append("(bh.so_policy LIKE ? OR kh.ho_ten LIKE ? OR x.ma_xe LIKE ?)")
            params.extend([keyword, keyword, keyword])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        count_query = f"""
            SELECT COUNT(*) FROM bao_hiem bh
            JOIN bao_hanh bhhh ON bh.bao_hanh_id = bhhh.id
            JOIN khach_hang kh ON bhhh.khach_hang_id = kh.id
            LEFT JOIN xe x ON bhhh.xe_id = x.id
            WHERE {where_clause}
        """
        count_cursor = self.conn.execute(count_query, params)
        total = count_cursor.fetchone()[0]

        data_query = f"""
            SELECT
                   bh.id,
                   bh.bao_hanh_id,
                   bh.loai_bh,
                   bh.so_policy,
                   bh.ngay_mua,
                   bh.ngay_het_han,
                   bh.phi_bh,
                   bh.trang_thai,
                   bh.ghi_chu,
                   bh.ngay_hieu_luc,
                   bh.gia_tri_bh,
                   bh.cong_ty_bh_id,
                   kh.ho_ten as kh_ho_ten,
                   kh.so_dien_thoai as kh_sdt,
                   bhhh.id as bh_id,
                   bhhh.so_khung,
                   bhhh.so_may,
                   bhhh.is_external,
                   x.ma_xe,
                   x.hang,
                   x.dong_xe
            FROM bao_hiem bh
            JOIN bao_hanh bhhh ON bh.bao_hanh_id = bhhh.id
            JOIN khach_hang kh ON bhhh.khach_hang_id = kh.id
            LEFT JOIN xe x ON bhhh.xe_id = x.id
            WHERE {where_clause}
            ORDER BY bh.id DESC
            LIMIT ? OFFSET ?
        """
        data_params = params + [limit, offset]
        cursor = self.conn.execute(data_query, data_params)
        cols = [desc[0] for desc in cursor.description]
        items = [{col: val for col, val in zip(cols, row)} for row in cursor.fetchall()]

        return items, total