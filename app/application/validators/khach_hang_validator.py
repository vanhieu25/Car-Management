"""Validators for KhachHang entity - customer management module.

Business rules validated here:
- BR-KH-01: Required fields (ho_ten, so_dien_thoai, email)
- BR-KH-02: so_dien_thoai must be unique
- BR-KH-06: Email valid (BR-DATA-04), SĐT VN (BR-DATA-05)
- BR-CALC-03: Customer classification thresholds
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class KhachHangValidationResult:
    """Result of KhachHang validation."""
    is_valid: bool
    errors: list = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def add_error(self, error: str):
        self.is_valid = False
        self.errors.append(error)


class KhachHangValidator:
    """Validator for KhachHang entity data."""
    
    # Email pattern (BR-DATA-04) - simplified RFC 5322
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Vietnam phone pattern (BR-DATA-05): 10 digits, starts with 0, valid prefix
    PHONE_PATTERN = re.compile(r'^0[3-9][0-9]{8}$')
    
    # Customer classification thresholds (BR-CALC-03)
    THUONG_THRESHOLD = 500_000_000      # < 500tr = Thường
    THAN_THIET_THRESHOLD = 1_500_000_000  # < 1.5ty = Thân thiết, >= 1.5ty = VIP
    
    @classmethod
    def validate_email(cls, email: str) -> Optional[str]:
        """Validate email format (BR-DATA-04).
        
        Args:
            email: Email address to validate.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not email or not email.strip():
            return "Email không được để trống"
        
        if not cls.EMAIL_PATTERN.match(email):
            return "Email không hợp lệ (định dạng: local@domain.tld)"
        
        return None
    
    @classmethod
    def validate_phone(cls, phone: str) -> Optional[str]:
        """Validate Vietnam phone number (BR-DATA-05).
        
        Args:
            phone: Phone number to validate.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not phone or not phone.strip():
            return "Số điện thoại không được để trống"
        
        # Remove spaces and dashes
        phone_clean = phone.strip().replace(" ", "").replace("-", "")
        
        if not cls.PHONE_PATTERN.match(phone_clean):
            return "Số điện thoại không hợp lệ (phải là số điện thoại Việt Nam 10 số, bắt đầu bằng 0)"
        
        return None
    
    @classmethod
    def validate_ho_ten(cls, ho_ten: str) -> Optional[str]:
        """Validate customer name.
        
        Args:
            ho_ten: Customer name to validate.
            
        Returns:
            Error message if invalid, None if valid.
        """
        if not ho_ten or not ho_ten.strip():
            return "Họ tên không được để trống"
        
        if len(ho_ten) < 2:
            return "Họ tên phải có ít nhất 2 ký tự"
        
        if len(ho_ten) > 100:
            return "Họ tên không được vượt quá 100 ký tự"
        
        return None
    
    @classmethod
    def validate_ngay_sinh(cls, ngay_sinh: str) -> Optional[str]:
        """Validate birth date.
        
        Args:
            ngay_sinh: Birth date in ISO format (YYYY-MM-DD).
            
        Returns:
            Error message if invalid, None if valid.
        """
        from datetime import datetime
        
        if not ngay_sinh:
            return None  # Optional field
        
        try:
            birth_date = datetime.strptime(ngay_sinh, "%Y-%m-%d")
            today = datetime.now()
            
            if birth_date > today:
                return "Ngày sinh không thể là ngày trong tương lai"
            
            age = today.year - birth_date.year
            if age > 120:
                return "Ngày sinh không hợp lệ (tuổi > 120)"
            
        except ValueError:
            return "Ngày sinh không hợp lệ (định dạng: YYYY-MM-DD)"
        
        return None
    
    @classmethod
    def validate_create(cls, data: dict) -> KhachHangValidationResult:
        """Validate data for creating a new customer.
        
        Args:
            data: Dict with customer data.
            
        Returns:
            KhachHangValidationResult with any errors.
        """
        result = KhachHangValidationResult(is_valid=True)
        
        # Validate required fields
        ho_ten_error = cls.validate_ho_ten(data.get("ho_ten", ""))
        if ho_ten_error:
            result.add_error(ho_ten_error)
        
        phone_error = cls.validate_phone(data.get("so_dien_thoai", ""))
        if phone_error:
            result.add_error(phone_error)
        
        email_error = cls.validate_email(data.get("email", ""))
        if email_error:
            result.add_error(email_error)
        
        # Validate optional fields if provided
        ngay_sinh = data.get("ngay_sinh")
        if ngay_sinh:
            ngay_sinh_error = cls.validate_ngay_sinh(ngay_sinh)
            if ngay_sinh_error:
                result.add_error(ngay_sinh_error)
        
        return result
    
    @classmethod
    def validate_update(cls, data: dict) -> KhachHangValidationResult:
        """Validate data for updating a customer.
        
        Args:
            data: Dict with customer data.
            
        Returns:
            KhachHangValidationResult with any errors.
        """
        result = KhachHangValidationResult(is_valid=True)
        
        if "ho_ten" in data:
            ho_ten_error = cls.validate_ho_ten(data["ho_ten"])
            if ho_ten_error:
                result.add_error(ho_ten_error)
        
        if "so_dien_thoai" in data:
            phone_error = cls.validate_phone(data["so_dien_thoai"])
            if phone_error:
                result.add_error(phone_error)
        
        if "email" in data:
            email_error = cls.validate_email(data["email"])
            if email_error:
                result.add_error(email_error)
        
        if "ngay_sinh" in data and data["ngay_sinh"]:
            ngay_sinh_error = cls.validate_ngay_sinh(data["ngay_sinh"])
            if ngay_sinh_error:
                result.add_error(ngay_sinh_error)
        
        return result
    
    @classmethod
    def calculate_phan_loai(cls, tong_gia_tri_mua: int) -> str:
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
        if tong_gia_tri_mua >= cls.THAN_THIET_THRESHOLD:
            return "VIP"
        elif tong_gia_tri_mua >= cls.THUONG_THRESHOLD:
            return "Than_thiet"
        else:
            return "Thuong"
    
    @classmethod
    def get_classification_thresholds(cls) -> dict:
        """Get customer classification thresholds for UI display.
        
        Returns:
            Dict with threshold values.
        """
        return {
            "thuong_max": cls.THUONG_THRESHOLD,
            "than_thiet_min": cls.THUONG_THRESHOLD,
            "than_thiet_max": cls.THAN_THIET_THRESHOLD,
            "vip_min": cls.THAN_THIET_THRESHOLD,
        }
