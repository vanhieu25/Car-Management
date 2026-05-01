"""Migration 018: Create indexes for tra_gop_lich_su (installment schedule).

Indexes on:
- tra_gop_lich_su.ngay_den_han: for TRG-07 queries (overdue by date range)
- tra_gop_lich_su.trang_thai: for filtering by status (chua_tra/da_tra/qua_han)

Note: These indexes are also covered by the composite index
idx_tgls_qua_han(trang_thai, ngay_den_han) from migration_013.
This migration adds the individual column indexes for explicit query patterns.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 018."""
    cursor = conn.cursor()

    # Index on ngay_den_han for date-range queries (TRG-07)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tgls_ngay_den_han_v2
        ON tra_gop_lich_su(ngay_den_han)
    """)

    # Index on trang_thai for filtering overdue payments
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tgls_trang_thai_v2
        ON tra_gop_lich_su(trang_thai)
    """)

    logger.info("Migration 018: tra_gop_lich_su indexes created")