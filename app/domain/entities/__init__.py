"""Base entity class for all domain entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class BaseEntity:
    """Base class for all domain entities."""

    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert entity to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result

    @classmethod
    def from_row(cls, row):
        """Create entity from database row."""
        if row is None:
            return None
        return cls(**dict(row))


@dataclass
class NhanVien(BaseEntity):
    """Nhân viên entity."""

    username: str = ""
    mat_khau_hash: str = ""
    ho_ten: str = ""
    email: str = ""
    so_dien_thoai: str = ""
    vai_tro_id: int = 0
    trang_thai: str = "active"
    lan_dang_nhap_sai: int = 0
    khoa_den: Optional[str] = None
    must_change_password: int = 0
    password_min_length: int = 8
    last_password_change: Optional[str] = None


@dataclass
class VaiTro(BaseEntity):
    """Vai trò entity."""

    ma_vai_tro: str = ""
    ten_vai_tro: str = ""
    mo_ta: str = ""


@dataclass
class Xe(BaseEntity):
    """Xe entity."""

    ma_xe: str = ""
    hang: str = ""
    dong_xe: str = ""
    nam_san_xuat: int = 0
    mau_sac: str = ""
    gia_ban: int = 0
    so_luong_ton: int = 0
    muc_toi_thieu: int = 2
    trang_thai: str = "con_hang"
    ngay_nhap_dau_tien: Optional[str] = None
    mo_ta: str = ""


@dataclass
class KhachHang(BaseEntity):
    """Khách hàng entity."""

    ho_ten: str = ""
    so_dien_thoai: str = ""
    email: str = ""
    dia_chi: str = ""
    ngay_sinh: Optional[str] = None
    phan_loai: str = "Thuong"
    tong_gia_tri_mua: int = 0
    so_xe_da_mua: int = 0


@dataclass
class HopDong(BaseEntity):
    """Hợp đồng entity."""

    ma_hop_dong: str = ""
    khach_hang_id: int = 0
    xe_id: int = 0
    nhan_vien_id: int = 0
    khuyen_mai_id: Optional[int] = None
    gia_xe: int = 0
    tong_gia_phu_kien: int = 0
    tien_giam_km: int = 0
    tong_tien: int = 0
    trang_thai: str = "moi_tao"
    ngay_tao: Optional[str] = None
    ngay_thanh_toan: Optional[str] = None
    ngay_giao_xe: Optional[str] = None
    ly_do_huy: Optional[str] = None
    ghi_chu: str = ""


@dataclass
class PhuKien(BaseEntity):
    """Phụ kiện entity."""

    ma_pk: str = ""
    ten_pk: str = ""
    phan_loai: str = ""
    gia_ban: int = 0
    ton_kho: int = 0
    mo_ta: str = ""


@dataclass
class ComboPhuKien(BaseEntity):
    """Combo phụ kiện entity."""

    ten_combo: str = ""
    he_so_giam: float = 1.0
    mo_ta: str = ""


@dataclass
class KhuyenMai(BaseEntity):
    """Khuyến mãi entity."""

    ten_km: str = ""
    mo_ta: str = ""
    loai_km: str = ""
    gia_tri: int = 0
    kieu_gia_tri: str = "tien"
    tu_ngay: str = ""
    den_ngay: str = ""
    trang_thai: str = "dang_chay"
    so_luong_cho_phep: Optional[int] = None
    so_luong_da_su_dung: int = 0


@dataclass
class BaoHanh(BaseEntity):
    """Bảo hành entity."""

    hop_dong_id: int = 0
    xe_id: int = 0
    khach_hang_id: int = 0
    thoi_han_bh: int = 24
    ngay_bat_dau: str = ""
    ngay_ket_thuc: str = ""
    pham_vi: str = ""
    trang_thai: str = "con_hieu_luc"


@dataclass
class NhaCungCap(BaseEntity):
    """Nhà cung cấp entity."""

    ma_ncc: str = ""
    ten_ncc: str = ""
    dia_chi: str = ""
    so_dien_thoai: str = ""
    email: str = ""
    nguoi_lien_he: str = ""
    diem_chat_luong: int = 0
    diem_thoi_gian_giao: int = 0
    diem_gia_ca: int = 0
    diem_tong: int = 0


@dataclass
class TraGop(BaseEntity):
    """Trả góp entity."""

    hop_dong_id: int = 0
    ngan_hang: str = ""
    so_tien_vay: int = 0
    lai_suat_nam: float = 0.0
    so_ky: int = 0
    so_tien_tra_thang: int = 0


@dataclass
class ChienDichMk(BaseEntity):
    """Chiến dịch marketing entity."""

    ten_chien_dich: str = ""
    kenh_tiep_thi: str = ""
    ngay_bat_dau: str = ""
    ngay_ket_thuc: str = ""
    ngan_sach: int = 0
    muc_tieu: str = ""
    so_luong_lead_muc_tieu: int = 0
    trang_thai: str = "nhap"


@dataclass
class Lead(BaseEntity):
    """Lead marketing entity."""

    chien_dich_id: Optional[int] = None
    ho_ten: str = ""
    so_dien_thoai: str = ""
    email: str = ""
    nguon: str = ""
    nhu_cau: str = ""
    nhan_vien_phu_trach_id: Optional[int] = None
    trang_thai: str = "moi"
    khach_hang_id: Optional[int] = None
    ghi_chu: str = ""


@dataclass
class KhieuNai(BaseEntity):
    """Khiếu nại entity."""

    khach_hang_id: int = 0
    hop_dong_id: Optional[int] = None
    nhan_vien_xu_ly_id: Optional[int] = None
    tieu_de: str = ""
    noi_dung: str = ""
    muc_do: str = "trung_binh"
    nguon_goc: str = "khac"
    trang_thai: str = "moi"
    ngay_xu_ly: Optional[str] = None
    ngay_dong: Optional[str] = None
    danh_gia_hai_long: Optional[int] = None
    ly_do: Optional[str] = None


@dataclass
class AuditLog(BaseEntity):
    """Audit log entity."""

    nhan_vien_id: Optional[int] = None
    hanh_dong: str = ""
    bang_anh_huong: Optional[str] = None
    ban_ghi_id: Optional[int] = None
    noi_dung: Optional[str] = None
    thoi_gian: Optional[str] = None


@dataclass
class SystemSettings(BaseEntity):
    """System settings entity."""

    ma_settings: str = ""
    gia_tri: str = ""
    mo_ta: str = ""
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None


@dataclass
class BaoDuong(BaseEntity):
    """Bảo dưỡng entity."""

    khach_hang_id: int = 0
    xe_id: int = 0
    nhan_vien_id: Optional[int] = None
    ngay_du_kien: str = ""
    ngay_thuc_te: Optional[str] = None
    km_xe: int = 0
    noi_dung: str = ""
    chi_phi: int = 0
    trang_thai: str = "cho_xac_nhan"
    ghi_chu: str = ""


@dataclass
class CuuHo(BaseEntity):
    """Cứu hộ entity."""

    khach_hang_id: int = 0
    xe_id: int = 0
    nhan_vien_id: Optional[int] = None
    vi_tri: str = ""
    mo_ta: str = ""
    thoi_gian_xu_ly: Optional[str] = None
    trang_thai: str = "tiep_nhan"
    chi_phi: int = 0
    ghi_chu: str = ""