"""Xe repository - vehicle data access layer.

Provides database operations for Xe entity with search capabilities.
"""

from dataclasses import dataclass
from typing import Optional, List, Any, Dict

import sqlite3

from app.domain.entities import Xe
from app.infrastructure.repositories.base_repository import BaseRepository


@dataclass
class XeSearchFilter:
    """Filter for vehicle search."""
    hang: Optional[str] = None
    dong_xe: Optional[str] = None
    nam_san_xuat_min: Optional[int] = None
    nam_san_xuat_max: Optional[int] = None
    gia_min: Optional[int] = None
    gia_max: Optional[int] = None
    mau_sac: Optional[str] = None
    trang_thai: Optional[str] = None
    keyword: Optional[str] = None
    low_stock_only: bool = False


class XeRepository(BaseRepository[Xe]):
    """Repository for Xe entity with search and specific queries."""
    
    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        super().__init__(conn, Xe)
    
    def find_by_ma_xe(self, ma_xe: str) -> Optional[Xe]:
        """Find a vehicle by its code.
        
        Args:
            ma_xe: Vehicle code to search for.
            
        Returns:
            Xe if found, None otherwise.
        """
        cursor = self.conn.execute(
            "SELECT * FROM xe WHERE ma_xe = ?",
            (ma_xe,)
        )
        row = cursor.fetchone()
        if row:
            return Xe.from_row(row)
        return None
    
    def exists_by_ma_xe(self, ma_xe: str, exclude_id: int = None) -> bool:
        """Check if ma_xe already exists.
        
        Args:
            ma_xe: Vehicle code to check.
            exclude_id: ID to exclude from check (for updates).
            
        Returns:
            True if exists, False otherwise.
        """
        if exclude_id:
            cursor = self.conn.execute(
                "SELECT 1 FROM xe WHERE ma_xe = ? AND id != ?",
                (ma_xe, exclude_id)
            )
        else:
            cursor = self.conn.execute(
                "SELECT 1 FROM xe WHERE ma_xe = ?",
                (ma_xe,)
            )
        return cursor.fetchone() is not None
    
    def search(self, filter: XeSearchFilter, limit: int = 100, offset: int = 0) -> List[Xe]:
        """Search vehicles with dynamic filters.
        
        Args:
            filter: XeSearchFilter with filter criteria.
            limit: Maximum results to return.
            offset: Offset for pagination.
            
        Returns:
            List of matching Xe entities.
        """
        conditions = []
        params = []
        
        if filter.hang:
            conditions.append("hang = ?")
            params.append(filter.hang)
        
        if filter.dong_xe:
            conditions.append("dong_xe = ?")
            params.append(filter.dong_xe)
        
        if filter.nam_san_xuat_min is not None:
            conditions.append("nam_san_xuat >= ?")
            params.append(filter.nam_san_xuat_min)
        
        if filter.nam_san_xuat_max is not None:
            conditions.append("nam_san_xuat <= ?")
            params.append(filter.nam_san_xuat_max)
        
        if filter.gia_min is not None:
            conditions.append("gia_ban >= ?")
            params.append(filter.gia_min)
        
        if filter.gia_max is not None:
            conditions.append("gia_ban <= ?")
            params.append(filter.gia_max)
        
        if filter.mau_sac:
            conditions.append("mau_sac = ?")
            params.append(filter.mau_sac)
        
        if filter.trang_thai:
            conditions.append("trang_thai = ?")
            params.append(filter.trang_thai)
        
        if filter.keyword:
            # BR-XE-07: keyword search on ma_xe, hang, dong_xe (case-insensitive, supports Vietnamese)
            keyword_pattern = f"%{filter.keyword}%"
            conditions.append("(ma_xe LIKE ? OR hang LIKE ? OR dong_xe LIKE ?)")
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
        if filter.low_stock_only:
            conditions.append("so_luong_ton <= muc_toi_thieu")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM xe 
            WHERE {where_clause}
            ORDER BY hang, dong_xe, nam_san_xuat DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor = self.conn.execute(query, params)
        return [Xe.from_row(row) for row in cursor.fetchall()]
    
    def count_search(self, filter: XeSearchFilter) -> int:
        """Count vehicles matching filter.
        
        Args:
            filter: XeSearchFilter with filter criteria.
            
        Returns:
            Count of matching vehicles.
        """
        conditions = []
        params = []
        
        if filter.hang:
            conditions.append("hang = ?")
            params.append(filter.hang)
        
        if filter.dong_xe:
            conditions.append("dong_xe = ?")
            params.append(filter.dong_xe)
        
        if filter.nam_san_xuat_min is not None:
            conditions.append("nam_san_xuat >= ?")
            params.append(filter.nam_san_xuat_min)
        
        if filter.nam_san_xuat_max is not None:
            conditions.append("nam_san_xuat <= ?")
            params.append(filter.nam_san_xuat_max)
        
        if filter.gia_min is not None:
            conditions.append("gia_ban >= ?")
            params.append(filter.gia_min)
        
        if filter.gia_max is not None:
            conditions.append("gia_ban <= ?")
            params.append(filter.gia_max)
        
        if filter.mau_sac:
            conditions.append("mau_sac = ?")
            params.append(filter.mau_sac)
        
        if filter.trang_thai:
            conditions.append("trang_thai = ?")
            params.append(filter.trang_thai)
        
        if filter.keyword:
            keyword_pattern = f"%{filter.keyword}%"
            conditions.append("(ma_xe LIKE ? OR hang LIKE ? OR dong_xe LIKE ?)")
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
        if filter.low_stock_only:
            conditions.append("so_luong_ton <= muc_toi_thieu")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM xe WHERE {where_clause}",
            params
        )
        return cursor.fetchone()[0]
    
    def find_low_stock(self, limit: int = 50) -> List[Xe]:
        """Find vehicles with stock below minimum threshold.
        
        Args:
            limit: Maximum number of results.
            
        Returns:
            List of low stock Xe entities.
        """
        cursor = self.conn.execute(
            """SELECT * FROM xe 
               WHERE so_luong_ton <= muc_toi_thieu AND trang_thai != 'da_ban'
               ORDER BY so_luong_ton ASC
               LIMIT ?""",
            (limit,)
        )
        return [Xe.from_row(row) for row in cursor.fetchall()]
    
    def find_by_hang(self, hang: str, limit: int = 100) -> List[Xe]:
        """Find all vehicles of a brand.
        
        Args:
            hang: Brand name.
            limit: Maximum results.
            
        Returns:
            List of Xe entities.
        """
        cursor = self.conn.execute(
            """SELECT * FROM xe WHERE hang = ?
               ORDER BY dong_xe, nam_san_xuat DESC
               LIMIT ?""",
            (hang, limit)
        )
        return [Xe.from_row(row) for row in cursor.fetchall()]
    
    def get_distinct_hangs(self) -> List[str]:
        """Get list of distinct vehicle brands.
        
        Returns:
            List of brand names.
        """
        cursor = self.conn.execute(
            "SELECT DISTINCT hang FROM xe ORDER BY hang"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_distinct_dong_xe_by_hang(self, hang: str) -> List[str]:
        """Get list of distinct models for a brand.
        
        Args:
            hang: Brand name.
            
        Returns:
            List of model names.
        """
        cursor = self.conn.execute(
            "SELECT DISTINCT dong_xe FROM xe WHERE hang = ? ORDER BY dong_xe",
            (hang,)
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_distinct_mau_sac(self) -> List[str]:
        """Get list of distinct colors.
        
        Returns:
            List of color values.
        """
        cursor = self.conn.execute(
            "SELECT DISTINCT mau_sac FROM xe WHERE mau_sac IS NOT NULL AND mau_sac != '' ORDER BY mau_sac"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def has_active_contracts(self, xe_id: int) -> bool:
        """Check if vehicle has active (non-cancelled) contracts.
        
        BR-REF-01: Cannot delete vehicle if it has active contracts.
        
        Args:
            xe_id: Vehicle ID to check.
            
        Returns:
            True if has active contracts, False otherwise.
        """
        cursor = self.conn.execute(
            """SELECT 1 FROM hop_dong WHERE xe_id = ? AND trang_thai != 'huy' LIMIT 1""",
            (xe_id,)
        )
        return cursor.fetchone() is not None
    
    def update_stock(self, xe_id: int, new_stock: int) -> None:
        """Update stock quantity for a vehicle.
        
        Args:
            xe_id: Vehicle ID.
            new_stock: New stock quantity.
        """
        from datetime import datetime
        self.conn.execute(
            """UPDATE xe SET so_luong_ton = ?, updated_at = ? WHERE id = ?""",
            (new_stock, datetime.now().isoformat(), xe_id)
        )
        self.conn.commit()
    
    def adjust_stock(self, xe_id: int, delta: int) -> int:
        """Adjust stock by a delta value.
        
        BR-XE-04: When stock reaches 0 with active contracts, status → da_ban.
        BR-XE-05: When stock increases from 0 for da_ban vehicle, status → con_hang.
        
        Args:
            xe_id: Vehicle ID.
            delta: Amount to adjust (positive = add, negative = subtract).
            
        Returns:
            New stock level after adjustment.
        """
        from datetime import datetime
        
        # Get current vehicle
        xe = self.find_by_id(xe_id)
        if not xe:
            raise ValueError(f"Vehicle {xe_id} not found")
        
        new_stock = max(0, xe.so_luong_ton + delta)
        old_stock = xe.so_luong_ton
        
        # Update stock
        self.conn.execute(
            """UPDATE xe SET so_luong_ton = ?, updated_at = ? WHERE id = ?""",
            (new_stock, datetime.now().isoformat(), xe_id)
        )
        
        # BR-XE-05: Stock increased from 0 for da_ban vehicle → con_hang
        if old_stock == 0 and new_stock > 0 and xe.trang_thai == "da_ban":
            self.conn.execute(
                """UPDATE xe SET trang_thai = 'con_hang', updated_at = ? WHERE id = ?""",
                (datetime.now().isoformat(), xe_id)
            )
        
        self.conn.commit()
        
        return new_stock
    
    def update_status(self, xe_id: int, new_status: str) -> None:
        """Update vehicle status.
        
        Args:
            xe_id: Vehicle ID.
            new_status: New status value.
        """
        from datetime import datetime
        self.conn.execute(
            """UPDATE xe SET trang_thai = ?, updated_at = ? WHERE id = ?""",
            (new_status, datetime.now().isoformat(), xe_id)
        )
        self.conn.commit()
