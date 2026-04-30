"""Migration 003: Create hop_dong and hop_dong_phu_kien tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 003."""
    cursor = conn.cursor()

    # Create hop_dong table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hop_dong (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_hop_dong TEXT UNIQUE NOT NULL,
            khach_hang_id INTEGER NOT NULL,
            xe_id INTEGER NOT NULL,
            nhan_vien_id INTEGER NOT NULL,
            khuyen_mai_id INTEGER,
            gia_xe INTEGER NOT NULL,
            tong_gia_phu_kien INTEGER DEFAULT 0,
            tien_giam_km INTEGER DEFAULT 0,
            tong_tien INTEGER NOT NULL,
            trang_thai TEXT DEFAULT 'moi_tao' CHECK (trang_thai IN ('moi_tao', 'da_thanh_toan', 'da_giao_xe', 'huy')),
            ngay_tao TEXT DEFAULT CURRENT_TIMESTAMP,
            ngay_thanh_toan TEXT,
            ngay_giao_xe TEXT,
            ly_do_huy TEXT,
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (xe_id) REFERENCES xe(id),
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (khuyen_mai_id) REFERENCES khuyen_mai(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create hop_dong_phu_kien junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hop_dong_phu_kien (
            hop_dong_id INTEGER NOT NULL,
            phu_kien_id INTEGER NOT NULL,
            so_luong INTEGER DEFAULT 1 CHECK (so_luong >= 1),
            gia_ban INTEGER NOT NULL,
            PRIMARY KEY (hop_dong_id, phu_kien_id),
            FOREIGN KEY (hop_dong_id) REFERENCES hop_dong(id),
            FOREIGN KEY (phu_kien_id) REFERENCES phu_kien(id)
        )
    """)

    # Create indexes for hop_dong
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_khach ON hop_dong(khach_hang_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_xe ON hop_dong(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_nv ON hop_dong(nhan_vien_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_trang_thai ON hop_dong(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_ngay_tao ON hop_dong(ngay_tao)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_hd_ma ON hop_dong(ma_hop_dong)")

    logger.info("Migration 003: hop_dong and hop_dong_phu_kien tables created")