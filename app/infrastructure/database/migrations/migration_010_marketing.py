"""Migration 010: Create marketing tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 010."""
    cursor = conn.cursor()

    # Create chien_dich_mk table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chien_dich_mk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten_chien_dich TEXT NOT NULL,
            kenh_tiep_thi TEXT NOT NULL CHECK (kenh_tiep_thi IN ('facebook', 'google_ads', 'youtube', 'truyen_hinh', 'bao_chi', 'truyen_mieng', 'khac')),
            ngay_bat_dau TEXT NOT NULL,
            ngay_ket_thuc TEXT NOT NULL,
            ngan_sach INTEGER DEFAULT 0 CHECK (ngan_sach >= 0),
            muc_tieu TEXT,
            so_luong_lead_muc_tieu INTEGER DEFAULT 0,
            trang_thai TEXT DEFAULT 'nhap' CHECK (trang_thai IN ('nhap', 'dang_chay', 'ket_thuc')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id),
            CHECK (ngay_ket_thuc >= ngay_bat_dau)
        )
    """)

    # Create lead table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chien_dich_id INTEGER,
            ho_ten TEXT NOT NULL,
            so_dien_thoai TEXT NOT NULL,
            email TEXT,
            nguon TEXT,
            nhu_cau TEXT,
            nhan_vien_phu_trach_id INTEGER,
            trang_thai TEXT DEFAULT 'moi' CHECK (trang_thai IN ('moi', 'dang_cham_soc', 'chuyen_doi', 'tu_choi')),
            khach_hang_id INTEGER,
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (chien_dich_id) REFERENCES chien_dich_mk(id),
            FOREIGN KEY (nhan_vien_phu_trach_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cd_trang_thai ON chien_dich_mk(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cd_ngay ON chien_dich_mk(ngay_bat_dau, ngay_ket_thuc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_chien_dich ON lead(chien_dich_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_trang_thai ON lead(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_nv ON lead(nhan_vien_phu_trach_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_so_dt ON lead(so_dien_thoai)")

    logger.info("Migration 010: marketing tables created")