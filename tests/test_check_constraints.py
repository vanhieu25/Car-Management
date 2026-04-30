"""Test CHECK constraints: verify IntegrityError is raised for invalid data."""

import pytest
import sqlite3
import tempfile
import os
import sys


@pytest.fixture
def fresh_db():
    """Create a fresh database with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from app.infrastructure.database.migrations.runner import MigrationRunner

    runner = MigrationRunner(db_path)
    runner.run_pending()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


def test_xe_nam_san_xuat_check_constraint(fresh_db):
    """Test nam_san_xuat must be >= 1990 and <= 2100."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Valid year should work
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('TEST-001', 'Toyota', 'Camry', 2020, 500000000)"""
    )
    conn.commit()

    # Year too old (1980) should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO xe 
               (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
               VALUES ('TEST-002', 'Toyota', 'Camry', 1980, 500000000)"""
        )
        conn.commit()

    # Year too far in future should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO xe 
               (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
               VALUES ('TEST-003', 'Toyota', 'Camry', 2150, 500000000)"""
        )
        conn.commit()

    # Year 1990 boundary should work
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('TEST-004', 'Toyota', 'Camry', 1990, 500000000)"""
    )
    conn.commit()

    # Year 2100 boundary should work
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('TEST-005', 'Toyota', 'Camry', 2100, 500000000)"""
    )
    conn.commit()

    conn.close()


def test_xe_gia_ban_check_constraint(fresh_db):
    """Test gia_ban must be >= 0."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Zero price should work
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('TEST-G1', 'Toyota', 'Camry', 2020, 0)"""
    )
    conn.commit()

    # Negative price should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO xe 
               (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
               VALUES ('TEST-G2', 'Toyota', 'Camry', 2020, -1)"""
        )
        conn.commit()

    conn.close()


def test_xe_so_luong_ton_check_constraint(fresh_db):
    """Test so_luong_ton must be >= 0."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Zero stock should work
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban, so_luong_ton) 
           VALUES ('TEST-S1', 'Toyota', 'Camry', 2020, 500000000, 0)"""
    )
    conn.commit()

    # Negative stock should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO xe 
               (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban, so_luong_ton) 
               VALUES ('TEST-S2', 'Toyota', 'Camry', 2020, 500000000, -1)"""
        )
        conn.commit()

    conn.close()


def test_khach_hang_phan_loai_check_constraint(fresh_db):
    """Test phan_loai must be 'Thuong', 'Than_thiet', or 'VIP'."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Valid values should work
    for loai in ["Thuong", "Than_thiet", "VIP"]:
        conn.execute(
            """INSERT INTO khach_hang 
               (ho_ten, so_dien_thoai, email, phan_loai) 
               VALUES (?, ?, ?, ?)""",
            (f"Test {loai}", f"09999999{loai[0]}", f"{loai}@test.com", loai),
        )
        conn.commit()

    # Invalid value should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO khach_hang 
               (ho_ten, so_dien_thoai, email, phan_loai) 
               VALUES ('Invalid', '0888888888', 'invalid@test.com', 'Regular')"""
        )
        conn.commit()

    # Empty string should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO khach_hang 
               (ho_ten, so_dien_thoai, email, phan_loai) 
               VALUES ('Invalid2', '0777777777', 'invalid2@test.com', '')"""
        )
        conn.commit()

    conn.close()


def test_nhan_vien_trang_thai_check_constraint(fresh_db):
    """Test trang_thai must be 'active' or 'inactive'."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Valid values should work
    for status in ["active", "inactive"]:
        conn.execute(
            """INSERT INTO nhan_vien 
               (username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai) 
               VALUES (?, ?, ?, ?, 1, ?)""",
            (f"test_{status}", "hash", "Test", f"{status}@test.com", status),
        )
        conn.commit()

    # Invalid value should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO nhan_vien 
               (username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai) 
               VALUES ('bad_status', 'hash', 'Bad', 'bad@test.com', 1, 'suspended')"""
        )
        conn.commit()

    conn.close()


def test_khuyen_mai_loai_km_check_constraint(fresh_db):
    """Test loai_km must be one of the allowed values."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    valid_types = ["giam_tien_mat", "giam_phan_tram", "tang_phu_kien", "giam_lai_suat", "combo"]
    for i, loai in enumerate(valid_types):
        conn.execute(
            """INSERT INTO khuyen_mai 
               (ten_km, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay) 
               VALUES (?, ?, 1000, 'tien', '2026-01-01', '2026-12-31')""",
            (f"KM {loai}", loai),
        )
        conn.commit()

    # Invalid type should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO khuyen_mai 
               (ten_km, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay) 
               VALUES ('Bad Type', 'giam_gia', 1000, 'tien', '2026-01-01', '2026-12-31')"""
        )
        conn.commit()

    conn.close()


