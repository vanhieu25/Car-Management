"""ChienDichMk Service - Marketing Campaign Service.

Implements business rules:
- BR-MK-01: Campaign status flow (nhap → dang_chay → ket_thuc)
- BR-CALC-06: Conversion rate = lead_chuyen_doi / tong_lead * 100
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

import sqlite3

from app.infrastructure.repositories.chien_dich_mk_repository import ChienDichMkRepository


class ChienDichMkServiceError(Exception):
    """Base exception for ChienDichMk service errors."""
    pass


class ValidationError(ChienDichMkServiceError):
    """Validation error."""
    pass


class ChienDichMkNotFoundError(ChienDichMkServiceError):
    """Raised when campaign not found."""
    pass


@dataclass
class ChienDichMkCreateData:
    """"Data for creating a marketing campaign."""
    ten_chien_dich: str
    kenh_tiep_thi: str
    ngay_bat_dau: str
    ngay_ket_thuc: str
    ngan_sach: int = 0
    muc_tieu: str = ""
    so_luong_lead_muc_tieu: int = 0
    trang_thai: str = "nhap"
    created_by: Optional[int] = None


@dataclass
class ChienDichMkUpdateData:
    """Data for updating a marketing campaign."""
    ten_chien_dich: Optional[str] = None
    kenh_tiep_thi: Optional[str] = None
    ngay_bat_dau: Optional[str] = None
    ngay_ket_thuc: Optional[str] = None
    ngan_sach: Optional[int] = None
    muc_tieu: Optional[str] = None
    so_luong_lead_muc_tieu: Optional[int] = None
    trang_thai: Optional[str] = None


