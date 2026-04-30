"""KhachHang repository - customer data access layer.

Provides database operations for KhachHang entity with search capabilities.
"""

from dataclasses import dataclass
from typing import Optional, List, Any

import sqlite3

from app.domain.entities import KhachHang
from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class KhachHangSearchFilter:
    """Filter for customer search."""
    keyword: Optional[str] = None  # Search in name, phone, email
    phan_loai: Optional[str] = None  # Thuong, Than_thiet, VIP
    from_birthday_days: Optional[int] = None  # Birthday within N days


class KhachHangRepository(BaseRepository[KhachHang]):
    """Repository for KhachHang entity with search and specific queries."""
    
    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, KhachHang)
    
    def find_by_phone(self, phone: str) -> Optional[KhachHang]:
        """Find a customer by phone number.
        
        Args:
            phone: Phone number to search for.
            
        Returns:
            KhachHang if found, None otherwise.
        """
        # Remove spaces and dashes for search
        phone_clean = phone.strip().replace(" ", "").replace("-", "")
        
        cursor = self.conn.execute(
            "SELECT * FROM khach_hang WHERE so_dien_thoai = ?",
            (phone_clean,)
        )
        row = cursor.fetchone()
        if row:
            return KhachHang.from_row(row)
        return None
    
    def find_by_email(self, email: str) -> Optional[KhachHang]:
        """Find a customer by email.
        
        Args:
            email: Email address to search for.
            
        Returns:
            KhachHang if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM khach_hang WHERE email = ?",
            (email,)
        )
        row = cursor.fetchone()
        if row:
            return KhachHang.from_row(row)
        return None
    
    def exists_by_phone(self, phone: str, exclude_id: int = None) -> bool:
        """Check if phone already exists.
        
        Args:
            phone: Phone number to check.
            exclude_id: Customer ID to exclude from check (for updates).
            
        Returns:
            True if exists, False otherwise.
        """
        phone_clean = phone.strip().replace(" ", "").replace("-", "")
        
        if exclude_id:
            cursor = self.conn.execute(
                "SELECT 1 FROM khach_hang WHERE so_dien_thoai = ? AND id != ?",
                (phone_clean, exclude_id)
            )
        else:
            cursor = self.conn.execute(
                "SELECT 1 FROM khach_hang WHERE so_dien_thoai = ?",
                (phone_clean,)
            )
        return cursor.fetchone() is not None
    
    def exists_by_email(self, email: str, exclude_id: int = None) -> bool:
        """Check if email already exists.
        
        Args:
            email: Email to check.
            exclude_id: Customer ID to exclude from check (for updates).
            
        Returns:
            True if exists, False otherwise.
        """
        if exclude_id:
            cursor = self.conn.execute(
                "SELECT 1 FROM khach_hang WHERE email = ? AND id != ?",
                (email, exclude_id)
            )
        else:
            cursor = self.conn.execute(
                "SELECT 1 FROM khach_hang WHERE email = ?",
                (email,)
            )
        return cursor.fetchone() is not None
    
    def search(
        self,
        filter: KhachHangSearchFilter,
        limit: int = 100,
        offset: int = 0,
    ) -> List[KhachHang]:
        """Search customers with dynamic filters.
        
        Args:
            filter: KhachHangSearchFilter with filter criteria.
            limit: Maximum results to return.
            offset: Offset for pagination.
            
        Returns:
            List of matching KhachHang entities.
        """
        conditions = []
        params = []
        
        if filter.keyword:
            keyword_pattern = f"%{filter.keyword}%"
            conditions.append(
                "(ho_ten LIKE ? OR so_dien_thoai LIKE ? OR email LIKE ?)"
            )
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
        if filter.phan_loai:
            conditions.append("phan_loai = ?")
            params.append(filter.phan_loai)
        
        if filter.from_birthday_days is not None:
            # Find customers with birthday within N days from today
            from datetime import datetime, timedelta
            
            today = datetime.now()
            
            # Calculate date range
            target_dates = []
            for i in range(-filter.from_birthday_days, filter.from_birthday_days + 1):
                target_date = today + timedelta(days=i)
                target_dates.append(target_date.strftime("%m-%d"))
            
            # Create conditions for each possible date
            birthday_conditions = " OR ".join(
                ["SUBSTR(ngay_sinh, 6, 5) = ?" for _ in target_dates]
            )
            conditions.append(f"({birthday_conditions})")
            params.extend(target_dates)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM khach_hang 
            WHERE {where_clause}
            ORDER BY ho_ten
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor = self.conn.execute(query, params)
        return [KhachHang.from_row(row) for row in cursor.fetchall()]
    
    def count_search(self, filter: KhachHangSearchFilter) -> int:
        """Count customers matching filter.
        
        Args:
            filter: KhachHangSearchFilter with filter criteria.
            
        Returns:
            Count of matching customers.
        """
        conditions = []
        params = []
        
        if filter.keyword:
            keyword_pattern = f"%{filter.keyword}%"
            conditions.append(
                "(ho_ten LIKE ? OR so_dien_thoai LIKE ? OR email LIKE ?)"
            )
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
        if filter.phan_loai:
            conditions.append("phan_loai = ?")
            params.append(filter.phan_loai)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM khach_hang WHERE {where_clause}",
            params
        )
        return cursor.fetchone()[0]
    
    def find_birthday_window(self, days: int = 7) -> List[KhachHang]:
        """Find customers with birthday within N days window.
        
        Args:
            days: Number of days before and after today to search.
            
        Returns:
            List of KhachHang with upcoming birthdays.
        """
        filter = KhachHangSearchFilter(from_birthday_days=days)
        return self.search(filter)
    
    def has_active_contracts(self, khach_hang_id: int) -> bool:
        """Check if customer has active (non-cancelled) contracts.
        
        BR-REF-03: Cannot delete customer if has active contracts.
        
        Args:
            khach_hang_id: Customer ID to check.
            
        Returns:
            True if has active contracts, False otherwise.
        """
        cursor = self.conn.execute(
            """SELECT 1 FROM hop_dong WHERE khach_hang_id = ? AND trang_thai != 'huy' LIMIT 1""",
            (khach_hang_id,)
        )
        return cursor.fetchone() is not None
    
    def update_purchase_stats(
        self,
        khach_hang_id: int,
        tong_gia_tri_mua: int,
        so_xe_da_mua: int,
    ) -> None:
        """Update customer's purchase statistics.
        
        Called after contract is completed (da_giao_xe) to update
        tong_gia_tri_mua and so_xe_da_mua.
        
        Args:
            khach_hang_id: Customer ID.
            tong_gia_tri_mua: New total purchase value.
            so_xe_da_mua: New number of purchased vehicles.
        """
        from datetime import datetime
        
        self.conn.execute(
            """UPDATE khach_hang 
               SET tong_gia_tri_mua = ?, so_xe_da_mua = ?, updated_at = ?
               WHERE id = ?""",
            (tong_gia_tri_mua, so_xe_da_mua, datetime.now().isoformat(), khach_hang_id)
        )
        self.conn.commit()
    
    def update_classification(self, khach_hang_id: int, phan_loai: str) -> None:
        """Update customer's classification.
        
        Args:
            khach_hang_id: Customer ID.
            phan_loai: New classification (Thuong, Than_thiet, VIP).
        """
        from datetime import datetime
        
        self.conn.execute(
            """UPDATE khach_hang SET phan_loai = ?, updated_at = ? WHERE id = ?""",
            (phan_loai, datetime.now().isoformat(), khach_hang_id)
        )
        self.conn.commit()
    
    def get_purchase_history(self, khach_hang_id: int) -> dict:
        """Get customer's purchase history including contracts, warranties, complaints.
        
        Args:
            khach_hang_id: Customer ID.
            
        Returns:
            Dict with lists of contracts, warranties, complaints.
        """
        # Get contracts
        cursor = self.conn.execute(
            """SELECT hd.*, xe.ma_xe, xe.hang, xe.dong_xe
               FROM hop_dong hd
               JOIN xe ON hd.xe_id = xe.id
               WHERE hd.khach_hang_id = ?
               ORDER BY hd.ngay_tao DESC""",
            (khach_hang_id,)
        )
        contracts = []
        for row in cursor.fetchall():
            contracts.append(dict(row))
        
        # Get warranties
        cursor = self.conn.execute(
            """SELECT bh.*, xe.ma_xe
               FROM bao_hanh bh
               JOIN xe ON bh.xe_id = xe.id
               WHERE bh.khach_hang_id = ?
               ORDER BY bh.ngay_bat_dau DESC""",
            (khach_hang_id,)
        )
        warranties = []
        for row in cursor.fetchall():
            warranties.append(dict(row))
        
        # Get complaints
        cursor = self.conn.execute(
            """SELECT * FROM khieu_nai
               WHERE khach_hang_id = ?
               ORDER BY ngay_tao DESC""",
            (khach_hang_id,)
        )
        complaints = []
        for row in cursor.fetchall():
            complaints.append(dict(row))
        
        return {
            "contracts": contracts,
            "warranties": warranties,
            "complaints": complaints,
        }
