"""BaoHanh service - warranty business logic layer.

Implements business rules:
- BR-BH-01..10: Warranty management
- BR-BH-01: Auto-create BH when contract is delivered
- BR-BH-02: ngay_ket_thuc = ngay_bat_dau + thoi_han_bh months
- BR-BH-03: Warn when warranty expiring within 30 days
- BR-BH-04: Classify requests (mien_phi / tinh_phi)
- BR-BH-05: Request status transitions
- BR-BH-06: chi_phi validation
- BR-BH-07: Warranty slip PDF content
- BR-BH-08: Multiple requests per warranty
- BR-BH-09: Cost reporting
- BR-BH-10: Delete BH when contract is cancelled
"""

from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any

import sqlite3

from app.infrastructure.repositories.bao_hanh_repository import BaoHanhRepository, BaoHanhYeuCau
from app.application.services.audit_log_service import AuditLogService
from app.application.services.system_settings_service import SystemSettingsService


class BaoHanhServiceError(Exception):
    """Base exception for BaoHanh service errors."""
    pass


class BaoHanhNotFoundError(BaoHanhServiceError):
    """Raised when warranty is not found."""
    pass


class BaoHanhYeuCauNotFoundError(BaoHanhServiceError):
    """Raised when warranty request is not found."""
    pass


class InvalidStateTransitionError(BaoHanhServiceError):
    """Raised when state transition is not allowed."""
    pass


class ValidationError(BaoHanhServiceError):
    """Raised when validation fails."""
    pass


# Keywords that indicate customer fault (tinh_phi)
CUSTOMER_FAULT_KEYWORDS = [
    "va đập", "va dap", "đập", "dap",
    "ngập nước", "ngap nuoc", "ngập", "ngap",
    "tai nan", "tai nạn",
    "sử dụng sai", "su dung sai",
    "không bảo dưỡng", "khong bao duong",
    "tự sửa", "tu sua",
    "rơi", "roi",
]


@dataclass
class BaoHanhYeuCauData:
    """Data for creating/updating a warranty request."""
    ngay_yeu_cau: str = ""
    loai_yeu_cau: str = "sua_chua"
    mo_ta_tinh_trang: str = ""
    phan_loai: str = "mien_phi"
    chi_phi: int = 0
    nhan_vien_id: int = 0
    ghi_chu: str = ""


