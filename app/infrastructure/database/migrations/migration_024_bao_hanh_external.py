"""Migration 024: Support external (ngoai) warranties for vehicles sold by other dealerships.

- hop_dong_id becomes nullable (was UNIQUE NOT NULL)
- Add so_khung, so_may for external vehicle identification
- Add is_external flag
- Indexes for so_khung, so_may, is_external

Note: Must drop views that reference bao_hanh before table rename,
then recreate them after (SQLite limitation).
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 024."""
    cursor = conn.cursor()

    # Drop views that depend on bao_hanh (required before table rename in SQLite)
    cursor.execute("DROP VIEW IF EXISTS view_dashboard_kpi")
    cursor.execute("DROP VIEW IF EXISTS view_dashboard_alerts")
    logger.info("Dropped views that reference bao_hanh")

    # Create new table with nullable hop_dong_id and new columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bao_hanh_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hop_dong_id INTEGER,
            xe_id INTEGER,
            khach_hang_id INTEGER NOT NULL,
            thoi_han_bh INTEGER NOT NULL,
            ngay_bat_dau TEXT NOT NULL,
            ngay_ket_thuc TEXT NOT NULL,
            pham_vi TEXT,
            trang_thai TEXT DEFAULT 'con_hieu_luc'
                CHECK (trang_thai IN ('con_hieu_luc', 'het_han')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            so_khung TEXT,
            so_may TEXT,
            is_external INTEGER DEFAULT 0,
            FOREIGN KEY (hop_dong_id) REFERENCES hop_dong(id),
            FOREIGN KEY (xe_id) REFERENCES xe(id),
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id),
            CHECK (ngay_ket_thuc >= ngay_bat_dau)
        )
    """)

    # Migrate existing data
    cursor.execute("""
        INSERT INTO bao_hanh_new
            (id, hop_dong_id, xe_id, khach_hang_id, thoi_han_bh, ngay_bat_dau,
             ngay_ket_thuc, pham_vi, trang_thai, created_at, updated_at, created_by,
             so_khung, so_may, is_external)
        SELECT id, hop_dong_id, xe_id, khach_hang_id, thoi_han_bh, ngay_bat_dau,
               ngay_ket_thuc, pham_vi, trang_thai, created_at, updated_at, created_by,
               NULL, NULL, 0
        FROM bao_hanh
    """)

    cursor.execute("DROP TABLE bao_hanh")
    cursor.execute("ALTER TABLE bao_hanh_new RENAME TO bao_hanh")

    # Recreate indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_hop_dong ON bao_hanh(hop_dong_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_xe ON bao_hanh(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_ngay_ket_thuc ON bao_hanh(ngay_ket_thuc)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_trang_thai ON bao_hanh(trang_thai)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhyc_bao_hanh ON bao_hanh_yeu_cau(bao_hanh_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhyc_trang_thai ON bao_hanh_yeu_cau(trang_thai)")
    # New indexes for external lookup
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_so_khung ON bao_hanh(so_khung)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_so_may ON bao_hanh(so_may)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_is_external ON bao_hanh(is_external)")

    # Recreate views
    _recreate_view_dashboard_kpi(cursor)
    _recreate_view_dashboard_alerts(cursor)

    logger.info("Migration 024: external warranty support added")


def _recreate_view_dashboard_kpi(cursor):
    """Recreate view_dashboard_kpi view."""
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_dashboard_kpi AS
        SELECT
            -- Doanh thu tháng hiện tại
            (SELECT COALESCE(SUM(tong_tien), 0)
             FROM hop_dong
             WHERE trang_thai = 'da_giao_xe'
               AND strftime('%Y-%m', ngay_giao_xe) = strftime('%Y-%m', 'now'))
            AS doanh_thu_thang_nay,

            -- Số HĐ tháng hiện tại
            (SELECT COUNT(*)
             FROM hop_dong
             WHERE trang_thai = 'da_giao_xe'
               AND strftime('%Y-%m', ngay_giao_xe) = strftime('%Y-%m', 'now'))
            AS so_hd_thang_nay,

            -- Số xe tồn
            (SELECT COALESCE(SUM(so_luong_ton), 0)
             FROM xe
             WHERE trang_thai = 'con_hang')
            AS so_xe_ton,

            -- BH sắp hết hạn (trong 30 ngày)
            (SELECT COUNT(*)
             FROM bao_hanh
             WHERE trang_thai = 'con_hieu_luc'
               AND date(ngay_ket_thuc) BETWEEN date('now') AND date('now', '+30 days'))
            AS bh_sap_het_han,

            -- TG quá hạn
            (SELECT COUNT(*)
             FROM tra_gop_lich_su
             WHERE trang_thai = 'qua_han')
            AS tg_qua_han,

            -- KN cấp cao đang mở
            (SELECT COUNT(*)
             FROM khieu_nai
             WHERE muc_do = 'cao'
               AND trang_thai IN ('moi', 'dang_xu_ly'))
            AS kn_cao_moi
    """)
    logger.info("View view_dashboard_kpi recreated")


def _recreate_view_dashboard_alerts(cursor):
    """Recreate view_dashboard_alerts view.

    Note: For external warranties (is_external=1), xe info may not exist.
    The alert uses LEFT JOIN with bao_hanh so it works for both internal and external.
    """
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_dashboard_alerts AS
        SELECT 'BH' AS loai,
               'Bảo hành sắp hết hạn' AS tieu_de,
               'BH-' || bh.id AS ma,
               kh.ho_ten AS khach_hang,
               COALESCE(xe.hang || ' ' || xe.dong_xe, bh.hang_xe || ' ' || bh.dong_xe) AS xe,
               bh.ngay_ket_thuc AS ngay_canh_bao
        FROM bao_hanh bh
        JOIN khach_hang kh ON bh.khach_hang_id = kh.id
        LEFT JOIN xe ON bh.xe_id = xe.id
        WHERE bh.trang_thai = 'con_hieu_luc'
          AND date(bh.ngay_ket_thuc) BETWEEN date('now') AND date('now', '+30 days')

        UNION ALL

        SELECT 'TG' AS loai,
               'Trả góp quá hạn' AS tieu_de,
               tg.ma_tra_gop AS ma,
               kh.ho_ten AS khach_hang,
               xe.hang || ' ' || xe.dong_xe AS xe,
               tgls.ngay_den_han AS ngay_canh_bao
        FROM tra_gop tg
        JOIN tra_gop_lich_su tgls ON tg.id = tgls.tra_gop_id
        JOIN hop_dong hd ON tg.hop_dong_id = hd.id
        JOIN khach_hang kh ON hd.khach_hang_id = kh.id
        JOIN xe ON hd.xe_id = xe.id
        WHERE tgls.trang_thai = 'qua_han'

        UNION ALL

        SELECT 'KN' AS loai,
               'Khiếu nại cấp cao' AS tieu_de,
               'KN-' || kn.id AS ma,
               kh.ho_ten AS khach_hang,
               kn.noi_dung AS xe,
               kn.ngay_tao AS ngay_canh_bao
        FROM khieu_nai kn
        JOIN khach_hang kh ON kn.khach_hang_id = kh.id
        WHERE kn.muc_do = 'cao'
          AND kn.trang_thai IN ('moi', 'dang_xu_ly')

        ORDER BY ngay_canh_bao ASC
    """)
    logger.info("View view_dashboard_alerts recreated")