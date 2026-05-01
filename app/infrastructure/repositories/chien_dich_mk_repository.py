"""ChienDichMk Repository - Marketing Campaign Repository."""

from typing import List, Optional, Dict, Any
import sqlite3


class ChienDichMkRepository:
    """Repository for marketing campaign operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn

    def create(self, data: Dict[str, Any]) -> int:
        """Create a new campaign.
        
        Args:
            data: Campaign data dict
            
        Returns:
            New campaign ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO chien_dich_mk (
                ten_chien_dich, kenh_tiep_thi, ngay_bat_dau, ngay_ket_thuc,
                ngan_sach, muc_tieu, so_luong_lead_muc_tieu, trang_thai,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (
            data['ten_chien_dich'],
            data['kenh_tiep_thi'],
            data['ngay_bat_dau'],
            data['ngay_ket_thuc'],
            data.get('ngan_sach', 0),
            data.get('muc_tieu', ''),
            data.get('so_luong_lead_muc_tieu', 0),
            data.get('trang_thai', 'nhap'),
            data.get('created_by')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def find_by_id(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Find campaign by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chien_dich_mk WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row, cursor.description)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Find all campaigns with pagination."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chien_dich_mk 
            ORDER BY ngay_bat_dau DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return self._rows_to_list(cursor)

    def update(self, campaign_id: int, data: Dict[str, Any]) -> bool:
        """Update campaign."""
        cursor = self.conn.cursor()
        fields = []
        values = []
        for key in ['ten_chien_dich', 'kenh_tiep_thi', 'ngay_bat_dau', 'ngay_ket_thuc',
                    'ngan_sach', 'muc_tieu', 'so_luong_lead_muc_tieu', 'trang_thai']:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if not fields:
            return False
        
        values.append(campaign_id)
        cursor.execute(
            f"UPDATE chien_dich_mk SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete(self, campaign_id: int) -> bool:
        """Delete campaign (only if no leads associated)."""
        cursor = self.conn.cursor()
        # Check for leads
        cursor.execute("SELECT COUNT(*) FROM lead WHERE chien_dich_id = ?", (campaign_id,))
        if cursor.fetchone()[0] > 0:
            return False
        cursor.execute("DELETE FROM chien_dich_mk WHERE id = ?", (campaign_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def find_by_status(self, trang_thai: str) -> List[Dict[str, Any]]:
        """Find campaigns by status."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chien_dich_mk 
            WHERE trang_thai = ?
            ORDER BY ngay_bat_dau DESC
        """, (trang_thai,))
        return self._rows_to_list(cursor)

    def find_active(self) -> List[Dict[str, Any]]:
        """Find active campaigns (dang_chay and current date between start/end)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chien_dich_mk 
            WHERE trang_thai = 'dang_chay'
            AND date('now') BETWEEN ngay_bat_dau AND ngay_ket_thuc
            ORDER BY ngay_bat_dau DESC
        """)
        return self._rows_to_list(cursor)

    def find_by_date_range(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """Find campaigns within date range."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chien_dich_mk 
            WHERE ngay_bat_dau >= ? AND ngay_ket_thuc <= ?
            ORDER BY ngay_bat_dau DESC
        """, (from_date, to_date))
        return self._rows_to_list(cursor)

    def count_all(self) -> int:
        """Count total campaigns."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chien_dich_mk")
        return cursor.fetchone()[0]

    def count_by_status(self, trang_thai: str) -> int:
        """Count campaigns by status."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chien_dich_mk WHERE trang_thai = ?", (trang_thai,))
        return cursor.fetchone()[0]

    def _row_to_dict(self, row: tuple, description: tuple) -> Dict[str, Any]:
        """Convert row to dict."""
        return dict(zip([col[0] for col in description], row))

    def _rows_to_list(self, cursor) -> List[Dict[str, Any]]:
        """Convert cursor to list of dicts."""
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
