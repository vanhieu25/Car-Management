"""Migration 035 - Add da_thanh_toan column to hop_dong table.

This column tracks the total amount paid for a contract.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 035."""
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(hop_dong)")
    columns = [row[1] for row in cursor.fetchall()]

    if "da_thanh_toan" not in columns:
        cursor.execute(
            "ALTER TABLE hop_dong ADD COLUMN da_thanh_toan INTEGER DEFAULT 0"
        )
        conn.commit()
        logger.info("Migration 035: Added da_thanh_toan column to hop_dong table")
    else:
        logger.info("Migration 035: da_thanh_toan column already exists in hop_dong table")