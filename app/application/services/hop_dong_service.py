"""HopDong service - contract business logic layer.

Implements business rules:
- BR-HD-01 to BR-HD-12: Contract lifecycle management
- BR-CALC-01: Total = gia_xe + tong_gia_phu_kien - tien_giam_km
- BR-CALC-02: 4 types of discount calculation
- BR-CALC-03: Customer classification auto-update
- TRG-01: Stock decrease on payment
- TRG-02: Warranty creation on delivery
- TRG-03: Stock return on cancellation
"""

from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import HopDong, KhachHang
from app.infrastructure.repositories.hop_dong_repository import HopDongRepository, HopDongSearchFilter
from app.application.services.audit_log_service import AuditLogService, AuditAction
from app.application.services.system_settings_service import SystemSettingsService


class HopDongServiceError(Exception):
    """Base exception for HopDong service errors."""
    pass


class HopDongNotFoundError(HopDongServiceError):
    """Raised when contract is not found."""
    pass


class InvalidStateTransitionError(HopDongServiceError):
    """Raised when state transition is not allowed."""
    pass


class ValidationError(HopDongServiceError):
    """Raised when contract validation fails."""
    pass


class InsufficientStockError(HopDongServiceError):
    """Raised when stock is insufficient."""
    pass


class NotAuthorizedError(HopDongServiceError):
    """Raised when user lacks permission."""
    pass


@dataclass
class HopDongCreateData:
    """Data for creating a new contract."""
    khach_hang_id: int
    xe_id: int
    nhan_vien_id: int
    khuyen_mai_id: Optional[int] = None
    ghi_chu: str = ""
    created_by: Optional[int] = None


@dataclass
class HopDongUpdateData:
    """Data for updating a contract."""
    khuyen_mai_id: Optional[int] = None
    ghi_chu: Optional[str] = None


@dataclass
class HopDongSearchResult:
    """Search result with metadata."""
    items: List[HopDong]
    total: int
    page: int
    page_size: int
    total_pages: int


@dataclass
class TotalBreakdown:
    """Total calculation breakdown."""
    gia_xe: int
    tong_pk: int
    tien_giam_km: int
    tong_tien: int
    km_ap_dung: Optional[Dict[str, Any]] = None


