"""KhieuNai Repository - Complaint/Feedback Repository."""

from typing import List, Optional, Dict, Any
import sqlite3


class KhieuNaiRepository:
    """Repository for complaint operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection."""
        self.conn = conn

    def create(self, data: Dict[str, Any]) -> int:
        """Create a new complaint.

        Args:
            data: Complaint data dict

        Returns:
            New complaint ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO khieu_nai (
                khach_hang_id, hop_dong_id, tieu_de, noi_dung,
                muc_do, nguon_goc, trang_thai, ly_do,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (
            data['khach_hang_id'],
            data.get('hop_dong_id'),
            data['tieu_de'],
            data['noi_dung'],
            data.get('muc_do', 'trung_binh'),
            data.get('nguon_goc'),
            data.get('trang_thai', 'moi'),
            data.get('ly_do', ''),
            data.get('created_by')
        ))
        self.conn.commit()
        return cursor.lastrowid

    def find_by_id(self, kn_id: int) -> Optional[Dict[str, Any]]:
        """Find complaint by ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT kn.*, 
                   kh.ho_ten as khach_hang_ten,
                   kh.so_dien_thoai as khach_hang_sdt,
                   nv.ho_ten as nhan_vien_xu_ly_ten,
                   hd.ma_hop_dong
            FROM khieu_nai kn
            LEFT JOIN khach_hang kh ON kn.khach_hang_id = kh.id
            LEFT JOIN nhan_vien nv ON kn.nhan_vien_xu_ly_id = nv.id
            LEFT JOIN hop_dong hd ON kn.hop_dong_id = hd.id
            WHERE kn.id = ?
        """, (kn_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row, cursor.description)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Find all complaints with pagination, ordered by priority (BR-KN-03)."""
        cursor = self.conn.cursor()
        # BR-KN-03: KN cấp 'cao' ưu tiên → ORDER BY muc_do DESC, ngay_tao
        cursor.execute("""
            SELECT kn.*,
                   kh.ho_ten as khach_hang_ten,
                   kh.so_dien_thoai as khach_hang_sdt,
                   nv.ho_ten as nhan_vien_xu_ly_ten,
                   hd.ma_hop_dong
            FROM khieu_nai kn
            LEFT JOIN khach_hang kh ON kn.khach_hang_id = kh.id
            LEFT JOIN nhan_vien nv ON kn.nhan_vien_xu_ly_id = nv.id
            LEFT JOIN hop_dong hd ON kn.hop_dong_id = hd.id
            ORDER BY 
                CASE kn.muc_do WHEN 'cao' THEN 1 WHEN 'trung_binh' THEN 2 WHEN 'thap' THEN 3 END,
                kn.ngay_tao DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return self._rows_to_list(cursor)

    def update(self, kn_id: int, data: Dict[str, Any]) -> bool:
        """Update complaint."""
        cursor = self.conn.cursor()
        fields = []
        values = []
        for key in ['tieu_de', 'noi_dung', 'muc_do', 'nguon_goc', 
                    'trang_thai', 'nhan_vien_xu_ly_id', 'ly_do',
                    'ngay_xu_ly', 'ngay_dong', 'danh_gia_hai_long']:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return False

        values.append(kn_id)
        cursor.execute(
            f"UPDATE khieu_nai SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete(self, kn_id: int) -> bool:
        """Delete complaint (only if status is 'moi')."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM khieu_nai WHERE id = ? AND trang_thai = 'moi'", (kn_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def find_by_status(self, trang_thai: str) -> List[Dict[str, Any]]:
        """Find complaints by status."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT kn.*,
                   kh.ho_ten as khach_hang_ten,
                   nv.ho_ten as nhan_vien_xu_ly_ten
            FROM khieu_nai kn
            LEFT JOIN khach_hang kh ON kn.khach_hang_id = kh.id
            LEFT JOIN nhan_vien nv ON kn.nhan_vien_xu_ly_id = nv.id
            WHERE kn.trang_thai = ?
            ORDER BY 
                CASE kn.muc_do WHEN 'cao' THEN 1 WHEN 'trung_binh' THEN 2 WHEN 'thap' THEN 3 END,
                kn.ngay_tao DESC
        """, (trang_thai,))
        return self._rows_to_list(cursor)

    def find_by_muc_do(self, muc_do: str) -> List[Dict[str, Any]]:
        """Find complaints by priority level."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT kn.*,
                   kh.ho_ten as khach_hang_ten,
                   nv.ho_ten as nhan_vien_xu_ly_ten
            FROM khieu_nai kn
            LEFT JOIN khach_hang kh ON kn.khach_hang_id = kh.id
            LEFT JOIN nhan_vien nv ON kn.nhan_vien_xu_ly_id = nv.id
            WHERE kn.muc_do = ?
            ORDER BY kn.ngay_tao DESC
        """, (muc_do,))
        return self._rows_to_list(cursor)

    def find_by_khach_hang(self, kh_id: int) -> List[Dict[str, Any]]:
        """Find complaints by customer."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM khieu_nai 
            WHERE khach_hang_id = ?
            ORDER BY ngay_tao DESC
        """, (kh_id,))
        return self._rows_to_list(cursor)

    def find_open_by_nv(self, nv_id: int) -> List[Dict[str, Any]]:
        """Find open (unresolved) complaints assigned to a staff."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT kn.*,
                   kh.ho_ten as khach_hang_ten,
                   hd.ma_hop_dong
            FROM khieu_nai kn
            LEFT JOIN khach_hang kh ON kn.khach_hang_id = kh.id
            LEFT JOIN hop_dong hd ON kn.hop_dong_id = hd.id
            WHERE kn.nhan_vien_xu_ly_id = ?
            AND kn.trang_thai IN ('moi', 'dang_xu_ly')
            ORDER BY 
                CASE kn.muc_do WHEN 'cao' THEN 1 WHEN 'trung_binh' THEN 2 WHEN 'thap' THEN 3 END,
                kn.ngay_tao ASC
        """, (nv_id,))
        return self._rows_to_list(cursor)

    def count_by_status(self, trang_thai: str) -> int:
        """Count complaints by status."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM khieu_nai WHERE trang_thai = ?", (trang_thai,))
        return cursor.fetchone()[0]

    def count_by_muc_do(self, muc_do: str) -> int:
        """Count complaints by priority."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM khieu_nai WHERE muc_do = ?", (muc_do,))
        return cursor.fetchone()[0]

    def count_all(self) -> int:
        """Count total complaints."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM khieu_nai")
        return cursor.fetchone()[0]

    def count_open(self) -> int:
        """Count open (unresolved) complaints."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM khieu_nai WHERE trang_thai IN ('moi', 'dang_xu_ly')")
        return cursor.fetchone()[0]

    def _row_to_dict(self, row: tuple, description: tuple) -> Dict[str, Any]:
        """Convert row to dict."""
        return dict(zip([col[0] for col in description], row))

    def _rows_to_list(self, cursor) -> List[Dict[str, Any]]:
        """Convert cursor to list of dicts."""
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
