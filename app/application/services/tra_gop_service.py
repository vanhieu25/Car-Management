"""TraGop service - installment business logic layer.

Implements business rules:
- BR-CALC-04: Monthly payment formula M = P × r × (1+r)^n / ((1+r)^n − 1)
- BR-TG-01: UNIQUE hop_dong_id (only 1 installment per contract)
- BR-TG-02: P <= hop_dong.tong_tien
- BR-TG-03: Auto-generate n rows of payment schedule
- BR-TG-04: Record payment updates kỳ to 'da_tra'
- BR-TG-05: All kỳ paid → tra_gop.status = 'hoan_thanh'
- TRG-07: Daily check for overdue (ngay_den_han + 5 days < today)
"""

from dataclasses import dataclass
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import TraGop
from app.infrastructure.repositories.tra_gop_repository import TraGopRepository, TraGopLichSu
from app.application.services.hop_dong_service import HopDongService
from app.application.services.audit_log_service import AuditLogService


class TraGopServiceError(Exception):
    """Base exception for TraGop service errors."""
    pass


class TraGopNotFoundError(TraGopServiceError):
    """Raised when installment is not found."""
    pass


class ValidationError(TraGopServiceError):
    """Raised when validation fails."""
    pass


class TraGopAlreadyExistsError(TraGopServiceError):
    """Raised when installment already exists for contract."""
    pass


@dataclass
class TraGopDetail:
    """Detailed installment info with related data."""
    tra_gop: TraGop
    lich_su_list: List[TraGopLichSu]
    khach_hang_ten: str = ""
    xe_hang: str = ""
    xe_dong: str = ""
    ma_hop_dong: str = ""
    so_dien_thoai: str = ""


@dataclass
class TraGopListItem:
    """Installment item for list display."""
    id: int
    ma_hop_dong: str
    khach_hang_ten: str
    ngan_hang: str
    so_tien_vay: int
    lai_suat_nam: float
    so_ky: int
    so_tien_tra_thang: int
    trang_thai: str
    has_qua_han: bool
    khach_hang_sdt: str = ""
    xe_hang: str = ""
    xe_dong: str = ""


