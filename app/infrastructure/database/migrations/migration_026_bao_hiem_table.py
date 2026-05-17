"""Migration 026: Create bao_hiem table.

Table for tracking insurance policies linked to warranties.
Supports CASE 1 (sold by current dealership) and CASE 2 (sold by other dealership).
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 026."""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bao_hiem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bao_hanh_id INTEGER NOT NULL,
            loai_bh TEXT NOT NULL DEFAULT 'tnds'
                CHECK (loai_bh IN ('tnds', 'tai_nan', 'chao_no', 'that_lac', 'khac')),
            so_policy TEXT,
            ngay_mua TEXT NOT NULL,
            ngay_het_han TEXT NOT NULL,
            phi_bh INTEGER DEFAULT 0,
            dai_ly_ban_id INTEGER,
            trang_thai TEXT DEFAULT 'con_hieu_luc'
                CHECK (trang_thai IN ('con_hieu_luc', 'het_han', 'huy')),
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (bao_hanh_id) REFERENCES bao_hanh(id),
            FOREIGN KEY (dai_ly_ban_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)
    logger.info("Created bao_hiem table")

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhiem_bao_hanh ON bao_hiem(bao_hanh_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhiem_so_policy ON bao_hiem(so_policy)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhiem_dai_ly ON bao_hiem(dai_ly_ban_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhiem_ngay_het_han ON bao_hiem(ngay_het_han)")

    logger.info("Migration 026: bao_hiem table created")