@dataclass
class YeuCauSearchResult:
    """Search result with metadata."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class BaoHanhService:
    """Service for warranty management operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = BaoHanhRepository(conn)
        self._audit_service = AuditLogService(conn)
        self._settings_service = SystemSettingsService(conn)

    def get_by_id(self, bh_id: int) -> Optional[Dict[str, Any]]:
        """Get warranty with full details.

        Args:
            bh_id: Warranty ID.

        Returns:
            Dict with warranty + KH + Xe + HD + requests or None.
        """
        return self._repo.get_warranty_with_details(bh_id)

    def get_by_hop_dong_id(self, hop_dong_id: int) -> Optional[Dict[str, Any]]:
        """Get warranty by contract ID.

        Args:
            hop_dong_id: Contract ID.

        Returns:
            Warranty dict or None.
        """
        bh = self._repo.find_by_hop_dong_id(hop_dong_id)
        if bh:
            return self._repo.get_warranty_with_details(bh.id)
        return None

    def get_all(
        self,
        trang_thai: str = None,
        search_keyword: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> YeuCauSearchResult:
        """Get all warranties with filter.

        Args:
            trang_thai: Filter by status ('con_hieu_luc', 'sap_het_han', 'het_han', 'tat_ca').
            search_keyword: Search by BH code or customer name.
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            YeuCauSearchResult with items and pagination.
        """
        offset = (page - 1) * page_size
        items, total = self._repo.get_all_with_filter(
            trang_thai=trang_thai,
            search_keyword=search_keyword,
            limit=page_size,
            offset=offset,
        )
        total_pages = max(1, (total + page_size - 1) // page_size)

        return YeuCauSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def auto_create_from_hop_dong(self, hop_dong_id: int, nhan_vien_id: int = None) -> Dict[str, Any]:
        """Auto-create warranty when contract is delivered (TRG-02).

        BR-BH-01: One warranty per contract
        BR-BH-02: ngay_ket_thuc = ngay_giao_xe + thoi_han_bh months
        Gets thoi_han_bh from system_settings

        Args:
            hop_dong_id: Contract ID.
            nhan_vien_id: Employee ID performing delivery.

        Returns:
            Dict with created warranty details.

        Raises:
            BaoHanhNotFoundError: If contract not found.
        """
        # Check if warranty already exists (UNIQUE constraint prevents duplicates)
        existing = self._repo.find_by_hop_dong_id(hop_dong_id)
        if existing:
            return self._repo.get_warranty_with_details(existing.id)

        # Get contract info
        cursor = self.conn.execute(
            "SELECT * FROM hop_dong WHERE id = ?", (hop_dong_id,)
        )
        hd_row = cursor.fetchone()
        if not hd_row:
            raise BaoHanhNotFoundError(f"Không tìm thấy hợp đồng với ID {hop_dong_id}")

        hop_dong = dict(hd_row)

        # Get warranty months from system settings
        thoi_han_bh = self._settings_service.get_warranty_months()

        # Calculate dates
        ngay_giao_xe = hop_dong.get("ngay_giao_xe")
        if not ngay_giao_xe:
            ngay_giao_xe = datetime.now().isoformat()

        ngay_bat_dau = ngay_giao_xe[:10] if len(ngay_giao_xe) >= 10 else ngay_giao_xe
        start_date = datetime.fromisoformat(ngay_bat_dau)
        ngay_ket_thuc = (start_date + relativedelta(months=thoi_han_bh)).strftime("%Y-%m-%d")

        now = datetime.now().isoformat()

        try:
            self.conn.execute("BEGIN TRANSACTION")

            # Insert warranty
            self.conn.execute(
                """INSERT INTO bao_hanh
                   (hop_dong_id, xe_id, khach_hang_id, thoi_han_bh,
                    ngay_bat_dau, ngay_ket_thuc, pham_vi, trang_thai,
                    created_at, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'con_hieu_luc', ?, ?)""",
                (
                    hop_dong_id,
                    hop_dong["xe_id"],
                    hop_dong["khach_hang_id"],
                    thoi_han_bh,
                    ngay_bat_dau,
                    ngay_ket_thuc,
                    "Bảo hành toàn diện theo điều khoản chuẩn của nhà sản xuất",
                    now,
                    nhan_vien_id,
                )
            )

            bh_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Audit log
        self._audit_service.log_create(
            action="CREATE_BH",
            nhan_vien_id=nhan_vien_id,
            table="bao_hanh",
            record_id=bh_id,
            record_data={"hop_dong_id": hop_dong_id, "thoi_han_bh": thoi_han_bh},
        )

        return self._repo.get_warranty_with_details(bh_id)

    def create_request(
        self,
        bh_id: int,
        data: BaoHanhYeuCauData,
        nhan_vien_id: int = None,
    ) -> Dict[str, Any]:
        """Create a warranty request.

        BR-BH-04: Classify as mien_phi (NSX fault) or tinh_phi (KH fault)
        Auto-suggest classification based on loai_yeu_cau keywords
        BR-BH-05: Status starts as 'dang_xu_ly'

        Args:
            bh_id: Warranty ID.
            data: BaoHanhYeuCauData with request details.
            nhan_vien_id: Employee creating the request.

        Returns:
            Dict with created request.

        Raises:
            BaoHanhNotFoundError: If warranty not found.
            ValidationError: If request date is after warranty end date.
        """
        # Get warranty
        warranty = self._repo.get_warranty_with_details(bh_id)
        if not warranty:
            raise BaoHanhNotFoundError(f"Không tìm thấy bảo hành với ID {bh_id}")

        # BR-BH-04: Validate date is within warranty period
        ngay_yeu_cau = data.ngay_yeu_cau[:10] if len(data.ngay_yeu_cau) >= 10 else data.ngay_yeu_cau
        ngay_ket_thuc = warranty.get("ngay_ket_thuc", "")[:10]

        if ngay_yeu_cau > ngay_ket_thuc:
            raise ValidationError(
                f"Ngày yêu cầu ({ngay_yeu_cau}) không được sau ngày kết thúc BH ({ngay_ket_thuc})"
            )

        # Auto-suggest classification based on keywords
        phan_loai = self._suggest_phan_loai(data.mo_ta_tinh_trang)

        # chi_phi: 0 for mien_phi, require for tinh_phi
        chi_phi = data.chi_phi if phan_loai == "tinh_phi" else 0

        # Assign to available technician if not specified
        nhan_vien_id = data.nhan_vien_id or self._find_available_technician()

        now = datetime.now().isoformat()

        req = BaoHanhYeuCau(
            bao_hanh_id=bh_id,
            nhan_vien_id=nhan_vien_id,
            ngay_yeu_cau=data.ngay_yeu_cau or now,
            mo_ta_tinh_trang=data.mo_ta_tinh_trang,
            loai_yeu_cau=data.loai_yeu_cau,
            chi_phi=chi_phi,
            trang_thai="dang_xu_ly",
            ghi_chu=data.ghi_chu,
            created_at=now,
            created_by=nhan_vien_id,
        )

        self._repo.create_yeu_cau(req)

        # Audit log
        self._audit_service.log_create(
            action="CREATE_BH_REQUEST",
            nhan_vien_id=nhan_vien_id,
            table="bao_hanh_yeu_cau",
            record_id=req.id,
            record_data=req.to_dict(),
        )

        return req.to_dict()

    def update_request(
        self,
        req_id: int,
        trang_thai: str = None,
        chi_phi: int = None,
        nhan_vien_id: int = None,
        ghi_chu: str = None,
        nhan_vien_id_current: int = None,
    ) -> Dict[str, Any]:
        """Update a warranty request.

        BR-BH-05: Valid transitions:
        - moi -> dang_xu_ly
        - dang_xu_ly -> da_hoan_thanh
        - dang_xu_ly -> da_dong (rejected)
        BR-BH-06: chi_phi validation

        Args:
            req_id: Request ID.
            trang_thai: New status (if changing).
            chi_phi: Final cost (when completing).
            nhan_vien_id: New technician ID (if reassigning).
            ghi_chu: Updated note.
            nhan_vien_id_current: Current user ID for audit.

        Returns:
            Dict with updated request.

        Raises:
            BaoHanhYeuCauNotFoundError: If request not found.
            InvalidStateTransitionError: If transition is not allowed.
        """
        req = self._repo.find_yeu_cau_by_id(req_id)
        if not req:
            raise BaoHanhYeuCauNotFoundError(f"Không tìm thấy yêu cầu BH với ID {req_id}")

        # BR-BH-05: Validate state transitions
        valid_transitions = {
            "moi": ["dang_xu_ly", "da_dong"],
            "dang_xu_ly": ["da_hoan_thanh", "da_dong"],
            "da_hoan_thanh": [],
            "da_dong": [],
        }

        if trang_thai and trang_thai != req.trang_thai:
            allowed = valid_transitions.get(req.trang_thai, [])
            if trang_thai not in allowed:
                raise InvalidStateTransitionError(
                    f"Không thể chuyển từ '{req.trang_thai}' sang '{trang_thai}'. "
                    f"Các trạng thái cho phép: {allowed}"
                )
            req.trang_thai = trang_thai

            # When completing, set ngay_hoan_thanh
            if trang_thai == "da_hoan_thanh":
                req.ngay_hoan_thanh = datetime.now().isoformat()

        # Update chi_phi if provided
        if chi_phi is not None:
            req.chi_phi = chi_phi

        # Reassign technician if provided
        if nhan_vien_id is not None:
            req.nhan_vien_id = nhan_vien_id

        # Update note if provided
        if ghi_chu is not None:
            req.ghi_chu = ghi_chu

        req.updated_at = datetime.now().isoformat()
        self._repo.update_yeu_cau(req)

        # Audit log
        self._audit_service.log_update(
            action="UPDATE_BH_REQUEST",
            nhan_vien_id=nhan_vien_id_current,
            table="bao_hanh_yeu_cau",
            record_id=req_id,
            before={"trang_thai": req.trang_thai, "chi_phi": req.chi_phi},
            after={"trang_thai": trang_thai or req.trang_thai, "chi_phi": chi_phi or req.chi_phi},
        )

        return req.to_dict()

    def find_expiring_in_30_days(self) -> List[Dict[str, Any]]:
        """Find warranties expiring within 30 days (BR-BH-03).

        For dashboard warning display.

        Returns:
            List of warranty dicts with KH info.
        """
        return self._repo.find_expiring_in_30_days()

    def export_warranty_pdf(self, bh_id: int, output_path: str) -> str:
        """Export warranty as PDF.

        BR-BH-07: Warranty slip must contain:
        - Vehicle info
        - Customer info
        - Warranty period
        - Request content
        - Technician
        - Total cost

        Args:
            bh_id: Warranty ID.
            output_path: Path to save PDF.

        Returns:
            Path to saved PDF.
        """
        from app.infrastructure.pdf_renderer import PdfRenderer
        import os

        # Get template directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )))
        template_dir = os.path.join(base_dir, "resources", "templates")
        css_path = os.path.join(template_dir, "warranty.css")

        renderer = PdfRenderer(template_dir, css_path)
        return renderer.render_warranty(bh_id, output_path, self.conn)

    def _suggest_phan_loai(self, mo_ta: str) -> str:
        """Suggest classification based on description keywords.

        BR-BH-04: Keywords like "va đập", "ngập nước" → tinh_phi

        Args:
            mo_ta: Description text.

        Returns:
            "mien_phi" or "tinh_phi".
        """
        mo_ta_lower = mo_ta.lower()
        for keyword in CUSTOMER_FAULT_KEYWORDS:
            if keyword in mo_ta_lower:
                return "tinh_phi"
        return "mien_phi"

    def _find_available_technician(self) -> int:
        """Find an available technician.

        Returns:
            Technician's nhan_vien_id, or 0 if none found.
        """
        cursor = self.conn.execute(
            """SELECT id FROM nhan_vien
               WHERE trang_thai = 'active'
               LIMIT 1"""
        )
        row = cursor.fetchone()
        return row[0] if row else 0
