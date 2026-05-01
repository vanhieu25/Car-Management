"""Repositories module - data access layer."""

from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.nhan_vien_repository import NhanVienRepository
from app.infrastructure.repositories.xe_repository import XeRepository, XeSearchFilter
from app.infrastructure.repositories.khach_hang_repository import KhachHangRepository, KhachHangSearchFilter
from app.infrastructure.repositories.nhap_kho_repository import NhapKhoRepository
from app.infrastructure.repositories.hop_dong_repository import HopDongRepository, HopDongSearchFilter
from app.infrastructure.repositories.chien_dich_mk_repository import ChienDichMkRepository
from app.infrastructure.repositories.lead_repository import LeadRepository
from app.infrastructure.repositories.khieu_nai_repository import KhieuNaiRepository

__all__ = [
    "BaseRepository",
    "NhanVienRepository",
    "XeRepository",
    "XeSearchFilter",
    "KhachHangRepository",
    "KhachHangSearchFilter",
    "NhapKhoRepository",
    "HopDongRepository",
    "HopDongSearchFilter",
    "ChienDichMkRepository",
    "LeadRepository",
    "KhieuNaiRepository",
]
