"""Lead Repository - Sales Lead Repository."""

from typing import List, Optional, Dict, Any
import sqlite3


class LeadRepository:
    """Repository for lead operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn

    def create(self, data: Dict[str, Any]) -> int:
        """Create a new lead.
        
        Args:
            data: Lead data dict
            
        Returns:
            New lead ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO lead (
                chien_dich_id, ho_ten, so_dien_thoai, email, nguon, nhu_cau,
                nhan_vien_phu_trach_id, trang_thai, ghi_chu,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (
            data.get('chien_dich_id'),
            data['ho_ten'],
            data['so_dien_thoai'],
            data.get('email', ''),
            data.get('nguon', ''),
            data.get('nhu_cau', ''),
            data.get('nhan_vien_phu_trach_id'),
            data.get('trang_thai', 'moi'),
            data.get('ghi_chu', ''),
            data.get('created_by')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def find_by_id(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """Find lead by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM lead WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row, cursor.description)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Find all leads with pagination."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.*, cd.ten_chien_dich, nv.ho_ten as nhan_vien_ten
            FROM lead l
            LEFT JOIN chien_dich_mk cd ON l.chien_dich_id = cd.id
            LEFT JOIN nhan_vien nv ON l.nhan_vien_phu_trach_id = nv.id
            ORDER BY l.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return self._rows_to_list(cursor)

    def update(self, lead_id: int, data: Dict[str, Any]) -> bool:
        """Update lead."""
        cursor = self.conn.cursor()
        fields = []
        values = []
        for key in ['ho_ten', 'so_dien_thoai', 'email', 'nguon', 'nhu_cau',
                    'nhan_vien_phu_trach_id', 'trang_thai', 'khach_hang_id', 'ghi_chu']:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if not fields:
            return False
        
        values.append(lead_id)
        cursor.execute(
            f"UPDATE lead SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete(self, lead_id: int) -> bool:
        """Delete lead."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM lead WHERE id = ?", (lead_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def find_by_chien_dich(self, chien_dich_id: int) -> List[Dict[str, Any]]:
        """Find leads by campaign."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.*, nv.ho_ten as nhan_vien_ten
            FROM lead l
            LEFT JOIN nhan_vien nv ON l.nhan_vien_phu_trach_id = nv.id
            WHERE l.chien_dich_id = ?
            ORDER BY l.created_at DESC
        """, (chien_dich_id,))
        return self._rows_to_list(cursor)

    def find_by_status(self, trang_thai: str) -> List[Dict[str, Any]]:
        """Find leads by status."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.*, cd.ten_chien_dich, nv.ho_ten as nhan_vien_ten
            FROM lead l
            LEFT JOIN chien_dich_mk cd ON l.chien_dich_id = cd.id
            LEFT JOIN nhan_vien nv ON l.nhan_vien_phu_trach_id = nv.id
            WHERE l.trang_thai = ?
            ORDER BY l.created_at DESC
        """, (trang_thai,))
        return self._rows_to_list(cursor)

    def find_by_nv(self, nv_id: int) -> List[Dict[str, Any]]:
        """Find leads by assigned staff."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.*, cd.ten_chien_dich
            FROM lead l
            LEFT JOIN chien_dich_mk cd ON l.chien_dich_id = cd.id
            WHERE l.nhan_vien_phu_trach_id = ?
            ORDER BY l.created_at DESC
        """, (nv_id,))
        return self._rows_to_list(cursor)

    def find_by_phone(self, so_dien_thoai: str) -> Optional[Dict[str, Any]]:
        """Find lead by phone number."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM lead WHERE so_dien_thoai = ?", (so_dien_thoai,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row, cursor.description)
        return None

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """Search leads by keyword (name, phone, email)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT l.*, cd.ten_chien_dich, nv.ho_ten as nhan_vien_ten
            FROM lead l
            LEFT JOIN chien_dich_mk cd ON l.chien_dich_id = cd.id
            LEFT JOIN nhan_vien nv ON l.nhan_vien_phu_trach_id = nv.id
            WHERE l.ho_ten LIKE ? OR l.so_dien_thoai LIKE ? OR l.email LIKE ?
            ORDER BY l.created_at DESC
        """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        return self._rows_to_list(cursor)

    def count_by_status(self, trang_thai: str) -> int:
        """Count leads by status."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM lead WHERE trang_thai = ?", (trang_thai,))
        return cursor.fetchone()[0]

    def count_by_chien_dich(self, chien_dich_id: int) -> int:
        """Count leads by campaign."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM lead WHERE chien_dich_id = ?", (chien_dich_id,))
        return cursor.fetchone()[0]

    def count_converted_by_chien_dich(self, chien_dich_id: int) -> int:
        """Count converted leads by campaign."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM lead 
            WHERE chien_dich_id = ? AND trang_thai = 'chuyen_doi'
        """, (chien_dich_id,))
        return cursor.fetchone()[0]

    def count_all(self) -> int:
        """Count total leads."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM lead")
        return cursor.fetchone()[0]

    def _row_to_dict(self, row: tuple, description: tuple) -> Dict[str, Any]:
        """Convert row to dict."""
        return dict(zip([col[0] for col in description], row))

    def _rows_to_list(self, cursor) -> List[Dict[str, Any]]:
        """Convert cursor to list of dicts."""
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
