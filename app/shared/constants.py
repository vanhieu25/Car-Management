"""Shared constants for the Car Management application."""

from enum import Enum


# === VAI TRÒ NGƯỜI DÙNG ===
class VaiTro(str, Enum):
    """Vai trò người dùng trong hệ thống."""

    ADMIN = "admin"
    SALES = "sales"
    KY_THUAT_BH = "ky_thuat_bh"


# === TRẠNG THÁI HỢP ĐỒNG ===
class TrangThaiHopDong(str, Enum):
    """Trạng thái hợp đồng."""

    MOI_TAO = "moi_tao"
    DA_THANH_TOAN = "da_thanh_toan"
    DA_GIAO_XE = "da_giao_xe"
    HUY = "huy"


# === TRẠNG THÁI XE ===
class TrangThaiXe(str, Enum):
    """Trạng thái xe trong kho."""

    CON_HANG = "con_hang"
    DA_BAN = "da_ban"
    SAP_VE = "sap_ve"


# === TRẠNG THÁI KHUYẾN MÃI ===
class TrangThaiKhuyenMai(str, Enum):
    """Trạng thái khuyến mãi."""

    NHAP = "nhap"
    DANG_CHAY = "dang_chay"
    TAM_DUNG = "tam_dung"
    KET_THUC = "ket_thuc"


# === LOẠI KHUYẾN MÃI ===
class LoaiKhuyenMai(str, Enum):
    """Loại khuyến mãi."""

    GIAM_TIEN_MAT = "giam_tien_mat"
    GIAM_PHAN_TRAM = "giam_phan_tram"
    TANG_PHU_KIEN = "tang_phu_kien"
    GIAM_LAI_SUAT = "giam_lai_suat"
    COMBO = "combo"


# === TRẠNG THÁI BẢO HÀNH ===
class TrangThaiBaoHanh(str, Enum):
    """Trạng thái bảo hành."""

    MOI = "moi"
    DANG_XU_LY = "dang_xu_ly"
    DA_HOAN_THANH = "da_hoan_thanh"
    DA_DONG = "da_dong"


# === TRẠNG THÁI KHIẾU NẠI ===
class TrangThaiKhieuNai(str, Enum):
    """Trạng thái khiếu nại."""

    MOI = "moi"
    DANG_XU_LY = "dang_xu_ly"
    DA_GIAI_QUYET = "da_giai_quyet"
    DA_DONG = "da_dong"


# === MỨC ĐỘ KHIẾU NẠI ===
class MucDoKhieuNai(str, Enum):
    """Mức độ khiếu nại."""

    THAP = "thap"
    TRUNG_BINH = "trung_binh"
    CAO = "cao"


# === TRẠNG THÁI LEAD MARKETING ===
class TrangThaiLead(str, Enum):
    """Trạng thái lead marketing."""

    MOI = "moi"
    DANG_CHAM_SOC = "dang_cham_soc"
    CHUYEN_DOI = "chuyen_doi"
    TU_CHOI = "tu_choi"


# === PHÂN LOẠI KHÁCH HÀNG ===
class PhanLoaiKhachHang(str, Enum):
    """Phân loại khách hàng."""

    THUONG = "thuong"
    THAN_THIET = "than_thiet"
    VIP = "vip"


# === TRẠNG THÁI TRẢ GÓP ===
class TrangThaiTraGop(str, Enum):
    """Trạng thái kỳ trả góp."""

    CHUA_TRA = "chua_tra"
    DA_TRA = "da_tra"
    QUA_HAN = "qua_han"


# === DATE/TIME FORMAT ===
DATE_FORMAT = "dd/MM/yyyy"
DATETIME_FORMAT = "dd/MM/yyyy HH:mm:ss"
ISO_DATE_FORMAT = "yyyy-MM-dd"
TIMEZONE = "Asia/Ho_Chi_Minh"

# === CURRENCY FORMAT ===
CURRENCY_SYMBOL = "đ"
CURRENCY_FORMAT = "{:,.0f}đ"  # e.g., 1,500,000đ


# === SESSION CONFIG ===
SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


# === PASSWORD REQUIREMENTS ===
PASSWORD_MIN_LENGTH = 8
BCRYPT_ROUNDS = 12


# === BUSINESS RULES ===
THOI_HAN_BAO_HANH_DEFAULT_MONTHS = 24
BAN_KINH_BAO_DUONG_KM = 5000
BENH_VIEN_KM = 5000


# === PAGINATION ===
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100