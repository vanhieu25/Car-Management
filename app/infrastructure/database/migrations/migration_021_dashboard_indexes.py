"""Migration 021: Dashboard-specific indexes for Sprint G5.4.

Performance optimization for dashboard queries:
- BR-TIME-01: BH sắp hết hạn trong 30 ngày
- BR-TIME-02: Nhắc lịch BD trước 7 ngày
- BR-TIME-03: Cảnh báo trả góp chậm ≥ 5 ngày
- BR-TIME-05: Sinh nhật KH trong ±7 ngày
- BR-TIME-04: Cảnh báo tồn kho thấp

These indexes complement migration_013 and migration_020 views.
C-PERF-04: Query báo cáo với 10,000 record < 3s
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 021."""
    cursor = conn.cursor()

    # ============================================================
    # Index for BR-TIME-05: Sinh nhật KH ±7 ngày
    # view_dashboard_alerts uses khach_hang.ngay_sinh for birthday alerts
    # Pattern: WHERE ngay_sinh IS NOT NULL AND (...)
    # ============================================================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_kh_ngay_sinh_not_null 
        ON khach_hang(ngay_sinh) 
        WHERE ngay_sinh IS NOT NULL
    """)
    logger.info("Index idx_kh_ngay_sinh_not_null created for birthday alerts")

    # ============================================================
    # Index for BR-TIME-02: Bao duong schedule 7 days
    # Pattern: WHERE ngay_bao_duong BETWEEN date('now') AND date('now', '+7 days')
    # ============================================================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bd_ngay_du_kien_7days 
        ON bao_duong(ngay_du_kien) 
        WHERE trang_thai = 'cho_xac_nhan'
    """)
    logger.info("Index idx_bd_ngay_du_kien_7days created")

    # ============================================================
    # Index for hop_dong delivery date (RP-01 revenue by time)
    # Pattern: WHERE trang_thai='da_giao_xe' AND ngay_giao_xe BETWEEN ? AND ?
    # Combined index for very common query pattern
    # ============================================================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_hd_giao_ngay_status 
        ON hop_dong(ngay_giao_xe, trang_thai) 
        WHERE trang_thai = 'da_giao_xe'
    """)
    logger.info("Index idx_hd_giao_ngay_status created for revenue queries")

    # ============================================================
    # Index for xe inventory alerts (BR-KHO-02, BR-TIME-04)
    # Pattern: WHERE trang_thai='con_hang' AND so_luong_ton <= muc_toi_thieu
    # ============================================================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_xe_ton_low 
        ON xe(so_luong_ton, muc_toi_thieu) 
        WHERE trang_thai = 'con_hang'
    """)
    logger.info("Index idx_xe_ton_low created for inventory alerts")

    # ============================================================
    # Index for bao_hanh expiration (BR-TIME-01, BR-BH-03)
    # Pattern: WHERE trang_thai='con_hieu_luc' AND ngay_ket_thuc BETWEEN date('now') AND date('now', '+30 days')
    # ============================================================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bh_expiring_30days 
        ON bao_hanh(ngay_ket_thuc, trang_thai) 
        WHERE trang_thai = 'con_hieu_luc'
    """)
    logger.info("Index idx_bh_expiring_30days created for BH expiration alerts")

    # ============================================================
    # Index for tra_gop_lich_su overdue (BR-TIME-03, BR-TG-09)
    # Pattern: WHERE trang_thai='chua_tra' AND ngay_den_han < date('now', '-5 days')
    # ============================================================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tgls_chua_tra_den_han 
        ON tra_gop_lich_su(ngay_den_han, trang_thai) 
        WHERE trang_thai = 'chua_tra'
    """)
    logger.info("Index idx_tgls_chua_tra_den_han created for TG overdue queries")

    logger.info("Migration 021: dashboard-specific indexes for G5.4 created successfully")