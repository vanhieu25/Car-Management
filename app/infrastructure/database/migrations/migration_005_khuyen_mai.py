"""Migration 005: Create khuyen_mai tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 005."""
    cursor = conn.cursor()

    # Create khuyen_mai table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS khuyen_mai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_km TEXT NOT NULL,
            mo_ta TEXT,
            loai_km TEXT NOT NULL CHECK (loai_km IN ('giam_tien_mat', 'giam_phan_tram', 'tang_phu_kien', 'giam_lai_suat', 'combo')),
            gia_tri INTEGER NOT NULL,
            kieu_gia_tri TEXT NOT NULL CHECK (kieu_gia_tri IN ('tien', 'phan_tram')),
            tu_ngay TEXT NOT NULL,
            den_ngay TEXT NOT NULL,
            trang_thai TEXT DEFAULT 'dang_chay' CHECK (trang_thai IN ('nhap', 'dang_chay', 'tam_dung', 'ket_thuc')),
            so_luong_cho_phep INTEGER,
            so_luong_da_su_dung INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id),
            CHECK (den_ngay >= tu_ngay)
        )
    """)

    # Create km_pham_vi table (scope of promotion application)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS km_pham_vi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            khuyen_mai_id INTEGER NOT NULL,
            loai_ap_dung TEXT NOT NULL CHECK (loai_ap_dung IN ('all', 'hang', 'dong_xe', 'xe')),
            gia_tri_ap_dung TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (khuyen_mai_id) REFERENCES khuyen_mai(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_km_trang_thai ON khuyen_mai(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_km_ngay ON khuyen_mai(tu_ngay, den_ngay)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_km_loai ON khuyen_mai(loai_km)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kmp_km ON km_pham_vi(khuyen_mai_id)")

    logger.info("Migration 005: khuyen_mai tables created")