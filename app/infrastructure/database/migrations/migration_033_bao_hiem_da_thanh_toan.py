"""Migration 033: Add da_thanh_toan to bao_hiem trang_thai CHECK constraint."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 033."""
    cursor = conn.cursor()

    # Cleanup leftover table from failed migration if exists
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.execute("DROP TABLE IF EXISTS bao_hiem_new")
    cursor.execute("PRAGMA foreign_keys=ON")

    # Check if already migrated - look at CHECK constraint values
    cursor.execute("PRAGMA table_info(bao_hiem)")
    cols = [row[1] for row in cursor.fetchall()]
    if "id" not in cols:
        logger.info("Migration 033: bao_hiem table not found, skipping")
        return

    # Recreate bao_hiem table with updated CHECK constraint
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bao_hiem_new (
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
                CHECK (trang_thai IN ('con_hieu_luc', 'het_han', 'huy', 'da_thanh_toan')),
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            cong_ty_bh_id INTEGER REFERENCES cong_ty_bh(id),
            ngay_hieu_luc TEXT,
            xe_id INTEGER REFERENCES xe(id),
            hop_dong_id INTEGER REFERENCES hop_dong(id),
            gia_tri_bh INTEGER DEFAULT 0,
            FOREIGN KEY (bao_hanh_id) REFERENCES bao_hanh(id),
            FOREIGN KEY (dai_ly_ban_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Copy data from old table (disable FK check for migration)
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.execute("""
        INSERT INTO bao_hiem_new (id, bao_hanh_id, loai_bh, so_policy, ngay_mua,
            ngay_het_han, phi_bh, dai_ly_ban_id, trang_thai, ghi_chu,
            created_at, updated_at, created_by, cong_ty_bh_id, ngay_hieu_luc,
            xe_id, hop_dong_id, gia_tri_bh)
        SELECT id, bao_hanh_id, loai_bh, so_policy, ngay_mua,
            ngay_het_han, phi_bh, dai_ly_ban_id, trang_thai, ghi_chu,
            created_at, updated_at, created_by, cong_ty_bh_id, ngay_hieu_luc,
            xe_id, hop_dong_id, gia_tri_bh
        FROM bao_hiem
    """)
    cursor.execute("PRAGMA foreign_keys=ON")

    # Drop old table and rename new
    cursor.execute("DROP TABLE bao_hiem")
    cursor.execute("ALTER TABLE bao_hiem_new RENAME TO bao_hiem")

    # Recreate indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bao_hiem_bao_hanh ON bao_hiem(bao_hanh_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bao_hiem_xe ON bao_hiem(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bao_hiem_trang_thai ON bao_hiem(trang_thai)")

    logger.info("Migration 033: Added da_thanh_toan to bao_hiem trang_thai CHECK constraint")