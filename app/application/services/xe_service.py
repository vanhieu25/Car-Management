"""Xe service - vehicle business logic layer.

Implements business rules:
- BR-XE-01: ma_xe is immutable after creation
- BR-XE-02: Cannot delete vehicle with active contracts
- BR-XE-04: Auto-set da_ban when stock=0 and has da_giao_xe contract
- BR-XE-05: Auto-set con_hang when stock increases for da_ban vehicle
- BR-XE-06, BR-XE-07: Advanced search with keyword support
- BR-XE-08: Low stock warning
- BR-XE-09: nam_san_xuat validation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.domain.entities import Xe
from app.infrastructure.repositories.xe_repository import XeRepository, XeSearchFilter
from app.application.validators.xe_validator import XeValidator
from app.application.services.audit_decorator import audit


class XeServiceError(Exception):
    """Base exception for Xe service errors."""
    pass


class ValidationError(XeServiceError):
    """Validation error with field-specific messages."""
    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        super().__init__(message)
        self.field = field
        self.errors = errors or []


class DuplicateMaXeError(XeServiceError):
    """Raised when ma_xe already exists."""
    pass


class DeleteNotAllowedError(XeServiceError):
    """Raised when deletion is not allowed due to constraints."""
    pass


class XeNotFoundError(XeServiceError):
    """Raised when vehicle is not found."""
    pass


@dataclass
class XeCreateData:
    """Data for creating a new vehicle."""
    ma_xe: str
    hang: str
    dong_xe: str
    nam_san_xuat: int
    gia_ban: int
    mau_sac: str = ""
    so_luong_ton: int = 0
    muc_toi_thieu: int = 2
    mo_ta: str = ""
    created_by: int = None


@dataclass
class XeUpdateData:
    """Data for updating a vehicle."""
    hang: str = None
    dong_xe: str = None
    nam_san_xuat: int = None
    gia_ban: int = None
    mau_sac: str = None
    so_luong_ton: int = None
    muc_toi_thieu: int = None
    trang_thai: str = None
    mo_ta: str = None


@dataclass
class XeSearchResult:
    """Search result with metadata."""
    items: List[Xe]
    total: int
    page: int
    page_size: int
    total_pages: int


class XeService:
    """Service for vehicle management operations."""
    
    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.
        
        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
        self._repo = XeRepository(conn)
    
    def get_by_id(self, xe_id: int) -> Optional[Xe]:
        """Get vehicle by ID.
        
        Args:
            xe_id: Vehicle ID.
            
        Returns:
            Xe if found, None otherwise.
        """
        return self._repo.find_by_id(xe_id)
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Xe]:
        """Get all vehicles with pagination.
        
        Args:
            limit: Maximum results.
            offset: Offset for pagination.
            
        Returns:
            List of Xe entities.
        """
        return self._repo.find_all(limit, offset)
    
    def get_by_ma_xe(self, ma_xe: str) -> Optional[Xe]:
        """Get vehicle by ma_xe.
        
        Args:
            ma_xe: Vehicle code.
            
        Returns:
            Xe if found, None otherwise.
        """
        return self._repo.find_by_ma_xe(ma_xe)
    
    @audit(action="CREATE_XE")
    def create(self, data: XeCreateData, nhan_vien_id: int = None) -> Xe:
        """Create a new vehicle.
        
        Validates:
        - BR-XE-01: ma_xe must be unique and immutable
        - BR-XE-09: nam_san_xuat ∈ [1990, current_year + 1]
        - BR-DATA-01: gia_ban ≥ 0
        - BR-DATA-02: so_luong_ton ≥ 0
        
        Args:
            data: XeCreateData with vehicle data.
            nhan_vien_id: ID of creating user (for audit).
            
        Returns:
            Created Xe entity.
            
        Raises:
            ValidationError: If validation fails.
            DuplicateMaXeError: If ma_xe already exists.
        """
        # Build validation dict
        validation_dict = {
            "ma_xe": data.ma_xe,
            "hang": data.hang,
            "dong_xe": data.dong_xe,
            "nam_san_xuat": data.nam_san_xuat,
            "gia_ban": data.gia_ban,
            "so_luong_ton": data.so_luong_ton,
        }
        
        # Validate
        result = XeValidator.validate_create(validation_dict)
        if not result.is_valid:
            raise ValidationError(
                "; ".join(result.errors),
                errors=result.errors
            )
        
        # Check ma_xe uniqueness (BR-XE-01)
        if self._repo.exists_by_ma_xe(data.ma_xe):
            raise DuplicateMaXeError(f"Mã xe '{data.ma_xe}' đã tồn tại")
        
        # Create entity
        now = datetime.now().isoformat()
        xe = Xe(
            ma_xe=data.ma_xe,
            hang=data.hang,
            dong_xe=data.dong_xe,
            nam_san_xuat=data.nam_san_xuat,
            mau_sac=data.mau_sac,
            gia_ban=data.gia_ban,
            so_luong_ton=data.so_luong_ton,
            muc_toi_thieu=data.muc_toi_thieu,
            trang_thai="con_hang",
            ngay_nhap_dau_tien=now if data.so_luong_ton > 0 else None,
            mo_ta=data.mo_ta,
            created_by=data.created_by,
        )
        
        created = self._repo.create(xe)
        
        # Update ngay_nhap_dau_tien if stock was provided
        if data.so_luong_ton > 0:
            self.conn.execute(
                "UPDATE xe SET ngay_nhap_dau_tien = ? WHERE id = ?",
                (now, created.id)
            )
            self.conn.commit()
        
        return created
    
    @audit(action="UPDATE_XE")
    def update(self, xe_id: int, data: XeUpdateData, nhan_vien_id: int = None) -> Xe:
        """Update a vehicle.
        
        BR-XE-01: ma_xe cannot be changed after creation.
        
        Args:
            xe_id: Vehicle ID to update.
            data: XeUpdateData with fields to update.
            nhan_vien_id: ID of updating user (for audit).
            
        Returns:
            Updated Xe entity.
            
        Raises:
            XeNotFoundError: If vehicle not found.
            ValidationError: If validation fails.
        """
        # Get current vehicle
        xe = self._repo.find_by_id(xe_id)
        if not xe:
            raise XeNotFoundError(f"Không tìm thấy xe với ID {xe_id}")
        
        # Build validation dict with original ma_xe
        validation_dict = data.__dict__.copy()
        # Remove None values
        validation_dict = {k: v for k, v in validation_dict.items() if v is not None}
        
        # Validate
        result = XeValidator.validate_update(validation_dict, xe.ma_xe)
        if not result.is_valid:
            raise ValidationError(
                "; ".join(result.errors),
                errors=result.errors
            )
        
        # Update fields
        update_data = {}
        if data.hang is not None:
            update_data["hang"] = data.hang
        if data.dong_xe is not None:
            update_data["dong_xe"] = data.dong_xe
        if data.nam_san_xuat is not None:
            update_data["nam_san_xuat"] = data.nam_san_xuat
        if data.gia_ban is not None:
            update_data["gia_ban"] = data.gia_ban
        if data.mau_sac is not None:
            update_data["mau_sac"] = data.mau_sac
        if data.so_luong_ton is not None:
            update_data["so_luong_ton"] = data.so_luong_ton
        if data.muc_toi_thieu is not None:
            update_data["muc_toi_thieu"] = data.muc_toi_thieu
        if data.trang_thai is not None:
            update_data["trang_thai"] = data.trang_thai
        if data.mo_ta is not None:
            update_data["mo_ta"] = data.mo_ta
        
        if update_data:
            update_data["updated_at"] = datetime.now().isoformat()
            
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(xe_id)
            
            self.conn.execute(
                f"UPDATE xe SET {set_clause} WHERE id = ?",
                values
            )
            self.conn.commit()
        
        # Refresh and return
        return self._repo.find_by_id(xe_id)
    
    @audit(action="DELETE_XE")
    def delete(self, xe_id: int, nhan_vien_id: int = None) -> bool:
        """Delete a vehicle.
        
        BR-XE-02 + BR-REF-01: Cannot delete if vehicle has active contracts.
        
        Args:
            xe_id: Vehicle ID to delete.
            nhan_vien_id: ID of deleting user (for audit).
            
        Returns:
            True if deleted.
            
        Raises:
            XeNotFoundError: If vehicle not found.
            DeleteNotAllowedError: If deletion is not allowed.
        """
        # Check vehicle exists
        xe = self._repo.find_by_id(xe_id)
        if not xe:
            raise XeNotFoundError(f"Không tìm thấy xe với ID {xe_id}")
        
        # BR-XE-02: Check for active contracts
        if self._repo.has_active_contracts(xe_id):
            raise DeleteNotAllowedError(
                "Không thể xóa xe đang có hợp đồng chưa hủy. "
                "Vui lòng hủy các hợp đồng liên quan trước."
            )
        
        return self._repo.delete(xe_id)
    
    def search(
        self,
        hang: str = None,
        dong_xe: str = None,
        nam_san_xuat_min: int = None,
        nam_san_xuat_max: int = None,
        gia_min: int = None,
        gia_max: int = None,
        mau_sac: str = None,
        trang_thai: str = None,
        keyword: str = None,
        low_stock_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> XeSearchResult:
        """Search vehicles with filters.
        
        BR-XE-06, BR-XE-07: Advanced search with keyword support.
        
        Args:
            hang: Filter by brand.
            dong_xe: Filter by model.
            nam_san_xuat_min: Minimum manufacturing year.
            nam_san_xuat_max: Maximum manufacturing year.
            gia_min: Minimum price.
            gia_max: Maximum price.
            mau_sac: Filter by color.
            trang_thai: Filter by status.
            keyword: Keyword search (ma_xe, hang, dong_xe).
            low_stock_only: Only vehicles below stock threshold.
            page: Page number (1-indexed).
            page_size: Results per page.
            
        Returns:
            XeSearchResult with items and pagination info.
        """
        filter = XeSearchFilter(
            hang=hang,
            dong_xe=dong_xe,
            nam_san_xuat_min=nam_san_xuat_min,
            nam_san_xuat_max=nam_san_xuat_max,
            gia_min=gia_min,
            gia_max=gia_max,
            mau_sac=mau_sac,
            trang_thai=trang_thai,
            keyword=keyword,
            low_stock_only=low_stock_only,
        )
        
        offset = (page - 1) * page_size
        items = self._repo.search(filter, limit=page_size, offset=offset)
        total = self._repo.count_search(filter)
        total_pages = max(1, (total + page_size - 1) // page_size)
        
        return XeSearchResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    def get_low_stock_vehicles(self, limit: int = 50) -> List[Xe]:
        """Get vehicles with low stock.
        
        BR-XE-08: Low stock warning.
        
        Args:
            limit: Maximum results.
            
        Returns:
            List of low stock Xe entities.
        """
        return self._repo.find_low_stock(limit)
    
    def adjust_inventory(self, xe_id: int, delta: int, nhan_vien_id: int = None) -> Xe:
        """Adjust vehicle inventory by delta.
        
        Used by:
        - TRG-04: Stock reaches 0 with da_giao_xe contracts → da_ban
        - TRG-05: Stock increases from 0 for da_ban → con_hang
        
        Args:
            xe_id: Vehicle ID.
            delta: Amount to adjust (positive = add stock, negative = remove).
            nhan_vien_id: ID of user making adjustment (for audit).
            
        Returns:
            Updated Xe entity.
        """
        xe = self._repo.find_by_id(xe_id)
        if not xe:
            raise XeNotFoundError(f"Không tìm thấy xe với ID {xe_id}")
        
        new_stock = self._repo.adjust_stock(xe_id, delta)
        
        # BR-XE-04: Stock reached 0 and has da_giao_xe contracts → da_ban
        if new_stock == 0:
            # Check if has active (da_giao_xe) contracts
            cursor = self.conn.execute(
                """SELECT 1 FROM hop_dong 
                   WHERE xe_id = ? AND trang_thai = 'da_giao_xe' LIMIT 1""",
                (xe_id,)
            )
            if cursor.fetchone():
                self._repo.update_status(xe_id, "da_ban")
        
        return self._repo.find_by_id(xe_id)
    
    def get_distinct_hangs(self) -> List[str]:
        """Get list of distinct brands.
        
        Returns:
            List of brand names.
        """
        return self._repo.get_distinct_hangs()
    
    def get_distinct_dong_xe(self, hang: str) -> List[str]:
        """Get list of distinct models for a brand.
        
        Args:
            hang: Brand name.
            
        Returns:
            List of model names.
        """
        return self._repo.get_distinct_dong_xe_by_hang(hang)
    
    def get_distinct_mau_sac(self) -> List[str]:
        """Get list of distinct colors.
        
        Returns:
            List of color values.
        """
        return self._repo.get_distinct_mau_sac()
    
    def check_ma_xe_exists(self, ma_xe: str, exclude_id: int = None) -> bool:
        """Check if ma_xe already exists.
        
        Args:
            ma_xe: Vehicle code to check.
            exclude_id: ID to exclude (for updates).
            
        Returns:
            True if exists, False otherwise.
        """
        return self._repo.exists_by_ma_xe(ma_xe, exclude_id)
