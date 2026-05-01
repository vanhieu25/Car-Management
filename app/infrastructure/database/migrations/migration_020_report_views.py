"""Migration 020: Report views for Sprint G5.4 - Báo cáo & Dashboard.

BR-BC-01: Báo cáo doanh thu hỗ trợ filter ngày/tháng/quý/năm + NV + dòng xe
BR-BC-02: Top 10 xe = COUNT HĐ da_giao_xe GROUP BY xe
BR-BC-03: KH VIP = sắp xếp tong_gia_tri_mua giảm dần
BR-BC-04: KPI NV = BR-CALC-05
BR-BC-07: Báo cáo doanh thu chỉ tính HĐ da_giao_xe

Views:
- view_revenue_by_month: Doanh thu theo tháng (RP-01)
- view_top_xe_sold: Top xe bán chạy (RP-02)
- view_kpi_nv: KPI nhân viên (RP-03)
- view_vip_customers: KH VIP (RP-04)
- view_bh_cost: Chi phí bảo hành (RP-05)
- view_km_efficiency: Hiệu quả khuyến mãi (RP-06)
- view_mk_efficiency: Hiệu quả marketing (RP-07)
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 020."""
    cursor = conn.cursor()

    # ============================================================
    # VIEW: view_revenue_by_month
    # RP-01: Doanh thu theo thời gian (ngày/tháng/quý/năm)
    # BR-BC-01: filter ngày/tháng/quý/năm + NV + dòng xe
    # BR-BC-07: chỉ tính HĐ da_giao_xe
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_revenue_by_month AS
        SELECT 
            strftime('%Y-%m', hd.ngay_giao_xe) AS thang,
            hd.nhan_vien_id,
            nv.ho_ten AS nhan_vien,
            xe.hang,
            xe.dong_xe,
            COUNT(hd.id) AS so_hop_dong,
            SUM(hd.tong_tien) AS tong_doanh_thu,
            SUM(hd.tien_giam_km) AS tong_giam_km
        FROM hop_dong hd
        JOIN nhan_vien nv ON hd.nhan_vien_id = nv.id
        JOIN xe ON hd.xe_id = xe.id
        WHERE hd.trang_thai = 'da_giao_xe'
          AND hd.ngay_giao_xe IS NOT NULL
        GROUP BY strftime('%Y-%m', hd.ngay_giao_xe), hd.nhan_vien_id, xe.hang, xe.dong_xe
        ORDER BY thang DESC, tong_doanh_thu DESC
    """)
    logger.info("View view_revenue_by_month created")

    # ============================================================
    # VIEW: view_top_xe_sold
    # RP-02: Top 10 xe bán chạy
    # BR-BC-02: COUNT HĐ da_giao_xe GROUP BY xe trong khoảng thời gian
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_top_xe_sold AS
        SELECT 
            xe.id AS xe_id,
            xe.ma_xe,
            xe.hang,
            xe.dong_xe,
            xe.nam_san_xuat,
            COUNT(hd.id) AS so_lan_ban,
            SUM(hd.gia_xe) AS doanh_thu_xe,
            SUM(hd.tong_tien) AS doanh_thu_tong
        FROM xe
        LEFT JOIN hop_dong hd ON xe.id = hd.xe_id AND hd.trang_thai = 'da_giao_xe'
        GROUP BY xe.id, xe.ma_xe, xe.hang, xe.dong_xe, xe.nam_san_xuat
        ORDER BY so_lan_ban DESC, doanh_thu_tong DESC
        LIMIT 10
    """)
    logger.info("View view_top_xe_sold created")

    # ============================================================
    # VIEW: view_kpi_nv
    # RP-03: Hiệu suất nhân viên
    # BR-BC-04: KPI NV = BR-CALC-05 = COUNT(hop_dong) + SUM(tong_tien)
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_kpi_nv AS
        SELECT 
            nv.id AS nhan_vien_id,
            nv.username,
            nv.ho_ten,
            nv.vai_tro_id,
            vt.ten_vai_tro,
            COUNT(hd.id) AS so_hop_dong,
            SUM(hd.tong_tien) AS tong_doanh_thu,
            SUM(CASE WHEN hd.trang_thai = 'da_giao_xe' THEN 1 ELSE 0 END) AS so_hd_da_giao,
            SUM(CASE WHEN hd.trang_thai = 'da_giao_xe' THEN hd.tong_tien ELSE 0 END) AS doanh_thu_da_giao
        FROM nhan_vien nv
        LEFT JOIN vai_tro vt ON nv.vai_tro_id = vt.id
        LEFT JOIN hop_dong hd ON nv.id = hd.nhan_vien_id
        WHERE nv.trang_thai = 'active'
        GROUP BY nv.id, nv.username, nv.ho_ten, nv.vai_tro_id, vt.ten_vai_tro
        ORDER BY doanh_thu_da_giao DESC
    """)
    logger.info("View view_kpi_nv created")

    # ============================================================
    # VIEW: view_vip_customers
    # RP-04: Khách hàng VIP
    # BR-BC-03: sắp xếp tong_gia_tri_mua giảm dần
    # BR-CALC-03: VIP = so_xe >= 3 OR tong_gia_tri >= 2_000_000_000
    # Note: khach_hang has no trang_thai column - all records are active
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_vip_customers AS
        SELECT 
            kh.id AS khach_hang_id,
            kh.ho_ten,
            kh.so_dien_thoai,
            kh.email,
            kh.dia_chi,
            kh.phan_loai,
            kh.so_xe_da_mua,
            kh.tong_gia_tri_mua,
            kh.ngay_sinh,
            COUNT(hd.id) AS so_hop_dong,
            MAX(hd.ngay_giao_xe) AS lan_mua_cuoi
        FROM khach_hang kh
        LEFT JOIN hop_dong hd ON kh.id = hd.khach_hang_id AND hd.trang_thai = 'da_giao_xe'
        GROUP BY kh.id, kh.ho_ten, kh.so_dien_thoai, kh.email, 
                 kh.dia_chi, kh.phan_loai, kh.so_xe_da_mua, 
                 kh.tong_gia_tri_mua, kh.ngay_sinh
        ORDER BY kh.tong_gia_tri_mua DESC
    """)
    logger.info("View view_vip_customers created")

    # ============================================================
    # VIEW: view_bh_cost
    # RP-05: Chi phí bảo hành theo tháng
    # Tháng, số yêu cầu, miễn phí, tính phí, tổng chi phí
    # Note: bao_hanh_yeu_cau uses ngay_hoan_thanh for completed date
    #       and loai_yeu_cau for phan_loai (not phan_loai column)
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_bh_cost AS
        SELECT 
            strftime('%Y-%m', bhyc.ngay_hoan_thanh) AS thang,
            COUNT(bhyc.id) AS so_yeu_cau,
            SUM(CASE WHEN bhyc.loai_yeu_cau = 'mien_phi' THEN 1 ELSE 0 END) AS so_mien_phi,
            SUM(CASE WHEN bhyc.loai_yeu_cau = 'tinh_phi' THEN 1 ELSE 0 END) AS so_tinh_phi,
            SUM(CASE WHEN bhyc.loai_yeu_cau = 'mien_phi' THEN bhyc.chi_phi ELSE 0 END) AS chi_phi_mien_phi,
            SUM(CASE WHEN bhyc.loai_yeu_cau = 'tinh_phi' THEN bhyc.chi_phi ELSE 0 END) AS chi_phi_tinh_phi,
            SUM(bhyc.chi_phi) AS tong_chi_phi
        FROM bao_hanh_yeu_cau bhyc
        WHERE bhyc.trang_thai = 'hoan_thanh'
          AND bhyc.ngay_hoan_thanh IS NOT NULL
        GROUP BY strftime('%Y-%m', bhyc.ngay_hoan_thanh)
        ORDER BY thang DESC
    """)
    logger.info("View view_bh_cost created")

    # ============================================================
    # VIEW: view_km_efficiency
    # RP-06: Hiệu quả khuyến mãi
    # KM, số HĐ áp dụng, doanh thu, tiền giảm
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_km_efficiency AS
        SELECT 
            km.id AS khuyen_mai_id,
            km.ten_km,
            km.loai_km,
            km.gia_tri,
            km.kieu_gia_tri,
            km.tu_ngay,
            km.den_ngay,
            km.trang_thai,
            COUNT(hd.id) AS so_hop_dong_ap_dung,
            SUM(hd.tong_tien) AS doanh_thu,
            SUM(hd.tien_giam_km) AS tong_tien_giam
        FROM khuyen_mai km
        LEFT JOIN hop_dong hd ON km.id = hd.khuyen_mai_id 
            AND hd.trang_thai = 'da_giao_xe'
        WHERE km.trang_thai IN ('dang_chay', 'tam_dung', 'ket_thuc')
        GROUP BY km.id, km.ten_km, km.loai_km, km.gia_tri, 
                 km.kieu_gia_tri, km.tu_ngay, km.den_ngay, km.trang_thai
        ORDER BY so_hop_dong_ap_dung DESC, tong_tien_giam DESC
    """)
    logger.info("View view_km_efficiency created")

    # ============================================================
    # VIEW: view_mk_efficiency
    # RP-07: Hiệu quả marketing
    # Chiến dịch, ngân sách, lead, chuyển đổi, ROI
    # BR-CALC-06: ti_le_chuyen_doi = (lead_chuyen_doi / tong_lead) * 100
    # Note: chien_dich_mk has ngay_bat_dau/ngay_ket_thuc (not tu_ngay/den_ngay)
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_mk_efficiency AS
        SELECT 
            cd.id AS chien_dich_id,
            cd.ten_chien_dich,
            cd.ngan_sach,
            cd.ngay_bat_dau,
            cd.ngay_ket_thuc,
            cd.kenh_tiep_thi,
            cd.trang_thai,
            COUNT(lead.id) AS tong_lead,
            SUM(CASE WHEN lead.trang_thai = 'chuyen_doi' THEN 1 ELSE 0 END) AS lead_chuyen_doi,
            SUM(CASE WHEN lead.trang_thai = 'tu_choi' THEN 1 ELSE 0 END) AS lead_tu_choi,
            COUNT(DISTINCT CASE WHEN lead.trang_thai = 'chuyen_doi' THEN lead.khach_hang_id END) AS kh_chuyen_doi
        FROM chien_dich_mk cd
        LEFT JOIN lead ON cd.id = lead.chien_dich_id
        WHERE cd.trang_thai != 'inactive'
        GROUP BY cd.id, cd.ten_chien_dich, cd.ngan_sach, 
                 cd.ngay_bat_dau, cd.ngay_ket_thuc, cd.kenh_tiep_thi, cd.trang_thai
        ORDER BY cd.ngay_bat_dau DESC
    """)
    logger.info("View view_mk_efficiency created")

    # ============================================================
    # VIEW: view_dashboard_kpi (for S-DB-01 Dashboard)
    # Tổng hợp KPI tiles cho Dashboard
    # ============================================================
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
    logger.info("View view_dashboard_kpi created")

    # ============================================================
    # VIEW: view_dashboard_alerts (cảnh báo cho Dashboard)
    # BH 30 ngày, TG quá hạn, sinh nhật KH, KN cấp cao
    # Note: khieu_nai has id (not ma_kn), bao_hanh has ma_bh
    # ============================================================
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_dashboard_alerts AS
        SELECT 'BH' AS loai, 
               'Bảo hành sắp hết hạn' AS tieu_de,
               bh.ma_bh AS ma,
               kh.ho_ten AS khach_hang,
               xe.hang || ' ' || xe.dong_xe AS xe,
               bh.ngay_ket_thuc AS ngay_canh_bao
        FROM bao_hanh bh
        JOIN khach_hang kh ON bh.khach_hang_id = kh.id
        JOIN xe ON bh.xe_id = xe.id
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
    logger.info("View view_dashboard_alerts created")

    logger.info("Migration 020: report views for G5.4 created successfully")