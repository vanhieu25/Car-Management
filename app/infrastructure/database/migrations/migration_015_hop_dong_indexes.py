"""Migration 015: Add hop_dong composite indexes for reporting and filtering."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 015."""
    cursor = conn.cursor()

    # Composite index for common query patterns on hop_dong
    # Supports filtering by: trang_thai + ngay_tao, trang_thai + nhan_vien_id, etc.
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_hop_dong_ngay_trang_thai "
        "ON hop_dong(ngay_tao, trang_thai)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_hop_dong_trang_thai_nv "
        "ON hop_dong(trang_thai, nhan_vien_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_hop_dong_khach_hang "
        "ON hop_dong(khach_hang_id)"
    )
    # Note: idx_hd_nv_ngay already exists in migration_013 (idx_hd_nv_ngay ON hop_dong(nhan_vien_id, ngay_tao))
    # We add the reverse-order index for different query patterns
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_hop_dong_ngay_nv "
        "ON hop_dong(ngay_tao, nhan_vien_id)"
    )

    logger.info("Migration 015: hop_dong composite indexes created")
