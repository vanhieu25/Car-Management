"""DashboardService - Dashboard KPI Summary Service.

Implements BR-BC-05: Dashboard KPI tiles calculation.
Provides role-based filtering:
- A-01 (admin): sees all
- A-02 (manager): sees own department/team
- A-03 (staff): sees limited

KPI tiles:
1. revenue_month - doanh thu tháng hiện tại
2. hop_dong_month - số HĐ mới tháng
3. xe_ton_kho - tổng tồn kho xe
4. bh_expiring_30d - BH sắp hết trong 30 ngày
5. tg_qua_han - số hồ sơ trả góp qua hạn
6. kh_birthday_7d - KH có sinh nhật ±7 ngày
7. kn_cao - KN cấp cao chưa đóng
"""

from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import sqlite3

from app.infrastructure.database.connection import get_connection


class DashboardServiceError(Exception):
    """Base exception for Dashboard service errors."""
    pass


class PermissionDeniedError(DashboardServiceError):
    """Raised when user lacks permission."""
    pass


@dataclass
class DashboardKPIs:
    """Dashboard KPI container."""
    revenue_month: int = 0
    hop_dong_month: int = 0
    xe_ton_kho: int = 0
    bh_expiring_30d: int = 0
    tg_qua_han: int = 0
    kh_birthday_7d: int = 0
    kn_cao: int = 0


