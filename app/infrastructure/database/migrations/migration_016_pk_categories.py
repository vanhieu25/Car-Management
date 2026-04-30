"""Migration 016: Update phu_kien.phan_loai categories to match BRD §5.6 (BR-PK-01).

Previous schema used: den, cam_bien, phu_kien_noi_that, phu_kien_ngoai_that, dung_cu
BRD §5.6 specifies: noi_that, ngoai_that, dien_tu, bao_ve, trang_tri

This migration updates the CHECK constraint to align with BRD.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 016."""
    cursor = conn.cursor()

    # Step 1: Drop the old CHECK constraint by recreating the table
    # SQLite doesn't support DROP CONSTRAINT directly, so we need to:
    # 1. Create new table with correct constraint
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table

    # Create temporary table with new constraint
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phu_kien_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_pk TEXT UNIQUE NOT NULL,
            ten_pk TEXT NOT NULL,
            phan_loai TEXT NOT NULL CHECK (phan_loai IN ('noi_that', 'ngoai_that', 'dien_tu', 'bao_ve', 'trang_tri')),
            gia_ban INTEGER NOT NULL CHECK (gia_ban >= 0),
            ton_kho INTEGER DEFAULT 0 CHECK (ton_kho >= 0),
            mo_ta TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Copy data from old table to new table
    cursor.execute("""
        INSERT INTO phu_kien_new (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta, created_at, updated_at, created_by)
        SELECT id, ma_pk, ten_pk, 
               CASE 
                   WHEN phan_loai = 'den' THEN 'trang_tri'
                   WHEN phan_loai = 'cam_bien' THEN 'dien_tu'
                   WHEN phan_loai = 'phu_kien_noi_that' THEN 'noi_that'
                   WHEN phan_loai = 'phu_kien_ngoai_that' THEN 'ngoai_that'
                   WHEN phan_loai = 'dung_cu' THEN 'bao_ve'
                   ELSE phan_loai
               END AS phan_loai,
               gia_ban, ton_kho, mo_ta, created_at, updated_at, created_by
        FROM phu_kien
    """)

    # Drop old table
    cursor.execute("DROP TABLE phu_kien")

    # Rename new table to original name
    cursor.execute("ALTER TABLE phu_kien_new RENAME TO phu_kien")

    # Recreate indexes
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pk_ma ON phu_kien(ma_pk)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pk_phan_loai ON phu_kien(phan_loai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pk_ton_kho ON phu_kien(ton_kho)")

    logger.info("Migration 016: phu_kien.phan_loai categories updated to BRD standard")