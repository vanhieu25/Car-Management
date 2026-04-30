"""Migration 001: Create users and roles tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 001."""
    cursor = conn.cursor()

    # Create vai_tro table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vai_tro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_vai_tro TEXT UNIQUE NOT NULL,
            ten_vai_tro TEXT NOT NULL,
            mo_ta TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create nhan_vien table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nhan_vien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            mat_khau_hash TEXT NOT NULL,
            ho_ten TEXT NOT NULL,
            email TEXT NOT NULL,
            so_dien_thoai TEXT,
            vai_tro_id INTEGER NOT NULL,
            trang_thai TEXT DEFAULT 'active' CHECK (trang_thai IN ('active', 'inactive')),
            lan_dang_nhap_sai INTEGER DEFAULT 0,
            khoa_den TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (vai_tro_id) REFERENCES vai_tro(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nv_username ON nhan_vien(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nv_vai_tro ON nhan_vien(vai_tro_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nv_trang_thai ON nhan_vien(trang_thai)")

    # Insert default vai_tro records
    cursor.executemany(
        "INSERT OR IGNORE INTO vai_tro (ma_vai_tro, ten_vai_tro, mo_ta) VALUES (?, ?, ?)",
        [
            ("admin", "Quản trị viên", "Toàn quyền hệ thống"),
            ("sales", "Nhân viên bán hàng", "Tư vấn và bán xe"),
            ("ky_thuat_bh", "Nhân viên kỹ thuật bảo hành", "Xử lý bảo hành và bảo dưỡng"),
        ]
    )

    logger.info("Migration 001: users and roles tables created")