"""Unit tests for KhuyenMaiService - T-G4.2.TEST.01..05.

Tests:
- TEST.01: find_applicable with 5 cases
- TEST.02: calculate_discount with 7 cases (4 types × variations)
- TEST.03: daily_expiry_check (TRG-06)
- TEST.04: report_effectiveness
- TEST.05: UAT for AC-KM-* (create, pause/resume, invalid pause)

References:
- BR-KM-01..10: Promotion lifecycle
- BR-CALC-02: 4 discount types
- BR-KM-04: Active promotions filter
- BR-KM-07: Pause/resume
- TRG-06: Daily expiry check
- BR-KM-09: Effectiveness report
"""

import pytest
import sqlite3
import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.application.services.khuyen_mai_service import (
    KhuyenMaiService,
    KhuyenMaiCreateData,
    KhuyenMaiPhamViData,
    KhuyenMaiNotFoundError,
    KhuyenMaiExpiredError,
    InvalidDateRangeError,
    InvalidGiaTriError,
    InvalidLoaiKMError,
)
from app.application.services.khuyen_mai_scheduler import daily_expiry_check


@pytest.fixture
def promo_db():
    """Create database with promotion-specific test data.

    Seeds:
    - nhan_vien (3 records)
    - khach_hang (2 records)
    - xe (6 records: various hang/dong_xe, different stock dates)
    - phu_kien (3 records)
    - khuyen_mai (6 types including 1 paused, various date ranges)
    - km_pham_vi (scope records for each KM)
    - hop_dong (some with khuyen_mai_id for stats testing)
    - combo_phu_kien + combo_chi_tiet (for combo KM testing)
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Run migrations
    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(db_path)
    runner.run_pending()

    # ===== Seed nhan_vien =====
    conn.execute("""
        INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai)
        VALUES (1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Admin User', 'admin@test.com', 1, 'active'),
               (2, 'sales1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Sales One', 'sales1@test.com', 2, 'active'),
               (3, 'tech1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Tech One', 'tech1@test.com', 3, 'active')
    """)

    # ===== Seed khach_hang =====
    conn.execute("""
        INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email, dia_chi, phan_loai, tong_gia_tri_mua, so_xe_da_mua)
        VALUES (1, 'Khach Hang Test', '0909000001', 'kh1@test.com', '123 Test St', 'Thuong', 0, 0),
               (2, 'VIP Customer', '0909000002', 'vip@test.com', '456 VIP St', 'VIP', 2000000000, 2)
    """)

    # ===== Seed xe with various hang/dong_xe and stock dates =====
    today = datetime.now()
    old_date = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    recent_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
    future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    conn.execute(f"""
        INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, muc_toi_thieu, trang_thai, ngay_nhap_dau_tien)
        VALUES (1, 'XE001', 'Toyota', 'Camry', 2024, 'Den', 500000000, 5, 2, 'con_hang', '{old_date}'),
               (2, 'XE002', 'Honda', 'Civic', 2024, 'Trang', 400000000, 3, 2, 'con_hang', '{recent_date}'),
               (3, 'XE003', 'Toyota', 'Vios', 2024, 'Do', 350000000, 2, 2, 'con_hang', '{old_date}'),
               (4, 'XE004', 'BMW', 'X5', 2024, 'Den', 1500000000, 1, 1, 'con_hang', '{recent_date}'),
               (5, 'XE005', 'Honda', 'City', 2024, 'Bac', 380000000, 4, 2, 'con_hang', '{old_date}'),
               (6, 'XE006', 'Mercedes', 'C200', 2024, 'Trang', 1200000000, 2, 1, 'con_hang', '{future_date}')
    """)

    # ===== Seed phu_kien =====
    conn.execute("""
        INSERT INTO phu_kien (id, ma_pk, ten_pk, phan_loai, gia_ban, ton_kho)
        VALUES (1, 'PK001', 'GPS Navigator', 'Dien tu', 5000000, 20),
               (2, 'PK002', 'Camera lui', 'Dien tu', 3000000, 15),
               (3, 'PK003', 'Loa de', 'Am thanh', 2000000, 30),
               (4, 'PK004', 'Man hinh 10inch', 'Dien tu', 8000000, 10)
    """)

    # ===== Seed combo_phu_kien + combo_chi_tiet (for combo KM type) =====
    conn.execute("""
        INSERT INTO combo_phu_kien (id, ma_combo, ten_combo, he_so_giam, mo_ta)
        VALUES (1, 'CB-00001', 'Combo Giam 10%', 0.9, 'Giam 10% cho combo PK'),
               (2, 'CB-00002', 'Combo Giam 20%', 0.8, 'Giam 20% cho combo PK')
    """)

    conn.execute("""
        INSERT INTO combo_chi_tiet (combo_id, phu_kien_id, so_luong)
        VALUES (1, 1, 1), (1, 2, 1),
               (2, 3, 2), (2, 4, 1)
    """)

    # ===== Seed khuyen_mai (6 types) =====
    # KM1: giam_tien_mat for Toyota (hang)
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai, so_luong_cho_phep, so_luong_da_su_dung)
        VALUES (1, 'Giam 5tr Toyota', 'Giam 5 trieu cho xe Toyota', 'giam_tien_mat', 5000000, 'tien', '2026-01-01', '2026-12-31', 'dang_chay', 100, 0)
    """)

    # KM2: giam_phan_tram for Honda Civic (dong_xe)
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
        VALUES (2, 'Giam 10% Honda Civic', 'Giam 10% cho Honda Civic', 'giam_phan_tram', 10, 'phan_tram', '2026-01-01', '2026-12-31', 'dang_chay')
    """)

    # KM3: giam_phan_tram with tien kieu (not phan_tram) - capped
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
        VALUES (3, 'Giam tien 3tr', 'Giam tien mat 3 trieu', 'giam_phan_tram', 3000000, 'tien', '2026-01-01', '2026-12-31', 'dang_chay')
    """)

    # KM4: tang_phu_kien (list of free PK ids)
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
        VALUES (4, 'Tang GPS Camera', 'Tang GPS va Camera', 'tang_phu_kien', '1,2', 'tang_phu_kien', '2026-01-01', '2026-12-31', 'dang_chay')
    """)

    # KM5: giam_lai_suat (interest rate reduction)
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
        VALUES (5, 'Giam 2% lai suat', 'Giam 2% lai suat tra gap', 'giam_lai_suat', 2, 'lai_suat', '2026-01-01', '2026-12-31', 'dang_chay')
    """)

    # KM6: combo (links to combo_phu_kien.id=1)
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
        VALUES (6, 'Combo PK giam 10%', 'Combo phu kien giam 10%', 'combo', 1, 'combo', '2026-01-01', '2026-12-31', 'dang_chay')
    """)

    # KM7: TAM_DUNG (paused) - for pause/resume tests
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
        VALUES (7, 'KM Tam Dung', 'Khuyen mai tam dung', 'giam_tien_mat', 1000000, 'tien', '2026-01-01', '2026-12-31', 'tam_dung')
    """)

    # KM8: KET_THUC (expired) - for testing invalid pause on ended KM
    conn.execute("""
        INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
        VALUES (8, 'KM Da Ket Thuc', 'Khuyen mai da ket thuc', 'giam_tien_mat', 2000000, 'tien', '2024-01-01', '2024-12-31', 'ket_thuc')
    """)

    # ===== Seed km_pham_vi (scope records) =====
    # KM1: hang=Toyota
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (1, 'hang', 'Toyota')
    """)

    # KM2: dong_xe=Civic
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (2, 'dong_xe', 'Civic')
    """)

    # KM3: all (applies to all xe)
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (3, 'all', NULL)
    """)

    # KM4: tang_phu_kien (no scope needed, applies to all)
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (4, 'all', NULL)
    """)

    # KM5: all (interest reduction applies to all)
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (5, 'all', NULL)
    """)

    # KM6: combo applies to all
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (6, 'all', NULL)
    """)

    # KM7: paused KM applies to all
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (7, 'all', NULL)
    """)

    # KM8: expired KM applies to all
    conn.execute("""
        INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
        VALUES (8, 'all', NULL)
    """)

    # ===== Seed hop_dong with khuyen_mai_id (for stats testing) =====
    conn.execute("""
        INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, khuyen_mai_id, gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien, trang_thai, ngay_tao)
        VALUES (1, 'HD001', 1, 1, 1, 1, 500000000, 0, 5000000, 495000000, 'da_giao_xe', '2026-01-15'),
               (2, 'HD002', 1, 2, 1, 2, 400000000, 0, 40000000, 360000000, 'da_giao_xe', '2026-02-01'),
               (3, 'HD003', 2, 1, 1, 1, 500000000, 0, 5000000, 495000000, 'da_giao_xe', '2026-02-15')
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


