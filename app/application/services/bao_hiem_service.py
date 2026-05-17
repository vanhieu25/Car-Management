"""BaoHiem service - insurance business logic layer.

Insurance types: tnds (TNDS), tai_nan, chao_no, that_lac

CASE 1: Insurance sold by current dealership (dai_ly_ban_id = NULL or current)
CASE 2: Insurance sold by other dealership (dai_ly_ban_id = other dealership ID)
"""

from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import BaoHiem
from app.infrastructure.repositories.bao_hiem_repository import BaoHiemRepository
from app.application.services.audit_log_service import AuditLogService


class BaoHiemServiceError(Exception):
    """Base exception for BaoHiem service errors."""
    pass


class BaoHiemNotFoundError(BaoHiemServiceError):
    """Raised when insurance is not found."""
    pass


class ValidationError(BaoHiemServiceError):
    """Raised when validation fails."""
    pass


@dataclass
class InsuranceData:
    """Data for creating/updating insurance."""
    bao_hanh_id: int = 0
    xe_id: Optional[int] = None
    hop_dong_id: Optional[int] = None
    cong_ty_bh_id: Optional[int] = None
    dai_ly_ban_id: Optional[int] = None
    loai_bh: str = "tnds"
    so_policy: str = ""
    ngay_mua: str = ""
    ngay_hieu_luc: str = ""
    ngay_het_han: str = ""
    phi_bh: int = 0
    gia_tri_bh: int = 0
    trang_thai: str = "con_hieu_luc"
    ghi_chu: str = ""


