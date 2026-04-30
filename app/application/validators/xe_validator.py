"""Validators for Xe entity - vehicle management module.

Business rules validated here:
- BR-XE-01: ma_xe is immutable after creation
- BR-XE-09: nam_san_xuat ∈ [1990, current_year + 1]
- BR-DATA-01: gia_ban ≥ 0
- BR-DATA-02: so_luong_ton ≥ 0
- BR-DATA-10: ma_xe format (A-Z0-9-_)
- BR-XE-03: trang_thai must be one of con_hang, da_ban, sap_ve
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class XeValidationResult:
    """Result of Xe validation."""
    is_valid: bool
    errors: list[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def add_error(self, error: str):
        self.is_valid = False
        self.errors.append(error)


class XeValidator:
    """Validator for Xe entity data."""
    
    # Valid status values
    VALID_TRANG_THAI = {"con_hang", "da_ban", "sap_ve"}
    
    # ma_xe pattern: only letters, numbers, underscore, hyphen (BR-DATA-10)
    MA_XE_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')
    
    @classmethod
    def validate_ma_xe(cls, ma_xe: str, is_update: bool = False) -> Optional[str]:
        """Validate ma_xe format and uniqueness rule.
        
        Args:
            ma_xe: Vehicle code to validate.
            is_update: True if this is an update operation (ma_xe should not change).
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not ma_xe or not ma_xe.strip():
            return "Mã xe không được để trống"
        
        if not cls.MA_XE_PATTERN.match(ma_xe):
            return "Mã xe chỉ được chứa chữ, số, dấu gạch dưới và gạch ngang"
        
        if len(ma_xe) < 3:
            return "Mã xe phải có ít nhất 3 ký tự"
        
        if len(ma_xe) > 50:
            return "Mã xe không được vượt quá 50 ký tự"
        
        return None
    
    @classmethod
    def validate_nam_san_xuat(cls, nam_san_xuat: int) -> Optional[str]:
        """Validate manufacturing year (BR-XE-09 + BR-DATA-03).
        
        Args:
            nam_san_xuat: Manufacturing year.
            
        Returns:
            Error message if invalid, None if valid.
        """
        from datetime import datetime
        
        current_year = datetime.now().year
        min_year = 1990
        max_year = current_year + 1
        
        if not isinstance(nam_san_xuat, int):
            return "Năm sản xuất phải là số nguyên"
        
        if nam_san_xuat < min_year or nam_san_xuat > max_year:
            return f"Năm sản xuất phải từ {min_year} đến {max_year}"
        
        return None
    
    @classmethod
    def validate_gia_ban(cls, gia_ban: int) -> Optional[str]:
        """Validate selling price (BR-DATA-01).
        
        Args:
            gia_ban: Selling price in VND.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not isinstance(gia_ban, int):
            return "Giá bán phải là số nguyên"
        
        if gia_ban < 0:
            return "Giá bán không được âm"
        
        if gia_ban > 10_000_000_000:  # 10 billion VND
            return "Giá bán không được vượt quá 10 tỷ VND"
        
        return None
    
    @classmethod
    def validate_so_luong_ton(cls, so_luong_ton: int) -> Optional[str]:
        """Validate stock quantity (BR-DATA-02).
        
        Args:
            so_luong_ton: Stock quantity.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not isinstance(so_luong_ton, int):
            return "Số lượng tồn phải là số nguyên"
        
        if so_luong_ton < 0:
            return "Số lượng tồn không được âm"
        
        return None
    
    @classmethod
    def validate_trang_thai(cls, trang_thai: str) -> Optional[str]:
        """Validate vehicle status (BR-XE-03).
        
        Args:
            trang_thai: Status value.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if trang_thai not in cls.VALID_TRANG_THAI:
            return f"Trạng thái xe phải là một trong các giá trị: {', '.join(cls.VALID_TRANG_THAI)}"
        
        return None
    
    @classmethod
    def validate_hang(cls, hang: str) -> Optional[str]:
        """Validate vehicle brand.
        
        Args:
            hang: Brand name.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not hang or not hang.strip():
            return "Hãng xe không được để trống"
        
        if len(hang) > 100:
            return "Hãng xe không được vượt quá 100 ký tự"
        
        return None
    
    @classmethod
    def validate_dong_xe(cls, dong_xe: str) -> Optional[str]:
        """Validate vehicle model.
        
        Args:
            dong_xe: Model name.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not dong_xe or not dong_xe.strip():
            return "Dòng xe không được để trống"
        
        if len(dong_xe) > 100:
            return "Dòng xe không được vượt quá 100 ký tự"
        
        return None
    
    @classmethod
    def validate_create(cls, data: dict) -> XeValidationResult:
        """Validate data for creating a new vehicle.
        
        Args:
            data: Dict with vehicle data.
            
        Returns:
            XeValidationResult with any errors.
        """
        result = XeValidationResult(is_valid=True)
        
        # Validate ma_xe
        ma_xe_error = cls.validate_ma_xe(data.get("ma_xe", ""))
        if ma_xe_error:
            result.add_error(ma_xe_error)
        
        # Validate required fields
        hang_error = cls.validate_hang(data.get("hang", ""))
        if hang_error:
            result.add_error(hang_error)
        
        dong_xe_error = cls.validate_dong_xe(data.get("dong_xe", ""))
        if dong_xe_error:
            result.add_error(dong_xe_error)
        
        # Validate nam_san_xuat
        nam_error = cls.validate_nam_san_xuat(data.get("nam_san_xuat", 0))
        if nam_error:
            result.add_error(nam_error)
        
        # Validate gia_ban
        gia_error = cls.validate_gia_ban(data.get("gia_ban", -1))
        if gia_error:
            result.add_error(gia_error)
        
        # Validate so_luong_ton if provided
        if "so_luong_ton" in data:
            sl_error = cls.validate_so_luong_ton(data.get("so_luong_ton", -1))
            if sl_error:
                result.add_error(sl_error)
        
        # Validate trang_thai if provided
        if "trang_thai" in data:
            tt_error = cls.validate_trang_thai(data.get("trang_thai", ""))
            if tt_error:
                result.add_error(tt_error)
        
        return result
    
    @classmethod
    def validate_update(cls, data: dict, original_ma_xe: str = None) -> XeValidationResult:
        """Validate data for updating a vehicle.
        
        BR-XE-01: ma_xe cannot be changed after creation.
        
        Args:
            data: Dict with vehicle data.
            original_ma_xe: Original ma_xe if updating.
            
        Returns:
            XeValidationResult with any errors.
        """
        result = XeValidationResult(is_valid=True)
        
        # Check ma_xe is not being changed (BR-XE-01)
        if "ma_xe" in data and original_ma_xe:
            if data["ma_xe"] != original_ma_xe:
                result.add_error("Không thể thay đổi mã xe sau khi tạo")
        
        # Validate ma_xe format if being set
        if "ma_xe" in data:
            ma_xe_error = cls.validate_ma_xe(data["ma_xe"], is_update=True)
            if ma_xe_error:
                result.add_error(ma_xe_error)
        
        # Validate nam_san_xuat
        if "nam_san_xuat" in data:
            nam_error = cls.validate_nam_san_xuat(data["nam_san_xuat"])
            if nam_error:
                result.add_error(nam_error)
        
        # Validate gia_ban
        if "gia_ban" in data:
            gia_error = cls.validate_gia_ban(data["gia_ban"])
            if gia_error:
                result.add_error(gia_error)
        
        # Validate so_luong_ton
        if "so_luong_ton" in data:
            sl_error = cls.validate_so_luong_ton(data["so_luong_ton"])
            if sl_error:
                result.add_error(sl_error)
        
        # Validate trang_thai
        if "trang_thai" in data:
            tt_error = cls.validate_trang_thai(data["trang_thai"])
            if tt_error:
                result.add_error(tt_error)
        
        # Validate hang/dong_xe
        if "hang" in data:
            hang_error = cls.validate_hang(data["hang"])
            if hang_error:
                result.add_error(hang_error)
        
        if "dong_xe" in data:
            dong_xe_error = cls.validate_dong_xe(data["dong_xe"])
            if dong_xe_error:
                result.add_error(dong_xe_error)
        
        return result
