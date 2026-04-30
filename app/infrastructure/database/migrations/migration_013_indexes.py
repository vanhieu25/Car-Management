"""Migration 013: Create additional performance indexes."""

from app.shared.logger import logger


def run(conn):
    """Execute migration 013."""
    cursor = conn.cursor()

    # Additional indexes for performance optimization
    # These complement the indexes created in earlier migrations

    # hop_dong - additional composite indexes for reporting
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_nv_ngay ON hop_dong(nhan_vien_id, ngay_tao)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hd_tong_tien ON hop_dong(tong_tien)")

    # khach_hang - for VIP and segmentation queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kh_tong_gia_tri ON khach_hang(tong_gia_tri_mua DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kh_ngay_sinh ON khach_hang(ngay_sinh)")

    # bao_hanh - for warranty expiration alerts
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_ngay_ket_thuc_trang_thai ON bao_hanh(ngay_ket_thuc, trang_thai)")

    # tra_gop_lich_su - for overdue payment alerts
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tgls_qua_han ON tra_gop_lich_su(trang_thai, ngay_den_han)")

    # lead - for conversion rate calculations
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_chuyen_doi ON lead(trang_thai, chien_dich_id)")

    # audit_log - for log analysis
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_al_thoi_gian_hanh_dong ON audit_log(thoi_gian, hanh_dong)")

    logger.info("Migration 013: additional performance indexes created")