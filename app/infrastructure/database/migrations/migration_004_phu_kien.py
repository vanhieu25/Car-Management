"""Migration 004: Create phu_kien and combo tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 004."""
    cursor = conn.cursor()

    # Create phu_kien table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phu_kien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_pk TEXT UNIQUE NOT NULL,
            ten_pk TEXT NOT NULL,
            phan_loai TEXT NOT NULL CHECK (phan_loai IN ('den', 'cam_bien', 'phu_kien_noi_that', 'phu_kien_ngoai_that', 'dung_cu')),
            gia_ban INTEGER NOT NULL CHECK (gia_ban >= 0),
            ton_kho INTEGER DEFAULT 0 CHECK (ton_kho >= 0),
            mo_ta TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create combo_phu_kien table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combo_phu_kien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_combo TEXT NOT NULL,
            he_so_giam REAL NOT NULL CHECK (he_so_giam > 0 AND he_so_giam <= 1),
            mo_ta TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create combo_chi_tiet junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combo_chi_tiet (
            combo_id INTEGER NOT NULL,
            phu_kien_id INTEGER NOT NULL,
            so_luong INTEGER DEFAULT 1 CHECK (so_luong >= 1),
            PRIMARY KEY (combo_id, phu_kien_id),
            FOREIGN KEY (combo_id) REFERENCES combo_phu_kien(id),
            FOREIGN KEY (phu_kien_id) REFERENCES phu_kien(id)
        )
    """)

    # Create indexes for phu_kien
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_pk_ma ON phu_kien(ma_pk)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pk_phan_loai ON phu_kien(phan_loai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pk_ton_kho ON phu_kien(ton_kho)")

    # Create indexes for combo_phu_kien
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_combo_ten ON combo_phu_kien(ten_combo)")

    logger.info("Migration 004: phu_kien and combo tables created")