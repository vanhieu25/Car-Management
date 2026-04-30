"""Test seed: verify insert 100%% record without errors."""

import pytest
import sqlite3
import tempfile
import os
import sys


@pytest.fixture
def seeded_db():
    """Create a database with migrations and seed data applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Run migrations
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from app.infrastructure.database.migrations.runner import MigrationRunner

    runner = MigrationRunner(db_path)
    runner.run_pending()

    # Run seeds
    from app.infrastructure.database.seeds.dev_seed import seed_all
    seed_all(db_path)

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_seed_inserts_all_data_without_error(seeded_db):
    """Test that seed_all() completes without any errors."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Verify all seed data is present
    assert conn.execute("SELECT COUNT(*) FROM vai_tro").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM nhan_vien").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM xe").fetchone()[0] == 30
    assert conn.execute("SELECT COUNT(*) FROM khach_hang").fetchone()[0] == 20
    assert conn.execute("SELECT COUNT(*) FROM phu_kien").fetchone()[0] == 25
    assert conn.execute("SELECT COUNT(*) FROM khuyen_mai").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM nha_cung_cap").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM hop_dong").fetchone()[0] == 15

    conn.close()


def test_seed_vai_tro_records(seeded_db):
    """Test vai_tro seed data has correct structure."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.execute("SELECT ma_vai_tro, ten_vai_tro FROM vai_tro ORDER BY id")
    roles = cursor.fetchall()

    assert len(roles) == 3
    ma_vai_tros = [r[0] for r in roles]
    assert "admin" in ma_vai_tros
    assert "sales" in ma_vai_tros
    assert "ky_thuat_bh" in ma_vai_tros

    conn.close()


def test_seed_nhan_vien_records(seeded_db):
    """Test nhan_vien seed data has correct foreign keys."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # All nhan_vien should have valid vai_tro_id
    cursor = conn.execute("""
        SELECT COUNT(*) FROM nhan_vien nv 
        WHERE NOT EXISTS (SELECT 1 FROM vai_tro vt WHERE vt.id = nv.vai_tro_id)
    """)
    assert cursor.fetchone()[0] == 0, "All nhan_vien should have valid vai_tro_id"

    # All should have unique usernames
    cursor = conn.execute("SELECT COUNT(DISTINCT username) FROM nhan_vien")
    total = conn.execute("SELECT COUNT(*) FROM nhan_vien").fetchone()[0]
    assert cursor.fetchone()[0] == total, "Usernames should be unique"

    conn.close()


def test_seed_xe_records(seeded_db):
    """Test xe seed data has correct values."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # All xe should have valid years (1990-2100 per CHECK constraint)
    cursor = conn.execute("SELECT COUNT(*) FROM xe WHERE nam_san_xuat < 1990 OR nam_san_xuat > 2100")
    assert cursor.fetchone()[0] == 0, "All xe should have valid manufacturing years"

    # All xe should have gia_ban >= 0
    cursor = conn.execute("SELECT COUNT(*) FROM xe WHERE gia_ban < 0")
    assert cursor.fetchone()[0] == 0, "All xe should have non-negative prices"

    # All xe should have so_luong_ton >= 0
    cursor = conn.execute("SELECT COUNT(*) FROM xe WHERE so_luong_ton < 0")
    assert cursor.fetchone()[0] == 0, "All xe should have non-negative stock"

    # Check for expected brands
    cursor = conn.execute("SELECT DISTINCT hang FROM xe")
    brands = [r[0] for r in cursor.fetchall()]
    expected_brands = ["Toyota", "Honda", "Ford", "BMW", "Mercedes"]
    for brand in expected_brands:
        assert brand in brands, f"Expected brand '{brand}' not found in seed data"

    conn.close()


def test_seed_khach_hang_records(seeded_db):
    """Test khach_hang seed data has correct structure."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # All customers should have valid phone numbers (unique)
    cursor = conn.execute("SELECT COUNT(DISTINCT so_dien_thoai) FROM khach_hang")
    total = conn.execute("SELECT COUNT(*) FROM khach_hang").fetchone()[0]
    assert cursor.fetchone()[0] == total, "Phone numbers should be unique"

    # All should have valid classification
    cursor = conn.execute("""
        SELECT COUNT(*) FROM khach_hang 
        WHERE phan_loai NOT IN ('Thuong', 'Than_thiet', 'VIP')
    """)
    assert cursor.fetchone()[0] == 0, "All customers should have valid classification"

    conn.close()