@dataclass
class InsuranceSearchResult:
    """Search result with metadata."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class BaoHiemService:
    """Service for insurance management operations."""

    LOAI_BH_LABELS = {
        "tnds": "TNDS",
        "tai_nan": "Tai nạn",
        "chao_no": "Cháy nổ",
        "that_lac": "Thất lạc",
        "khac": "Khác",
    }

    TRANG_THAI_LABELS = {
        "con_hieu_luc": "Còn hiệu lực",
        "het_han": "Hết hạn",
        "huy": "Đã hủy",
    }

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = BaoHiemRepository(conn)
        self._audit_service = AuditLogService(conn)

    def create(
        self,
        data: InsuranceData,
        nhan_vien_id: int = None,
    ) -> BaoHiem:
        """Create a new insurance record.

        Args:
            data: InsuranceData with insurance details.
            nhan_vien_id: Employee creating the insurance.

        Returns:
            Created BaoHiem entity.

        Raises:
            ValidationError: If bao_hanh_id is invalid or dates are invalid.
        """
        # Validate bao_hanh exists
        cursor = self.conn.execute(
            "SELECT id FROM bao_hanh WHERE id = ?",
            (data.bao_hanh_id,)
        )
        if not cursor.fetchone():
            raise ValidationError(f"Không tìm thấy bảo hành với ID {data.bao_hanh_id}")

        # Validate dates
        ngay_mua = data.ngay_mua[:10] if len(data.ngay_mua) >= 10 else data.ngay_mua
        ngay_het_han = data.ngay_het_han[:10] if len(data.ngay_het_han) >= 10 else data.ngay_het_han

        if ngay_het_han <= ngay_mua:
            raise ValidationError("Ngày hết hạn phải sau ngày mua")

        now = datetime.now().isoformat()

        insurance = BaoHiem(
            bao_hanh_id=data.bao_hanh_id,
            xe_id=data.xe_id,
            hop_dong_id=data.hop_dong_id,
            cong_ty_bh_id=data.cong_ty_bh_id,
            dai_ly_ban_id=data.dai_ly_ban_id,
            loai_bh=data.loai_bh,
            so_policy=data.so_policy,
            ngay_mua=ngay_mua,
            ngay_hieu_luc=data.ngay_hieu_luc[:10] if data.ngay_hieu_luc and len(data.ngay_hieu_luc) >= 10 else data.ngay_hieu_luc,
            ngay_het_han=ngay_het_han,
            phi_bh=data.phi_bh,
            gia_tri_bh=data.gia_tri_bh,
            trang_thai=data.trang_thai,
            ghi_chu=data.ghi_chu,
            created_at=now,
            created_by=nhan_vien_id,
        )

        self._repo.create(insurance)

        # Audit log
        self._audit_service.log_create(
            action="CREATE_BAO_HIEM",
            nhan_vien_id=nhan_vien_id,
            table="bao_hiem",
            record_id=insurance.id,
            record_data=insurance.to_dict(),
        )

        return insurance

    def get_by_id(self, bh_id: int) -> Optional[BaoHiem]:
        """Get insurance by ID.

        Args:
            bh_id: Insurance ID.

        Returns:
            BaoHiem if found, None otherwise.
        """
        return self._repo.find_by_id(bh_id)

    def get_by_bao_hanh(self, bao_hanh_id: int) -> List[BaoHiem]:
        """Get all insurance for a warranty.

        Args:
            bao_hanh_id: Warranty ID.

        Returns:
            List of BaoHiem entities.
        """
        return self._repo.find_by_bao_hanh_id(bao_hanh_id)

    def get_all(
        self,
        loai_bh: str = None,
        trang_thai: str = None,
        search_keyword: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> InsuranceSearchResult:
        """Get all insurance with filter.

        Args:
            loai_bh: Filter by insurance type.
            trang_thai: Filter by status.
            search_keyword: Search by so_policy, customer name, or vehicle plate.
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            InsuranceSearchResult with items and pagination.
        """
        offset = (page - 1) * page_size
        items, total = self._repo.get_all_with_filter(
            loai_bh=loai_bh,
            trang_thai=trang_thai,
            search_keyword=search_keyword,
            limit=page_size,
            offset=offset,
        )
        total_pages = max(1, (total + page_size - 1) // page_size)

        return InsuranceSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update(
        self,
        bh_id: int,
        data: InsuranceData,
        nhan_vien_id: int = None,
    ) -> BaoHiem:
        """Update an insurance record.

        Args:
            bh_id: Insurance ID.
            data: InsuranceData with updated details.
            nhan_vien_id: Employee making the update.

        Returns:
            Updated BaoHiem entity.

        Raises:
            BaoHiemNotFoundError: If insurance not found.
            ValidationError: If dates are invalid.
        """
        insurance = self._repo.find_by_id(bh_id)
        if not insurance:
            raise BaoHiemNotFoundError(f"Không tìm thấy bảo hiểm với ID {bh_id}")

        # Validate dates if being updated
        if data.ngay_mua or data.ngay_het_han:
            ngay_mua = data.ngay_mua[:10] if data.ngay_mua and len(data.ngay_mua) >= 10 else insurance.ngay_mua
            ngay_het_han = data.ngay_het_han[:10] if data.ngay_het_han and len(data.ngay_het_han) >= 10 else insurance.ngay_het_han

            if ngay_het_han <= ngay_mua:
                raise ValidationError("Ngày hết hạn phải sau ngày mua")

            insurance.ngay_mua = ngay_mua
            insurance.ngay_het_han = ngay_het_han

        if data.loai_bh:
            insurance.loai_bh = data.loai_bh
        if data.so_policy is not None:
            insurance.so_policy = data.so_policy
        if data.phi_bh is not None:
            insurance.phi_bh = data.phi_bh
        if data.cong_ty_bh_id is not None:
            insurance.cong_ty_bh_id = data.cong_ty_bh_id
        if data.ngay_hieu_luc is not None:
            insurance.ngay_hieu_luc = data.ngay_hieu_luc[:10] if data.ngay_hieu_luc and len(data.ngay_hieu_luc) >= 10 else data.ngay_hieu_luc
        if data.dai_ly_ban_id is not None:
            insurance.dai_ly_ban_id = data.dai_ly_ban_id
        if data.trang_thai:
            insurance.trang_thai = data.trang_thai
        if data.ghi_chu is not None:
            insurance.ghi_chu = data.ghi_chu

        insurance.updated_at = datetime.now().isoformat()
        self._repo.update(insurance)

        # Audit log
        self._audit_service.log_update(
            action="UPDATE_BAO_HIEM",
            nhan_vien_id=nhan_vien_id,
            table="bao_hiem",
            record_id=bh_id,
            before={},
            after=insurance.to_dict(),
        )

        return insurance

    def renew(
        self,
        bh_id: int,
        ngay_het_han_moi: str,
        phi_bh_moi: int,
        nhan_vien_id: int = None,
    ) -> BaoHiem:
        """Renew an insurance policy.

        Creates a new insurance record with updated expiry date.
        Marks the old one as expired.

        Args:
            bh_id: Current insurance ID.
            ngay_het_han_moi: New expiry date.
            phi_bh_moi: New insurance fee.
            nhan_vien_id: Employee performing renewal.

        Returns:
            New BaoHiem entity for the renewed policy.

        Raises:
            BaoHiemNotFoundError: If insurance not found.
        """
        old = self._repo.find_by_id(bh_id)
        if not old:
            raise BaoHiemNotFoundError(f"Không tìm thấy bảo hiểm với ID {bh_id}")

        # Mark old as expired
        old.trang_thai = "het_han"
        old.updated_at = datetime.now().isoformat()
        self._repo.update(old)

        # Create new insurance
        ngay_het_han_moi = ngay_het_han_moi[:10] if len(ngay_het_han_moi) >= 10 else ngay_het_han_moi
        new_insurance = BaoHiem(
            bao_hanh_id=old.bao_hanh_id,
            xe_id=old.xe_id,
            hop_dong_id=old.hop_dong_id,
            cong_ty_bh_id=old.cong_ty_bh_id,
            loai_bh=old.loai_bh,
            so_policy=old.so_policy,  # Same policy number (renewal)
            ngay_mua=old.ngay_het_han,  # Starts from old expiry
            ngay_hieu_luc=old.ngay_hieu_luc,
            ngay_het_han=ngay_het_han_moi,
            phi_bh=phi_bh_moi,
            dai_ly_ban_id=old.dai_ly_ban_id,
            trang_thai="con_hieu_luc",
            ghi_chu=f"Gia hạn từ BH {bh_id}",
            created_at=datetime.now().isoformat(),
            created_by=nhan_vien_id,
        )

        self._repo.create(new_insurance)

        # Audit log
        self._audit_service.log_create(
            action="RENEW_BAO_HIEM",
            nhan_vien_id=nhan_vien_id,
            table="bao_hiem",
            record_id=new_insurance.id,
            record_data={
                "old_id": bh_id,
                "old_expiry": old.ngay_het_han,
                "new_expiry": ngay_het_han_moi,
                "new_fee": phi_bh_moi,
            },
        )

        return new_insurance

    def cancel(
        self,
        bh_id: int,
        ly_do: str,
        nhan_vien_id: int = None,
    ) -> BaoHiem:
        """Cancel an insurance policy.

        Args:
            bh_id: Insurance ID.
            ly_do: Cancellation reason.
            nhan_vien_id: Employee performing cancellation.

        Returns:
            Updated BaoHiem entity.

        Raises:
            BaoHiemNotFoundError: If insurance not found.
        """
        insurance = self._repo.find_by_id(bh_id)
        if not insurance:
            raise BaoHiemNotFoundError(f"Không tìm thấy bảo hiểm với ID {bh_id}")

        insurance.trang_thai = "huy"
        insurance.ghi_chu = f"{insurance.ghi_chu}\nHủy: {ly_do}" if insurance.ghi_chu else f"Hủy: {ly_do}"
        insurance.updated_at = datetime.now().isoformat()
        self._repo.update(insurance)

        # Audit log
        self._audit_service.log_update(
            action="CANCEL_BAO_HIEM",
            nhan_vien_id=nhan_vien_id,
            table="bao_hiem",
            record_id=bh_id,
            before={"trang_thai": "con_hieu_luc"},
            after={"trang_thai": "huy", "ly_do": ly_do},
        )

        return insurance

    def find_expiring(self, days: int = 30, dai_ly_ban_id: int = None) -> List[dict]:
        """Find insurance expiring within N days.

        For dashboard warnings.

        Args:
            days: Number of days from today.
            dai_ly_ban_id: Optional dealership filter.

        Returns:
            List of insurance dicts with warranty + customer info.
        """
        return self._repo.find_expiring(days, dai_ly_ban_id)

    def get_dealership_stats(self, dai_ly_ban_id: int = None) -> Dict[str, Any]:
        """Get insurance statistics.

        Args:
            dai_ly_ban_id: Optional dealership filter.

        Returns:
            Dict with total, active, expired counts and total revenue.
        """
        conditions = []
        params = []

        if dai_ly_ban_id is not None:
            conditions.append("dai_ly_ban_id = ?")
            params.append(dai_ly_ban_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Total count
        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM bao_hiem WHERE {where_clause}",
            params
        )
        total = cursor.fetchone()[0]

        # Active count
        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM bao_hiem WHERE {where_clause} AND trang_thai = 'con_hieu_luc'",
            params
        )
        active = cursor.fetchone()[0]

        # Total revenue
        cursor = self.conn.execute(
            f"SELECT COALESCE(SUM(phi_bh), 0) FROM bao_hiem WHERE {where_clause}",
            params
        )
        revenue = cursor.fetchone()[0]

        return {
            "total": total,
            "active": active,
            "expired": total - active,
            "revenue": revenue,
        }

    @staticmethod
    def get_loai_bh_label(loai_bh: str) -> str:
        """Get display label for insurance type."""
        return BaoHiemService.LOAI_BH_LABELS.get(loai_bh, loai_bh)

    @staticmethod
    def get_trang_thai_label(trang_thai: str) -> str:
        """Get display label for insurance status."""
        return BaoHiemService.TRANG_THAI_LABELS.get(trang_thai, trang_thai)