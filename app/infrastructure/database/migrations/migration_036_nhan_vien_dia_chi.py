"""Migration 036 - Add dia_chi column to nhan_vien table.

This column stores employee address.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 036."""
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(nhan_vien)")
    columns = [row[1] for row in cursor.fetchall()]

    if "dia_chi" not in columns:
        cursor.execute("ALTER TABLE nhan_vien ADD COLUMN dia_chi TEXT")
        conn.commit()
        logger.info("Migration 036: Added dia_chi column to nhan_vien table")
    else:
        logger.info("Migration 036: dia_chi column already exists in nhan_vien table")