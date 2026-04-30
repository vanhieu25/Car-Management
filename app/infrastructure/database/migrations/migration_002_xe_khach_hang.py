"""Migration 002: Create xe and khach_hang tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 002."""
    cursor = conn.cursor()

    # Create khach_hang table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS khach_hang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ho_ten TEXT NOT NULL,
            so_dien_thoai TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            dia_chi TEXT,
            ngay_sinh TEXT,
            phan_loai TEXT DEFAULT 'Thuong' CHECK (phan_loai IN ('Thuong', 'Than_thiet', 'VIP')),
            tong_gia_tri_mua INTEGER DEFAULT 0,
            so_xe_da_mua INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create xe table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_xe TEXT UNIQUE NOT NULL,
            hang TEXT NOT NULL,
            dong_xe TEXT NOT NULL,
            nam_san_xuat INTEGER NOT NULL CHECK (nam_san_xuat >= 1990 AND nam_san_xuat <= 2100),
            mau_sac TEXT,
            gia_ban INTEGER NOT NULL CHECK (gia_ban >= 0),
            so_luong_ton INTEGER DEFAULT 0 CHECK (so_luong_ton >= 0),
            muc_toi_thieu INTEGER DEFAULT 2,
            trang_thai TEXT DEFAULT 'con_hang' CHECK (trang_thai IN ('con_hang', 'da_ban', 'sap_ve')),
            ngay_nhap_dau_tien TEXT,
            mo_ta TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create indexes for xe
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xe_hang_dong ON xe(hang, dong_xe)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xe_trang_thai ON xe(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xe_gia_ban ON xe(gia_ban)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_xe_ma_xe ON xe(ma_xe)")

    # Create indexes for khach_hang
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_kh_so_dien_thoai ON khach_hang(so_dien_thoai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kh_email ON khach_hang(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kh_phan_loai ON khach_hang(phan_loai)")

    logger.info("Migration 002: xe and khach_hang tables created")