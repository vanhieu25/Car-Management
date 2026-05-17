"""Migration 031: Add gia_tri_bh column to bao_hiem table.

Insurance value field for better tracking.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 031."""
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(bao_hiem)")
    columns = [row[1] for row in cursor.fetchall()]

    if "gia_tri_bh" not in columns:
        cursor.execute("ALTER TABLE bao_hiem ADD COLUMN gia_tri_bh INTEGER DEFAULT 0")
        logger.info("Migration 031: Added gia_tri_bh column to bao_hiem table")
    else:
        logger.info("Migration 031: gia_tri_bh column already exists in bao_hiem table")