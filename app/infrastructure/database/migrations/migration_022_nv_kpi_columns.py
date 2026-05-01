"""Migration 022: Add so_hop_dong and doanh_thu columns to nhan_vien table.

These columns track employee KPI and are updated by hop_dong_service when
contracts are delivered (set_delivered).
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 022."""
    cursor = conn.cursor()

    # Add so_hop_dong column (number of contracts sold by this NV)
    cursor.execute("""
        ALTER TABLE nhan_vien
        ADD COLUMN so_hop_dong INTEGER DEFAULT 0
    """)

    # Add doanh_thu column (total revenue from contracts)
    cursor.execute("""
        ALTER TABLE nhan_vien
        ADD COLUMN doanh_thu INTEGER DEFAULT 0
    """)

    logger.info("Migration 022: so_hop_dong and doanh_thu columns added to nhan_vien")