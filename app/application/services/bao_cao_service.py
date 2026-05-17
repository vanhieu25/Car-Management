"""BaoCaoService - Reporting and Analytics Service.

Implements business rules for reporting:
- BR-BC-01..05: Reporting requirements
- BR-CALC-01: Total calculation for revenue
- BR-CALC-05: Employee KPI calculation formula
- BR-CALC-06: Conversion rate formula

This service provides:
- RP-01: Revenue report (by day/month/quarter/year)
- RP-02: Top-selling vehicle report
- RP-03: Employee KPI report
- RP-04: VIP customer report
- RP-05: Warranty cost report
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import sqlite3

from app.infrastructure.database.connection import get_connection


class BaoCaoServiceError(Exception):
    """Base exception for BaoCao service errors."""
    pass


class ValidationError(BaoCaoServiceError):
    """Raised when validation fails."""
    pass


@dataclass
class RevenueBreakdown:
    """Revenue report breakdown by period."""
    period: str  # day/month/quarter/year key
    period_label: str  # human-readable label
    so_hop_dong: int
    doanh_thu: int
    lai_xe: int
    ty_le_xe: float  # percentage of total revenue


@dataclass
class TopXeItem:
    """Top vehicle sales item."""
    xe_id: int
    hang: str
    dong_xe: str
    mau_sac: str
    so_lan_ban: int
    doanh_thu: int


@dataclass
class KPIItem:
    """Employee KPI item."""
    nhan_vien_id: int
    ho_ten: str
    so_hop_dong_moi_tao: int
    so_hop_dong_da_thanh_toan: int
    so_hop_dong_giao_thanh_cong: int
    doanh_thu: int
    ti_le_chot: float  # percentage


@dataclass
class VIPCustomerItem:
    """VIP customer item."""
    khach_hang_id: int
    ho_ten: str
    so_dien_thoai: str
    email: str
    phan_loai: str
    tong_gia_tri_mua: int
    so_xe_da_mua: int


@dataclass
class WarrantyCostItem:
    """Warranty cost breakdown item."""
    loai_phi: str  # "mien_phi" or "tinh_phi"
    so_yeu_cau: int
    tong_chi_phi: int


class BaoCaoService:
    """Service for report generation operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn

    def revenue(
        self,
        from_date: str,
        to_date: str,
        group_by: str = "month",
        nhan_vien_id: Optional[int] = None,
        dong_xe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate revenue report (RP-01).

        BR-BC-01: Revenue report with period grouping.
        BR-CALC-01: tong_tien calculation.

        Args:
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).
            group_by: 'day', 'month', 'quarter', or 'year'.
            nhan_vien_id: Optional filter by employee.
            dong_xe: Optional filter by vehicle line (dong_xe).

        Returns:
            Dict with breakdown list, total revenue, filtered totals.
        """
        # Validate dates
        self._validate_date_range(from_date, to_date)

        if group_by not in ("day", "month", "quarter", "year"):
            raise ValidationError(
                f"group_by must be one of: day, month, quarter, year. Got: {group_by}"
            )

        # Build query conditions
        conditions = [
            "hd.trang_thai IN ('da_thanh_toan', 'da_giao_xe')",
            "DATE(hd.ngay_tao) >= DATE(?)",
            "DATE(hd.ngay_tao) <= DATE(?)",
        ]
        params = [from_date, to_date]

        if nhan_vien_id is not None:
            conditions.append("hd.nhan_vien_id = ?")
            params.append(nhan_vien_id)

        if dong_xe:
            conditions.append("xe.dong_xe = ?")
            params.append(dong_xe)

        where_clause = " AND ".join(conditions)

        # Group by period
        if group_by == "day":
            period_expr = "DATE(hd.ngay_tao)"
            period_format = "%Y-%m-%d"
        elif group_by == "month":
            period_expr = "STRFTIME('%Y-%m', hd.ngay_tao)"
            period_format = "%Y-%m"
        elif group_by == "quarter":
            period_expr = "STRFTIME('%Y-', hd.ngay_tao) || 'Q' || ((CAST(STRFTIME('%m', hd.ngay_tao) AS INTEGER) + 2) / 3)"
            period_format = "YYYY-Q"
        else:  # year
            period_expr = "STRFTIME('%Y', hd.ngay_tao)"
            period_format = "%Y"

        query = f"""
            SELECT
                {period_expr} as period,
                COUNT(hd.id) as so_hop_dong,
                COALESCE(SUM(hd.tong_tien), 0) as doanh_thu
            FROM hop_dong hd
            LEFT JOIN xe ON hd.xe_id = xe.id
            WHERE {where_clause}
            GROUP BY {period_expr}
            ORDER BY period ASC
        """

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        breakdown = []
        total_revenue = 0
        total_contracts = 0

        for row in rows:
            period = row["period"]
            so_hop_dong = row["so_hop_dong"] or 0
            doanh_thu = row["doanh_thu"] or 0

            total_revenue += doanh_thu
            total_contracts += so_hop_dong

            breakdown.append({
                "period": period,
                "so_hop_dong": so_hop_dong,
                "doanh_thu": doanh_thu,
            })

        # Calculate percentage for each period
        for item in breakdown:
            if total_revenue > 0:
                item["ty_le"] = round(item["doanh_thu"] / total_revenue * 100, 2)
            else:
                item["ty_le"] = 0.0

        # Calculate filtered totals
        filtered_total = sum(item["doanh_thu"] for item in breakdown)

        return {
            "breakdown": breakdown,
            "total_revenue": total_revenue,
            "total_contracts": total_contracts,
            "from_date": from_date,
            "to_date": to_date,
            "group_by": group_by,
            "filters": {
                "nhan_vien_id": nhan_vien_id,
                "dong_xe": dong_xe,
            },
        }

    def top_xe(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        top: int = 10,
    ) -> List[Dict[str, Any]]:
        """Generate top-selling vehicles report (RP-02).

        BR-BC-02: Top vehicle sales by count and revenue.

        Args:
            from_date: Optional start date filter.
            to_date: Optional end date filter.
            top: Number of top vehicles to return (default 10).

        Returns:
            List of dicts with xe info, count, and total revenue.
        """
        if top <= 0:
            top = 10

        conditions = [
            "hd.trang_thai IN ('da_thanh_toan', 'da_giao_xe')",
        ]
        params = []

        if from_date:
            conditions.append("DATE(hd.ngay_tao) >= DATE(?)")
            params.append(from_date)

        if to_date:
            conditions.append("DATE(hd.ngay_tao) <= DATE(?)")
            params.append(to_date)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT
                xe.id as xe_id,
                xe.hang,
                xe.dong_xe,
                xe.mau_sac,
                COUNT(hd.id) as so_lan_ban,
                COALESCE(SUM(hd.tong_tien), 0) as doanh_thu
            FROM hop_dong hd
            JOIN xe ON hd.xe_id = xe.id
            WHERE {where_clause}
            GROUP BY xe.id
            ORDER BY doanh_thu DESC
            LIMIT ?
        """
        params.append(top)
        params.append(top)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def kpi_nv(self, month: str) -> List[Dict[str, Any]]:
        """Generate employee KPI report (RP-03).

        BR-CALC-05: Employee KPI formula:
        - so_hop_dong_giao_thanh_cong: count of da_giao_xe
        - doanh_thu: sum of tong_tien for da_giao_xe
        - ti_le_chot = so_hop_dong_da_thanh_toan / so_hop_dong_moi_tao * 100

        Args:
            month: Month in 'YYYY-MM' format.

        Returns:
            List of dicts with employee info and KPI values.
        """
        self._validate_month(month)

        # Parse month for range
        year, month_num = map(int, month.split("-"))
        from_date = f"{year}-{month_num:02d}-01"

        # Calculate end date
        if month_num == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month_num + 1
        to_date = f"{next_year}-{next_month:02d}-01"

        query = """
            SELECT
                nv.id as nhan_vien_id,
                nv.ho_ten,
                vt.ten_vai_tro as vai_tro,
                COUNT(CASE WHEN hd.trang_thai IN ('moi_tao', 'da_thanh_toan', 'da_giao_xe')
                      THEN hd.id END) as so_hop_dong_moi_tao,
                COUNT(CASE WHEN hd.trang_thai = 'da_thanh_toan'
                      THEN hd.id END) as so_hop_dong_da_thanh_toan,
                COUNT(CASE WHEN hd.trang_thai = 'da_giao_xe'
                      THEN hd.id END) as so_hop_dong_giao_thanh_cong,
                COALESCE(SUM(CASE WHEN hd.trang_thai = 'da_giao_xe'
                      THEN hd.tong_tien ELSE 0 END), 0) as doanh_thu
            FROM nhan_vien nv
            LEFT JOIN vai_tro vt ON nv.vai_tro_id = vt.id
            LEFT JOIN hop_dong hd ON nv.id = hd.nhan_vien_id
                AND DATE(hd.ngay_tao) >= DATE(?)
                AND DATE(hd.ngay_tao) < DATE(?)
            WHERE nv.trang_thai = 'active'
            GROUP BY nv.id
            ORDER BY doanh_thu DESC
        """

        cursor = self.conn.execute(query, (from_date, to_date))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            so_hop_dong_moi = row["so_hop_dong_moi_tao"] or 0
            so_hop_dong_da_tt = row["so_hop_dong_da_thanh_toan"] or 0
            so_hop_dong_giao = row["so_hop_dong_giao_thanh_cong"] or 0
            doanh_thu = row["doanh_thu"] or 0

            # BR-CALC-06: ti_le_chot calculation
            if so_hop_dong_moi > 0:
                ti_le_chot = round(so_hop_dong_da_tt / so_hop_dong_moi * 100, 2)
            else:
                ti_le_chot = 0.0

            result.append({
                "nhan_vien_id": row["nhan_vien_id"],
                "ho_ten": row["ho_ten"],
                "vai_tro": row["vai_tro"],
                "so_hop_dong_moi_tao": so_hop_dong_moi,
                "so_hop_dong_da_thanh_toan": so_hop_dong_da_tt,
                "so_hop_dong_giao_thanh_cong": so_hop_dong_giao,
                "doanh_thu": doanh_thu,
                "ti_le_chot": ti_le_chot,
                "month": month,
            })

        return result

    def vip_customers(self, top: int = 20) -> List[Dict[str, Any]]:
        """Generate VIP customer report (RP-04).

        BR-BC-03: Top customers by total purchase value.

        Args:
            top: Number of top customers to return (default 20).

        Returns:
            List of customer dicts with purchase history summary.
        """
        if top <= 0:
            top = 20

        query = """
            SELECT
                kh.id as khach_hang_id,
                kh.ho_ten,
                kh.so_dien_thoai,
                kh.email,
                kh.phan_loai,
                kh.tong_gia_tri_mua,
                kh.so_xe_da_mua,
                COUNT(hd.id) as so_hop_dong,
                MAX(hd.ngay_tao) as lan_mua_cuoi
            FROM khach_hang kh
            LEFT JOIN hop_dong hd ON kh.id = hd.khach_hang_id
                AND hd.trang_thai IN ('da_thanh_toan', 'da_giao_xe')
            WHERE kh.tong_gia_tri_mua > 0
            GROUP BY kh.id
            ORDER BY kh.tong_gia_tri_mua DESC
            LIMIT ?
        """

        cursor = self.conn.execute(query, (top,))
        return [dict(row) for row in cursor.fetchall()]

    def warranty_cost(
        self,
        from_date: str,
        to_date: str,
    ) -> Dict[str, Any]:
        """Generate warranty cost report (RP-05).

        BR-BC-04: Warranty cost breakdown by loai_phi (mien_phi/tinh_phi).
        BR-BH-04: Classification of requests.

        Args:
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).

        Returns:
            Dict with breakdown by loai_phi and totals.
        """
        self._validate_date_range(from_date, to_date)

        query = """
            SELECT
                bhyc.phan_loai as loai_phi,
                COUNT(bhyc.id) as so_yeu_cau,
                COALESCE(SUM(bhyc.chi_phi), 0) as tong_chi_phi
            FROM bao_hanh_yeu_cau bhyc
            JOIN bao_hanh bh ON bhyc.bao_hanh_id = bh.id
            WHERE DATE(bhyc.ngay_yeu_cau) >= DATE(?)
              AND DATE(bhyc.ngay_yeu_cau) <= DATE(?)
              AND bhyc.trang_thai = 'da_hoan_thanh'
            GROUP BY bhyc.phan_loai
            ORDER BY tong_chi_phi DESC
        """

        cursor = self.conn.execute(query, (from_date, to_date))
        rows = cursor.fetchall()

        breakdown = []
        total_cost = 0

        for row in rows:
            loai_phi = row["loai_phi"] or "mien_phi"
            so_yeu_cau = row["so_yeu_cau"] or 0
            chi_phi = row["tong_chi_phi"] or 0

            total_cost += chi_phi
            breakdown.append({
                "loai_phi": loai_phi,
                "loai_phi_label": "Miễn phí" if loai_phi == "mien_phi" else "Tính phí",
                "so_yeu_cau": so_yeu_cau,
                "tong_chi_phi": chi_phi,
            })

        # Calculate percentage
        for item in breakdown:
            if total_cost > 0:
                item["ty_le"] = round(item["tong_chi_phi"] / total_cost * 100, 2)
            else:
                item["ty_le"] = 0.0

        return {
            "breakdown": breakdown,
            "total_cost": total_cost,
            "from_date": from_date,
            "to_date": to_date,
        }

    def new_customers(
        self,
        from_date: str,
        to_date: str,
    ) -> Dict[str, Any]:
        """Generate new customer report.

        Args:
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).

        Returns:
            Dict with new customer count and list.
        """
        self._validate_date_range(from_date, to_date)

        query = """
            SELECT id, ho_ten, so_dien_thoai, email, ngay_sinh, created_at
            FROM khach_hang
            WHERE date(created_at) BETWEEN date(?) AND date(?)
            ORDER BY created_at DESC
        """
        cursor = self.conn.execute(query, (from_date, to_date))
        customers = [dict(row) for row in cursor.fetchall()]

        return {
            "customers": customers,
            "total_new": len(customers),
            "from_date": from_date,
            "to_date": to_date,
        }

    def maintenance_report(
        self,
        from_date: str,
        to_date: str,
        group_by: str = "month",
    ) -> Dict[str, Any]:
        """Generate maintenance report.

        Args:
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).
            group_by: 'day', 'month', 'quarter', or 'year'.

        Returns:
            Dict with maintenance stats breakdown.
        """
        self._validate_date_range(from_date, to_date)

        # Date truncation based on group_by
        date_format = {
            "day": "%Y-%m-%d",
            "month": "%Y-%m",
            "quarter": "strftime('%Y-', ngay_du_kien) || printf('%02d', (cast(strftime('%m', ngay_du_kien) as integer) + 2) / 3)",
            "year": "%Y",
        }.get(group_by, "%Y-%m")

        if group_by == "quarter":
            date_expr = f"""strftime('%Y-', bd.ngay_du_kien) || 'Q' || ((cast(strftime('%m', bd.ngay_du_kien) as integer) + 2) / 3)"""
        else:
            date_expr = f"""strftime('{date_format}', bd.ngay_du_kien)"""

        query = f"""
            SELECT 
                {date_expr} as period,
                COUNT(*) as so_luong,
                COALESCE(SUM(bd.chi_phi), 0) as tong_chi_phi,
                COUNT(CASE WHEN bd.trang_thai = 'hoan_thanh' THEN 1 END) as da_hoan_thanh,
                COUNT(CASE WHEN bd.trang_thai = 'huy' THEN 1 END) as da_huy
            FROM bao_duong bd
            WHERE date(bd.ngay_du_kien) BETWEEN date(?) AND date(?)
            GROUP BY period
            ORDER BY period DESC
        """

        cursor = self.conn.execute(query, (from_date, to_date))
        breakdown = [dict(row) for row in cursor.fetchall()]

        # Totals
        totals = self.conn.execute(
            """SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(chi_phi), 0) as total_cost,
                COUNT(CASE WHEN trang_thai = 'hoan_thanh' THEN 1 END) as completed,
                COUNT(CASE WHEN trang_thai = 'huy' THEN 1 END) as cancelled
            FROM bao_duong
            WHERE date(ngay_du_kien) BETWEEN date(?) AND date(?)""",
            (from_date, to_date)
        ).fetchone()

        return {
            "breakdown": breakdown,
            "total_count": totals["total_count"] if totals else 0,
            "total_cost": totals["total_cost"] if totals and totals["total_cost"] else 0,
            "completed": totals["completed"] if totals else 0,
            "cancelled": totals["cancelled"] if totals else 0,
            "from_date": from_date,
            "to_date": to_date,
        }

    def promotion_report(
        self,
        from_date: str,
        to_date: str,
    ) -> Dict[str, Any]:
        """Generate promotion effectiveness report.

        Args:
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).

        Returns:
            Dict with promotion stats.
        """
        self._validate_date_range(from_date, to_date)

        query = """
            SELECT 
                km.id,
                km.ten_km,
                km.loai_km,
                km.gia_tri,
                km.kieu_gia_tri,
                km.trang_thai,
                km.den_ngay,
                COUNT(hd.id) as so_hop_dong,
                COALESCE(SUM(hd.tien_giam_km), 0) as tong_giam
            FROM khuyen_mai km
            LEFT JOIN hop_dong hd ON km.id = hd.khuyen_mai_id
                AND date(hd.ngay_tao) BETWEEN date(?) AND date(?)
            GROUP BY km.id
            ORDER BY so_hop_dong DESC, tong_giam DESC
        """
        cursor = self.conn.execute(query, (from_date, to_date))
        promotions = [dict(row) for row in cursor.fetchall()]

        # Overall stats
        total_km = self.conn.execute(
            """SELECT COUNT(*) as count, COALESCE(SUM(tien_giam_km), 0) as total 
               FROM hop_dong 
               WHERE khuyen_mai_id IS NOT NULL 
               AND date(ngay_tao) BETWEEN date(?) AND date(?)""",
            (from_date, to_date)
        ).fetchone()

        return {
            "promotions": promotions,
            "total_applied": total_km["count"] if total_km else 0,
            "total_discount": total_km["total"] if total_km and total_km["total"] else 0,
            "from_date": from_date,
            "to_date": to_date,
        }

    def _validate_date_range(self, from_date: str, to_date: str) -> None:
        """Validate date range.

        Args:
            from_date: Start date (YYYY-MM-DD).
            to_date: End date (YYYY-MM-DD).

        Raises:
            ValidationError: If dates are invalid or from_date > to_date.
        """
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")

            # Auto-swap if from_date is after to_date
            if from_dt > to_dt:
                from_dt, to_dt = to_dt, from_dt
                from_date = from_dt.strftime("%Y-%m-%d")
                to_date = to_dt.strftime("%Y-%m-%d")
        except ValueError as e:
            raise ValidationError(f"Định dạng ngày không hợp lệ: {e}. Dùng YYYY-MM-DD.")

    def _validate_month(self, month: str) -> None:
        """Validate month format.

        Args:
            month: Month in 'YYYY-MM' format.

        Raises:
            ValidationError: If format is invalid.
        """
        try:
            parts = month.split("-")
            if len(parts) != 2:
                raise ValidationError("Month must be in YYYY-MM format")

            year, month_num = int(parts[0]), int(parts[1])
            if not (1 <= month_num <= 12):
                raise ValidationError(f"Month must be 01-12, got: {month_num}")
        except ValueError as e:
            raise ValidationError(f"Invalid month format: {e}. Use YYYY-MM.")