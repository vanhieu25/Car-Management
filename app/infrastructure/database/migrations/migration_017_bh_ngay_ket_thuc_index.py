"""Migration 017: Add single-column index on bao_hanh.ngay_ket_thuc.

This supports BR-BH-03: cảnh báo BH sắp hết hạn trước 30 ngày.
Query pattern: SELECT * FROM bao_hanh WHERE ngay_ket_thuc BETWEEN ? AND ?

Note: A composite index idx_bh_ngay_ket_thuc_trang_thai(ngay_ket_thuc, trang_thai)
already exists in migration_013. This single-column index is added for queries
that filter only by ngay_ket_thuc (without trang_thai), providing targeted
performance for dashboard warranty expiration alerts.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 017."""
    cursor = conn.cursor()

    # Single-column index for ngay_ket_thuc queries
    # Supports: WHERE ngay_ket_thuc BETWEEN date('now') AND date('now', '+30 days')
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_bh_ngay_ket_thuc "
        "ON bao_hanh(ngay_ket_thuc)"
    )

    logger.info("Migration 017: bao_hanh.ngay_ket_thuc single-column index created")