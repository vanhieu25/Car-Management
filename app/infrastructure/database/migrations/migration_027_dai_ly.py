"""Migration 027: Create dai_ly (dealership) table.

Table for managing dealership/agency information.
Staff (nhan_vien) will belong to a dai_ly.
Insurance can be sold by different dealerships.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 027."""
    cursor = conn.cursor()

    # Create dai_ly table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dai_ly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_dai_ly TEXT NOT NULL UNIQUE,
            ten_dai_ly TEXT NOT NULL,
            dia_chi TEXT,
            so_dien_thoai TEXT,
            email TEXT,
            trang_thai TEXT DEFAULT 'hoat_dong'
                CHECK (trang_thai IN ('hoat_dong', 'khong_hoat_dong')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        )
    """)
    logger.info("Created dai_ly table")

    # Add dai_ly_id to nhan_vien to link staff to dealership
    cursor.execute("""
        ALTER TABLE nhan_vien ADD COLUMN dai_ly_id INTEGER
            REFERENCES dai_ly(id)
    """)
    logger.info("Added dai_ly_id column to nhan_vien")

    # Create index for faster lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nv_dai_ly ON nhan_vien(dai_ly_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dl_ma ON dai_ly(ma_dai_ly)")

    # Insert default dealership (current company)
    cursor.execute("""
        INSERT INTO dai_ly (ma_dai_ly, ten_dai_ly, dia_chi, so_dien_thoai, email)
        VALUES ('DL001', 'Đại lý A (Chính)', 'HCM', '0900000001', 'dlA@company.com')
    """)
    logger.info("Inserted default dealership DL001")

    # Update existing admin user to belong to the default dealership
    cursor.execute("""
        UPDATE nhan_vien SET dai_ly_id = 1 WHERE id = 1
    """)
    logger.info("Updated admin user to belong to DL001")

    logger.info("Migration 027: dai_ly table created")