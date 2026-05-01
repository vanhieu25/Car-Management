"""Migration 019: Khiếu nại improvements for Sprint G5.3.

Changes:
- Add composite index for priority queries (BR-KN-03: KN cao ưu tiên)
- Add index for nguon_goc filtering
- Add composite index for (trang_thai, muc_do) filtering
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 019."""
    cursor = conn.cursor()

    # BR-KN-03: Composite index for priority queries
    # KN cấp 'cao' ưu tiên hiển thị đầu → query ORDER BY muc_do DESC, ngay_tao
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_kn_priority 
        ON khieu_nai(muc_do DESC, ngay_tao ASC)
    """)

    # Filter by nguon_goc (BR-KN-02: 4 nguồn gốc)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kn_nguon_goc ON khieu_nai(nguon_goc)")

    # Filter by trang_thai combined with muc_do (for list views)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_kn_status_muc_do 
        ON khieu_nai(trang_thai, muc_do)
    """)

    # Index for finding open complaints by customer
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_kn_kh_open 
        ON khieu_nai(khach_hang_id, trang_thai) 
        WHERE trang_thai IN ('moi', 'dang_xu_ly')
    """)

    # Index for NV assignment lookup
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_kn_nv_open 
        ON khieu_nai(nhan_vien_xu_ly_id, trang_thai) 
        WHERE trang_thai IN ('moi', 'dang_xu_ly')
    """)

    logger.info("Migration 019: khieu_nai improvements for G5.3 complete")
