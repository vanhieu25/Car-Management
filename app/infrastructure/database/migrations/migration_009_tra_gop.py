"""Migration 009: Create tra_gop tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 009."""
    cursor = conn.cursor()

    # Create tra_gop table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tra_gop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hop_dong_id INTEGER UNIQUE NOT NULL,
            ngan_hang TEXT NOT NULL,
            so_tien_vay INTEGER NOT NULL CHECK (so_tien_vay >= 0),
            lai_suat_nam REAL NOT NULL CHECK (lai_suat_nam >= 0 AND lai_suat_nam <= 30),
            so_ky INTEGER NOT NULL CHECK (so_ky >= 6 AND so_ky <= 84),
            so_tien_tra_thang INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (hop_dong_id) REFERENCES hop_dong(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create tra_gop_lich_su table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tra_gop_lich_su (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tra_gop_id INTEGER NOT NULL,
            ky_thu INTEGER NOT NULL,
            ngay_den_han TEXT NOT NULL,
            so_tien_phai_tra INTEGER NOT NULL,
            ngay_thuc_te TEXT,
            trang_thai TEXT DEFAULT 'chua_tra' CHECK (trang_thai IN ('chua_tra', 'da_tra', 'qua_han')),
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tra_gop_id) REFERENCES tra_gop(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tg_hop_dong ON tra_gop(hop_dong_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tg_ngan_hang ON tra_gop(ngan_hang)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tgls_tra_gop ON tra_gop_lich_su(tra_gop_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tgls_ngay_den_han ON tra_gop_lich_su(ngay_den_han)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tgls_trang_thai ON tra_gop_lich_su(trang_thai)")

    logger.info("Migration 009: tra_gop tables created")