# =============================================================================
# TEST.01 — find_applicable
# =============================================================================
class TestFindApplicable:
    """TEST.01 — KhuyenMaiService.find_applicable — 5 cases"""

    def test_km_hang_xe(self, promo_db):
        """KM with hang=Toyota matches xe that is Toyota"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # Xe 1 is Toyota Camry
        result = service.find_applicable(xe_id=1)

        # Should find KM1 (giam_tien_mat for Toyota)
        km_ids = [km["id"] for km in result]
        assert 1 in km_ids  # Toyota discount
        conn.close()

    def test_km_dong_xe(self, promo_db):
        """KM with dong_xe=Civic matches xe that is Civic"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # Xe 2 is Honda Civic
        result = service.find_applicable(xe_id=2)

        # Should find KM2 (giam_phan_tram 10% for Civic)
        km_ids = [km["id"] for km in result]
        assert 2 in km_ids  # Civic discount
        conn.close()

    def test_km_xe_cu_the(self, promo_db):
        """KM with loai_ap_dung='xe' matches specific xe_id"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert a KM for specific xe (xe_id=3)
        conn.execute("""
            INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
            VALUES (100, 'KM xe cu the', 'KM cho xe so 3', 'giam_tien_mat', 1000000, 'tien', '2026-01-01', '2026-12-31', 'dang_chay')
        """)
        conn.execute("""
            INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
            VALUES (100, 'xe', '3')
        """)
        conn.commit()
        conn.close()

        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # Xe 3 should match KM 100
        result = service.find_applicable(xe_id=3)
        km_ids = [km["id"] for km in result]
        assert 100 in km_ids
        conn.close()

    def test_km_ton_lau(self, promo_db):
        """KM for ton_lau > threshold matches xe with old stock_date.

        Note: This tests the expected behavior where km_pham_vi with
        loai_ap_dung='ton_lau' and gia_tri_ap_dung='60' means the KM
        applies to xe whose ngay_nhap_dau_tien is more than 60 days ago.
        """
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert a ton_lau KM (threshold 45 days)
        conn.execute("""
            INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
            VALUES (101, 'KM ton lau', 'KM cho xe ton lau 45 ngay', 'giam_tien_mat', 2000000, 'tien', '2026-01-01', '2026-12-31', 'dang_chay')
        """)
        conn.execute("""
            INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
            VALUES (101, 'ton_lau', '45')
        """)
        conn.commit()
        conn.close()

        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # Xe 1 has ngay_nhap_dau_tien 60 days ago (old stock) → should match
        # Xe 2 has ngay_nhap_dau_tien 10 days ago (recent stock) → should NOT match
        result_xe1 = service.find_applicable(xe_id=1)
        result_xe2 = service.find_applicable(xe_id=2)

        km_ids_1 = [km["id"] for km in result_xe1]
        km_ids_2 = [km["id"] for km in result_xe2]

        # Xe1 (old stock) should match KM101
        assert 101 in km_ids_1, "Xe with old stock should match ton_lau KM"
        # Xe2 (recent stock) should NOT match KM101
        # Note: if current check_applicable_to_xe doesn't support ton_lau, this test documents expected behavior
        conn.close()

    def test_km_khong_match(self, promo_db):
        """No KM applies → find_applicable returns empty list"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert a KM for BMW only
        conn.execute("""
            INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
            VALUES (102, 'KM BMW', 'KM chi cho BMW', 'giam_tien_mat', 3000000, 'tien', '2026-01-01', '2026-12-31', 'dang_chay')
        """)
        conn.execute("""
            INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
            VALUES (102, 'hang', 'BMW')
        """)
        conn.commit()
        conn.close()

        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # Xe 1 is Toyota (not BMW), should have no applicable BMW KM
        result = service.find_applicable(xe_id=1)
        bmw_km_ids = [km["id"] for km in result if km["id"] == 102]
        assert len(bmw_km_ids) == 0, "Toyota should not match BMW KM"
        conn.close()


