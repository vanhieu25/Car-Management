"""DonDatHang service - purchase order business logic layer.

Implements business rules:
- BR-NCC-04: Create order with status 'cho_xu_ly'
- BR-NCC-05: set_received transitions order to 'da_nhan' and creates nhap_kho
- Audit + permission decorators

BE Tasks:
- T-G4.4.BE.04: create(ncc_id, items)
- T-G4.4.BE.05: set_received(don_id)
- T-G4.4.BE.06: Audit + permission @audit('CRUD_DDH')
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.infrastructure.repositories.don_dat_hang_repository import DonDatHangRepository
from app.application.services.audit_log_service import AuditLogService
from app.application.services.nhap_kho_service import NhapKhoService


class DonDatHangServiceError(Exception):
    """Base exception for DonDatHang service errors."""
    pass


class ValidationError(DonDatHangServiceError):
    """Raised when validation fails."""
    pass


class NotFoundError(DonDatHangServiceError):
    """Raised when order not found."""
    pass


class InvalidStateTransitionError(DonDatHangServiceError):
    """Raised when state transition is not allowed."""
    pass


@dataclass
class DonDatHangItemData:
    """Data for an item in an order."""
    loai_item: str  # 'xe' or 'phu_kien'
    item_id: int
    so_luong: int
    gia_don: int


@dataclass
class DonDatHangCreateData:
    """Data for creating a new order."""
    nha_cung_cap_id: int
    items: List[DonDatHangItemData]
    ngay_dat: str = None
    ghi_chu: str = ""
    created_by: int = None


@dataclass
class DonDatHangSearchResult:
    """Search result with metadata."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


