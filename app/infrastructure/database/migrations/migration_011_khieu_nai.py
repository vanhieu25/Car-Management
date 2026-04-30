"""Migration 011: Create khieu_nai table."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 011."""
    cursor = conn.cursor()

    # Create khieu_nai table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS khieu_nai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id INTEGER NOT NULL,
            hop_dong_id INTEGER,
            nhan_vien_xu_ly_id INTEGER,
            tieu_de TEXT NOT NULL,
            noi_dung TEXT NOT NULL,
            muc_do TEXT DEFAULT 'trung_binh' CHECK (muc_do IN ('thap', 'trung_binh', 'cao')),
            nguon_goc TEXT CHECK (nguon_goc IN ('chat_luong_xe', 'dich_vu', 'bao_hanh', 'khac')),
            trang_thai TEXT DEFAULT 'moi' CHECK (trang_thai IN ('moi', 'dang_xu_ly', 'da_giai_quyet', 'da_dong')),
            ngay_tao TEXT DEFAULT CURRENT_TIMESTAMP,
            ngay_xu_ly TEXT,
            ngay_dong TEXT,
            danh_gia_hai_long INTEGER CHECK (danh_gia_hai_long BETWEEN 1 AND 5),
            ly_do TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (hop_dong_id) REFERENCES hop_dong(id),
            FOREIGN KEY (nhan_vien_xu_ly_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kn_khach ON khieu_nai(khach_hang_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kn_hop_dong ON khieu_nai(hop_dong_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kn_nv_xu_ly ON khieu_nai(nhan_vien_xu_ly_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kn_trang_thai ON khieu_nai(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kn_muc_do ON khieu_nai(muc_do)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kn_ngay_tao ON khieu_nai(ngay_tao)")

    logger.info("Migration 011: khieu_nai table created")