def test_khuyen_mai_den_ngay_check_constraint(fresh_db):
    """Test den_ngay must be >= tu_ngay."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Valid date range should work
    conn.execute(
        """INSERT INTO khuyen_mai 
           (ten_km, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay) 
           VALUES ('Valid', 'giam_tien_mat', 1000, 'tien', '2026-01-01', '2026-12-31')"""
    )
    conn.commit()

    # Invalid date range (end before start) should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO khuyen_mai 
               (ten_km, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay) 
               VALUES ('Invalid', 'giam_tien_mat', 1000, 'tien', '2026-12-31', '2026-01-01')"""
        )
        conn.commit()

    conn.close()


def test_phu_kien_phan_loai_check_constraint(fresh_db):
    """Test phu_kien.phan_loai must be one of the allowed values."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    valid_cats = ["den", "cam_bien", "phu_kien_noi_that", "phu_kien_ngoai_that", "dung_cu"]
    for i, cat in enumerate(valid_cats):
        conn.execute(
            """INSERT INTO phu_kien 
               (ma_pk, ten_pk, phan_loai, gia_ban) 
               VALUES (?, ?, ?, 100000)""",
            (f"PK{i:03d}", f"Phu kien {cat}", cat),
        )
        conn.commit()

    # Invalid category should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO phu_kien 
               (ma_pk, ten_pk, phan_loai, gia_ban) 
               VALUES ('PK-INVALID', 'Invalid', 'phu_kien', 100000)"""
        )
        conn.commit()

    conn.close()


def test_nha_cung_cap_diem_check_constraints(fresh_db):
    """Test diem ratings must be between 1 and 5."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Valid scores should work (all 1-5)
    conn.execute(
        """INSERT INTO nha_cung_cap 
           (ma_ncc, ten_ncc, diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca) 
           VALUES ('NCC-TEST', 'Test Supplier', 3, 4, 5)"""
    )
    conn.commit()

    # Score 0 should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO nha_cung_cap 
               (ma_ncc, ten_ncc, diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca) 
               VALUES ('NCC-TEST2', 'Test Supplier 2', 0, 4, 5)"""
        )
        conn.commit()

    # Score 6 should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO nha_cung_cap 
               (ma_ncc, ten_ncc, diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca) 
               VALUES ('NCC-TEST3', 'Test Supplier 3', 3, 4, 6)"""
        )
        conn.commit()

    conn.close()


def test_tra_gop_lai_suat_check_constraint(fresh_db):
    """Test lai_suat_nam must be between 0 and 30."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Insert required related records
    conn.execute(
        """INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('admin', 'Admin')"""
    )
    conn.execute(
        """INSERT INTO nhan_vien 
           (username, mat_khau_hash, ho_ten, email, vai_tro_id) 
           VALUES ('sales', 'hash', 'Sales', 'sales@test.com', 1)"""
    )
    conn.execute(
        """INSERT INTO khach_hang 
           (ho_ten, so_dien_thoai, email) 
           VALUES ('Customer', '0999999999', 'customer@test.com')"""
    )
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('XE-TEST', 'Toyota', 'Camry', 2020, 500000000)"""
    )
    conn.execute(
        """INSERT INTO hop_dong 
           (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien) 
           VALUES ('HD-TEST', 1, 1, 1, 500000000, 500000000)"""
    )
    conn.commit()

    # Valid interest rate should work
    conn.execute(
        """INSERT INTO tra_gop 
           (hop_dong_id, ngan_hang, so_tien_vay, lai_suat_nam, so_ky, so_tien_tra_thang) 
           VALUES (1, 'VCB', 400000000, 8.5, 60, 8000000)"""
    )
    conn.commit()

    # Negative interest rate should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO tra_gop 
               (hop_dong_id, ngan_hang, so_tien_vay, lai_suat_nam, so_ky, so_tien_tra_thang) 
               VALUES (1, 'VCB', 400000000, -1, 60, 8000000)"""
        )
        conn.commit()

    # Interest rate > 30 should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO tra_gop 
               (hop_dong_id, ngan_hang, so_tien_vay, lai_suat_nam, so_ky, so_tien_tra_thang) 
               VALUES (1, 'VCB', 400000000, 35, 60, 8000000)"""
        )
        conn.commit()

    conn.close()


def test_tra_gop_so_ky_check_constraint(fresh_db):
    """Test so_ky must be between 6 and 84."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Insert required related records (reuse from above)
    conn.execute(
        """INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('admin', 'Admin')"""
    )
    conn.execute(
        """INSERT INTO nhan_vien 
           (username, mat_khau_hash, ho_ten, email, vai_tro_id) 
           VALUES ('sales2', 'hash', 'Sales2', 'sales2@test.com', 1)"""
    )
    conn.execute(
        """INSERT INTO khach_hang 
           (ho_ten, so_dien_thoai, email) 
           VALUES ('Customer2', '0999999998', 'customer2@test.com')"""
    )
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('XE-TEST2', 'Honda', 'Civic', 2021, 600000000)"""
    )
    conn.execute(
        """INSERT INTO hop_dong 
           (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien) 
           VALUES ('HD-TEST2', 1, 1, 1, 600000000, 600000000)"""
    )
    conn.commit()

    # Valid term (6 months) should work
    conn.execute(
        """INSERT INTO tra_gop 
           (hop_dong_id, ngan_hang, so_tien_vay, lai_suat_nam, so_ky, so_tien_tra_thang) 
           VALUES (1, 'VCB', 400000000, 8.5, 6, 70000000)"""
    )
    conn.commit()

    # Valid term (84 months) should work
    conn.execute(
        """INSERT INTO tra_gop 
           (hop_dong_id, ngan_hang, so_tien_vay, lai_suat_nam, so_ky, so_tien_tra_thang) 
           VALUES (1, 'ACB', 400000000, 9.0, 84, 6000000)"""
    )
    conn.commit()

    # Too short term (< 6 months) should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO tra_gop 
               (hop_dong_id, ngan_hang, so_tien_vay, lai_suat_nam, so_ky, so_tien_tra_thang) 
               VALUES (1, 'TPB', 400000000, 8.5, 3, 140000000)"""
        )
        conn.commit()

    # Too long term (> 84 months) should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO tra_gop 
               (hop_dong_id, ngan_hang, so_tien_vay, lai_suat_nam, so_ky, so_tien_tra_thang) 
               VALUES (1, 'TPB', 400000000, 8.5, 96, 5000000)"""
        )
        conn.commit()

    conn.close()


def test_bao_hanh_date_check_constraint(fresh_db):
    """Test ngay_ket_thuc must be >= ngay_bat_dau."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Insert required related records
    conn.execute(
        """INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('admin', 'Admin')"""
    )
    conn.execute(
        """INSERT INTO nhan_vien 
           (username, mat_khau_hash, ho_ten, email, vai_tro_id) 
           VALUES ('sales3', 'hash', 'Sales3', 'sales3@test.com', 1)"""
    )
    conn.execute(
        """INSERT INTO khach_hang 
           (ho_ten, so_dien_thoai, email) 
           VALUES ('Customer3', '0999999997', 'customer3@test.com')"""
    )
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('XE-TEST3', 'Ford', 'Everest', 2022, 800000000)"""
    )
    conn.execute(
        """INSERT INTO hop_dong 
           (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien) 
           VALUES ('HD-TEST3', 1, 1, 1, 800000000, 800000000)"""
    )
    conn.commit()

    # Valid warranty period should work
    conn.execute(
        """INSERT INTO bao_hanh 
           (hop_dong_id, xe_id, khach_hang_id, thoi_han_bh, ngay_bat_dau, ngay_ket_thuc) 
           VALUES (1, 1, 1, 24, '2026-01-01', '2028-01-01')"""
    )
    conn.commit()

    # Invalid warranty period (end before start) should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO bao_hanh 
               (hop_dong_id, xe_id, khach_hang_id, thoi_han_bh, ngay_bat_dau, ngay_ket_thuc) 
               VALUES (1, 1, 1, 24, '2028-01-01', '2026-01-01')"""
        )
        conn.commit()

    conn.close()