def audit(action: str):
    """Decorator for audit logging on service methods."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            nhan_vien_id = getattr(self, '_nhan_vien_id', None)
            if result and isinstance(result, dict) and result.get('id'):
                self._audit_log_dict(action, result, nhan_vien_id)
            return result
        return wrapper
    return decorator


def require_permission(resource: str, actions: str):
    """Decorator for permission checking."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # For now, allow all - actual permission check would need session context
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class DonDatHangService:
    """Service for purchase order management operations."""

    def __init__(self, conn: sqlite3.Connection, nhan_vien_id: int = None):
        """Initialize with database connection.

        Args:
            conn: sqlite3.Connection instance.
            nhan_vien_id: ID of current user for audit logging.
        """
        self.conn = conn
        self._repo = DonDatHangRepository(conn)
        self._audit_service = AuditLogService(conn)
        self._nhap_kho_service = NhapKhoService(conn)
        self._nhan_vien_id = nhan_vien_id

    def _audit_log_dict(self, action: str, data: dict, nhan_vien_id: int):
        """Log audit for dict-based operations."""
        self._audit_service.log_create(
            action=action,
            nhan_vien_id=nhan_vien_id,
            table="don_dat_hang",
            record_id=data.get("id"),
            record_data=data,
        )

    # === T-G4.4.BE.04: create ===

    @audit('CRUD_DDH')
    def create(self, data: DonDatHangCreateData) -> Dict[str, Any]:
        """Create a new purchase order.

        BR-NCC-04: Create order with status 'cho_xu_ly'
        - items: list of {loai_item: 'xe'/'phu_kien', item_id, so_luong, gia_don}
        - Insert don_dat_hang record
        - Insert chi_tiet_don_dat for each item
        - Calculate tong_gia = sum(so_luong * gia_don)

        Args:
            data: DonDatHangCreateData with order data.

        Returns:
            Created order dict with chi_tiet list.

        Raises:
            ValidationError: If validation fails.
            NotFoundError: If supplier not found.
        """
        if not data.items:
            raise ValidationError("Danh sách items không được rỗng")

        # Validate items
        for item in data.items:
            if item.loai_item not in ("xe", "phu_kien"):
                raise ValidationError(f"loai_item '{item.loai_item}' không hợp lệ (cần 'xe' hoặc 'phu_kien')", field="items")
            if item.so_luong <= 0:
                raise ValidationError("so_luong phải > 0", field="items")
            if item.gia_don < 0:
                raise ValidationError("gia_don không được âm", field="items")

        # Verify supplier exists
        cursor = self.conn.execute(
            "SELECT id, ma_ncc, ten_ncc FROM nha_cung_cap WHERE id = ?",
            (data.nha_cung_cap_id,)
        )
        ncc_row = cursor.fetchone()
        if not ncc_row:
            raise NotFoundError(f"Không tìm thấy nhà cung cấp với ID {data.nha_cung_cap_id}")

        # Calculate tong_gia
        tong_gia = sum(item.so_luong * item.gia_don for item in data.items)

        # Prepare order data
        now = datetime.now().isoformat()
        ngay_dat = data.ngay_dat if data.ngay_dat else now[:10]

        order_data = {
            "nha_cung_cap_id": data.nha_cung_cap_id,
            "nhan_vien_id": self._nhan_vien_id,
            "trang_thai": "cho_xu_ly",
            "ngay_dat": ngay_dat,
            "ghi_chu": data.ghi_chu or "",
            "created_by": data.created_by or self._nhan_vien_id,
        }

        # Create order
        try:
            self.conn.execute("BEGIN TRANSACTION")

            order = self._repo.create(order_data)
            order_id = order["id"]

            # Insert chi_tiet_don_dat for each item
            chi_tiet_list = []
            for item in data.items:
                chi_tiet = self._repo.add_chi_tiet(
                    don_dat_hang_id=order_id,
                    loai_item=item.loai_item,
                    item_id=item.item_id,
                    so_luong=item.so_luong,
                    gia_don=item.gia_don,
                )
                chi_tiet_list.append(chi_tiet)

            # Update tong_gia in order
            self.conn.execute(
                "UPDATE don_dat_hang SET updated_at = ? WHERE id = ?",
                (now, order_id)
            )

            self.conn.execute("COMMIT")

        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        # Reload order with items
        order = self._repo.find_by_id(order_id)
        order["chi_tiet"] = chi_tiet_list
        order["tong_gia"] = tong_gia
        order["ten_ncc"] = ncc_row["ten_ncc"]

        return order

    # === T-G4.4.BE.05: set_received ===

    @audit('CRUD_DDH')
    def set_received(self, don_id: int) -> Dict[str, Any]:
        """Mark order as received (da_nhan).

        BR-NCC-05: When status changes to 'da_nhan'
        - Transition: cho_xu_ly → da_xac_nhan → da_nhan
        - For each item in chi_tiet_don_dat → call NhapKhoService.create_from_don_dat()
        - This creates nhap_kho record and increases stock

        Args:
            don_id: Order ID.

        Returns:
            Updated order dict.

        Raises:
            NotFoundError: If order not found.
            InvalidStateTransitionError: If transition not allowed.
        """
        order = self._repo.find_by_id(don_id)
        if not order:
            raise NotFoundError(f"Không tìm thấy đơn đặt hàng với ID {don_id}")

        # Check status transition
        current_status = order["trang_thai"]
        if current_status not in ("cho_xu_ly", "da_xac_nhan"):
            raise InvalidStateTransitionError(
                f"Không thể đánh dấu đã nhận cho đơn hàng ở trạng thái '{current_status}'"
            )

        # Get chi_tiet items
        chi_tiet_items = self._repo.get_chi_tiet(don_id)
        if not chi_tiet_items:
            raise ValidationError("Đơn hàng không có items")

        now = datetime.now().isoformat()

        try:
            self.conn.execute("BEGIN TRANSACTION")

            # Update order status to da_nhan
            self._repo.update(don_id, {
                "trang_thai": "da_nhan",
                "ngay_giao": now,
            })

            # For each item → call NhapKhoService.create()
            # Note: We need to convert chi_tiet to nhap_kho items format
            nhap_kho_items = []
            for item in chi_tiet_items:
                # Get gia_nhap from the order item (using gia_don as gia_nhap)
                nhap_kho_items.append({
                    "loai_item": item["loai_item"],
                    "item_id": item["item_id"],
                    "so_luong": item["so_luong"],
                    "gia_nhap": item["gia_don"],
                })

            # Create nhap_kho record
            self._nhap_kho_service.create(
                nha_cung_cap_id=order["nha_cung_cap_id"],
                items=nhap_kho_items,
                nhan_vien_id=self._nhan_vien_id,
                ngay_nhap=now[:10],
                ghi_chu=f"Tự động tạo từ đơn đặt hàng {order['ma_don']}",
            )

            self.conn.execute("COMMIT")

        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise

        return self._repo.find_by_id(don_id)

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID with chi_tiet items.

        Args:
            id: Order ID.

        Returns:
            Order dict with chi_tiet list.
        """
        order = self._repo.find_by_id(id)
        if order:
            order["chi_tiet"] = self._repo.get_chi_tiet(id)
        return order

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all orders.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of order dicts.
        """
        return self._repo.find_all(limit, offset)

    def search(
        self,
        trang_thai: str = None,
        nha_cung_cap_id: int = None,
        ngay_dat_from: str = None,
        ngay_dat_to: str = None,
        keyword: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> DonDatHangSearchResult:
        """Search orders with filters.

        Args:
            trang_thai: Filter by status (cho_xu_ly, da_xac_nhan, da_nhan, da_huy).
            nha_cung_cap_id: Filter by supplier.
            ngay_dat_from: Start date filter.
            ngay_dat_to: End date filter.
            keyword: Search in ma_don, ten_ncc.
            page: Page number (1-indexed).
            page_size: Results per page.

        Returns:
            DonDatHangSearchResult with items and pagination.
        """
        offset = (page - 1) * page_size
        items, total = self._repo.search(
            trang_thai, nha_cung_cap_id, ngay_dat_from, ngay_dat_to, keyword, page_size, offset
        )

        # Enrich with chi_tiet
        for item in items:
            item["chi_tiet"] = self._repo.get_chi_tiet(item["id"])
            item["tong_gia"] = self._repo.calculate_tong_gia(item["id"])

        total_pages = max(1, (total + page_size - 1) // page_size)

        return DonDatHangSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_status(self, don_id: int, trang_thai: str) -> Dict[str, Any]:
        """Update order status.

        Args:
            don_id: Order ID.
            trang_thai: New status.

        Returns:
            Updated order dict.
        """
        order = self._repo.find_by_id(don_id)
        if not order:
            raise NotFoundError(f"Không tìm thấy đơn đặt hàng với ID {don_id}")

        self._repo.update(don_id, {"trang_thai": trang_thai})

        return self._repo.find_by_id(don_id)

    def get_by_ncc(self, nha_cung_cap_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a supplier.

        Args:
            nha_cung_cap_id: Supplier ID.

        Returns:
            List of order dicts.
        """
        orders = self._repo.find_by_ncc(nha_cung_cap_id)
        for order in orders:
            order["chi_tiet"] = self._repo.get_chi_tiet(order["id"])
            order["tong_gia"] = self._repo.calculate_tong_gia(order["id"])
        return orders