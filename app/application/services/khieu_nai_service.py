"""KhieuNai Service - Complaint/Feedback Service.

Implements business rules:
- BR-KN-01: Complaint lifecycle (moi → dang_xu_ly → da_giai_quyet/da_dong)
- BR-KN-03: Priority 'cao' should be displayed first
- BR-KN-04: Satisfaction rating 1-5 required before closing
- BR-KN-05: Reason (ly_do) required when updating status
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import sqlite3

from app.infrastructure.repositories.khieu_nai_repository import KhieuNaiRepository


class KhieuNaiServiceError(Exception):
    """Base exception for KhieuNai service errors."""
    pass


class ValidationError(KhieuNaiServiceError):
    """Validation error."""
    pass


class KhieuNaiNotFoundError(KhieuNaiServiceError):
    """Raised when complaint not found."""
    pass


class PermissionDeniedError(KhieuNaiServiceError):
    """Raised when user lacks permission."""
    pass


@dataclass
class KhieuNaiCreateData:
    """Data for creating a complaint."""
    khach_hang_id: int
    tieu_de: str
    noi_dung: str
    hop_dong_id: Optional[int] = None
    muc_do: str = 'trung_binh'
    nguon_goc: Optional[str] = None
    created_by: Optional[int] = None


@dataclass
class KhieuNaiUpdateData:
    """Data for updating a complaint."""
    tieu_de: Optional[str] = None
    noi_dung: Optional[str] = None
    muc_do: Optional[str] = None
    nguon_goc: Optional[str] = None
    trang_thai: Optional[str] = None
    nhan_vien_xu_ly_id: Optional[int] = None
    ly_do: Optional[str] = None
    danh_gia_hai_long: Optional[int] = None


class KhieuNaiService:
    """Service for complaint operations."""

    VALID_MUC_DO = ['thap', 'trung_binh', 'cao']
    VALID_NGUON_GOC = ['chat_luong_xe', 'dich_vu', 'bao_hanh', 'khac']
    VALID_TRANG_THAI = ['moi', 'dang_xu_ly', 'da_giai_quyet', 'da_dong']

    # BR-KN-01: Status transitions
    STATUS_TRANSITIONS = {
        'moi': ['dang_xu_ly'],
        'dang_xu_ly': ['da_giai_quyet', 'da_dong', 'moi'],  # có thể revert
        'da_giai_quyet': ['dang_xu_ly'],  # reopen
        'da_dong': [],  # terminal
    }

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn
        self._repo = KhieuNaiRepository(conn)

    def create(self, data: KhieuNaiCreateData) -> Dict[str, Any]:
        """Create a new complaint.

        Validates:
        - khach_hang_id exists
        - muc_do is valid
        - nguon_goc is valid (if provided)
        """
        # Validate customer exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM khach_hang WHERE id = ?", (data.khach_hang_id,))
        if not cursor.fetchone():
            raise ValidationError(f"Khách hàng {data.khach_hang_id} không tồn tại")

        # Validate muc_do
        if data.muc_do not in self.VALID_MUC_DO:
            raise ValidationError(f"Mức độ '{data.muc_do}' không hợp lệ. Chọn: {self.VALID_MUC_DO}")

        # Validate nguon_goc
        if data.nguon_goc and data.nguon_goc not in self.VALID_NGUON_GOC:
            raise ValidationError(f"Nguồn gốc '{data.nguon_goc}' không hợp lệ. Chọn: {self.VALID_NGUON_GOC}")

        # Validate hop_dong if provided
        if data.hop_dong_id:
            cursor.execute("SELECT id FROM hop_dong WHERE id = ?", (data.hop_dong_id,))
            if not cursor.fetchone():
                raise ValidationError(f"Hợp đồng {data.hop_dong_id} không tồn tại")

        kn_id = self._repo.create({
            'khach_hang_id': data.khach_hang_id,
            'hop_dong_id': data.hop_dong_id,
            'tieu_de': data.tieu_de,
            'noi_dung': data.noi_dung,
            'muc_do': data.muc_do,
            'nguon_goc': data.nguon_goc,
            'trang_thai': 'moi',
            'ly_do': '',
            'created_by': data.created_by,
        })

        return self._repo.find_by_id(kn_id)

    def update(self, kn_id: int, data: KhieuNaiUpdateData, nv_id: int = None) -> Dict[str, Any]:
        """Update a complaint.
        
        Args:
            kn_id: Complaint ID.
            data: KhieuNaiUpdateData with fields to update.
            nv_id: ID of staff making the update (for audit)."""
        existing = self._repo.find_by_id(kn_id)
        if not existing:
            raise KhieuNaiNotFoundError(f"Khiếu nại {kn_id} không tồn tại")

        update_dict = {}
        if data.tieu_de is not None:
            update_dict['tieu_de'] = data.tieu_de
        if data.noi_dung is not None:
            update_dict['noi_dung'] = data.noi_dung
        if data.muc_do is not None:
            if data.muc_do not in self.VALID_MUC_DO:
                raise ValidationError(f"Mức độ '{data.muc_do}' không hợp lệ")
            update_dict['muc_do'] = data.muc_do
        if data.nguon_goc is not None:
            if data.nguon_goc and data.nguon_goc not in self.VALID_NGUON_GOC:
                raise ValidationError(f"Nguồn gốc '{data.nguon_goc}' không hợp lệ")
            update_dict['nguon_goc'] = data.nguon_goc
        if data.nhan_vien_xu_ly_id is not None:
            update_dict['nhan_vien_xu_ly_id'] = data.nhan_vien_xu_ly_id
        if data.trang_thai is not None:
            if data.trang_thai not in self.VALID_TRANG_THAI:
                raise ValidationError(f"Trạng thái '{data.trang_thai}' không hợp lệ")
            current_status = existing['trang_thai']
            allowed = self.STATUS_TRANSITIONS.get(current_status, [])
            if data.trang_thai not in allowed:
                raise ValidationError(
                    f"Không thể chuyển từ '{current_status}' sang '{data.trang_thai}'. "
                    f"Các chuyển đổi được phép: {allowed}"
                )
            update_dict['trang_thai'] = data.trang_thai
        if data.danh_gia_hai_long is not None:
            if not (1 <= data.danh_gia_hai_long <= 5):
                raise ValidationError("Đánh giá hài lòng phải từ 1-5")
            update_dict['danh_gia_hai_long'] = data.danh_gia_hai_long

        if update_dict:
            self._repo.update(kn_id, update_dict)

        return self._repo.find_by_id(kn_id)

    def assign(self, kn_id: int, nv_id: int) -> Dict[str, Any]:
        """Assign complaint to a staff member.

        BR-KN-02: Only A-01 (Admin) can assign.
        """
        existing = self._repo.find_by_id(kn_id)
        if not existing:
            raise KhieuNaiNotFoundError(f"Khiếu nại {kn_id} không tồn tại")

        # Validate NV exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM nhan_vien WHERE id = ?", (nv_id,))
        if not cursor.fetchone():
            raise ValidationError(f"Nhân viên {nv_id} không tồn tại")

        # Only allow assignment when status is 'moi' or 'dang_xu_ly'
        if existing['trang_thai'] in ('da_giai_quyet', 'da_dong'):
            raise ValidationError("Không thể phân công khiếu nại đã giải quyết hoặc đóng")

        self._repo.update(kn_id, {
            'nhan_vien_xu_ly_id': nv_id,
            'trang_thai': 'dang_xu_ly',
            'ngay_xu_ly': None,  # Will be set when actually processed
        })

        return self._repo.find_by_id(kn_id)

    def update_status(self, kn_id: int, new_status: str, ly_do: str = None) -> Dict[str, Any]:
        """Update complaint status.

        BR-KN-05: ly_do is REQUIRED when updating status.
        """
        if new_status not in self.VALID_TRANG_THAI:
            raise ValidationError(f"Trạng thái '{new_status}' không hợp lệ")

        existing = self._repo.find_by_id(kn_id)
        if not existing:
            raise KhieuNaiNotFoundError(f"Khiếu nại {kn_id} không tồn tại")

        current_status = existing['trang_thai']

        # Validate transition
        allowed = self.STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed and new_status != current_status:
            raise ValidationError(
                f"Không thể chuyển từ '{current_status}' sang '{new_status}'. "
                f"Chuyển đổi hợp lệ: {allowed}"
            )

        # BR-KN-05: ly_do is required when updating status
        if not ly_do or not ly_do.strip():
            raise ValidationError("Phải ghi rõ lý do khi cập nhật trạng thái (BR-KN-05)")

        update_data = {
            'trang_thai': new_status,
            'ly_do': ly_do,
        }

        # Set timestamps based on new status
        if new_status == 'da_giai_quyet':
            update_data['ngay_xu_ly'] = "date('now')"
        elif new_status == 'da_dong':
            update_data['ngay_dong'] = "date('now')"

        self._repo.update(kn_id, update_data)
        return self._repo.find_by_id(kn_id)

    def close(self, kn_id: int, danh_gia_hai_long: int) -> Dict[str, Any]:
        """Close a complaint with satisfaction rating.

        BR-KN-04: danh_gia_hai_long (1-5) is REQUIRED before closing.
        """
        existing = self._repo.find_by_id(kn_id)
        if not existing:
            raise KhieuNaiNotFoundError(f"Khiếu nại {kn_id} không tồn tại")

        # BR-KN-04: Satisfaction rating 1-5 is mandatory
        if danh_gia_hai_long is None or not (1 <= danh_gia_hai_long <= 5):
            raise ValidationError("Đánh giá hài lòng phải từ 1-5 sao (BR-KN-04)")

        # Only allow close from 'dang_xu_ly' or 'da_giai_quyet' status
        if existing['trang_thai'] not in ('dang_xu_ly', 'da_giai_quyet'):
            raise ValidationError(f"Không thể đóng khiếu nại ở trạng thái '{existing['trang_thai']}'")

        self._repo.update(kn_id, {
            'trang_thai': 'da_dong',
            'danh_gia_hai_long': danh_gia_hai_long,
            'ngay_dong': "date('now')",
        })

        return self._repo.find_by_id(kn_id)

    def get_by_id(self, kn_id: int) -> Dict[str, Any]:
        """Get complaint by ID."""
        kn = self._repo.find_by_id(kn_id)
        if not kn:
            raise KhieuNaiNotFoundError(f"Khiếu nại {kn_id} không tồn tại")
        return kn

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all complaints, ordered by priority (BR-KN-03)."""
        return self._repo.find_all(limit, offset)

    def get_by_status(self, trang_thai: str) -> List[Dict[str, Any]]:
        """Get complaints by status."""
        return self._repo.find_by_status(trang_thai)

    def get_by_muc_do(self, muc_do: str) -> List[Dict[str, Any]]:
        """Get complaints by priority level."""
        return self._repo.find_by_muc_do(muc_do)

    def get_by_khach_hang(self, kh_id: int) -> List[Dict[str, Any]]:
        """Get complaints for a customer."""
        return self._repo.find_by_khach_hang(kh_id)

    def get_open_by_nv(self, nv_id: int) -> List[Dict[str, Any]]:
        """Get open complaints assigned to a staff."""
        return self._repo.find_open_by_nv(nv_id)

    def delete(self, kn_id: int) -> bool:
        """Delete a complaint (only 'moi' status)."""
        existing = self._repo.find_by_id(kn_id)
        if not existing:
            raise KhieuNaiNotFoundError(f"Khiếu nại {kn_id} không tồn tại")

        if existing['trang_thai'] != 'moi':
            raise ValidationError("Chỉ khiếu nại ở trạng thái 'mới' mới được xóa")

        return self._repo.delete(kn_id)

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get overall complaint statistics."""
        return {
            'tong_khieu_nai': self._repo.count_all(),
            'moi': self._repo.count_by_status('moi'),
            'dang_xu_ly': self._repo.count_by_status('dang_xu_ly'),
            'da_giai_quyet': self._repo.count_by_status('da_giai_quyet'),
            'da_dong': self._repo.count_by_status('da_dong'),
            'cao': self._repo.count_by_muc_do('cao'),
            'trung_binh': self._repo.count_by_muc_do('trung_binh'),
            'thap': self._repo.count_by_muc_do('thap'),
            'chua_xu_ly': self._repo.count_open(),
        }
