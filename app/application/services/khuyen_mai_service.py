"""KhuyenMai service - promotion business logic layer.

Implements business rules:
- BR-KM-01 to BR-KM-10: Promotion lifecycle management
- BR-CALC-02: 4 types of discount calculation
- BR-KM-04: Active promotions (dang_chay) within date range
- BR-KM-07: Pause/resume promotion status
- TRG-06: Daily expiry check for promotions
- BR-KM-09: Promotion effectiveness report
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import KhuyenMai
from app.infrastructure.repositories.khuyen_mai_repository import KhuyenMaiRepository, KhuyenMaiPhamVi


class KhuyenMaiServiceError(Exception):
    """Base exception for KhuyenMai service errors."""
    pass


class KhuyenMaiNotFoundError(KhuyenMaiServiceError):
    """Raised when promotion is not found."""
    pass


class InvalidDateRangeError(KhuyenMaiServiceError):
    """Raised when date range is invalid (den_ngay <= tu_ngay)."""
    pass


class InvalidGiaTriError(KhuyenMaiServiceError):
    """Raised when gia_tri is invalid (gia_tri <= 0)."""
    pass


class InvalidLoaiKMError(KhuyenMaiServiceError):
    """Raised when loai_km is not valid."""
    pass


class KhuyenMaiExpiredError(KhuyenMaiServiceError):
    """Raised when operation not allowed on expired promotion."""
    pass


VALID_LOAI_KM = {"giam_tien_mat", "giam_phan_tram", "tang_phu_kien", "giam_lai_suat", "combo"}


@dataclass
class KhuyenMaiCreateData:
    """Data for creating a new promotion."""
    ten_km: str
    mo_ta: str = ""
    loai_km: str  # 'giam_tien_mat', 'giam_phan_tram', 'tang_phu_kien', 'giam_lai_suat', 'combo'
    gia_tri: int
    kieu_gia_tri: str = "tien"  # 'tien' or 'phan_tram'
    tu_ngay: str  # ISO date string YYYY-MM-DD
    den_ngay: str  # ISO date string YYYY-MM-DD
    trang_thai: str = "dang_chay"
    so_luong_cho_phep: Optional[int] = None
    created_by: int = None


@dataclass
class KhuyenMaiPhamViData:
    """Data for a promotion scope."""
    loai_ap_dung: str  # 'all', 'hang', 'dong_xe', 'xe'
    gia_tri_ap_dung: Optional[str] = None


@dataclass
class KhuyenMaiWithPhamVi:
    """Promotion with its scopes."""
    id: int
    ten_km: str
    mo_ta: str
    loai_km: str
    gia_tri: int
    kieu_gia_tri: str
    tu_ngay: str
    den_ngay: str
    trang_thai: str
    so_luong_cho_phep: Optional[int]
    so_luong_da_su_dung: int
    pham_vi: List[KhuyenMaiPhamViData]


@dataclass
class DiscountResult:
    """Result of discount calculation."""
    loai_km: str
    gia_tri: int
    kieu_gia_tri: str
    tien_giam: int
    gia_sau_km: int
    tang_phu_kien: Optional[List[Dict[str, Any]]] = None  # For tang_phu_kien type
    lai_suat_fig: Optional[float] = None  # For giam_lai_suat type
    gia_combo: Optional[int] = None  # For combo type


class KhuyenMaiService:
    """Service for promotion management operations."""

    def __init__(self, conn: sqlite3.Connection, session=None):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
            session: Current user session (optional, for audit/permission).
        """
        self.conn = conn
        self._repo = KhuyenMaiRepository(conn)
        self._session = session

    def get_by_id(self, km_id: int) -> Optional[KhuyenMai]:
        """Get promotion by ID.

        Args:
            km_id: Promotion ID.

        Returns:
            KhuyenMai if found, None otherwise.
        """
        return self._repo.find_by_id(km_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[KhuyenMai]:
        """Get all promotions with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of KhuyenMai entities.
        """
        return self._repo.find_all(limit, offset)

    def get_with_pham_vi(self, km_id: int) -> Optional[KhuyenMaiWithPhamVi]:
        """Get promotion with its scopes.

        Args:
            km_id: Promotion ID.

        Returns:
            KhuyenMaiWithPhamVi if found, None otherwise.
        """
        km = self._repo.find_by_id(km_id)
        if not km:
            return None

        pham_vi_rows = self._repo.get_pham_vi(km_id)
        pham_vi_list = [
            KhuyenMaiPhamViData(
                loai_ap_dung=pv.loai_ap_dung,
                gia_tri_ap_dung=pv.gia_tri_ap_dung,
            )
            for pv in pham_vi_rows
        ]

        return KhuyenMaiWithPhamVi(
            id=km.id,
            ten_km=km.ten_km,
            mo_ta=km.mo_ta or "",
            loai_km=km.loai_km,
            gia_tri=km.gia_tri,
            kieu_gia_tri=km.kieu_gia_tri,
            tu_ngay=km.tu_ngay,
            den_ngay=km.den_ngay,
            trang_thai=km.trang_thai,
            so_luong_cho_phep=km.so_luong_cho_phep,
            so_luong_da_su_dung=km.so_luong_da_su_dung,
            pham_vi=pham_vi_list,
        )

    def create(self, data: KhuyenMaiCreateData, pham_vi_list: List[KhuyenMaiPhamViData] = None) -> KhuyenMaiWithPhamVi:
        """Create a new promotion.

        T-G4.2.BE.01:
        - Validate den_ngay > tu_ngay
        - Validate gia_tri > 0
        - Validate loai_km in valid types
        - Create km record + km_pham_vi records

        Args:
            data: KhuyenMaiCreateData with promotion data.
            pham_vi_list: List of scope data (optional).

        Returns:
            Created KhuyenMaiWithPhamVi.

        Raises:
            InvalidDateRangeError: If den_ngay <= tu_ngay.
            InvalidGiaTriError: If gia_tri <= 0.
            InvalidLoaiKMError: If loai_km not in valid types.
        """
        # Validate date range
        if data.den_ngay <= data.tu_ngay:
            raise InvalidDateRangeError(
                "Ngày kết thúc phải lớn hơn ngày bắt đầu"
            )

        # Validate gia_tri > 0
        if data.gia_tri <= 0:
            raise InvalidGiaTriError(
                "Giá trị khuyến mãi phải lớn hơn 0"
            )

        # Validate loai_km
        if data.loai_km not in VALID_LOAI_KM:
            raise InvalidLoaiKMError(
                f"Loại khuyến mãi không hợp lệ. Các loại hợp lệ: {', '.join(sorted(VALID_LOAI_KM))}"
            )

        # Create promotion entity
        now = datetime.now().isoformat()
        km = KhuyenMai(
            ten_km=data.ten_km,
            mo_ta=data.mo_ta,
            loai_km=data.loai_km,
            gia_tri=data.gia_tri,
            kieu_gia_tri=data.kieu_gia_tri,
            tu_ngay=data.tu_ngay,
            den_ngay=data.den_ngay,
            trang_thai=data.trang_thai,
            so_luong_cho_phep=data.so_luong_cho_phep,
            so_luong_da_su_dung=0,
            created_at=now,
            created_by=data.created_by,
        )

        try:
            self.conn.execute("BEGIN TRANSACTION")

            # Create promotion
            created_km = self._repo.create(km)

            # Create pham_vi records
            if pham_vi_list:
                for pv in pham_vi_list:
                    self._repo.create_pham_vi(
                        created_km.id,
                        pv.loai_ap_dung,
                        pv.gia_tri_ap_dung,
                    )

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        return self.get_with_pham_vi(created_km.id)

    def find_applicable(self, xe_id: int) -> List[Dict[str, Any]]:
        """Find all active promotions applicable to a vehicle.

        T-G4.2.BE.02:
        - BR-KM-04: Filter active KM (trang_thai = 'dang_chay')
        - Check date range (tu_ngay <= today <= den_ngay)
        - Match scope: hang_xe/dong_xe/xe_cu_the/ton_lau (via km_pham_vi)
        - Return list of applicable KM ordered by priority

        Args:
            xe_id: Vehicle ID.

        Returns:
            List of applicable promotion dicts with km info and pham_vi.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Get all active promotions
        cursor = self.conn.execute(
            """SELECT * FROM khuyen_mai
               WHERE trang_thai = 'dang_chay'
               AND tu_ngay <= ?
               AND den_ngay >= ?""",
            (today, today)
        )

        applicable = []
        for row in cursor.fetchall():
            km = dict(row)

            # Check quantity limit
            if km["so_luong_cho_phep"] is not None:
                if km["so_luong_da_su_dung"] >= km["so_luong_cho_phep"]:
                    continue  # Quota exhausted

            # Check scope via km_pham_vi
            if self._repo.check_applicable_to_xe(km["id"], xe_id):
                applicable.append({
                    "id": km["id"],
                    "ten_km": km["ten_km"],
                    "mo_ta": km["mo_ta"] or "",
                    "loai_km": km["loai_km"],
                    "gia_tri": km["gia_tri"],
                    "kieu_gia_tri": km["kieu_gia_tri"],
                    "tu_ngay": km["tu_ngay"],
                    "den_ngay": km["den_ngay"],
                    "so_luong_cho_phep": km["so_luong_cho_phep"],
                    "so_luong_da_su_dung": km["so_luong_da_su_dung"],
                })

        # Sort by priority (currently by id, could be enhanced with a priority field)
        applicable.sort(key=lambda x: x["id"])
        return applicable

    def calculate_discount(
        self,
        km_id: int,
        gia_xe: int,
        tong_pk: int = 0,
    ) -> DiscountResult:
        """Calculate discount amount for a promotion.

        T-G4.2.BE.03:
        BR-CALC-02: 5 types:
        - giam_tien_mat: tien_giam = min(gia_tri, gia_xe)
        - giam_phan_tram: tien_giam = gia_xe * gia_tri / 100
        - tang_phu_kien: no direct discount on price, return list of free PK
        - giam_lai_suat: return lai_suat_fig after discount
        - combo: gia_combo from combo_service.calculate_price()

        Args:
            km_id: Promotion ID.
            gia_xe: Vehicle price.
            tong_pk: Total accessory price (for combo calculation).

        Returns:
            DiscountResult with breakdown.

        Raises:
            KhuyenMaiNotFoundError: If promotion not found.
        """
        km = self._repo.find_by_id(km_id)
        if not km:
            raise KhuyenMaiNotFoundError(f"Không tìm thấy khuyến mãi với ID {km_id}")

        loai_km = km.loai_km
        gia_tri = km.gia_tri
        kieu_gia_tri = km.kieu_gia_tri
        base = gia_xe + tong_pk

        tien_giam = 0
        tang_phu_kien = None
        lai_suat_fig = None
        gia_combo = None

        if loai_km == "giam_tien_mat":
            # BR-CALC-02: tien_mat - trực tiếp trừ vào gia_xe
            tien_giam = min(gia_tri, gia_xe)

        elif loai_km == "giam_phan_tram":
            # BR-CALC-02: phan_tram - tính % của gia_xe (hoặc base nếu có pk)
            if kieu_gia_tri == "phan_tram":
                tien_giam = int(gia_xe * gia_tri / 100)
            else:
                tien_giam = min(gia_tri, gia_xe)

        elif loai_km == "tang_phu_kien":
            # BR-CALC-02: tang_phu_kien - không giảm tong_tien
            # PK tặng có gia_ban=0, return list of free PK from pham_vi
            # For tang_phu_kien, gia_tri contains the list of free phu_kien_ids or similar
            # Assuming gia_tri is a comma-separated list of phu_kien_ids
            if km.gia_tri and str(km.gia_tri).strip():
                try:
                    pk_ids = [int(x.strip()) for x in str(km.gia_tri).split(",")]
                    tang_phu_kien = []
                    for pk_id in pk_ids:
                        cursor = self.conn.execute(
                            "SELECT id, ma_pk, ten_pk, gia_ban FROM phu_kien WHERE id = ?",
                            (pk_id,)
                        )
                        row = cursor.fetchone()
                        if row:
                            tang_phu_kien.append({
                                "phu_kien_id": row[0],
                                "ma_pk": row[1],
                                "ten_pk": row[2],
                                "gia_ban": row[3],
                            })
                except (ValueError, TypeError):
                    tang_phu_kien = []
            else:
                tang_phu_kien = []

        elif loai_km == "giam_lai_suat":
            # BR-CALC-02: giam_lai_suat - return lai_suat_fig after discount
            # gia_tri is the interest rate reduction (e.g., 2 for reducing 2%)
            # Return the figure after discount (e.g., if base rate is 10% and gia_tri=2, return 8%)
            # For now, return the gia_tri as the new rate figure (assuming it's a rate value)
            lai_suat_fig = float(gia_tri)

        elif loai_km == "combo":
            # BR-CALC-02: combo - gia_combo from combo_service.calculate_price()
            # gia_tri is the combo_id in this case
            from app.application.services.combo_service import ComboService
            combo_service = ComboService(self.conn, self._session)
            try:
                combo_result = combo_service.calculate_price(gia_tri)
                gia_combo = combo_result["gia_combo"]
                tien_giam = base - gia_combo
            except Exception:
                # If combo not found, no discount
                tien_giam = 0
                gia_combo = base

        gia_sau_km = max(0, base - tien_giam)

        return DiscountResult(
            loai_km=loai_km,
            gia_tri=gia_tri,
            kieu_gia_tri=kieu_gia_tri,
            tien_giam=tien_giam,
            gia_sau_km=gia_sau_km,
            tang_phu_kien=tang_phu_kien,
            lai_suat_fig=lai_suat_fig,
            gia_combo=gia_combo,
        )

    def pause(self, km_id: int) -> KhuyenMai:
        """Pause a promotion.

        T-G4.2.BE.04:
        - BR-KM-07: Update trang_thai to 'tam_dung'
        - Cannot pause a KM that is already 'ket_thuc'

        Args:
            km_id: Promotion ID.

        Returns:
            Updated KhuyenMai entity.

        Raises:
            KhuyenMaiNotFoundError: If promotion not found.
            KhuyenMaiExpiredError: If promotion is already 'ket_thuc'.
        """
        km = self._repo.find_by_id(km_id)
        if not km:
            raise KhuyenMaiNotFoundError(f"Không tìm thấy khuyến mãi với ID {km_id}")

        if km.trang_thai == "ket_thuc":
            raise KhuyenMaiExpiredError(
                "Không thể tạm dừng khuyến mãi đã kết thúc"
            )

        self._repo.update_status(km_id, "tam_dung")
        return self._repo.find_by_id(km_id)

    def resume(self, km_id: int) -> KhuyenMai:
        """Resume a paused promotion.

        T-G4.2.BE.04:
        - BR-KM-07: Update trang_thai to 'dang_chay'
        - Cannot resume a KM that is not 'tam_dung'

        Args:
            km_id: Promotion ID.

        Returns:
            Updated KhuyenMai entity.

        Raises:
            KhuyenMaiNotFoundError: If promotion not found.
            InvalidStateTransitionError: If promotion is not 'tam_dung'.
        """
        km = self._repo.find_by_id(km_id)
        if not km:
            raise KhuyenMaiNotFoundError(f"Không tìm thấy khuyến mãi với ID {km_id}")

        if km.trang_thai != "tam_dung":
            raise KhuyenMaiExpiredError(
                f"Không thể khôi phục khuyến mãi ở trạng thái '{km.trang_thai}'. Chỉ có thể khôi phục khuyến mãi đang tạm dừng."
            )

        self._repo.update_status(km_id, "dang_chay")
        return self._repo.find_by_id(km_id)

    def daily_expiry_check(self) -> Dict[str, Any]:
        """Daily job to check and expire promotions.

        T-G4.2.BE.05:
        - TRG-06: Find all KM where den_ngay < today and trang_thai = 'dang_chay'
        - Update to trang_thai = 'ket_thuc'
        - This would be called by a scheduler (e.g., APScheduler or cron)

        Returns:
            Dict with count of expired promotions.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Find expired promotions
        expired_list = self._repo.find_expired(today)

        count = 0
        for km in expired_list:
            self._repo.update_status(km.id, "ket_thuc")
            count += 1

        return {
            "expired_count": count,
            "today": today,
        }

    def report_effectiveness(self, km_id: int) -> Dict[str, Any]:
        """Get promotion effectiveness report.

        T-G4.2.BE.06:
        - BR-KM-09: Return stats for a KM:
          - so_hop_dong: COUNT contracts using this KM
          - doanh_thu: SUM(tong_tien) of those contracts
          - tong_giam: SUM(tien_giam_km) of those contracts
        - Query hop_dong table filtered by khuyen_mai_id

        Args:
            km_id: Promotion ID.

        Returns:
            Dict with effectiveness statistics.

        Raises:
            KhuyenMaiNotFoundError: If promotion not found.
        """
        km = self._repo.find_by_id(km_id)
        if not km:
            raise KhuyenMaiNotFoundError(f"Không tìm thấy khuyến mãi với ID {km_id}")

        stats = self._repo.get_contract_stats(km_id)

        return {
            "km_id": km_id,
            "ten_km": km.ten_km,
            "loai_km": km.loai_km,
            "tu_ngay": km.tu_ngay,
            "den_ngay": km.den_ngay,
            "trang_thai": km.trang_thai,
            "so_hop_dong": stats["so_hop_dong"],
            "doanh_thu": stats["doanh_thu"],
            "tong_giam": stats["tong_giam"],
        }

    def update(self, km_id: int, data: KhuyenMaiCreateData, pham_vi_list: List[KhuyenMaiPhamViData] = None) -> KhuyenMaiWithPhamVi:
        """Update a promotion.

        Args:
            km_id: Promotion ID to update.
            data: KhuyenMaiCreateData with fields to update.
            pham_vi_list: List of scope data to replace.

        Returns:
            Updated KhuyenMaiWithPhamVi.

        Raises:
            KhuyenMaiNotFoundError: If promotion not found.
            InvalidDateRangeError: If den_ngay <= tu_ngay.
            InvalidGiaTriError: If gia_tri <= 0.
            InvalidLoaiKMError: If loai_km not in valid types.
        """
        km = self._repo.find_by_id(km_id)
        if not km:
            raise KhuyenMaiNotFoundError(f"Không tìm thấy khuyến mãi với ID {km_id}")

        # Validate date range if provided
        if data.den_ngay and data.tu_ngay and data.den_ngay <= data.tu_ngay:
            raise InvalidDateRangeError("Ngày kết thúc phải lớn hơn ngày bắt đầu")

        if data.gia_tri <= 0:
            raise InvalidGiaTriError("Giá trị khuyến mãi phải lớn hơn 0")

        if data.loai_km not in VALID_LOAI_KM:
            raise InvalidLoaiKMError(
                f"Loại khuyến mãi không hợp lệ. Các loại hợp lệ: {', '.join(sorted(VALID_LOAI_KM))}"
            )

        now = datetime.now().isoformat()

        try:
            self.conn.execute("BEGIN TRANSACTION")

            # Update promotion
            self.conn.execute(
                """UPDATE khuyen_mai
                   SET ten_km = ?, mo_ta = ?, loai_km = ?, gia_tri = ?,
                       kieu_gia_tri = ?, tu_ngay = ?, den_ngay = ?,
                       so_luong_cho_phep = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    data.ten_km,
                    data.mo_ta or "",
                    data.loai_km,
                    data.gia_tri,
                    data.kieu_gia_tri,
                    data.tu_ngay,
                    data.den_ngay,
                    data.so_luong_cho_phep,
                    now,
                    km_id,
                )
            )

            # Update pham_vi if provided
            if pham_vi_list is not None:
                self._repo.delete_pham_vi(km_id)
                for pv in pham_vi_list:
                    self._repo.create_pham_vi(km_id, pv.loai_ap_dung, pv.gia_tri_ap_dung)

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        return self.get_with_pham_vi(km_id)

    def delete(self, km_id: int) -> bool:
        """Delete a promotion.

        Cannot delete a promotion that has associated contracts.

        Args:
            km_id: Promotion ID to delete.

        Returns:
            True if deleted.

        Raises:
            KhuyenMaiNotFoundError: If promotion not found.
        """
        km = self._repo.find_by_id(km_id)
        if not km:
            raise KhuyenMaiNotFoundError(f"Không tìm thấy khuyến mãi với ID {km_id}")

        # Check if has contracts
        contract_count = self._repo.count_contracts(km_id)
        if contract_count > 0:
            raise KhuyenMaiServiceError(
                f"Không thể xóa khuyến mãi đã có {contract_count} hợp đồng sử dụng"
            )

        try:
            self.conn.execute("BEGIN TRANSACTION")

            # Delete pham_vi
            self._repo.delete_pham_vi(km_id)

            # Delete promotion
            cursor = self.conn.execute(
                "DELETE FROM khuyen_mai WHERE id = ?",
                (km_id,)
            )

            self.conn.execute("COMMIT")
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise