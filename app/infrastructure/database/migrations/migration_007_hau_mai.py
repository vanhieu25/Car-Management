"""Migration 007: Create hau_mai tables (bao_duong, cuu_ho)."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 007."""
    cursor = conn.cursor()

    # Create bao_duong table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bao_duong (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id INTEGER NOT NULL,
            xe_id INTEGER NOT NULL,
            nhan_vien_id INTEGER,
            ngay_du_kien TEXT NOT NULL,
            ngay_thuc_te TEXT,
            km_xe INTEGER CHECK (km_xe >= 0),
            noi_dung TEXT,
            chi_phi INTEGER DEFAULT 0 CHECK (chi_phi >= 0),
            trang_thai TEXT DEFAULT 'cho_xac_nhan' CHECK (trang_thai IN ('cho_xac_nhan', 'da_xac_nhan', 'dang_thuc_hien', 'da_hoan_thanh', 'huy')),
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (xe_id) REFERENCES xe(id),
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create cuu_ho table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuu_ho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id INTEGER NOT NULL,
            xe_id INTEGER NOT NULL,
            nhan_vien_id INTEGER,
            vi_tri TEXT NOT NULL,
            mo_ta TEXT,
            thoi_gian_yeu_cau TEXT DEFAULT CURRENT_TIMESTAMP,
            thoi_gian_xu_ly TEXT,
            trang_thai TEXT DEFAULT 'tiep_nhan' CHECK (trang_thai IN ('tiep_nhan', 'dang_xu_ly', 'hoan_thanh')),
            chi_phi INTEGER DEFAULT 0 CHECK (chi_phi >= 0),
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (xe_id) REFERENCES xe(id),
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bd_khach ON bao_duong(khach_hang_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bd_xe ON bao_duong(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bd_ngay ON bao_duong(ngay_du_kien)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bd_trang_thai ON bao_duong(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ch_khach ON cuu_ho(khach_hang_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ch_xe ON cuu_ho(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ch_trang_thai ON cuu_ho(trang_thai)")

    logger.info("Migration 007: bao_duong and cuu_ho tables created")