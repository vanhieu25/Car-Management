"""Migration 008: Create ncc, nhap_kho, don_dat_hang tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 008."""
    cursor = conn.cursor()

    # Create nha_cung_cap table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nha_cung_cap (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_ncc TEXT UNIQUE NOT NULL,
            ten_ncc TEXT NOT NULL,
            dia_chi TEXT,
            so_dien_thoai TEXT,
            email TEXT,
            nguoi_lien_he TEXT,
            diem_chat_luong INTEGER DEFAULT 0 CHECK (diem_chat_luong BETWEEN 1 AND 5),
            diem_thoi_gian_giao INTEGER DEFAULT 0 CHECK (diem_thoi_gian_giao BETWEEN 1 AND 5),
            diem_gia_ca INTEGER DEFAULT 0 CHECK (diem_gia_ca BETWEEN 1 AND 5),
            diem_tong INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create nhap_kho table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nhap_kho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nha_cung_cap_id INTEGER NOT NULL,
            nhan_vien_id INTEGER NOT NULL,
            ngay_nhap TEXT DEFAULT CURRENT_TIMESTAMP,
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (nha_cung_cap_id) REFERENCES nha_cung_cap(id),
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create chi_tiet_nhap_kho (detailed items for each warehouse import)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_tiet_nhap_kho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nhap_kho_id INTEGER NOT NULL,
            loai_item TEXT NOT NULL CHECK (loai_item IN ('xe', 'phu_kien')),
            item_id INTEGER NOT NULL,
            so_luong INTEGER NOT NULL CHECK (so_luong > 0),
            gia_nhap INTEGER NOT NULL CHECK (gia_nhap >= 0),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nhap_kho_id) REFERENCES nhap_kho(id)
        )
    """)

    # Create don_dat_hang table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS don_dat_hang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nha_cung_cap_id INTEGER NOT NULL,
            nhan_vien_id INTEGER NOT NULL,
            ma_don TEXT UNIQUE NOT NULL,
            ngay_dat TEXT DEFAULT CURRENT_TIMESTAMP,
            trang_thai TEXT DEFAULT 'nhap' CHECK (trang_thai IN ('nhap', 'da_gui', 'da_nhan', 'huy')),
            ngay_giao TEXT,
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (nha_cung_cap_id) REFERENCES nha_cung_cap(id),
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create chi_tiet_don_dat (detailed items for each order)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chi_tiet_don_dat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            don_dat_hang_id INTEGER NOT NULL,
            loai_item TEXT NOT NULL CHECK (loai_item IN ('xe', 'phu_kien')),
            item_id INTEGER NOT NULL,
            so_luong INTEGER NOT NULL CHECK (so_luong > 0),
            gia_don INTEGER NOT NULL CHECK (gia_don >= 0),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (don_dat_hang_id) REFERENCES don_dat_hang(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ncc_ma ON nha_cung_cap(ma_ncc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ncc_ten ON nha_cung_cap(ten_ncc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nk_ncc ON nhap_kho(nha_cung_cap_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nk_ngay ON nhap_kho(ngay_nhap)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ddh_ncc ON don_dat_hang(nha_cung_cap_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ddh_trang_thai ON don_dat_hang(trang_thai)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ddh_ma ON don_dat_hang(ma_don)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ctnk_nhap ON chi_tiet_nhap_kho(nhap_kho_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ctdd_don ON chi_tiet_don_dat(don_dat_hang_id)")

    logger.info("Migration 008: ncc, nhap_kho, don_dat_hang tables created")