class ChienDichMkService:
    """Service for marketing campaign operations."""

    VALID_KENH = ['facebook', 'google_ads', 'youtube', 'truyen_hinh', 'bao_chi', 'truyen_mieng', 'khac']
    VALID_TRANG_THAI = ['nhap', 'dang_chay', 'ket_thuc']

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn
        self._repo = ChienDichMkRepository(conn)

    def create(self, data: ChienDichMkCreateData) -> Dict[str, Any]:
        """Create a new marketing campaign.
        
        Validates:
        - ngan_sach >= 0
        - ngay_ket_thuc >= ngay_bat_dau
        - kenh_tiep_thi is valid
        """
        # Validate
        if data.ngan_sach < 0:
            raise ValidationError("Ngân sách phải >= 0")
        
        if data.kenh_tiep_thi not in self.VALID_KENH:
            raise ValidationError(f"Kênh tiếp thị không hợp lệ: {data.kenh_tiep_thi}")
        
        try:
            ngay_bat_dau = datetime.strptime(data.ngay_bat_dau, '%Y-%m-%d')
            ngay_ket_thuc = datetime.strptime(data.ngay_ket_thuc, '%Y-%m-%d')
            if ngay_ket_thuc < ngay_bat_dau:
                raise ValidationError("Ngày kết thúc phải >= ngày bắt đầu")
        except ValueError as e:
            raise ValidationError(f"Định dạng ngày không hợp lệ: {e}")
        
        # Create
        campaign_id = self._repo.create({
            'ten_chien_dich': data.ten_chien_dich,
            'kenh_tiep_thi': data.kenh_tiep_thi,
            'ngay_bat_dau': data.ngay_bat_dau,
            'ngay_ket_thuc': data.ngay_ket_thuc,
            'ngan_sach': data.ngan_sach,
            'muc_tieu': data.muc_tieu,
            'so_luong_lead_muc_tieu': data.so_luong_lead_muc_tieu,
            'trang_thai': data.trang_thai,
            'created_by': data.created_by
        })
        
        return self._repo.find_by_id(campaign_id)

    def update(self, campaign_id: int, data: ChienDichMkUpdateData, nv_id: int = None) -> Dict[str, Any]:
        """Update a campaign.
        
        Args:
            campaign_id: Campaign ID.
            data: ChienDichMkUpdateData with fields to update.
            nv_id: ID of staff making the update (for audit)."""
        existing = self._repo.find_by_id(campaign_id)
        if not existing:
            raise ChienDichMkNotFoundError(f"Chiến dịch {campaign_id} không tồn tại")
        
        update_dict = {}
        if data.ten_chien_dich is not None:
            update_dict['ten_chien_dich'] = data.ten_chien_dich
        if data.kenh_tiep_thi is not None:
            if data.kenh_tiep_thi not in self.VALID_KENH:
                raise ValidationError(f"Kênh tiếp thị không hợp lệ")
            update_dict['kenh_tiep_thi'] = data.kenh_tiep_thi
        if data.ngay_bat_dau is not None:
            update_dict['ngay_bat_dau'] = data.ngay_bat_dau
        if data.ngay_ket_thuc is not None:
            update_dict['ngay_ket_thuc'] = data.ngay_ket_thuc
        if data.ngan_sach is not None:
            if data.ngan_sach < 0:
                raise ValidationError("Ngân sách phải >= 0")
            update_dict['ngan_sach'] = data.ngan_sach
        if data.muc_tieu is not None:
            update_dict['muc_tieu'] = data.muc_tieu
        if data.so_luong_lead_muc_tieu is not None:
            update_dict['so_luong_lead_muc_tieu'] = data.so_luong_lead_muc_tieu
        if data.trang_thai is not None:
            if data.trang_thai not in self.VALID_TRANG_THAI:
                raise ValidationError(f"Trạng thái không hợp lệ: {data.trang_thai}")
            update_dict['trang_thai'] = data.trang_thai
        
        if update_dict:
            self._repo.update(campaign_id, update_dict)
        
        return self._repo.find_by_id(campaign_id)

    def get_by_id(self, campaign_id: int) -> Dict[str, Any]:
        """Get campaign by ID."""
        campaign = self._repo.find_by_id(campaign_id)
        if not campaign:
            raise ChienDichMkNotFoundError(f"Chiến dịch {campaign_id} không tồn tại")
        return campaign

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all campaigns."""
        return self._repo.find_all(limit, offset)

    def get_active(self) -> List[Dict[str, Any]]:
        """Get active campaigns (dang_chay and current date between start/end)."""
        return self._repo.find_active()

    def get_by_status(self, trang_thai: str) -> List[Dict[str, Any]]:
        """Get campaigns by status."""
        return self._repo.find_by_status(trang_thai)

    def delete(self, campaign_id: int) -> bool:
        """Delete campaign (only if no leads)."""
        existing = self._repo.find_by_id(campaign_id)
        if not existing:
            raise ChienDichMkNotFoundError(f"Chiến dịch {campaign_id} không tồn tại")
        
        success = self._repo.delete(campaign_id)
        if not success:
            raise ValidationError("Không thể xóa: chiến dịch đang có lead")
        return True

    def calculate_conversion_rate(self, campaign_id: int) -> float:
        """Calculate conversion rate for a campaign.
        
        BR-CALC-06: ty_le_chuyen_doi = lead_chuyen_doi / tong_lead * 100
        
        Returns:
            Conversion rate as percentage (0-100)
        """
        campaign = self._repo.find_by_id(campaign_id)
        if not campaign:
            raise ChienDichMkNotFoundError(f"Chiến dịch {campaign_id} không tồn tại")
        
        from app.infrastructure.repositories.lead_repository import LeadRepository
        lead_repo = LeadRepository(self.conn)
        
        total_leads = lead_repo.count_by_chien_dich(campaign_id)
        converted_leads = lead_repo.count_converted_by_chien_dich(campaign_id)
        
        if total_leads == 0:
            return 0.0
        
        return round((converted_leads / total_leads) * 100, 2)

    def get_campaign_summary(self, campaign_id: int) -> Dict[str, Any]:
        """Get campaign summary with lead statistics.
        
        Returns:
            Dict with: campaign data, tong_lead, lead_chuyen_doi, ty_le_chuyen_doi, so_lead_dat
        """
        campaign = self._repo.find_by_id(campaign_id)
        if not campaign:
            raise ChienDichMkNotFoundError(f"Chiến dịch {campaign_id} không tồn tại")
        
        from app.infrastructure.repositories.lead_repository import LeadRepository
        lead_repo = LeadRepository(self.conn)
        
        tong_lead = lead_repo.count_by_chien_dich(campaign_id)
        lead_chuyen_doi = lead_repo.count_converted_by_chien_dich(campaign_id)
        ty_le_chuyen_doi = round((lead_chuyen_doi / tong_lead * 100), 2) if tong_lead > 0 else 0.0
        so_lead_dat = tong_lead >= campaign['so_luong_lead_muc_tieu'] if campaign['so_luong_lead_muc_tieu'] > 0 else True
        
        return {
            **campaign,
            'tong_lead': tong_lead,
            'lead_chuyen_doi': lead_chuyen_doi,
            'ty_le_chuyen_doi': ty_le_chuyen_doi,
            'so_lead_dat': so_lead_dat
        }

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get overall marketing stats."""
        return {
            'tong_chien_dich': self._repo.count_all(),
            'dang_chay': self._repo.count_by_status('dang_chay'),
            'ket_thuc': self._repo.count_by_status('ket_thuc'),
            'nhap': self._repo.count_by_status('nhap')
        }