def test_hop_dong_trang_thai_check_constraint(fresh_db):
    """Test hop_dong.trang_thai must be one of the allowed values."""
    conn = sqlite3.connect(fresh_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Insert required related records
    conn.execute(
        """INSERT INTO vai_tro (ma_vai_tro, ten_vai_tro) VALUES ('admin', 'Admin')"""
    )
    conn.execute(
        """INSERT INTO nhan_vien 
           (username, mat_khau_hash, ho_ten, email, vai_tro_id) 
           VALUES ('sales4', 'hash', 'Sales4', 'sales4@test.com', 1)"""
    )
    conn.execute(
        """INSERT INTO khach_hang 
           (ho_ten, so_dien_thoai, email) 
           VALUES ('Customer4', '0999999996', 'customer4@test.com')"""
    )
    conn.execute(
        """INSERT INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, gia_ban) 
           VALUES ('XE-TEST4', 'BMW', 'X5', 2023, 2000000000)"""
    )
    conn.commit()

    # Valid statuses should work
    for status in ["moi_tao", "da_thanh_toan", "da_giao_xe", "huy"]:
        conn.execute(
            """INSERT INTO hop_dong 
               (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien, trang_thai) 
               VALUES (?, 1, 1, 1, 2000000000, 2000000000, ?)""",
            (f"HD-{status}", status),
        )
        conn.commit()

    # Invalid status should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO hop_dong 
               (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_tien, trang_thai) 
               VALUES ('HD-BAD', 1, 1, 1, 2000000000, 2000000000, 'da_xac_nhan')"""
        )
        conn.commit()

    conn.close()
