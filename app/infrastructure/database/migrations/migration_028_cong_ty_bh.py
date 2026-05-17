"""Migration 028: Create cong_ty_bh (insurance company) table.

Danh mục công ty bảo hiểm cho xe ngoài và xe đại lý.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 028."""
    cursor = conn.cursor()

    # Create cong_ty_bh table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cong_ty_bh (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_cty TEXT NOT NULL UNIQUE,
            ten_cty TEXT NOT NULL,
            dia_chi TEXT,
            so_dien_thoai TEXT,
            email TEXT,
            trang_thai TEXT DEFAULT 'hoat_dong'
                CHECK (trang_thai IN ('hoat_dong', 'khong_hoat_dong')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        )
    """)
    logger.info("Created cong_ty_bh table")

    # Create index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cty_ma ON cong_ty_bh(ma_cty)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cty_trang_thai ON cong_ty_bh(trang_thai)")

    # Seed data - common insurance companies in Vietnam
    seed_data = [
        ("PTI", "Tổng Công Ty Bảo Hiểm Bưu Điện", "", "", ""),
        ("PVI", "Tổng Công Ty Bảo Hiểm Dầu Khí Việt Nam", "", "", ""),
        ("AIC", "Tổng Công Ty Bảo Hiểm AIC", "", "", ""),
        ("BHD", "Tổng Công Ty Bảo Hiểm Bảo Minh", "", "", ""),
        ("VBI", "Tổng Công Ty Bảo Hiểm Viettel", "", "", ""),
        ("TJ", "Tổng Công Ty Bảo Hiểm Thượng Hải", "", "", ""),
        ("LIB", "Tổng Công Ty Bảo Hiểm Liên Hiệp", "", "", ""),
        ("AAA", "Bảo Hiểm AAA", "", "", ""),
    ]

    for ma, ten, dc, sdt, em in seed_data:
        cursor.execute(
            "INSERT OR IGNORE INTO cong_ty_bh (ma_cty, ten_cty, dia_chi, so_dien_thoai, email) VALUES (?, ?, ?, ?, ?)",
            (ma, ten, dc, sdt, em)
        )
    logger.info(f"Seeded {len(seed_data)} insurance companies")

    logger.info("Migration 028: cong_ty_bh table created")