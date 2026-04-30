"""Migration 006: Create bao_hanh tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 006."""
    cursor = conn.cursor()

    # Create bao_hanh table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bao_hanh (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hop_dong_id INTEGER UNIQUE NOT NULL,
            xe_id INTEGER NOT NULL,
            khach_hang_id INTEGER NOT NULL,
            thoi_han_bh INTEGER NOT NULL,
            ngay_bat_dau TEXT NOT NULL,
            ngay_ket_thuc TEXT NOT NULL,
            pham_vi TEXT,
            trang_thai TEXT DEFAULT 'con_hieu_luc' CHECK (trang_thai IN ('con_hieu_luc', 'het_han')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (hop_dong_id) REFERENCES hop_dong(id),
            FOREIGN KEY (xe_id) REFERENCES xe(id),
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id),
            CHECK (ngay_ket_thuc >= ngay_bat_dau)
        )
    """)

    # Create bao_hanh_yeu_cau table (detailed repair requests)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bao_hanh_yeu_cau (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bao_hanh_id INTEGER NOT NULL,
            nhan_vien_id INTEGER NOT NULL,
            ngay_yeu_cau TEXT DEFAULT CURRENT_TIMESTAMP,
            mo_ta_tinh_trang TEXT NOT NULL,
            loai_yeu_cau TEXT NOT NULL CHECK (loai_yeu_cau IN ('bao_duong', 'sua_chua', 'thay_the')),
            chi_phi INTEGER DEFAULT 0 CHECK (chi_phi >= 0),
            trang_thai TEXT DEFAULT 'dang_xu_ly' CHECK (trang_thai IN ('moi', 'dang_xu_ly', 'da_hoan_thanh', 'da_dong')),
            ngay_hoan_thanh TEXT,
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (bao_hanh_id) REFERENCES bao_hanh(id),
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_hop_dong ON bao_hanh(hop_dong_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_xe ON bao_hanh(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_ngay_ket_thuc ON bao_hanh(ngay_ket_thuc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_trang_thai ON bao_hanh(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhyc_bao_hanh ON bao_hanh_yeu_cau(bao_hanh_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhyc_trang_thai ON bao_hanh_yeu_cau(trang_thai)")

    logger.info("Migration 006: bao_hanh tables created")