def test_seed_phu_kien_records(seeded_db):
    """Test phu_kien seed data has 25 items in correct categories."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.execute("SELECT COUNT(*) FROM phu_kien")
    assert cursor.fetchone()[0] == 25, f"Expected 25 phu_kien, found {cursor.fetchone()[0]}"

    # Check all categories are present
    cursor = conn.execute("SELECT DISTINCT phan_loai FROM phu_kien")
    categories = [r[0] for r in cursor.fetchall()]
    expected_cats = ["den", "cam_bien", "phu_kien_noi_that", "phu_kien_ngoai_that", "dung_cu"]
    assert len(categories) == 5, f"Expected 5 categories, found {len(categories)}"
    for cat in expected_cats:
        assert cat in categories, f"Category '{cat}' not found"

    # Each category should have 5 items
    for cat in expected_cats:
        cursor = conn.execute("SELECT COUNT(*) FROM phu_kien WHERE phan_loai = ?", (cat,))
        count = cursor.fetchone()[0]
        assert count == 5, f"Category '{cat}' should have 5 items, found {count}"

    conn.close()


def test_seed_khuyen_mai_records(seeded_db):
    """Test khuyen_mai seed data has 5 promotions."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.execute("SELECT COUNT(*) FROM khuyen_mai")
    assert cursor.fetchone()[0] == 5, f"Expected 5 khuyen_mai, found {cursor.fetchone()[0]}"

    # All should have valid loai_km
    cursor = conn.execute("""
        SELECT COUNT(*) FROM khuyen_mai 
        WHERE loai_km NOT IN ('giam_tien_mat', 'giam_phan_tram', 'tang_phu_kien', 'giam_lai_suat', 'combo')
    """)
    assert cursor.fetchone()[0] == 0, "All promotions should have valid type"

    # All should have valid trang_thai
    cursor = conn.execute("""
        SELECT COUNT(*) FROM khuyen_mai 
        WHERE trang_thai NOT IN ('nhap', 'dang_chay', 'tam_dung', 'ket_thuc')
    """)
    assert cursor.fetchone()[0] == 0, "All promotions should have valid status"

    conn.close()


def test_seed_nha_cung_cap_records(seeded_db):
    """Test nha_cung_cap seed data has 5 suppliers."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.execute("SELECT COUNT(*) FROM nha_cung_cap")
    assert cursor.fetchone()[0] == 5, f"Expected 5 nha_cung_cap, found {cursor.fetchone()[0]}"

    # All should have unique ma_ncc
    cursor = conn.execute("SELECT COUNT(DISTINCT ma_ncc) FROM nha_cung_cap")
    assert cursor.fetchone()[0] == 5, "All suppliers should have unique ma_ncc"

    # Rating scores should be between 1 and 5
    cursor = conn.execute("""
        SELECT COUNT(*) FROM nha_cung_cap 
        WHERE diem_chat_luong < 1 OR diem_chat_luong > 5
           OR diem_thoi_gian_giao < 1 OR diem_thoi_gian_giao > 5
           OR diem_gia_ca < 1 OR diem_gia_ca > 5
    """)
    assert cursor.fetchone()[0] == 0, "All rating scores should be between 1 and 5"

    conn.close()


def test_seed_hop_dong_records(seeded_db):
    """Test hop_dong seed data has 15 contracts with valid FKs."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.execute("SELECT COUNT(*) FROM hop_dong")
    assert cursor.fetchone()[0] == 15, f"Expected 15 hop_dong, found {cursor.fetchone()[0]}"

    # All contracts should have valid xe_id
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hop_dong hd 
        WHERE NOT EXISTS (SELECT 1 FROM xe WHERE xe.id = hd.xe_id)
    """)
    assert cursor.fetchone()[0] == 0, "All hop_dong should reference valid xe"

    # All contracts should have valid khach_hang_id
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hop_dong hd 
        WHERE NOT EXISTS (SELECT 1 FROM khach_hang WHERE khach_hang.id = hd.khach_hang_id)
    """)
    assert cursor.fetchone()[0] == 0, "All hop_dong should reference valid khach_hang"

    # All contracts should have valid nhan_vien_id
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hop_dong hd 
        WHERE NOT EXISTS (SELECT 1 FROM nhan_vien WHERE nhan_vien.id = hd.nhan_vien_id)
    """)
    assert cursor.fetchone()[0] == 0, "All hop_dong should reference valid nhan_vien"

    # All contracts should have valid trang_thai
    cursor = conn.execute("""
        SELECT COUNT(*) FROM hop_dong 
        WHERE trang_thai NOT IN ('moi_tao', 'da_thanh_toan', 'da_giao_xe', 'huy')
    """)
    assert cursor.fetchone()[0] == 0, "All hop_dong should have valid status"

    conn.close()


def test_seed_has_no_fk_violations(seeded_db):
    """Test that seed data has no foreign key violations."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Check all tables with FKs
    fk_checks = [
        ("nhan_vien", "vai_tro_id", "vai_tro", "id"),
        ("xe", "created_by", "nhan_vien", "id"),
        ("khach_hang", "created_by", "nhan_vien", "id"),
        ("hop_dong", "khach_hang_id", "khach_hang", "id"),
        ("hop_dong", "xe_id", "xe", "id"),
        ("hop_dong", "nhan_vien_id", "nhan_vien", "id"),
        ("hop_dong", "khuyen_mai_id", "khuyen_mai", "id"),
    ]

    for table, fk_col, ref_table, ref_col in fk_checks:
        cursor = conn.execute(f"""
            SELECT COUNT(*) FROM {table} t
            WHERE {fk_col} IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM {ref_table} r WHERE r.{ref_col} = t.{fk_col})
        """)
        count = cursor.fetchone()[0]
        assert count == 0, f"Table '{table}' has {count} rows with invalid {fk_col} referencing {ref_table}"

    conn.close()