class HopDongService:
    """Service for contract management operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = HopDongRepository(conn)
        self._audit_service = AuditLogService(conn)
        self._settings_service = SystemSettingsService(conn)

    def get_by_id(self, hop_dong_id: int) -> Optional[HopDong]:
        """Get contract by ID.

        Args:
            hop_dong_id: Contract ID.

        Returns:
            HopDong if found, None otherwise.
        """
        return self._repo.find_by_id(hop_dong_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> List[HopDong]:
        """Get all contracts with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of HopDong entities.
        """
        return self._repo.find_all(HopDongSearchFilter(), limit, offset)

    def get_full_contract(self, hop_dong_id: int) -> Optional[Dict[str, Any]]:
        """Get contract with all relations.

        Args:
            hop_dong_id: Contract ID.

        Returns:
            Dict with hop_dong, khach_hang, xe, phu_kien_list, khuyen_mai or None.
        """
        return self._repo.get_full_contract(hop_dong_id)

    def calculate_total(
        self,
        xe_id: int,
        pk_list: List[Dict[str, Any]],
        km_id: Optional[int] = None,
    ) -> TotalBreakdown:
        """Calculate contract total with discount applied.

        BR-CALC-01: tong_tien = gia_xe + tong_gia_phu_kien - tien_giam_km
        BR-CALC-02: 4 types of discount:
        - tien_mat: trực tiếp trừ vào tong_tien
        - phan_tram: tính % của (gia_xe + tong_pk), trừ ra
        - tang_phu_kien: không giảm tong_tien, PK tặng có gia_ban=0
        - combo: giảm theo combo he_so_giam

        Args:
            xe_id: Vehicle ID.
            pk_list: List of {phu_kien_id, so_luong}.
            km_id: Promotion ID (optional).

        Returns:
            TotalBreakdown with all price components.
        """
        # Get vehicle price
        cursor = self.conn.execute("SELECT gia_ban FROM xe WHERE id = ?", (xe_id,))
        row = cursor.fetchone()
        if not row:
            raise HopDongNotFoundError(f"Không tìm thấy xe với ID {xe_id}")
        gia_xe = row[0]

        # Calculate tong_pk from pk_list
        tong_pk = 0
        pk_snapshot = {}
        for pk_item in pk_list:
            pk_id = pk_item["phu_kien_id"]
            so_luong = pk_item.get("so_luong", 1)
            cursor = self.conn.execute("SELECT gia_ban FROM phu_kien WHERE id = ?", (pk_id,))
            row = cursor.fetchone()
            if row:
                gia_ban = row[0]
                tong_pk += gia_ban * so_luong
                pk_snapshot[pk_id] = {"gia_ban": gia_ban, "so_luong": so_luong}

        tien_giam_km = 0
        km_ap_dung = None

        if km_id:
            cursor = self.conn.execute(
                "SELECT * FROM khuyen_mai WHERE id = ? AND trang_thai = 'dang_chay'",
                (km_id,)
            )
            km_row = cursor.fetchone()
            if km_row:
                km = dict(km_row)
                km_ap_dung = {
                    "id": km["id"],
                    "ten_km": km["ten_km"],
                    "loai_km": km["loai_km"],
                    "gia_tri": km["gia_tri"],
                    "kieu_gia_tri": km["kieu_gia_tri"],
                }
                loai_km = km["loai_km"]
                gia_tri = km["gia_tri"]
                kieu_gia_tri = km["kieu_gia_tri"]

                if loai_km == "giam_tien_mat":
                    # BR-CALC-02: tien_mat - trực tiếp trừ vào tong_tien
                    tien_giam_km = gia_tri

                elif loai_km == "giam_phan_tram":
                    # BR-CALC-02: phan_tram - tính % của (gia_xe + tong_pk), trừ ra
                    base = gia_xe + tong_pk
                    if kieu_gia_tri == "phan_tram":
                        tien_giam_km = int(base * gia_tri / 100)
                    else:
                        tien_giam_km = gia_tri

                elif loai_km == "tang_phu_kien":
                    # BR-CALC-02: tang_phu_kien - không giảm tong_tien
                    # PK tặng có gia_ban=0
                    pass

                elif loai_km == "combo":
                    # BR-CALC-02: combo - giảm theo combo he_so_giam
                    # gia_tri is the he_so_giam factor
                    base = gia_xe + tong_pk
                    tien_giam_km = int(base * (1 - gia_tri))

        tong_tien = max(0, gia_xe + tong_pk - tien_giam_km)

        return TotalBreakdown(
            gia_xe=gia_xe,
            tong_pk=tong_pk,
            tien_giam_km=tien_giam_km,
            tong_tien=tong_tien,
            km_ap_dung=km_ap_dung,
        )

    def create(
        self,
        data: HopDongCreateData,
        phu_kien_list: List[Dict[str, Any]] = None,
        nhan_vien_id: int = None,
    ) -> HopDong:
        """Create a new contract.

        Validates all 4 steps completed (xe chọn, pk chọn, km chọn, thanh toán).
        Snapshots prices at creation time.
        Inserts hop_dong and hop_dong_phu_kien records within transaction.

        Args:
            data: HopDongCreateData with contract data.
            phu_kien_list: List of {phu_kien_id, so_luong} for accessories.
            nhan_vien_id: Employee ID creating the contract.

        Returns:
            Created HopDong entity.
        """
        # Validate vehicle exists and has stock
        cursor = self.conn.execute("SELECT * FROM xe WHERE id = ?", (data.xe_id,))
        xe_row = cursor.fetchone()
        if not xe_row:
            raise HopDongNotFoundError(f"Không tìm thấy xe với ID {data.xe_id}")

        # Validate customer exists
        cursor = self.conn.execute(
            "SELECT * FROM khach_hang WHERE id = ?", (data.khach_hang_id,)
        )
        if not cursor.fetchone():
            raise HopDongNotFoundError(
                f"Không tìm thấy khách hàng với ID {data.khach_hang_id}"
            )

        # Calculate total with discount
        pk_list = phu_kien_list or []
        total = self.calculate_total(data.xe_id, pk_list, data.khuyen_mai_id)

        # Create contract entity
        now = datetime.now().isoformat()
        hop_dong = HopDong(
            ma_hop_dong="",  # Will be auto-generated
            khach_hang_id=data.khach_hang_id,
            xe_id=data.xe_id,
            nhan_vien_id=data.nhan_vien_id,
            khuyen_mai_id=data.khuyen_mai_id,
            gia_xe=total.gia_xe,
            tong_gia_phu_kien=total.tong_pk,
            tien_giam_km=total.tien_giam_km,
            tong_tien=total.tong_tien,
            trang_thai="moi_tao",
            ngay_tao=now,
            ghi_chu=data.ghi_chu or "",
            created_by=data.created_by or nhan_vien_id,
        )

        # Insert within transaction
        try:
            self.conn.execute("BEGIN TRANSACTION")

            # Create contract
            created_hd = self._repo.create(hop_dong)

            # Insert accessories with snapshot prices
            for pk_item in pk_list:
                pk_id = pk_item["phu_kien_id"]
                so_luong = pk_item.get("so_luong", 1)
                cursor = self.conn.execute(
                    "SELECT gia_ban FROM phu_kien WHERE id = ?", (pk_id,)
                )
                row = cursor.fetchone()
                gia_ban = row[0] if row else 0
                self._repo.add_phu_kien(created_hd.id, pk_id, so_luong, gia_ban)

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Audit log
        self._audit_service.log_create(
            action="CREATE_HD",
            nhan_vien_id=nhan_vien_id,
            table="hop_dong",
            record_id=created_hd.id,
            record_data=created_hd.to_dict(),
        )

        return created_hd

    def update(
        self,
        hop_dong_id: int,
        data: HopDongUpdateData,
        nhan_vien_id: int = None,
        nhan_vien_vai_tro: str = None,
    ) -> HopDong:
        """Update a contract.

        BR-HD-09: Only allowed for moi_tao status.
        For da_thanh_toan, only A-01 can update.
        Cannot update if da_giao_xe.

        Args:
            hop_dong_id: Contract ID.
            data: HopDongUpdateData with fields to update.
            nhan_vien_id: Employee ID performing update.
            nhan_vien_vai_tro: Employee role code for permission check.

        Returns:
            Updated HopDong entity.

        Raises:
            HopDongNotFoundError: If contract not found.
            InvalidStateTransitionError: If status doesn't allow update.
            NotAuthorizedError: If user lacks permission.
        """
        hop_dong = self._repo.find_by_id(hop_dong_id)
        if not hop_dong:
            raise HopDongNotFoundError(
                f"Không tìm thấy hợp đồng với ID {hop_dong_id}"
            )

        # BR-HD-09: Cannot update if da_giao_xe
        if hop_dong.trang_thai == "da_giao_xe":
            raise InvalidStateTransitionError(
                "Không thể cập nhật hợp đồng đã giao xe"
            )

        # BR-HD-09: For da_thanh_toan, only A-01 can update
        if hop_dong.trang_thai == "da_thanh_toan":
            if nhan_vien_vai_tro != "A-01":
                raise NotAuthorizedError(
                    "Chỉ admin (A-01) mới được cập nhật hợp đồng đã thanh toán"
                )

        # BR-HD-09: Only moi_tao status allows direct update
        if hop_dong.trang_thai != "moi_tao":
            raise InvalidStateTransitionError(
                f"Không thể cập nhật hợp đồng ở trạng thái '{hop_dong.trang_thai}'"
            )

        # Build update data
        update_fields = {}
        if data.khuyen_mai_id is not None:
            update_fields["khuyen_mai_id"] = data.khuyen_mai_id
        if data.ghi_chu is not None:
            update_fields["ghi_chu"] = data.ghi_chu

        if not update_fields:
            return hop_dong

        update_fields["updated_at"] = datetime.now().isoformat()

        # Update
        set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values())
        values.append(hop_dong_id)

        self.conn.execute(
            f"UPDATE hop_dong SET {set_clause} WHERE id = ?",
            values
        )
        self.conn.commit()

        # Audit log
        self._audit_service.log_update(
            action="UPDATE_HD",
            nhan_vien_id=nhan_vien_id,
            table="hop_dong",
            record_id=hop_dong_id,
            before=hop_dong.to_dict(),
            after=self._repo.find_by_id(hop_dong_id).to_dict(),
        )

        return self._repo.find_by_id(hop_dong_id)

    def set_paid(
        self,
        hop_dong_id: int,
        nhan_vien_id: int = None,
    ) -> HopDong:
        """Mark contract as paid (da_thanh_toan).

        BR-HD-03: moi_tao → da_thanh_toan
        BR-HD-11: Verify xe.so_luong_ton >= 1 before proceeding
        BR-HD-12: Verify each pk ton_kho >= so_luong before proceeding
        TRG-01: Decrease xe.so_luong_ton by 1
        TRG-01: Decrease each pk's ton_kho by its quantity

        Args:
            hop_dong_id: Contract ID.
            nhan_vien_id: Employee ID processing payment.

        Returns:
            Updated HopDong entity.

        Raises:
            HopDongNotFoundError: If contract not found.
            InvalidStateTransitionError: If contract is not in moi_tao status.
            InsufficientStockError: If stock is insufficient.
        """
        hop_dong = self._repo.find_by_id(hop_dong_id)
        if not hop_dong:
            raise HopDongNotFoundError(
                f"Không tìm thấy hợp đồng với ID {hop_dong_id}"
            )

        if hop_dong.trang_thai != "moi_tao":
            raise InvalidStateTransitionError(
                f"Không thể thanh toán hợp đồng ở trạng thái '{hop_dong.trang_thai}'"
            )

        # BR-HD-11: Verify vehicle stock
        cursor = self.conn.execute(
            "SELECT so_luong_ton FROM xe WHERE id = ?", (hop_dong.xe_id,)
        )
        row = cursor.fetchone()
        if not row or row[0] < 1:
            raise InsufficientStockError(
                f"Xe không có đủ hàng tồn (ID: {hop_dong.xe_id})"
            )

        # BR-HD-12: Verify accessory stock and get quantities
        cursor = self.conn.execute(
            """SELECT phu_kien_id, so_luong FROM hop_dong_phu_kien
               WHERE hop_dong_id = ?""",
            (hop_dong_id,)
        )
        pk_items = cursor.fetchall()

        for pk_id, so_luong in pk_items:
            cursor = self.conn.execute(
                "SELECT ton_kho FROM phu_kien WHERE id = ?", (pk_id,)
            )
            row = cursor.fetchone()
            if not row or row[0] < so_luong:
                raise InsufficientStockError(
                    f"Phụ kiện (ID: {pk_id}) không có đủ hàng tồn"
                )

        try:
            self.conn.execute("BEGIN TRANSACTION")

            now = datetime.now().isoformat()

            # BR-HD-03: Update status
            self.conn.execute(
                """UPDATE hop_dong
                   SET trang_thai = 'da_thanh_toan',
                       ngay_thanh_toan = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (now, now, hop_dong_id)
            )

            # TRG-01: Decrease vehicle stock
            self.conn.execute(
                """UPDATE xe SET so_luong_ton = so_luong_ton - 1, updated_at = ?
                   WHERE id = ?""",
                (now, hop_dong.xe_id)
            )

            # TRG-01: Decrease accessory stock
            for pk_id, so_luong in pk_items:
                self.conn.execute(
                    """UPDATE phu_kien SET ton_kho = ton_kho - ?, updated_at = ?
                       WHERE id = ?""",
                    (so_luong, now, pk_id)
                )

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Audit log
        updated = self._repo.find_by_id(hop_dong_id)
        self._audit_service.log_update(
            action="UPDATE_HD_PAID",
            nhan_vien_id=nhan_vien_id,
            table="hop_dong",
            record_id=hop_dong_id,
            before=hop_dong.to_dict(),
            after=updated.to_dict(),
        )

        return updated

    def set_delivered(
        self,
        hop_dong_id: int,
        nhan_vien_id: int = None,
    ) -> HopDong:
        """Mark contract as delivered (da_giao_xe).

        BR-HD-04: da_thanh_toan → da_giao_xe
        TRG-02: Auto-create bao_hanh record with:
        - hop_dong_id, xe_id, khach_hang_id from contract
        - thoi_han_bh from system_settings
        - ngay_bat_dau = ngay_giao_xe
        - ngay_ket_thuc = ngay_giao_xe + thoi_han_bh months
        BR-CALC-03: Update KH tong_gia_tri_mua += tong_tien, so_xe_da_mua += 1
        Update NV KPI (so_hop_dong += 1, doanh_thu += tong_tien)

        Args:
            hop_dong_id: Contract ID.
            nhan_vien_id: Employee ID processing delivery.

        Returns:
            Updated HopDong entity.

        Raises:
            HopDongNotFoundError: If contract not found.
            InvalidStateTransitionError: If contract is not in da_thanh_toan status.
        """
        hop_dong = self._repo.find_by_id(hop_dong_id)
        if not hop_dong:
            raise HopDongNotFoundError(
                f"Không tìm thấy hợp đồng với ID {hop_dong_id}"
            )

        if hop_dong.trang_thai != "da_thanh_toan":
            raise InvalidStateTransitionError(
                f"Không thể giao xe hợp đồng ở trạng thái '{hop_dong.trang_thai}'"
            )

        # Get warranty period from system settings
        thoi_han_bh = self._settings_service.get_warranty_months()
        now = datetime.now()
        ngay_giao_xe = now.isoformat()
        ngay_ket_thuc = (now + relativedelta(months=thoi_han_bh)).isoformat()

        try:
            self.conn.execute("BEGIN TRANSACTION")

            # BR-HD-04: Update status
            self.conn.execute(
                """UPDATE hop_dong
                   SET trang_thai = 'da_giao_xe',
                       ngay_giao_xe = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (ngay_giao_xe, ngay_giao_xe, hop_dong_id)
            )

            # TRG-02: Create warranty record
            self.conn.execute(
                """INSERT INTO bao_hanh
                   (hop_dong_id, xe_id, khach_hang_id, thoi_han_bh,
                    ngay_bat_dau, ngay_ket_thuc, trang_thai, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'con_hieu_luc', ?)""",
                (
                    hop_dong_id,
                    hop_dong.xe_id,
                    hop_dong.khach_hang_id,
                    thoi_han_bh,
                    ngay_giao_xe,
                    ngay_ket_thuc,
                    ngay_giao_xe,
                )
            )

            # BR-CALC-03: Update customer purchase stats
            cursor = self.conn.execute(
                "SELECT tong_gia_tri_mua, so_xe_da_mua FROM khach_hang WHERE id = ?",
                (hop_dong.khach_hang_id,)
            )
            row = cursor.fetchone()
            if row:
                new_tong_gia_tri = row[0] + hop_dong.tong_tien
                new_so_xe = row[1] + 1

                # Update customer
                self.conn.execute(
                    """UPDATE khach_hang
                       SET tong_gia_tri_mua = ?,
                           so_xe_da_mua = ?,
                           phan_loai = ?,
                           updated_at = ?
                       WHERE id = ?""",
                    (
                        new_tong_gia_tri,
                        new_so_xe,
                        self._calculate_phan_loai(new_tong_gia_tri),
                        ngay_giao_xe,
                        hop_dong.khach_hang_id,
                    )
                )

            # Update NV KPI
            self.conn.execute(
                """UPDATE nhan_vien
                   SET so_hop_dong = COALESCE(so_hop_dong, 0) + 1,
                       doanh_thu = COALESCE(doanh_thu, 0) + ?,
                       updated_at = ?
                   WHERE id = ?""",
                (hop_dong.tong_tien, ngay_giao_xe, hop_dong.nhan_vien_id)
            )

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Audit log
        updated = self._repo.find_by_id(hop_dong_id)
        self._audit_service.log_update(
            action="UPDATE_HD_DELIVERED",
            nhan_vien_id=nhan_vien_id,
            table="hop_dong",
            record_id=hop_dong_id,
            before=hop_dong.to_dict(),
            after=updated.to_dict(),
        )

        return updated

    def cancel(
        self,
        hop_dong_id: int,
        ly_do: str,
        nhan_vien_id: int = None,
        nhan_vien_vai_tro: str = None,
    ) -> HopDong:
        """Cancel a contract.

        BR-HD-05: Only A-01 can cancel
        BR-HD-06: Cannot cancel if da_giao_xe
        TRG-03: Return stock — increase xe.so_luong_ton, increase pk ton_kho
        Delete related bao_hanh records
        Delete related tra_gop records
        Set trang_thai = 'huy', ly_do_huy = reason
        Audit log

        Args:
            hop_dong_id: Contract ID.
            ly_do: Cancellation reason.
            nhan_vien_id: Employee ID performing cancellation.
            nhan_vien_vai_tro: Employee role code for permission check.

        Returns:
            Updated HopDong entity.

        Raises:
            HopDongNotFoundError: If contract not found.
            InvalidStateTransitionError: If contract cannot be cancelled.
            NotAuthorizedError: If user lacks permission.
        """
        hop_dong = self._repo.find_by_id(hop_dong_id)
        if not hop_dong:
            raise HopDongNotFoundError(
                f"Không tìm thấy hợp đồng với ID {hop_dong_id}"
            )

        # BR-HD-05: Only A-01 can cancel
        if nhan_vien_vai_tro != "A-01":
            raise NotAuthorizedError(
                "Chỉ admin (A-01) mới được hủy hợp đồng"
            )

        # BR-HD-06: Cannot cancel if da_giao_xe
        if hop_dong.trang_thai == "da_giao_xe":
            raise InvalidStateTransitionError(
                "Không thể hủy hợp đồng đã giao xe"
            )

        try:
            self.conn.execute("BEGIN TRANSACTION")

            now = datetime.now().isoformat()

            # TRG-03: Return stock for vehicle (only if already paid)
            if hop_dong.trang_thai == "da_thanh_toan":
                self.conn.execute(
                    """UPDATE xe SET so_luong_ton = so_luong_ton + 1, updated_at = ?
                       WHERE id = ?""",
                    (now, hop_dong.xe_id)
                )

                # Return stock for accessories
                cursor = self.conn.execute(
                    """SELECT phu_kien_id, so_luong FROM hop_dong_phu_kien
                       WHERE hop_dong_id = ?""",
                    (hop_dong_id,)
                )
                for pk_id, so_luong in cursor.fetchall():
                    self.conn.execute(
                        """UPDATE phu_kien SET ton_kho = ton_kho + ?, updated_at = ?
                           WHERE id = ?""",
                        (so_luong, now, pk_id)
                    )

            # Delete related bao_hanh records
            self.conn.execute(
                "DELETE FROM bao_hanh WHERE hop_dong_id = ?",
                (hop_dong_id,)
            )

            # Delete related tra_gop records
            self.conn.execute(
                "DELETE FROM tra_gop WHERE hop_dong_id = ?",
                (hop_dong_id,)
            )

            # Update status to cancelled
            self.conn.execute(
                """UPDATE hop_dong
                   SET trang_thai = 'huy',
                       ly_do_huy = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (ly_do, now, hop_dong_id)
            )

            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Audit log
        updated = self._repo.find_by_id(hop_dong_id)
        self._audit_service.log_contract_cancel(
            nhan_vien_id=nhan_vien_id,
            hop_dong_id=hop_dong_id,
            ly_do=ly_do,
        )

        return updated

    def search(
        self,
        trang_thai: str = None,
        ngay_tao_from: str = None,
        ngay_tao_to: str = None,
        khach_hang_id: int = None,
        nhan_vien_id: int = None,
        keyword: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> HopDongSearchResult:
        """Search contracts with filters and pagination.

        Args:
            trang_thai: Filter by status.
            ngay_tao_from: Start date for creation date filter.
            ngay_tao_to: End date for creation date filter.
            khach_hang_id: Filter by customer ID.
            nhan_vien_id: Filter by employee ID.
            keyword: Search in ma_hop_dong and KH name.
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            HopDongSearchResult with items and pagination info.
        """
        filter = HopDongSearchFilter(
            trang_thai=trang_thai,
            ngay_tao_from=ngay_tao_from,
            ngay_tao_to=ngay_tao_to,
            khach_hang_id=khach_hang_id,
            nhan_vien_id=nhan_vien_id,
            keyword=keyword,
        )

        items, total = self._repo.search(filter, page, page_size)
        total_pages = max(1, (total + page_size - 1) // page_size)

        return HopDongSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def export_pdf(
        self,
        hop_dong_id: int,
        output_path: str,
    ) -> str:
        """Export contract as PDF.

        Args:
            hop_dong_id: Contract ID.
            output_path: Path to save PDF file.

        Returns:
            Path to the saved PDF file.
        """
        from app.infrastructure.pdf_renderer import PdfRenderer
        import os

        # Get template directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )))
        template_dir = os.path.join(base_dir, "resources", "templates")
        css_path = os.path.join(template_dir, "contract.css")

        renderer = PdfRenderer(template_dir, css_path)
        return renderer.render_contract(hop_dong_id, output_path, self.conn)

    def _calculate_phan_loai(self, tong_gia_tri_mua: int) -> str:
        """Calculate customer classification based on total purchase value.

        BR-CALC-03:
        - Thường: < 500 triệu
        - Thân thiết: >= 500 triệu and < 1.5 tỷ
        - VIP: >= 1.5 tỷ

        Args:
            tong_gia_tri_mua: Total purchase value in VND.

        Returns:
            Classification string: "Thuong", "Than_thiet", or "VIP".
        """
        if tong_gia_tri_mua >= 1_500_000_000:
            return "VIP"
        elif tong_gia_tri_mua >= 500_000_000:
            return "Than_thiet"
        else:
            return "Thuong"