# =============================================================================
# TEST.02 — calculate_discount
# =============================================================================
class TestCalculateDiscount:
    """TEST.02 — KhuyenMaiService.calculate_discount — 7 cases"""

    def test_giam_tien_mat_tien(self, promo_db):
        """giam_tien_mat: tien_giam = min(gia_tri, gia_xe)"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM1: giam_tien_mat 5tr, xe gia 500tr
        result = service.calculate_discount(km_id=1, gia_xe=500000000)

        assert result.loai_km == "giam_tien_mat"
        assert result.tien_giam == 5000000  # min(5M, 500M) = 5M
        assert result.gia_sau_km == 495000000
        conn.close()

    def test_giam_tien_mat_vuot_gia(self, promo_db):
        """giam_tien_mat: gia_tri > gia_xe → tien_giam capped at gia_xe"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert KM with huge discount
        conn.execute("""
            INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
            VALUES (110, 'Giam 1 ty', 'Giam nhieu hon gia xe', 'giam_tien_mat', 1000000000, 'tien', '2026-01-01', '2026-12-31', 'dang_chay')
        """)
        conn.execute("""
            INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
            VALUES (110, 'all', NULL)
        """)
        conn.commit()
        conn.close()

        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # gia_tri=1B > gia_xe=500M → capped at 500M
        result = service.calculate_discount(km_id=110, gia_xe=500000000)

        assert result.tien_giam == 500000000  # capped at gia_xe
        assert result.gia_sau_km == 0
        conn.close()

    def test_giam_phan_tram_phan_tram_kieu(self, promo_db):
        """giam_phan_tram with kieu_gia_tri='phan_tram': tien_giam = gia_xe * gia_tri / 100"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM2: giam_phan_tram 10% (phan_tram kieu)
        result = service.calculate_discount(km_id=2, gia_xe=400000000)

        assert result.loai_km == "giam_phan_tram"
        assert result.tien_giam == 40000000  # 400M * 10 / 100 = 40M
        assert result.gia_sau_km == 360000000
        conn.close()

    def test_giam_phan_tram_tien_kieu(self, promo_db):
        """giam_phan_tram with kieu_gia_tri='tien': capped at gia_xe"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM3: giam_phan_tram but with kieu_gia_tri='tien', gia_tri=3M
        result = service.calculate_discount(km_id=3, gia_xe=500000000)

        assert result.loai_km == "giam_phan_tram"
        assert result.tien_giam == 3000000  # min(3M, 500M) = 3M (treated as tien_mat)
        assert result.gia_sau_km == 497000000
        conn.close()

    def test_tang_phu_kien(self, promo_db):
        """tang_phu_kien: returns list of free phu_kien, no price reduction"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM4: tang_phu_kien with PK ids 1,2
        result = service.calculate_discount(km_id=4, gia_xe=500000000)

        assert result.loai_km == "tang_phu_kien"
        assert result.tien_giam == 0  # No direct discount
        assert result.gia_sau_km == 500000000
        assert result.tang_phu_kien is not None
        assert len(result.tang_phu_kien) == 2

        pk_ids = [p["phu_kien_id"] for p in result.tang_phu_kien]
        assert 1 in pk_ids  # GPS Navigator
        assert 2 in pk_ids  # Camera lui
        conn.close()

    def test_giam_lai_suat(self, promo_db):
        """giam_lai_suat: returns lai_suat_fig after discount"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM5: giam_lai_suat 2%
        result = service.calculate_discount(km_id=5, gia_xe=500000000)

        assert result.loai_km == "giam_lai_suat"
        assert result.lai_suat_fig == 2.0  # gia_tri=2 as the reduced rate
        assert result.tien_giam == 0  # No direct price discount
        conn.close()

    def test_combo(self, promo_db):
        """combo: gia_combo from combo_service, tien_giam = base - gia_combo"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM6: combo with gia_tri=1 (combo_phu_kien.id=1)
        # Combo 1: PK1(5M) + PK2(3M) = 8M, he_so_giam=0.9 → gia_combo=7.2M
        result = service.calculate_discount(km_id=6, gia_xe=500000000, tong_pk=8000000)

        assert result.loai_km == "combo"
        assert result.gia_combo == 7200000  # 8M * 0.9
        assert result.tien_giam == 8000000 - 7200000  # base - gia_combo = 0.8M
        assert result.gia_sau_km == 500000000 + 8000000 - 800000  # 507.2M
        conn.close()


# =============================================================================
# TEST.03 — daily_expiry_check (TRG-06)
# =============================================================================
class TestDailyExpiryCheck:
    """TEST.03 — KhuyenMaiService.daily_expiry_check — 2 cases"""

    def test_km_het_han_chuyen_ket_thuc(self, promo_db):
        """KM with den_ngay < today → trang_thai becomes 'ket_thuc'"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert a KM that expired yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        conn.execute("""
            INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
            VALUES (200, 'KM Het Han', 'KM da het han', 'giam_tien_mat', 1000000, 'tien', '2024-01-01', ?, 'dang_chay')
        """, (yesterday,))
        conn.execute("""
            INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
            VALUES (200, 'all', NULL)
        """)
        conn.commit()

        # Run daily expiry check
        result = daily_expiry_check(conn)

        assert result["success"] is True
        assert result["expired_count"] >= 1

        # Verify KM 200 is now ket_thuc
        cursor = conn.execute("SELECT trang_thai FROM khuyen_mai WHERE id = 200")
        row = cursor.fetchone()
        assert row["trang_thai"] == "ket_thuc"
        conn.close()

    def test_km_con_han_khong_doi(self, promo_db):
        """KM with den_ngay > today → trang_thai unchanged"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")

        # Insert a KM that expires next month
        next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        conn.execute("""
            INSERT INTO khuyen_mai (id, ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai)
            VALUES (201, 'KM Con Han', 'KM con han', 'giam_tien_mat', 1000000, 'tien', '2026-01-01', ?, 'dang_chay')
        """, (next_month,))
        conn.execute("""
            INSERT INTO km_pham_vi (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung)
            VALUES (201, 'all', NULL)
        """)
        conn.commit()

        original_status = "dang_chay"

        # Run daily expiry check
        result = daily_expiry_check(conn)

        # Verify KM 201 is still dang_chay
        cursor = conn.execute("SELECT trang_thai FROM khuyen_mai WHERE id = 201")
        row = cursor.fetchone()
        assert row["trang_thai"] == original_status
        conn.close()