class DashboardService:
    """Service for dashboard KPI operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn

    def get_summary(
        self,
        role: str = "A-01",
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get dashboard KPI summary.

        BR-BC-05: Role-based filtering for KPI tiles.
        - A-01 (admin): sees all
        - A-02 (manager): sees own (filter by nhan_vien_id)
        - A-03 (staff): limited view (revenue only)

        Args:
            role: User role code (A-01, A-02, A-03) or vai_tro_ma (admin, sales, ky_thuat_bh).
            user_id: User's nhan_vien_id for filtering.

        Returns:
            Dict with KPI values and metadata.
        """
        # Normalize role: vai_tro_ma names to role codes
        role_map = {
            "admin": "A-01",
            "A-01": "A-01",
            "sales": "A-02",
            "A-02": "A-02",
            "ky_thuat_bh": "A-03",
            "A-03": "A-03",
        }
        role = role_map.get(role, "A-03")  # Default to A-03 (limited) if unknown
        
        now = datetime.now()
        current_month_start = f"{now.year}-{now.month:02d}-01"

        # Get current month contract IDs (for filtering)
        hd_ids_this_month = self._get_month_contract_ids(now.year, now.month)

        kpis = {}

        if role == "A-01":
            # Admin sees all KPIs
            kpis = self._get_all_kpis(hd_ids_this_month, now.year, now.month)

        elif role == "A-02":
            # Manager sees own team's KPIs
            if user_id is None:
                raise PermissionDeniedError("user_id required for A-02 role")
            kpis = self._get_manager_kpis(user_id, hd_ids_this_month, now.year, now.month)

        else:  # A-03 - staff
            # Staff sees limited KPIs
            kpis = self._get_staff_kpis(hd_ids_this_month, user_id, now.year, now.month)

        return {
            "role": role,
            "user_id": user_id,
            "thang_ht": f"{now.year}-{now.month:02d}",
            "kpis": kpis,
            "timestamp": now.isoformat(),
        }

    def _get_all_kpis(
        self,
        hd_ids_this_month: List[int],
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Get all KPIs for admin (A-01).

        Args:
            hd_ids_this_month: List of contract IDs created this month.
            year: Current year.
            month: Current month.

        Returns:
            Dict with all KPI values.
        """
        # 1. revenue_month - doanh thu tháng hiện tại
        revenue_month = self._get_revenue_month(year, month)

        # 2. hop_dong_month - số HĐ mới tháng
        hop_dong_month = len(hd_ids_this_month)

        # 3. xe_ton_kho - tổng tồn kho xe
        xe_ton_kho = self._get_xe_ton_kho()

        # 4. bh_expiring_30d - BH sắp hết trong 30 ngày
        bh_expiring_30d = self._get_bh_expiring_30d()

        # 5. tg_qua_han - số hồ sơ trả góp qua hạn
        tg_qua_han = self._get_tg_qua_han()

        # 6. kh_birthday_7d - KH có sinh nhật ±7 ngày
        kh_birthday_7d = self._get_kh_birthday_7d()

        # 7. kn_cao - KN cấp cao chưa đóng
        kn_cao = self._get_kn_cao()

        return {
            "revenue_month": revenue_month,
            "hop_dong_month": hop_dong_month,
            "xe_ton_kho": xe_ton_kho,
            "bh_expiring_30d": bh_expiring_30d,
            "tg_qua_han": tg_qua_han,
            "kh_birthday_7d": kh_birthday_7d,
            "kn_cao": kn_cao,
        }

    def _get_manager_kpis(
        self,
        user_id: int,
        hd_ids_this_month: List[int],
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Get KPIs for manager (A-02) - filtered by user_id.

        Args:
            user_id: Manager's nhan_vien_id.
            hd_ids_this_month: List of contract IDs this month.
            year: Current year.
            month: Current month.

        Returns:
            Dict with filtered KPI values.
        """
        # For manager, KPIs are the same but may be filtered by their data
        # In this system, managers can see their own + team data
        # We'll filter revenue and contracts by nhan_vien_id = user_id

        # 1. revenue_month - filtered by user
        revenue_month = self._get_revenue_month(year, month, nhan_vien_id=user_id)

        # 2. hop_dong_month - filtered by user
        hop_dong_month = self._get_hop_dong_month(year, month, nhan_vien_id=user_id)

        # 3. xe_ton_kho - all (inventory is shared)
        xe_ton_kho = self._get_xe_ton_kho()

        # 4. bh_expiring_30d - all
        bh_expiring_30d = self._get_bh_expiring_30d()

        # 5. tg_qua_han - all (finance dept)
        tg_qua_han = self._get_tg_qua_han()

        # 6. kh_birthday_7d - all
        kh_birthday_7d = self._get_kh_birthday_7d()

        # 7. kn_cao - all
        kn_cao = self._get_kn_cao()

        return {
            "revenue_month": revenue_month,
            "hop_dong_month": hop_dong_month,
            "xe_ton_kho": xe_ton_kho,
            "bh_expiring_30d": bh_expiring_30d,
            "tg_qua_han": tg_qua_han,
            "kh_birthday_7d": kh_birthday_7d,
            "kn_cao": kn_cao,
        }

    def _get_staff_kpis(
        self,
        hd_ids_this_month: List[int],
        user_id: Optional[int],
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Get limited KPIs for staff (A-03).

        Staff can only see their own revenue and contracts.

        Args:
            hd_ids_this_month: List of contract IDs this month.
            user_id: Staff's nhan_vien_id.
            year: Current year.
            month: Current month.

        Returns:
            Dict with limited KPI values.
        """
        # Staff only sees their own revenue and contracts
        nhan_vien_id = user_id  # May be None for new staff

        revenue_month = self._get_revenue_month(year, month, nhan_vien_id=nhan_vien_id) if nhan_vien_id else 0
        hop_dong_month = self._get_hop_dong_month(year, month, nhan_vien_id=nhan_vien_id) if nhan_vien_id else 0

        # Other KPIs are hidden for staff (set to -1 or None to indicate no access)
        return {
            "revenue_month": revenue_month,
            "hop_dong_month": hop_dong_month,
            "xe_ton_kho": None,  # No access
            "bh_expiring_30d": None,  # No access
            "tg_qua_han": None,  # No access
            "kh_birthday_7d": None,  # No access
            "kn_cao": None,  # No access
        }

    def _get_revenue_month(
        self,
        year: int,
        month: int,
        nhan_vien_id: Optional[int] = None,
    ) -> int:
        """Get revenue for a specific month.

        Args:
            year: Year.
            month: Month (1-12).
            nhan_vien_id: Optional filter by employee.

        Returns:
            Total revenue in VND.
        """
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        from_date = f"{year}-{month:02d}-01"
        to_date = f"{next_year}-{next_month:02d}-01"

        conditions = [
            "trang_thai IN ('da_thanh_toan', 'da_giao_xe')",
            "DATE(ngay_tao) >= DATE(?)",
            "DATE(ngay_tao) < DATE(?)",
        ]
        params = [from_date, to_date]

        if nhan_vien_id is not None:
            conditions.append("nhan_vien_id = ?")
            params.append(nhan_vien_id)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT COALESCE(SUM(tong_tien), 0) as revenue
            FROM hop_dong
            WHERE {where_clause}
        """

        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        return row["revenue"] if row else 0

    def _get_hop_dong_month(
        self,
        year: int,
        month: int,
        nhan_vien_id: Optional[int] = None,
    ) -> int:
        """Get number of contracts created in a specific month.

        Args:
            year: Year.
            month: Month (1-12).
            nhan_vien_id: Optional filter by employee.

        Returns:
            Number of contracts.
        """
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        from_date = f"{year}-{month:02d}-01"
        to_date = f"{next_year}-{next_month:02d}-01"

        conditions = [
            "DATE(ngay_tao) >= DATE(?)",
            "DATE(ngay_tao) < DATE(?)",
        ]
        params = [from_date, to_date]

        if nhan_vien_id is not None:
            conditions.append("nhan_vien_id = ?")
            params.append(nhan_vien_id)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT COUNT(*) as count
            FROM hop_dong
            WHERE {where_clause}
        """

        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        return row["count"] if row else 0

    def _get_month_contract_ids(self, year: int, month: int) -> List[int]:
        """Get contract IDs for a specific month.

        Args:
            year: Year.
            month: Month (1-12).

        Returns:
            List of contract IDs.
        """
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        from_date = f"{year}-{month:02d}-01"
        to_date = f"{next_year}-{next_month:02d}-01"

        cursor = self.conn.execute(
            """SELECT id FROM hop_dong
               WHERE DATE(ngay_tao) >= DATE(?) AND DATE(ngay_tao) < DATE(?)""",
            (from_date, to_date)
        )
        return [row["id"] for row in cursor.fetchall()]

    def _get_xe_ton_kho(self) -> int:
        """Get total vehicle inventory count.

        Returns:
            Total available stock (so_luong_ton > 0).
        """
        cursor = self.conn.execute(
            "SELECT COALESCE(SUM(so_luong_ton), 0) as total FROM xe WHERE so_luong_ton > 0"
        )
        row = cursor.fetchone()
        return row["total"] if row else 0

    def _get_bh_expiring_30d(self) -> int:
        """Get count of warranties expiring within 30 days.

        Returns:
            Count of warranties expiring soon.
        """
        from app.infrastructure.repositories.bao_hanh_repository import BaoHanhRepository
        repo = BaoHanhRepository(self.conn)
        result = repo.find_expiring_in_30_days()
        return len(result)

    def _get_tg_qua_han(self) -> int:
        """Get count of overdue installment records.

        Returns:
            Count of 'qua_han' status in tra_gop_lich_su.
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) as count FROM tra_gop_lich_su WHERE trang_thai = 'qua_han'"
        )
        row = cursor.fetchone()
        return row["count"] if row else 0

    def _get_kh_birthday_7d(self) -> int:
        """Get count of customers with birthdays within 7 days.

        Returns:
            Count of customers with upcoming birthdays.
        """
        from app.infrastructure.repositories.khach_hang_repository import KhachHangRepository
        repo = KhachHangRepository(self.conn)
        result = repo.find_birthday_window(7)
        return len(result)

    def _get_kn_cao(self) -> int:
        """Get count of high-priority unresolved complaints.

        Returns:
            Count of complaints with muc_do='cao' and not 'da_giai_quyet'/'da_dong'.
        """
        from app.infrastructure.repositories.khieu_nai_repository import KhieuNaiRepository
        repo = KhieuNaiRepository(self.conn)
        return repo.count_by_muc_do("cao")