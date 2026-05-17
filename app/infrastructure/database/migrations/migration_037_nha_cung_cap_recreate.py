"""Migration 037 - Recreate nha_cung_cap table.

After migration 030 failed mid-way, both nha_cung_cap and nha_cung_cap_old
were dropped. This migration recreates the table with correct constraints.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 037."""
    cursor = conn.cursor()

    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nha_cung_cap'")
    if cursor.fetchone():
        logger.info("Migration 037: nha_cung_cap table already exists")
        return

    cursor.execute("PRAGMA foreign_keys=OFF")

    # Create table with corrected constraints (0-5 range, 0 is valid)
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

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ncc_ma ON nha_cung_cap(ma_ncc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ncc_ten ON nha_cung_cap(ten_ncc)")

    cursor.execute("PRAGMA foreign_keys=ON")

    logger.info("Migration 037: Recreated nha_cung_cap table")