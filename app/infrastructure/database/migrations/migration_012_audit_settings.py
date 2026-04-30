"""Migration 012: Create audit_log and system_settings tables."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 012."""
    cursor = conn.cursor()

    # Create audit_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nhan_vien_id INTEGER,
            hanh_dong TEXT NOT NULL,
            bang_anh_huong TEXT,
            ban_ghi_id INTEGER,
            noi_dung TEXT,
            thoi_gian TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id)
        )
    """)

    # Create system_settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_settings TEXT UNIQUE NOT NULL,
            gia_tri TEXT NOT NULL,
            mo_ta TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            FOREIGN KEY (updated_by) REFERENCES nhan_vien(id)
        )
    """)

    # Create indexes for audit_log
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_al_nv ON audit_log(nhan_vien_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_al_hanh_dong ON audit_log(hanh_dong)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_al_bang ON audit_log(bang_anh_huong)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_al_thoi_gian ON audit_log(thoi_gian)")

    # Create indexes for system_settings
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_ss_ma ON system_settings(ma_settings)")

    # Insert default system settings
    cursor.executemany(
        "INSERT OR IGNORE INTO system_settings (ma_settings, gia_tri, mo_ta) VALUES (?, ?, ?)",
        [
            ("thoi_han_bh_default", "24", "Thời hạn bảo hành mặc định (tháng)"),
            ("muc_toi_thieu_ton_kho", "2", "Ngưỡng tồn kho tối thiểu cảnh báo"),
            ("ten_dai_ly", "Đại lý xe hơi", "Tên đại lý hiển thị trên hệ thống"),
            ("dia_chi_dai_ly", "Việt Nam", "Địa chỉ đại lý"),
            ("so_dien_thoai_dai_ly", "0123456789", "Số điện thoại liên hệ"),
            ("email_dai_ly", "contact@dailyxeco.vn", "Email liên hệ"),
        ]
    )

    logger.info("Migration 012: audit_log and system_settings tables created")