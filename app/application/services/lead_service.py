"""Lead Service - Sales Lead Service.

Implements business rules:
- BR-MK-02: Lead status flow (moi → dang_cham_soc → chuyen_doi/tu_choi)
- BR-MK-03: Convert lead to customer
- BR-CALC-06: Conversion rate
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import sqlite3

from app.infrastructure.repositories.lead_repository import LeadRepository
from app.infrastructure.repositories.chien_dich_mk_repository import ChienDichMkRepository


class LeadServiceError(Exception):
    """Base exception for Lead service errors."""
    pass


class ValidationError(LeadServiceError):
    """Validation error."""
    pass


class LeadNotFoundError(LeadServiceError):
    """Raised when lead not found."""
    pass


class LeadConvertError(LeadServiceError):
    """Raised when lead conversion fails."""
    pass


@dataclass
class LeadCreateData:
    """Data for creating a new lead."""
    chien_dich_id: Optional[int] = None
    ho_ten: str = ""
    so_dien_thoai: str = ""
    email: str = ""
    nguon: str = ""
    nhu_cau: str = ""
    nhan_vien_phu_trach_id: Optional[int] = None
    ghi_chu: str = ""
    created_by: Optional[int] = None


@dataclass
class LeadUpdateData:
    """Data for updating a lead."""
    ho_ten: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    email: Optional[str] = None
    nguon: Optional[str] = None
    nhu_cau: Optional[str] = None
    nhan_vien_phu_trach_id: Optional[int] = None
    trang_thai: Optional[str] = None
    ghi_chu: Optional[str] = None


class LeadService:
    """Service for lead operations."""

    VALID_TRANG_THAI = ['moi', 'dang_cham_soc', 'chuyen_doi', 'tu_choi']
    VALID_STATUS_TRANSITIONS = {
        'moi': ['dang_cham_soc', 'tu_choi'],
        'dang_cham_soc': ['chuyen_doi', 'tu_choi'],
        'chuyen_doi': [],  # terminal
        'tu_choi': []      # terminal
    }

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn
        self._repo = LeadRepository(conn)
        self._campaign_repo = ChienDichMkRepository(conn)

    def create(self, data: LeadCreateData) -> Dict[str, Any]:
        """Create a new lead.
        
        Default status is 'moi'.
        """
        if not data.ho_ten.strip():
            raise ValidationError("Họ tên không được trống")
        if not data.so_dien_thoai.strip():
            raise ValidationError("Số điện thoại không được trống")
        
        # Validate campaign exists if provided
        if data.chien_dich_id:
            campaign = self._campaign_repo.find_by_id(data.chien_dich_id)
            if not campaign:
                raise ValidationError(f"Chiến dịch {data.chien_dich_id} không tồn tại")
        
        lead_id = self._repo.create({
            'chien_dich_id': data.chien_dich_id,
            'ho_ten': data.ho_ten,
            'so_dien_thoai': data.so_dien_thoai,
            'email': data.email,
            'nguon': data.nguon,
            'nhu_cau': data.nhu_cau,
            'nhan_vien_phu_trach_id': data.nhan_vien_phu_trach_id,
            'trang_thai': 'moi',
            'ghi_chu': data.ghi_chu,
            'created_by': data.created_by
        })
        
        return self._repo.find_by_id(lead_id)

    def update(self, lead_id: int, data: LeadUpdateData) -> Dict[str, Any]:
        """Update a lead."""
        existing = self._repo.find_by_id(lead_id)
        if not existing:
            raise LeadNotFoundError(f"Lead {lead_id} không tồn tại")
        
        update_dict = {}
        if data.ho_ten is not None:
            update_dict['ho_ten'] = data.ho_ten
        if data.so_dien_thoai is not None:
            update_dict['so_dien_thoai'] = data.so_dien_thoai
        if data.email is not None:
            update_dict['email'] = data.email
        if data.nguon is not None:
            update_dict['nguon'] = data.nguon
        if data.nhu_cau is not None:
            update_dict['nhu_cau'] = data.nhu_cau
        if data.nhan_vien_phu_trach_id is not None:
            update_dict['nhan_vien_phu_trach_id'] = data.nhan_vien_phu_trach_id
        if data.trang_thai is not None:
            update_dict['trang_thai'] = data.trang_thai
        if data.ghi_chu is not None:
            update_dict['ghi_chu'] = data.ghi_chu
        
        if update_dict:
            self._repo.update(lead_id, update_dict)
        
        return self._repo.find_by_id(lead_id)

    def update_status(self, lead_id: int, new_status: str) -> Dict[str, Any]:
        """Update lead status with validation.
        
        BR-MK-02: Only allow valid transitions.
        """
        if new_status not in self.VALID_TRANG_THAI:
            raise ValidationError(f"Trạng thái không hợp lệ: {new_status}")
        
        lead = self._repo.find_by_id(lead_id)
        if not lead:
            raise LeadNotFoundError(f"Lead {lead_id} không tồn tại")
        
        current_status = lead['trang_thai']
        
        # Check valid transition
        if new_status not in self.VALID_STATUS_TRANSITIONS.get(current_status, []):
            if current_status == new_status:
                return lead  # no change needed
            raise ValidationError(
                f"Không thể chuyển từ '{current_status}' sang '{new_status}'. "
                f"Chuyển đổi hợp lệ: {self.VALID_STATUS_TRANSITIONS.get(current_status, [])}"
            )
        
        self._repo.update(lead_id, {'trang_thai': new_status})
        return self._repo.find_by_id(lead_id)

    def get_by_id(self, lead_id: int) -> Dict[str, Any]:
        """Get lead by ID."""
        lead = self._repo.find_by_id(lead_id)
        if not lead:
            raise LeadNotFoundError(f"Lead {lead_id} không tồn tại")
        return lead

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all leads."""
        return self._repo.find_all(limit, offset)

    def get_by_chien_dich(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Get leads by campaign."""
        return self._repo.find_by_chien_dich(campaign_id)

    def get_by_status(self, trang_thai: str) -> List[Dict[str, Any]]:
        """Get leads by status."""
        return self._repo.find_by_status(trang_thai)

    def get_by_nv(self, nv_id: int) -> List[Dict[str, Any]]:
        """Get leads assigned to a staff member."""
        return self._repo.find_by_nv(nv_id)

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """Search leads by keyword."""
        return self._repo.search(keyword)

    def assign_to_nv(self, lead_id: int, nv_id: int) -> Dict[str, Any]:
        """Assign lead to a staff member."""
        lead = self._repo.find_by_id(lead_id)
        if not lead:
            raise LeadNotFoundError(f"Lead {lead_id} không tồn tại")
        
        self._repo.update(lead_id, {'nhan_vien_phu_trach_id': nv_id})
        return self._repo.find_by_id(lead_id)

    def convert_to_customer(self, lead_id: int) -> Dict[str, Any]:
        """Convert lead to customer.
        
        BR-MK-03: 
        1. Create khach_hang from lead data (ho_ten, so_dien_thoai, email)
        2. Update lead.khach_hang_id and lead.trang_thai = 'chuyen_doi'
        3. Transaction: both must succeed or rollback
        
        Returns:
            Dict with new khach_hang_id and lead data
        """
        lead = self._repo.find_by_id(lead_id)
        if not lead:
            raise LeadNotFoundError(f"Lead {lead_id} không tồn tại")
        
        if lead['trang_thai'] == 'chuyen_doi':
            raise LeadConvertError("Lead đã được chuyển đổi trước đó")
        
        if lead['khach_hang_id']:
            raise LeadConvertError("Lead đã có khách hàng liên kết")
        
        try:
            cursor = self.conn.cursor()
            
            # Create khach_hang record
            cursor.execute("""
                INSERT INTO khach_hang (
                    ho_ten, so_dien_thoai, email, nguon, created_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (lead['ho_ten'], lead['so_dien_thoai'], lead['email'], lead.get('nguon', '')))
            
            khach_hang_id = cursor.lastrowid
            
            # Update lead with khach_hang_id and status
            cursor.execute("""
                UPDATE lead 
                SET khach_hang_id = ?, trang_thai = 'chuyen_doi', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (khach_hang_id, lead_id))
            
            self.conn.commit()
            
            # Return updated lead
            return self._repo.find_by_id(lead_id)
            
        except Exception as e:
            self.conn.rollback()
            raise LeadConvertError(f"Chuyển đổi thất bại: {e}")

    def get_lead_stats(self, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Get lead statistics.
        
        Args:
            campaign_id: If provided, stats for specific campaign. Otherwise, overall stats.
            
        Returns:
            Dict with lead counts by status
        """
        cursor = self.conn.cursor()
        
        if campaign_id:
            # Stats for specific campaign
            cursor.execute("SELECT trang_thai, COUNT(*) as count FROM lead WHERE chien_dich_id = ? GROUP BY trang_thai", (campaign_id,))
            rows = cursor.fetchall()
            total = sum(r[1] for r in rows)
            stats = {status: 0 for status in self.VALID_TRANG_THAI}
            for row in rows:
                stats[row[0]] = row[1]
            return {
                'tong_lead': total,
                **stats
            }
        else:
            # Overall stats
            cursor.execute("SELECT trang_thai, COUNT(*) as count FROM lead GROUP BY trang_thai")
            rows = cursor.fetchall()
            total = sum(r[1] for r in rows)
            stats = {status: 0 for status in self.VALID_TRANG_THAI}
            for row in rows:
                stats[row[0]] = row[1]
            return {
                'tong_lead': total,
                **stats
            }

    def delete(self, lead_id: int) -> bool:
        """Delete a lead."""
        lead = self._repo.find_by_id(lead_id)
        if not lead:
            raise LeadNotFoundError(f"Lead {lead_id} không tồn tại")
        
        if lead['trang_thai'] == 'chuyen_doi':
            raise ValidationError("Không thể xóa lead đã chuyển đổi")
        
        return self._repo.delete(lead_id)