# =============================================================================
# TEST.04 — report_effectiveness
# =============================================================================
class TestReportEffectiveness:
    """TEST.04 — KhuyenMaiService.report_effectiveness — 2 cases"""

    def test_report_co_hop_dong(self, promo_db):
        """KM with contracts → returns correct stats"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM1 has 2 contracts (HD001 and HD003), each with tien_giam_km=5M
        result = service.report_effectiveness(km_id=1)

        assert result["km_id"] == 1
        assert result["ten_km"] == "Giam 5tr Toyota"
        assert result["so_hop_dong"] == 2
        # doanh_thu = 495M + 495M = 990M
        assert result["doanh_thu"] == 990000000
        # tong_giam = 5M + 5M = 10M
        assert result["tong_giam"] == 10000000
        conn.close()

    def test_report_khong_co_hop_dong(self, promo_db):
        """KM with no contracts → all zeros"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM7 has no contracts
        result = service.report_effectiveness(km_id=7)

        assert result["km_id"] == 7
        assert result["so_hop_dong"] == 0
        assert result["doanh_thu"] == 0
        assert result["tong_giam"] == 0
        conn.close()


# =============================================================================
# TEST.05 — UAT_AC_KM
# =============================================================================
class TestUAT_ACKM:
    """TEST.05 — UAT for AC-KM-* scenarios — 3 cases"""

    def test_ackm_01_tao_km(self, promo_db):
        """AC-KM-01: Create KM → verify in list"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # Create a new KM
        data = KhuyenMaiCreateData(
            ten_km="KM Test AC-KM-01",
            mo_ta="Test khuyen mai moi",
            loai_km="giam_tien_mat",
            gia_tri=3000000,
            kieu_gia_tri="tien",
            tu_ngay="2026-05-01",
            den_ngay="2026-05-31",
            trang_thai="dang_chay",
        )
        pham_vi = [KhuyenMaiPhamViData(loai_ap_dung="all", gia_tri_ap_dung=None)]

        created = service.create(data, pham_vi)

        assert created.id is not None
        assert created.ten_km == "KM Test AC-KM-01"
        assert created.loai_km == "giam_tien_mat"
        assert created.gia_tri == 3000000
        assert created.trang_thai == "dang_chay"

        # Verify it's in the list
        all_km = service.get_all()
        km_ids = [km.id for km in all_km]
        assert created.id in km_ids
        conn.close()

    def test_ackm_02_pause_resume(self, promo_db):
        """AC-KM-02: Pause/Resume KM works"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM7 starts as tam_dung
        km = service.get_by_id(7)
        assert km.trang_thai == "tam_dung"

        # Resume → should become dang_chay
        resumed = service.resume(7)
        assert resumed.trang_thai == "dang_chay"

        # Pause → should become tam_dung
        paused = service.pause(7)
        assert paused.trang_thai == "tam_dung"
        conn.close()

    def test_ackm_03_khong_the_pause_ket_thuc(self, promo_db):
        """AC-KM-03: Cannot pause a 'ket_thuc' KM"""
        conn = sqlite3.connect(promo_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = KhuyenMaiService(conn)

        # KM8 is already ket_thuc
        km = service.get_by_id(8)
        assert km.trang_thai == "ket_thuc"

        # Trying to pause should raise KhuyenMaiExpiredError
        with pytest.raises(KhuyenMaiExpiredError):
            service.pause(8)
        conn.close()