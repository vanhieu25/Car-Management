"""System settings service - load and manage system configuration.

Provides access to system settings stored in system_settings table.
Used by TopBar to display dealer name, logo, etc.
"""

from dataclasses import dataclass
from typing import Optional

import sqlite3


@dataclass
class SystemSettings:
    """System settings data class."""
    thoi_han_bh_default: int = 24  # Default warranty period in months
    muc_toi_thieu_ton_kho: int = 2  # Minimum stock threshold
    ten_dai_ly: str = "Đại lý xe hơi"  # Dealer name
    dia_chi_dai_ly: str = "Việt Nam"  # Dealer address
    so_dien_thoai_dai_ly: str = "0123456789"  # Dealer phone
    email_dai_ly: str = "contact@dailyxeco.vn"  # Dealer email
    logo_url: Optional[str] = None  # Logo URL/path
    version: str = "1.0.0"  # Application version


class SystemSettingsService:
    """Service for loading and managing system settings.
    
    Loads settings from the system_settings table.
    Caches settings for performance.
    """

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn
        self._cache: Optional[SystemSettings] = None

    def load_settings(self, force_reload: bool = False) -> SystemSettings:
        """Load all system settings.
        
        Args:
            force_reload: If True, bypass cache and reload from DB.
            
        Returns:
            SystemSettings object with all settings.
        """
        if self._cache is not None and not force_reload:
            return self._cache

        settings = SystemSettings()

        cursor = self.conn.execute(
            "SELECT ma_settings, gia_tri FROM system_settings"
        )
        for row in cursor.fetchall():
            ma_settings = row[0]
            gia_tri = row[1]

            if ma_settings == "thoi_han_bh_default":
                settings.thoi_han_bh_default = int(gia_tri)
            elif ma_settings == "muc_toi_thieu_ton_kho":
                settings.muc_toi_thieu_ton_kho = int(gia_tri)
            elif ma_settings == "ten_dai_ly":
                settings.ten_dai_ly = gia_tri
            elif ma_settings == "dia_chi_dai_ly":
                settings.dia_chi_dai_ly = gia_tri
            elif ma_settings == "so_dien_thoai_dai_ly":
                settings.so_dien_thoai_dai_ly = gia_tri
            elif ma_settings == "email_dai_ly":
                settings.email_dai_ly = gia_tri
            elif ma_settings == "logo_url":
                settings.logo_url = gia_tri
            elif ma_settings == "app_version":
                settings.version = gia_tri

        self._cache = settings
        return settings

    def get_setting(self, ma_settings: str) -> Optional[str]:
        """Get a single setting value.
        
        Args:
            ma_settings: Setting code.
            
        Returns:
            Setting value or None if not found.
        """
        cursor = self.conn.execute(
            "SELECT gia_tri FROM system_settings WHERE ma_settings = ?",
            (ma_settings,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def update_setting(
        self,
        ma_settings: str,
        gia_tri: str,
        updated_by: int = None,
    ) -> None:
        """Update a system setting.
        
        Args:
            ma_settings: Setting code.
            gia_tri: New value.
            updated_by: ID of user making the update.
        """
        from datetime import datetime

        now = datetime.now().isoformat()

        self.conn.execute(
            """UPDATE system_settings 
               SET gia_tri = ?, updated_at = ?, updated_by = ?
               WHERE ma_settings = ?""",
            (gia_tri, now, updated_by, ma_settings)
        )
        self.conn.commit()

        # Invalidate cache
        self._cache = None

    def get_warranty_months(self) -> int:
        """Get default warranty period in months."""
        settings = self.load_settings()
        return settings.thoi_han_bh_default

    def get_min_stock_threshold(self) -> int:
        """Get minimum stock threshold for low stock warnings."""
        settings = self.load_settings()
        return settings.muc_toi_thieu_ton_kho

    def get_dealer_info(self) -> dict:
        """Get dealer information for display.
        
        Returns:
            Dict with dealer name, address, phone, email.
        """
        settings = self.load_settings()
        return {
            "ten_dai_ly": settings.ten_dai_ly,
            "dia_chi": settings.dia_chi_dai_ly,
            "so_dien_thoai": settings.so_dien_thoai_dai_ly,
            "email": settings.email_dai_ly,
        }


# Global convenience function
def get_settings(conn: sqlite3.Connection) -> SystemSettings:
    """Get system settings using default service."""
    service = SystemSettingsService(conn)
    return service.load_settings()
