#!/usr/bin/env python3
"""
SIT Large Seed Data Generator for Performance Testing.

Generates large volumes of realistic test data for performance testing:
- 1000 Khách hàng (faker)
- 5000 Hợp đồng (faker)
- 100 Nhà cung cấp (faker)
- 200 Bảo hành records (faker)

Usage:
    python scripts/sit_seed.py                      # Run all seeds (full perf test data)
    python scripts/sit_seed.py --kh 500 --hd 1000   # Custom amounts
    python scripts/sit_seed.py --db-path /path/to/sit.db  # Target SIT DB
    python scripts/sit_seed.py --cleanup           # Clean up existing seed data first
"""

import argparse
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Faker import with fallback
try:
    from faker import Faker
    FAKE = Faker("vi_VN")
    FAKER_AVAILABLE = True
except ImportError:
    FAKE = None
    FAKER_AVAILABLE = False


# ─── Configuration ──────────────────────────────────────────────

DEFAULT_SIT_DB = Path(__file__).parent.parent / "data" / "car_management_sit.db"

SEED_COUNTS = {
    "khach_hang": 1000,
    "hop_dong": 5000,
    "nha_cung_cap": 100,
    "bao_hanh": 200,
}

# Realistic data generators
VIETNAMESE_CITIES = [
    "TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Cần Thơ", "Hải Phòng",
    "Biên Hoà", "Nha Trang", "Huế", "Qui Nhơn", "Vũng Tàu",
    "Thủ Dầu Một", "Long Xuyên", "Trà Vinh", "Cà Mau", "Bến Tre",
]

VIETNAMESE_STREETS = [
    "Nguyễn Trãi", "Lê Lợi", "Trần Hưng Đạo", "Cách Mạng Tháng 8",
    "Võ Văn Kiệt", "Nguyễn Văn Linh", "Điện Biên Phủ", "Phạm Văn Đồng",
    "Lê Văn Việt", "Nguyễn Oanh", "Phan Huy Ích", "Lý Thường Kiệt",
]

CAR_BRANDS_SEED = ["Toyota", "Honda", "Ford", "Hyundai", "Kia", "Mazda", "Mitsubishi", "Suzuki"]
CAR_MODELS_SEED = {
    "Toyota": ["Camry", "Corolla", "Fortuner", "RAV4", "Land Cruiser"],
    "Honda": ["Civic", "Accord", "CR-V", "City", "HR-V"],
    "Ford": ["Everest", "Ranger", "EcoSport", "Explorer", "Mustang"],
    "Hyundai": ["Sonata", "Tucson", "Santa Fe", "Grand i10", "Accent"],
    "Kia": ["Sportage", "Sorento", "Carnival", "Seltos", "K3"],
    "Mazda": ["CX-5", "CX-8", "Mazda3", "Mazda6", "CX-3"],
    "Mitsubishi": ["Xpander", "Pajero", "Outlander", "Triton", "Attrage"],
    "Suzuki": ["Swift", "Vitara", "Ertiga", "Jimny", "Ciaz"],
}

CAR_COLORS_SEED = ["Đen", "Trắng", "Bạc", "Đỏ", "Xanh Navy", "Xám", "Nâu", "Vàng"]


# ─── Helpers ────────────────────────────────────────────────────

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _date(days_offset=0):
    d = datetime.now() + timedelta(days=days_offset)
    return d.strftime("%Y-%m-%d")

def _datetime(days_offset=0, seconds_offset=0):
    d = datetime.now() + timedelta(days=days_offset, seconds=seconds_offset)
    return d.strftime("%Y-%m-%d %H:%M:%S")


# ─── Password Hash ──────────────────────────────────────────────

def _hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


# ─── Seed Functions ─────────────────────────────────────────────