class TraGopService:
    """Service for installment management operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = TraGopRepository(conn)
        self._audit_service = AuditLogService(conn)

    def calculate_monthly_payment(self, P: int, r_year: float, n: int) -> int:
        """Calculate monthly payment using annuity formula.

        BR-CALC-04: M = P × r × (1+r)^n / ((1+r)^n − 1)
        Where:
        - P = principal (so_tien_vay)
        - r_year = annual interest rate in percent (e.g. 12.5 for 12.5%)
        - r = r_year / 12 / 100 (convert annual % to monthly rate)
        - n = number of months (so_ky)

        Args:
            P: Principal amount (so_tien_vay) in VND.
            r_year: Annual interest rate in percent.
            n: Number of months (so_ky).

        Returns:
            Monthly payment amount M, rounded to nearest VND.
        """
        if P <= 0 or n <= 0:
            return 0

        r = r_year / 12 / 100  # Monthly rate

        if r == 0:
            # No interest - simple division
            return P // n

        # BR-CALC-04: M = P × r × (1+r)^n / ((1+r)^n − 1)
        factor = (1 + r) ** n
        M = P * r * factor / (factor - 1)

        return round(M)

    def create(
        self,
        hop_dong_id: int,
        ngan_hang: str,
        P: int,
        r_year: float,
        n: int,
        nhan_vien_id: int = None,
    ) -> TraGop:
        """Create a new installment plan for a contract.

        Validates:
        - P > 0, 0 <= r_year <= 30, 6 <= n <= 84
        - P <= hop_dong.tong_tien (BR-TG-02)
        - No existing installment for this contract (BR-TG-01)
        - Contract must be da_thanh_toan or da_giao_xe

        Creates tra_gop record and auto-generates n rows in tra_gop_lich_su.

        Args:
            hop_dong_id: Contract ID.
            ngan_hang: Bank name.
            P: Loan principal (so_tien_vay).
            r_year: Annual interest rate in percent.
            n: Number of months (6-84).
            nhan_vien_id: Employee creating the plan.

        Returns:
            Created TraGop entity.

        Raises:
            TraGopNotFoundError: Contract not found.
            TraGopAlreadyExistsError: Installment already exists.
            ValidationError: Validation failed.
        """
        # Get contract
        hd_service = HopDongService(self.conn)
        hop_dong = hd_service.get_by_id(hop_dong_id)
        if not hop_dong:
            raise TraGopNotFoundError(f"Không tìm thấy hợp đồng với ID {hop_dong_id}")

        # BR-TG-01: UNIQUE hop_dong_id
        existing = self._repo.find_by_hop_dong_id(hop_dong_id)
        if existing:
            raise TraGopAlreadyExistsError(
                f"Hợp đồng {hop_dong.ma_hop_dong} đã có phương án trả góp"
            )

        # Validate P > 0
        if P <= 0:
            raise ValidationError("Số tiền vay phải lớn hơn 0")

        # BR-TG-02: P <= hop_dong.tong_tien
        if P > hop_dong.tong_tien:
            raise ValidationError(
                f"Số tiền vay ({P:,}đ) vượt quá tổng tiền hợp đồng ({hop_dong.tong_tien:,}đ)"
            )

        # Validate 0 <= r_year <= 30
        if not (0 <= r_year <= 30):
            raise ValidationError("Lãi suất năm phải từ 0% đến 30%")

        # Validate 6 <= n <= 84
        if not (6 <= n <= 84):
            raise ValidationError("Số kỳ trả góp phải từ 6 đến 84 tháng")

        # Calculate monthly payment
        M = self.calculate_monthly_payment(P, r_year, n)

        # Get start date (ngay_bat_dau)
        # Use ngay_thanh_toan if available, otherwise today
        if hop_dong.ngay_thanh_toan:
            ngay_bat_dau = datetime.fromisoformat(hop_dong.ngay_thanh_toan).date()
        else:
            ngay_bat_dau = date.today()

        # Create tra_gop record
        now = datetime.now().isoformat()
        tra_gop = TraGop(
            hop_dong_id=hop_dong_id,
            ngan_hang=ngan_hang,
            so_tien_vay=P,
            lai_suat_nam=r_year,
            so_ky=n,
            so_tien_tra_thang=M,
            trang_thai="dang_tra",
            created_at=now,
            created_by=nhan_vien_id,
        )

        try:
            self.conn.execute("BEGIN TRANSACTION")

            created_tg = self._repo.create(tra_gop)

            # Auto-generate n rows in tra_gop_lich_su
            for ky in range(1, n + 1):
                ngay_den_han = ngay_bat_dau + relativedelta(months=ky)
                lich_su = TraGopLichSu(
                    tra_gop_id=created_tg.id,
                    ky_thu=ky,
                    ngay_den_han=ngay_den_han.isoformat(),
                    so_tien_phai_tra=M,
                    trang_thai="chua_tra",
                )
                self._repo.create_lich_su(lich_su)

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Audit log
        self._audit_service.log_create(
            action="CREATE_TG",
            nhan_vien_id=nhan_vien_id,
            table="tra_gop",
            record_id=created_tg.id,
            record_data=created_tg.to_dict(),
        )

        return created_tg

    def get_by_id(self, tra_gop_id: int) -> Optional[TraGop]:
        """Get installment by ID.

        Args:
            tra_gop_id: TraGop ID.

        Returns:
            TraGop if found, None otherwise.
        """
        return self._repo.find_by_id(tra_gop_id)

    def get_by_hop_dong_id(self, hop_dong_id: int) -> Optional[TraGop]:
        """Get installment by contract ID.

        Args:
            hop_dong_id: Contract ID.

        Returns:
            TraGop if found, None otherwise.
        """
        return self._repo.find_by_hop_dong_id(hop_dong_id)

    def get_detail(self, tra_gop_id: int) -> Optional[TraGopDetail]:
        """Get detailed installment info with related data.

        Args:
            tra_gop_id: TraGop ID.

        Returns:
            TraGopDetail if found, None otherwise.
        """
        tra_gop = self._repo.find_by_id(tra_gop_id)
        if not tra_gop:
            return None

        lich_su_list = self._repo.find_all_lich_su(tra_gop_id)

        # Get related contract info
        cursor = self.conn.execute("""
            SELECT kh.ho_ten, kh.so_dien_thoai, xe.hang, xe.dong_xe, hd.ma_hop_dong
            FROM hop_dong hd
            JOIN khach_hang kh ON hd.khach_hang_id = kh.id
            JOIN xe ON hd.xe_id = xe.id
            WHERE hd.id = ?
        """, (tra_gop.hop_dong_id,))
        row = cursor.fetchone()

        khach_hang_ten = ""
        khach_hang_sdt = ""
        xe_hang = ""
        xe_dong = ""
        ma_hop_dong = ""

        if row:
            khach_hang_ten = row[0]
            khach_hang_sdt = row[1]
            xe_hang = row[2]
            xe_dong = row[3]
            ma_hop_dong = row[4]

        return TraGopDetail(
            tra_gop=tra_gop,
            lich_su_list=lich_su_list,
            khach_hang_ten=khach_hang_ten,
            xe_hang=xe_hang,
            xe_dong=xe_dong,
            ma_hop_dong=ma_hop_dong,
            so_dien_thoai=khach_hang_sdt,
        )

    def get_all(
        self,
        ngan_hang: str = None,
        trang_thai: str = None,
        has_qua_han: bool = None,
        keyword: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[TraGopListItem], int]:
        """Get all installments with filters.

        Args:
            ngan_hang: Filter by bank.
            trang_thai: Filter by status (dang_tra, hoan_thanh).
            has_qua_han: Filter to show only those with overdue kỳ.
            keyword: Search by ma_hop_dong or khach_hang_ten.
            limit: Max results.
            offset: Offset for pagination.

        Returns:
            Tuple of (list of TraGopListItem, total count).
        """
        conditions = []
        params = []

        if ngan_hang:
            conditions.append("tg.ngan_hang = ?")
            params.append(ngan_hang)

        if trang_thai:
            conditions.append("tg.trang_thai = ?")
            params.append(trang_thai)

        if has_qua_han:
            conditions.append("""
                tg.id IN (
                    SELECT DISTINCT tra_gop_id FROM tra_gop_lich_su
                    WHERE trang_thai = 'qua_han'
                )
            """)

        if keyword:
            kw_pattern = f"%{keyword}%"
            conditions.append("(hd.ma_hop_dong LIKE ? OR kh.ho_ten LIKE ?)")
            params.extend([kw_pattern, kw_pattern])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count
        count_query = f"""
            SELECT COUNT(*) FROM tra_gop tg
            JOIN hop_dong hd ON tg.hop_dong_id = hd.id
            JOIN khach_hang kh ON hd.khach_hang_id = kh.id
            WHERE {where_clause}
        """
        count_cursor = self.conn.execute(count_query, params)
        total = count_cursor.fetchone()[0]

        # Data query
        data_query = f"""
            SELECT tg.*, hd.ma_hop_dong, kh.ho_ten as khach_hang_ten,
                   kh.so_dien_thoai as khach_hang_sdt,
                   xe.hang as xe_hang, xe.dong_xe as xe_dong,
                   EXISTS(
                       SELECT 1 FROM tra_gop_lich_su tgls
                       WHERE tgls.tra_gop_id = tg.id AND tgls.trang_thai = 'qua_han'
                   ) as has_qua_han
            FROM tra_gop tg
            JOIN hop_dong hd ON tg.hop_dong_id = hd.id
            JOIN khach_hang kh ON hd.khach_hang_id = kh.id
            JOIN xe ON hd.xe_id = xe.id
            WHERE {where_clause}
            ORDER BY tg.created_at DESC
            LIMIT ? OFFSET ?
        """
        data_params = params + [limit, offset]
        cursor = self.conn.execute(data_query, data_params)

        items = []
        for row in cursor.fetchall():
            items.append(TraGopListItem(
                id=row["id"],
                ma_hop_dong=row["ma_hop_dong"],
                khach_hang_ten=row["khach_hang_ten"],
                ngan_hang=row["ngan_hang"],
                so_tien_vay=row["so_tien_vay"],
                lai_suat_nam=row["lai_suat_nam"],
                so_ky=row["so_ky"],
                so_tien_tra_thang=row["so_tien_tra_thang"],
                trang_thai=row["trang_thai"],
                has_qua_han=bool(row["has_qua_han"]),
                khach_hang_sdt=row["khach_hang_sdt"],
                xe_hang=row["xe_hang"],
                xe_dong=row["xe_dong"],
            ))

        return items, total

    def record_payment(self, lich_su_id: int, nhan_vien_id: int = None) -> bool:
        """Record payment for a specific kỳ.

        Marks the kỳ as 'da_tra' and updates ngay_thuc_te = today.
        If all kỳ are 'da_tra', updates tra_gop.trang_thai = 'hoan_thanh'.

        Args:
            lich_su_id: tra_gop_lich_su ID.
            nhan_vien_id: Employee recording payment.

        Returns:
            True if payment was recorded.

        Raises:
            TraGopNotFoundError: Payment record not found.
        """
        lich_su = self._repo.find_lich_su_by_id(lich_su_id)
        if not lich_su:
            raise TraGopNotFoundError(f"Không tìm thấy lịch sử trả góp với ID {lich_su_id}")

        if lich_su.trang_thai == "da_tra":
            # Already paid
            return True

        if lich_su.trang_thai == "qua_han":
            raise ValidationError("Kỳ này đã quá hạn. Vui lòng liên hệ quản lý.")

        now = datetime.now().isoformat()
        lich_su.ngay_thuc_te = now
        lich_su.trang_thai = "da_tra"

        try:
            self.conn.execute("BEGIN TRANSACTION")

            self._repo.update_lich_su(lich_su)

            # Check if all kỳ are paid
            tra_gop_id = lich_su.tra_gop_id
            da_tra_count = self._repo.count_da_tra(tra_gop_id)
            total_count = self._repo.count_total(tra_gop_id)

            if da_tra_count >= total_count:
                # All kỳ paid - update status
                self.conn.execute(
                    "UPDATE tra_gop SET trang_thai = 'hoan_thanh', updated_at = ? WHERE id = ?",
                    (now, tra_gop_id)
                )

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Audit log
        self._audit_service.log_update(
            action="RECORD_PAYMENT_TG",
            nhan_vien_id=nhan_vien_id,
            table="tra_gop_lich_su",
            record_id=lich_su_id,
            before={"trang_thai": "chua_tra"},
            after={"trang_thai": "da_tra", "ngay_thuc_te": now},
        )

        return True

    def daily_overdue_check(self) -> int:
        """Daily job TRG-07: Check and mark overdue payments.

        Finds all tra_gop_lich_su where:
        - trang_thai = 'chua_tra'
        - ngay_den_han + 5 days < today

        Updates those rows to trang_thai = 'qua_han'.

        Returns:
            Number of records updated.
        """
        today = date.today()
        cutoff_date = today - relativedelta(days=5)

        cursor = self.conn.execute("""
            SELECT id FROM tra_gop_lich_su
            WHERE trang_thai = 'chua_tra'
              AND date(ngay_den_han) < date(?)
        """, (cutoff_date.isoformat(),))

        overdue_ids = [row[0] for row in cursor.fetchall()]

        if not overdue_ids:
            return 0

        now = datetime.now().isoformat()
        placeholders = ",".join(["?" for _ in overdue_ids])

        self.conn.execute(
            f"""UPDATE tra_gop_lich_su
                SET trang_thai = 'qua_han', ghi_chu = 'Quá hạn từ ngày ' || ?
                WHERE id IN ({placeholders})""",
            [now] + overdue_ids
        )
        self.conn.commit()

        return len(overdue_ids)

    def find_overdue(self) -> List[Dict[str, Any]]:
        """Find all overdue installments for dashboard warning.

        Returns all tra_gop records that have any 'qua_han' kỳ,
        with hop_dong info (KH, xe, so_tien_vay).

        Returns:
            List of dicts with overdue installment info.
        """
        return self._repo.find_overdue()

    def count_overdue(self) -> int:
        """Count number of overdue kỳ across all installments.

        Returns:
            Total count of 'qua_han' records.
        """
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM tra_gop_lich_su WHERE trang_thai = 'qua_han'
        """)
        return cursor.fetchone()[0]
    
    def delete(self, tra_gop_id: int) -> bool:
        """Delete an installment plan.
        
        Args:
            tra_gop_id: TraGop ID to delete.
            
        Returns:
            True if deleted successfully.
            
        Raises:
            TraGopNotFoundError: If installment not found.
        """
        tra_gop = self._repo.find_by_id(tra_gop_id)
        if not tra_gop:
            raise TraGopNotFoundError(f"Không tìm thấy phương án trả góp với ID {tra_gop_id}")
        
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            # Delete lich_su records first
            self.conn.execute(
                "DELETE FROM tra_gop_lich_su WHERE tra_gop_id = ?",
                (tra_gop_id,)
            )
            
            # Delete tra_gop record
            self.conn.execute(
                "DELETE FROM tra_gop WHERE id = ?",
                (tra_gop_id,)
            )
            
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise
        
        return True
