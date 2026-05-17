"""Migration 034: Add trang_thai column to khach_hang table.

This column is needed for soft-delete functionality when customers have active contracts.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 034."""
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute("PRAGMA table_info(khach_hang)")
    columns = [row[1] for row in cursor.fetchall()]

    if "trang_thai" not in columns:
        cursor.execute(
            "ALTER TABLE khach_hang ADD COLUMN trang_thai TEXT DEFAULT 'active' CHECK(trang_thai IN ('active', 'inactive'))"
        )
        conn.commit()
        logger.info("Migration 034: Added trang_thai column to khach_hang table")
    else:
        logger.info("Migration 034: trang_thai column already exists in khach_hang table")