def seed_khach_hang(conn: sqlite3.Connection, count: int = 1000, batch_size: int = 200):
    """Seed `count` khach_hang records with faker data.
    
    Classification distribution:
    - VIP: top 5% (based on tong_gia_tri_mua >= 2B or so_xe >= 3)
    - Than_thiet: next 15% (500M <= tong_gia_tri < 2B or so_xe >= 1)
    - Thuong: remaining 80%
    """
    print(f"  Seeding {count} khach_hang...")
    
    cursor = conn.cursor()
    now = _now()
    
    if FAKE:
        # Use faker for realistic data
        def generate_name():
            return f"{FAKE.last_name()} {FAKE.first_name()}"
        
        def generate_phone():
            prefix = random.choice(["098", "097", "096", "090", "093", "091"])
            suffix = f"{random.randint(1000000, 9999999)}"
            return prefix + suffix
        
        def generate_email(name: str, idx: int):
            return f"kh{idx}_{name.replace(' ', '.').lower()}@email.com"
        
        records = []
        for i in range(count):
            name = generate_name()
            phone = generate_phone()
            email = generate_email(name, i + 1)
            addr = f"{random.randint(1, 999)} {random.choice(VIETNAMESE_STREETS)}, {random.choice(VIETNAMESE_CITIES)}"
            
            # Random DOB (adult, 18-65 years old)
            days_ago = random.randint(18*365, 65*365)
            dob = _date(-days_ago)
            
            # Classification: VIP top 5%, Than_thiet next 15%
            if i < int(count * 0.05):
                phan_loai = "VIP"
                so_xe = random.randint(3, 8)
                tong_gia_tri = random.randint(2_000_000_000, 8_000_000_000)
            elif i < int(count * 0.20):
                phan_loai = "Than_thiet"
                so_xe = random.randint(1, 3)
                tong_gia_tri = random.randint(500_000_000, 1_999_000_000)
            else:
                phan_loai = "Thuong"
                so_xe = random.randint(0, 1)
                tong_gia_tri = random.randint(0, 499_000_000)
            
            records.append((name, phone, email, addr, dob, phan_loai, tong_gia_tri, so_xe, now))
            
            if len(records) >= batch_size:
                cursor.executemany(
                    """INSERT OR IGNORE INTO khach_hang
                       (ho_ten, so_dien_thoai, email, dia_chi, ngay_sinh, phan_loai, tong_gia_tri_mua, so_xe_da_mua, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    records,
                )
                conn.commit()
                print(f"    ... {i+1}/{count} seeded")
                records = []
        
        if records:
            cursor.executemany(
                """INSERT OR IGNORE INTO khach_hang
                   (ho_ten, so_dien_thoai, email, dia_chi, ngay_sinh, phan_loai, tong_gia_tri_mua, so_xe_da_mua, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records,
            )
    else:
        # Fallback without faker: simple deterministic data
        first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Vũ", "Đặng", "Bùi", "Đỗ"]
        last_names = ["An", "Bình", "Cường", "Dương", "Em", "Giang", "Huy", "Khoa", "Lam", "Minh",
                      "Nam", "Oanh", "Phong", "Quang", "Sơn", "Thanh", "Uyên", "Vân", "Xuan", "Yến"]
        
        for i in range(count):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            name = f"{fname} {lname}"
            phone = f"09{random.randint(10000000, 99999999)}"
            email = f"kh{i+1}@seed.com"
            addr = f"{random.randint(1, 999)} {random.choice(VIETNAMESE_STREETS)}, {random.choice(VIETNAMESE_CITIES)}"
            dob = f"19{random.randint(70, 99)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            
            if i < int(count * 0.05):
                phan_loai = "VIP"
                so_xe = random.randint(3, 8)
                tong_gia_tri = random.randint(2_000_000_000, 8_000_000_000)
            elif i < int(count * 0.20):
                phan_loai = "Than_thiet"
                so_xe = random.randint(1, 3)
                tong_gia_tri = random.randint(500_000_000, 1_999_000_000)
            else:
                phan_loai = "Thuong"
                so_xe = 0
                tong_gia_tri = 0
            
            cursor.execute(
                """INSERT OR IGNORE INTO khach_hang
                   (ho_ten, so_dien_thoai, email, dia_chi, ngay_sinh, phan_loai, tong_gia_tri_mua, so_xe_da_mua, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, phone, email, addr, dob, phan_loai, tong_gia_tri, so_xe, now),
            )
            
            if (i + 1) % 500 == 0:
                conn.commit()
                print(f"    ... {i+1}/{count} seeded")
        
    conn.commit()
    print(f"  ✅ Seeded {count} khach_hang records")


def seed_hop_dong(conn: sqlite3.Connection, count: int = 5000, batch_size: int = 500):
    """Seed `count` hop_dong records with faker data.
    
    Distribution of statuses:
    - 40% da_giao_xe (completed)
    - 25% da_thanh_toan (paid)
    - 30% moi_tao (pending)
    - 5% huy (cancelled)
    
    Includes realistic ma_hop_dong format: HD{YYYY}-{NNNN}
    """
    print(f"  Seeding {count} hop_dong...")
    
    cursor = conn.cursor()
    now = _now()
    
    # Get existing KH and Xe IDs
    cursor.execute("SELECT id FROM khach_hang ORDER BY id")
    kh_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, gia_ban FROM xe ORDER BY id")
    xe_data = cursor.fetchall()
    xe_ids = [row[0] for row in xe_data]
    xe_prices = {row[0]: row[1] for row in xe_data}
    
    cursor.execute("SELECT id FROM nhan_vien WHERE vai_tro_id = 2 AND trang_thai = 'active'")
    nv_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM khuyen_mai WHERE trang_thai = 'dang_chay'")
    km_ids = [row[0] for row in cursor.fetchall()]
    
    if not kh_ids or not xe_ids or not nv_ids:
        print(f"  [WARNING] Missing data: KH={len(kh_ids)}, xe={len(xe_ids)}, NV={len(nv_ids)}")
        print("  Run seed_khach_hang and ensure xe/nv exist first.")
        return
    
    # Status distribution
    statuses = (
        ["da_giao_xe"] * 40 +
        ["da_thanh_toan"] * 25 +
        ["moi_tao"] * 30 +
        ["huy"] * 5
    )
    
    hd_counter = {}  # year -> counter
    
    records = []
    for i in range(count):
        # Get next ma_hop_dong
        year = datetime.now().year
        if year not in hd_counter:
            # Find max existing for this year
            cursor.execute(
                "SELECT MAX(CAST(SUBSTR(ma_hop_dong, 8) AS INTEGER)) FROM hop_dong WHERE ma_hop_dong LIKE ?",
                (f"HD{year}-%",),
            )
            max_num = cursor.fetchone()[0]
            hd_counter[year] = max_num or 0
        
        hd_counter[year] += 1
        ma_hd = f"HD{year}-{hd_counter[year]:04d}"
        
        # Pick random related entities
        kh_id = random.choice(kh_ids)
        xe_id = random.choice(xe_ids)
        nv_id = random.choice(nv_ids)
        km_id = random.choice(km_ids) if random.random() < 0.4 else None
        
        # Get price from xe (snapshot)
        gia_xe = xe_prices.get(xe_id, 0)
        
        # Random PK total
        tong_gia_pk = random.choice([0, 500000, 800000, 1200000, 2000000, 3500000])
        
        # KM discount
        tien_giam = random.choice([0, 3000000, 5000000, 8000000, 10000000]) if km_id else 0
        
        tong_tien = gia_xe + tong_gia_pk - tien_giam
        
        status = random.choice(statuses)
        
        # Generate dates
        days_ago = random.randint(1, 365)
        ngay_tao = _date(-days_ago)
        
        if status in ["da_thanh_toan", "da_giao_xe"]:
            ngay_thanh_toan = _date(-days_ago + random.randint(1, 15))
        else:
            ngay_thanh_toan = None
        
        if status == "da_giao_xe":
            ngay_giao = _date(-days_ago + random.randint(16, 30))
        else:
            ngay_giao = None
        
        records.append((
            ma_hd, kh_id, xe_id, nv_id, km_id,
            gia_xe, tong_gia_pk, tien_giam, tong_tien,
            status, ngay_tao, ngay_thanh_toan, ngay_giao,
            now,
        ))
        
        if len(records) >= batch_size:
            cursor.executemany(
                """INSERT OR IGNORE INTO hop_dong
                   (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, khuyen_mai_id,
                    gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien,
                    trang_thai, ngay_tao, ngay_thanh_toan, ngay_giao_xe, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                records,
            )
            conn.commit()
            print(f"    ... {i+1}/{count} seeded")
            records = []
    
    if records:
        cursor.executemany(
            """INSERT OR IGNORE INTO hop_dong
               (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, khuyen_mai_id,
                gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien,
                trang_thai, ngay_tao, ngay_thanh_toan, ngay_giao_xe, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            records,
        )
    
    conn.commit()
    print(f"  ✅ Seeded {count} hop_dong records")


def seed_nha_cung_cap(conn: sqlite3.Connection, count: int = 100):
    """Seed `count` nha_cung_cap records with faker data."""
    print(f"  Seeding {count} nha_cung_cap...")
    
    cursor = conn.cursor()
    now = _now()
    
    if FAKE:
        def generate_supplier_name():
            types = ["TNHH", "Công ty", "CTY"]
            regions = ["Sài Gòn", "Hà Nội", "Đà Nẵng", "Hải Phòng", "Cần Thơ"]
            return f"{random.choice(types)} Ô tô {random.choice(regions)} {FAKE.company_suffix()}"
        
        for i in range(count):
            ma_ncc = f"NCC{1000+i+1:04d}"
            name = generate_supplier_name()
            addr = f"{random.randint(1, 999)} {random.choice(VIETNAMESE_STREETS)}, {random.choice(VIETNAMESE_CITIES)}"
            phone = f"02{random.randint(800000000, 899999999)}"
            email = f"contact{i+1}@ncc_seed.com"
            nguoi_lh = f"{FAKE.name()}"
            
            diem_cl = random.randint(3, 5)
            diem_tg = random.randint(3, 5)
            diem_gc = random.randint(3, 5)
            diem_tong = diem_cl + diem_tg + diem_gc
            
            cursor.execute(
                """INSERT OR IGNORE INTO nha_cung_cap
                   (ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email, nguoi_lien_he,
                    diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca, diem_tong, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ma_ncc, name, addr, phone, email, nguoi_lh, diem_cl, diem_tg, diem_gc, diem_tong, now),
            )
            
            if (i + 1) % 50 == 0:
                conn.commit()
                print(f"    ... {i+1}/{count} seeded")
    else:
        supplier_names = [
            "Công ty TNHH Ô tô Sài Gòn", "Toyota Việt Nam", "Honda Việt Nam",
            "Ford Việt Nam", "Hyundai Việt Nam", "Kia Việt Nam",
        ]
        for i in range(count):
            ma_ncc = f"NCC{1000+i+1:04d}"
            base_name = supplier_names[i % len(supplier_names)]
            name = f"{base_name} - Chi nhánh {i+1}"
            addr = f"{random.randint(1, 999)} Đường {random.choice(VIETNAMESE_STREETS)}, {random.choice(VIETNAMESE_CITIES)}"
            phone = f"02{random.randint(800000000, 899999999)}"
            email = f"contact{i+1}@ncc_seed.com"
            nguoi_lh = random.choice(["Ông A", "Bà B", "Ông C", "Bà D", "Ông E"])
            
            diem_cl = random.randint(3, 5)
            diem_tg = random.randint(3, 5)
            diem_gc = random.randint(3, 5)
            diem_tong = diem_cl + diem_tg + diem_gc
            
            cursor.execute(
                """INSERT OR IGNORE INTO nha_cung_cap
                   (ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email, nguoi_lien_he,
                    diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca, diem_tong, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ma_ncc, name, addr, phone, email, nguoi_lh, diem_cl, diem_tg, diem_gc, diem_tong, now),
            )
    
    conn.commit()
    print(f"  ✅ Seeded {count} nha_cung_cap records")


def seed_bao_hanh(conn: sqlite3.Connection, count: int = 200):
    """Seed `count` bao_hanh records (for WF-04 testing + perf).
    
    Generates bao_hanh records linked to existing hop_dong records.
    Per BR-BH-01: each hop_dong has at most 1 bao_hanh (UNIQUE hop_dong_id).
    Per BR-BH-02: ngay_ket_thuc = ngay_bat_dau + thoi_han_bh (default 24 months).
    """
    print(f"  Seeding {count} bao_hanh...")
    
    cursor = conn.cursor()
    now = _now()
    
    # Get HĐ that don't have bao_hanh yet
    cursor.execute(
        """SELECT hd.id, hd.ngay_giao_xe, hd.xe_id, hd.khach_hang_id
           FROM hop_dong hd
           WHERE hd.trang_thai = 'da_giao_xe'
           AND hd.ngay_giao_xe IS NOT NULL
           AND hd.id NOT IN (SELECT hop_dong_id FROM bao_hanh)
           LIMIT ?""",
        (count,),
    )
    hd_rows = cursor.fetchall()
    
    if not hd_rows:
        print(f"  [WARNING] No eligible hop_dong found for bao_hanh seeding.")
        print("  Ensure HĐ with status='da_giao_xe' exist first.")
        return
    
    print(f"  Found {len(hd_rows)} eligible hop_dong records")
    
    thoi_han_bh_default = 24  # months
    
    seeded = 0
    for hd_id, ngay_giao_xe, xe_id, kh_id in hd_rows[:count]:
        if not ngay_giao_xe:
            continue
        
        # Parse ngay_giao_xe
        try:
            start_date = datetime.strptime(ngay_giao_xe, "%Y-%m-%d")
        except (ValueError, TypeError):
            start_date = datetime.now()
        
        end_date = start_date + timedelta(days=thoi_han_bh_default * 30)
        
        # Check if still valid or expired
        if end_date > datetime.now():
            trang_thai = "con_hieu_luc"
        else:
            trang_thai = "het_han"
        
        cursor.execute(
            """INSERT OR IGNORE INTO bao_hanh
               (hop_dong_id, xe_id, khach_hang_id, thoi_han_bh, ngay_bat_dau, ngay_ket_thuc,
                pham_vi, trang_thai, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                hd_id, xe_id, kh_id, thoi_han_bh_default,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                "Bảo hành toàn diện theo điều khoản chuẩn",
                trang_thai,
                now,
            ),
        )
        seeded += 1
        
        if seeded % 50 == 0:
            conn.commit()
            print(f"    ... {seeded}/{count} seeded")
    
    conn.commit()
    print(f"  ✅ Seeded {seeded} bao_hanh records")


def cleanup_seed_data(conn: sqlite3.Connection):
    """Remove existing seed data before re-seeding (for clean re-runs)."""
    print("  Cleaning up existing seed data...")
    cursor = conn.cursor()
    
    tables = ["bao_hanh", "hop_dong", "khach_hang", "nha_cung_cap"]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"    Cleared {table}")
        except sqlite3.OperationalError:
            pass
    
    conn.commit()
    print("  Cleanup complete.")


# ─── Main ──────────────────────────────────────────────────────

def run_all_seeds(db_path: Path, counts: dict, cleanup: bool = False):
    """Run all seed operations."""
    print(f"\n=== SIT Large Seed Data Generator ===")
    print(f"  Database: {db_path}")
    print(f"  Counts: {counts}")
    
    if not db_path.exists():
        print(f"  [ERROR] Database not found: {db_path}")
        print("  Run setup_sit_env.py first to create the SIT DB.")
        return 1
    
    if not FAKER_AVAILABLE:
        print("  [WARNING] Faker not installed. Using simple deterministic data.")
        print("  Install with: pip install faker")
    
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    
    if cleanup:
        cleanup_seed_data(conn)
    
    print("\n[1/4] Seeding khach_hang...")
    seed_khach_hang(conn, count=counts["khach_hang"])
    
    print("\n[2/4] Seeding nha_cung_cap...")
    seed_nha_cung_cap(conn, count=counts["nha_cung_cap"])
    
    print("\n[3/4] Seeding hop_dong...")
    seed_hop_dong(conn, count=counts["hop_dong"])
    
    print("\n[4/4] Seeding bao_hanh...")
    seed_bao_hanh(conn, count=counts["bao_hanh"])
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("  ✅ All seed data generated successfully!")
    
    # Print summary
    print("\n  Database Summary:")
    conn2 = sqlite3.connect(str(db_path))
    cursor = conn2.cursor()
    for table, col in [
        ("khach_hang", "COUNT(*)"),
        ("hop_dong", "COUNT(*)"),
        ("nha_cung_cap", "COUNT(*)"),
        ("bao_hanh", "COUNT(*)"),
    ]:
        try:
            cursor.execute(f"SELECT {col} FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    {table}: {count:,} records")
        except sqlite3.OperationalError:
            pass
    conn2.close()
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate large seed data for SIT performance testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Full seed: 1000 KH, 5000 HD, 100 NCC, 200 BH
  %(prog)s --kh 500 --hd 2000        # Custom counts
  %(prog)s --cleanup                 # Clean existing seed data first
  %(prog)s --bao-hanh 500            # Seed extra BH records
        """,
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_SIT_DB,
        help=f"SIT database path (default: {DEFAULT_SIT_DB})",
    )
    parser.add_argument(
        "--kh", "--khach-hang",
        dest="kh_count",
        type=int,
        default=SEED_COUNTS["khach_hang"],
        help=f"Number of khach_hang to seed (default: {SEED_COUNTS['khach_hang']})",
    )
    parser.add_argument(
        "--hd", "--hop-dong",
        dest="hd_count",
        type=int,
        default=SEED_COUNTS["hop_dong"],
        help=f"Number of hop_dong to seed (default: {SEED_COUNTS['hop_dong']})",
    )
    parser.add_argument(
        "--ncc",
        dest="ncc_count",
        type=int,
        default=SEED_COUNTS["nha_cung_cap"],
        help=f"Number of nha_cung_cap to seed (default: {SEED_COUNTS['nha_cung_cap']})",
    )
    parser.add_argument(
        "--bh", "--bao-hanh",
        dest="bh_count",
        type=int,
        default=SEED_COUNTS["bao_hanh"],
        help=f"Number of bao_hanh to seed (default: {SEED_COUNTS['bao_hanh']})",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove existing seed data before re-seeding",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output",
    )
    
    args = parser.parse_args()
    
    counts = {
        "khach_hang": args.kh_count,
        "hop_dong": args.hd_count,
        "nha_cung_cap": args.ncc_count,
        "bao_hanh": args.bh_count,
    }
    
    return run_all_seeds(args.db_path, counts, cleanup=args.cleanup)


if __name__ == "__main__":
    sys.exit(main())