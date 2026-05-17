"""Migration 030: Fix nha_cung_cap score constraints.

The CHECK constraints on diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca
were written as BETWEEN 1 AND 5 but DEFAULT is 0, which violates the constraint.
Fix to allow 0 as a valid value.
"""

from app.shared.logger import logger
import sqlite3


def run(conn):
    """Execute migration 030."""
    cursor = conn.cursor()

    # Get all view names
    view_names = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    for row in cursor.fetchall():
        view_names.append(row[0])

    # Drop all views (ignore errors)
    for view_name in view_names:
        try:
            cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
        except Exception as e:
            logger.warning(f"Could not drop view {view_name}: {e}")

    # Now do the table rename
    # Check if nha_cung_cap exists before renaming
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nha_cung_cap'")
    if not cursor.fetchone():
        logger.info("Migration 030: nha_cung_cap table not found, skipping (already migrated)")
        return

    cursor.execute("DROP TABLE IF EXISTS nha_cung_cap_old")
    cursor.execute("ALTER TABLE nha_cung_cap RENAME TO nha_cung_cap_old")

    # Create new table with corrected constraints (0-5 range, not 1-5)
    cursor.execute("""
        CREATE TABLE nha_cung_cap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_ncc TEXT UNIQUE NOT NULL,
            ten_ncc TEXT NOT NULL,
            dia_chi TEXT,
            so_dien_thoai TEXT,
            email TEXT,
            nguoi_lien_he TEXT,
            diem_chat_luong INTEGER DEFAULT 0 CHECK (diem_chat_luong BETWEEN 0 AND 5),
            diem_thoi_gian_giao INTEGER DEFAULT 0 CHECK (diem_thoi_gian_giao BETWEEN 0 AND 5),
            diem_gia_ca INTEGER DEFAULT 0 CHECK (diem_gia_ca BETWEEN 0 AND 5),
            diem_tong INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Copy data from old table (disable FK check for migration)
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.execute("""
        INSERT INTO nha_cung_cap (id, ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email,
            nguoi_lien_he, diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca,
            diem_tong, created_at, updated_at, created_by)
        SELECT id, ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email,
            nguoi_lien_he, diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca,
            diem_tong, created_at, updated_at, created_by
        FROM nha_cung_cap_old
    """)
    cursor.execute("PRAGMA foreign_keys=ON")

    # Drop old table
    cursor.execute("DROP TABLE nha_cung_cap_old")

    # Recreate indexes
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ncc_ma ON nha_cung_cap(ma_ncc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ncc_ten ON nha_cung_cap(ten_ncc)")

    logger.info("Migration 030: Fixed nha_cung_cap score constraints (0-5 range)")