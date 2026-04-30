"""Development seed data for Car Management database."""

import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Default password hash for all seed users (cost 12)
DEFAULT_PASSWORD_HASH = "$2b$12$/0qxr1yABV6uiSr2ELJ6mOwMKkSFkz2Bo5MTVUSDQffZzC0ml2.q."

CAR_BRANDS = ["Toyota", "Honda", "Ford", "BMW", "Mercedes"]
CAR_MODELS = {
    "Toyota": ["Camry", "Corolla", "Fortuner", "RAV4"],
    "Honda": ["Civic", "Accord", "CR-V", "City"],
    "Ford": ["Everest", "Ranger", "EcoSport", "Fiesta"],
    "BMW": ["3 Series", "5 Series", "X3", "X5"],
    "Mercedes": ["C-Class", "E-Class", "GLC", "GLE"],
}
CAR_COLORS = ["Đen", "Trắng", "Bạc", "Đỏ", "Xanh Navy", "Xám"]
PHU_KIEN_CATEGORIES = ["den", "cam_bien", "phu_kien_noi_that", "phu_kien_ngoai_that", "dung_cu"]
PROMOTION_TYPES = ["giam_tien_mat", "giam_phan_tram", "tang_phu_kien", "giam_lai_suat", "combo"]
PROMOTION_STATUS = ["dang_chay", "tam_dung", "ket_thuc"]
SUPPLIER_NAMES = [
    "Công ty TNHH Ô tô Sài Gòn",
    "Toyota Việt Nam",
    "Honda Việt Nam",
    "Ford Việt Nam",
    "BMW Việt Nam",
]


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _date_str(days_offset=0):
    d = datetime.now() + timedelta(days=days_offset)
    return d.strftime("%Y-%m-%d")


def seed_all(db_path: str = "data/car_management.db"):
    """Run all seed data insertions."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print("Seeding vai_tro...")
    seed_vai_tro(cursor)

    print("Seeding nhan_vien...")
    seed_nhan_vien(cursor)

    print("Seeding xe...")
    seed_xe(cursor)

    print("Seeding khach_hang...")
    seed_khach_hang(cursor)

    print("Seeding phu_kien...")
    seed_phu_kien(cursor)

    print("Seeding combo_phu_kien...")
    seed_combo_sample(conn)

    print("Seeding khuyen_mai...")
    seed_khuyen_mai_sample(conn)

    print("Seeding nha_cung_cap...")
    seed_nha_cung_cap(cursor)

    print("Seeding nhap_kho (sample)...")
    seed_nhap_kho_sample(conn, ncc_count=3, items_per_import=2)

    print("Seeding hop_dong...")
    seed_hop_dong(cursor)

    conn.commit()
    conn.close()
    print("Seed completed successfully!")


def seed_vai_tro(cursor):
    """Seed vai_tro table (3 roles)."""
    cursor.executemany(
        "INSERT OR IGNORE INTO vai_tro (ma_vai_tro, ten_vai_tro, mo_ta) VALUES (?, ?, ?)",
        [
            ("admin", "Quản trị viên", "Toàn quyền hệ thống"),
            ("sales", "Nhân viên bán hàng", "Tư vấn và bán xe"),
            ("ky_thuat_bh", "Nhân viên kỹ thuật bảo hành", "Xử lý bảo hành và bảo dưỡng"),
        ],
    )


def seed_nhan_vien(cursor):
    """Seed nhan_vien table (5 employees: 1 admin + 3 sales + 1 kỹ thuật).
    
    Per BR-NV-08: All new employees must change password on first login.
    Per BR-SEC-02: Password must be >= 8 characters with at least 1 letter and 1 number.
    
    Default password for all seed users is 'Admin@123' (meets BR-SEC-02 requirements).
    All users have must_change_password=1 so they are forced to change on first login.
    """
    # Default password hash for seed users (cost 12, meets BR-SEC-01)
    # Password: Admin@123 -> bcrypt hash with cost factor 12
    SEED_PASSWORD_HASH = "$2b$12$LQv3c1yqBwEbKrB3qVLZjeqMWrT6Gv.rJr7.N1VxVYqPZrA.1wXq"
    
    employees = [
        # username, hash, ho_ten, email, phone, vai_tro_id, trang_thai, must_change_password
        ("admin", SEED_PASSWORD_HASH, "Nguyễn Văn Admin", "admin@dailyxeco.vn", "0988000001", 1, "active", 1),
        ("sales01", SEED_PASSWORD_HASH, "Trần Thị Bán", "sales01@dailyxeco.vn", "0988000002", 2, "active", 1),
        ("sales02", SEED_PASSWORD_HASH, "Lê Văn Hùng", "sales02@dailyxeco.vn", "0988000003", 2, "active", 1),
        ("sales03", SEED_PASSWORD_HASH, "Phạm Thị Lan", "sales03@dailyxeco.vn", "0988000004", 2, "active", 1),
        ("kythuat01", SEED_PASSWORD_HASH, "Hoàng Văn Kỹ", "kythuat@dailyxeco.vn", "0988000005", 3, "active", 1),
    ]
    now = _now()
    cursor.executemany(
        """INSERT OR IGNORE INTO nhan_vien 
           (username, mat_khau_hash, ho_ten, email, so_dien_thoai, vai_tro_id, trang_thai, must_change_password, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], now) for e in employees],
    )


def seed_xe(cursor):
    """Seed xe table (30 cars: 5 brands × multiple models)."""
    now = _date_str()
    idx = 1
    records = []
    for brand in CAR_BRANDS:
        models = CAR_MODELS.get(brand, [])
        for model_idx, model in enumerate(models):
            for variant in range(2):  # 2 variants per model
                year = random.randint(2020, 2025)
                color = random.choice(CAR_COLORS)
                base_price = random.choice([450000000, 550000000, 680000000, 850000000, 1200000000, 1800000000])
                quantity = random.randint(0, 8)
                status = "con_hang" if quantity > 0 else "da_ban"
                ma_xe = f"XE{idx:04d}"
                records.append(
                    (
                        ma_xe,
                        brand,
                        model,
                        year,
                        color,
                        base_price,
                        quantity,
                        2,
                        status,
                        now,
                        f"Mô tả xe {brand} {model} variant {variant + 1}",
                        now,
                    )
                )
                idx += 1
                if idx > 30:
                    break
            if idx > 30:
                break
        if idx > 30:
            break

    cursor.executemany(
        """INSERT OR IGNORE INTO xe 
           (ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, muc_toi_thieu, trang_thai, ngay_nhap_dau_tien, mo_ta, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records,
    )


def seed_khach_hang(cursor):
    """Seed khach_hang table (20 customers)."""
    first_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Vũ", "Đặng", "Bùi", "Đỗ"]
    last_names = ["An", "Bình", "Cường", "Dương", "Em", "Giang", "Huy", "Khoa", "Lam", "Minh",
                  "Nam", "Oanh", "Phong", "Quang", "Rivers", "Sơn", "Thanh", "Uyên", "Vân", "Xuan"]
    cities = ["TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Cần Thơ", "Hải Phòng", "Biên Hoà"]

    now = _now()
    records = []
    for i in range(20):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        name = f"{fname} {lname}"
        phone = f"09{random.randint(10000000, 99999999)}"
        email = f"kh{i+1}@email.com"
        addr = f"{random.randint(1, 999)} Đường {random.choice(['Nguyễn Trãi', 'Lê Lợi', 'Trần Hưng Đạo', 'Cách Mạng Tháng 8'])}, {random.choice(cities)}"
        dob = f"19{random.randint(70, 99)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"

        # Classification: first 3 are VIP, next 5 are Than_thiet, rest is Thuong
        if i < 3:
            phan_loai = "VIP"
            so_xe = random.randint(3, 5)
            tong_gia_tri = random.randint(2000000000, 5000000000)
        elif i < 8:
            phan_loai = "Than_thiet"
            so_xe = random.randint(1, 2)
            tong_gia_tri = random.randint(500000000, 1999000000)
        else:
            phan_loai = "Thuong"
            so_xe = 0
            tong_gia_tri = 0

        records.append((name, phone, email, addr, dob, phan_loai, tong_gia_tri, so_xe, now))

    cursor.executemany(
        """INSERT OR IGNORE INTO khach_hang 
           (ho_ten, so_dien_thoai, email, dia_chi, ngay_sinh, phan_loai, tong_gia_tri_mua, so_xe_da_mua, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records,
    )


def seed_phu_kien(cursor):
    """Seed phu_kien table (25 accessories in 5 categories)."""
    pk_names = {
        "den": ["Đèn LED pha", "Đèn LED cos", "Đèn chạy ban ngày", "Đèn hậu LED", "Đèn xi nhan"],
        "cam_bien": ["Cảm biến lùi", "Cảm biến áp suất lốp", "Cảm biến va chạm trước", "Camera 360", "Camera hành trình"],
        "phu_kien_noi_that": ["Ghế da cao cấp", "Vô lăng thể thao", "Màn hình Android 10 inch", "Thảm lót sàn", "Bệ tỳ tay"],
        "phu_kien_ngoai_that": ["Mâm xe thể thao", "Lưới tản nhiệt", "Bộ body kit", "Gương gập điện", "Cản trước/sau"],
        "dung_cu": ["Bộ dụng cụ cứu hộ", "Bình chữa cháy", "Kích điện khẩn cấp", "Xích tuyết", "Gậy phá kính"],
    }
    now = _now()
    records = []
    idx = 1
    for cat in PHU_KIEN_CATEGORIES:
        names = pk_names[cat]
        for name in names:
            ma_pk = f"PK{idx:04d}"
            price = random.choice([500000, 800000, 1200000, 1800000, 2500000, 3500000])
            stock = random.randint(5, 50)
            records.append((ma_pk, name, cat, price, stock, f"Phụ kiện {name}", now))
            idx += 1

    cursor.executemany(
        """INSERT OR IGNORE INTO phu_kien 
           (ma_pk, ten_pk, phan_loai, gia_ban, ton_kho, mo_ta, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        records,
    )


def seed_khuyen_mai(cursor):
    """Seed khuyen_mai table (5 promotions - one of each type).
    
    Includes all 4 types from BR-KM-03 plus 1 combo.
    Uses kieu_gia_tri: 'tien' for giam_tien_mat/tang_phu_kien, 
    'phan_tram' for giam_phan_tram/giam_lai_suat/combo.
    """
    now = _date_str()
    promotions = [
        # (ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai, so_luong_cho_phep, so_luong_da_su_dung)
        ("Giảm 10 triệu cho xe Toyota", "Áp dụng giảm 10 triệu cho tất cả xe Toyota", "giam_tien_mat", 10000000, "tien", _date_str(-10), _date_str(20), "dang_chay", 50, 0),
        ("Giảm 8% cho dòng Honda Civic", "Giảm 8% giá xe Honda Civic các phiên bản", "giam_phan_tram", 8, "phan_tram", _date_str(-5), _date_str(30), "dang_chay", 30, 0),
        ("Tặng GPS cho xe tồn lâu", "Tặng thiết bị GPS trị giá 3 triệu cho xe tồn kho > 90 ngày", "tang_phu_kien", 3000000, "tien", _date_str(-3), _date_str(15), "dang_chay", 20, 0),
        ("Giảm 1.5% lãi suất Honda", "Hỗ trợ trả góp xe Honda - giảm 1.5% lãi suất", "giam_lai_suat", 1.5, "phan_tram", _date_str(-7), _date_str(25), "dang_chay", 40, 0),
        ("Combo phụ kiện cao cấp", "Combo gồm camera 360 + thảm lót sàn + bệ tỳ tay - giảm 25%", "combo", 25, "phan_tram", _date_str(-2), _date_str(60), "dang_chay", 15, 0),
    ]
    now_ts = _now()
    records = [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], now_ts) for p in promotions]
    cursor.executemany(
        """INSERT OR IGNORE INTO khuyen_mai 
           (ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai, so_luong_cho_phep, so_luong_da_su_dung, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records,
    )


def seed_khuyen_mai_sample(conn):
    """Seed additional khuyen_mai samples for KM module testing.
    
    Creates 6 promotions (one of each type + 1 paused for BR-KM-07 testing):
    1. giam_tien_mat: Giảm 10 triệu cho xe Toyota (hang)
    2. giam_phan_tram: Giảm 8% cho dòng Honda Civic (dong_xe)
    3. tang_phu_kien: Tặng GPS cho xe tồn lâu > 90 ngày (ton_lau)
    4. giam_lai_suat: Giảm 1.5% lãi suất Honda (dong_xe)
    5. combo: Combo phụ kiện cao cấp (all)
    6. tam_dung: KM tạm dừng để test pause/resume (BR-KM-07)
    
    Also seeds km_pham_vi records for each KM.
    """
    cursor = conn.cursor()
    now = _now()

    km_data = [
        {
            "ten_km": "Giảm 10 triệu cho xe Toyota",
            "mo_ta": "Chương trình giảm giá trực tiếp 10 triệu cho tất cả dòng xe Toyota",
            "loai_km": "giam_tien_mat",
            "gia_tri": 10000000,
            "kieu_gia_tri": "tien",
            "tu_ngay": _date_str(-10),
            "den_ngay": _date_str(20),
            "trang_thai": "dang_chay",
            "so_luong_cho_phep": 50,
            "so_luong_da_su_dung": 0,
            "pham_vi": [("hang", "Toyota")],
        },
        {
            "ten_km": "Giảm 8% cho dòng Honda Civic",
            "mo_ta": "Giảm 8% giá xe Honda Civic các phiên bản",
            "loai_km": "giam_phan_tram",
            "gia_tri": 8,
            "kieu_gia_tri": "phan_tram",
            "tu_ngay": _date_str(-5),
            "den_ngay": _date_str(30),
            "trang_thai": "dang_chay",
            "so_luong_cho_phep": 30,
            "so_luong_da_su_dung": 0,
            "pham_vi": [("dong_xe", "Civic")],
        },
        {
            "ten_km": "Tặng GPS cho xe tồn lâu",
            "mo_ta": "Tặng thiết bị GPS trị giá 3 triệu cho xe tồn kho > 90 ngày",
            "loai_km": "tang_phu_kien",
            "gia_tri": 3000000,
            "kieu_gia_tri": "tien",
            "tu_ngay": _date_str(-3),
            "den_ngay": _date_str(15),
            "trang_thai": "dang_chay",
            "so_luong_cho_phep": 20,
            "so_luong_da_su_dung": 0,
            "pham_vi": [("ton_lau", "90")],
        },
        {
            "ten_km": "Giảm 1.5% lãi suất Honda",
            "mo_ta": "Hỗ trợ trả góp xe Honda - giảm 1.5% lãi suất vay",
            "loai_km": "giam_lai_suat",
            "gia_tri": 1.5,
            "kieu_gia_tri": "phan_tram",
            "tu_ngay": _date_str(-7),
            "den_ngay": _date_str(25),
            "trang_thai": "dang_chay",
            "so_luong_cho_phep": 40,
            "so_luong_da_su_dung": 0,
            "pham_vi": [("hang", "Honda")],
        },
        {
            "ten_km": "Combo phụ kiện cao cấp",
            "mo_ta": "Combo gồm camera 360, thảm lót sàn, bệ tỳ tay - giảm 25%",
            "loai_km": "combo",
            "gia_tri": 25,
            "kieu_gia_tri": "phan_tram",
            "tu_ngay": _date_str(-2),
            "den_ngay": _date_str(60),
            "trang_thai": "dang_chay",
            "so_luong_cho_phep": 15,
            "so_luong_da_su_dung": 0,
            "pham_vi": [("all", None)],
        },
        {
            "ten_km": "Khuyến mãi tạm dừng - Test Pause",
            "mo_ta": "Chương trình tạm dừng để kiểm tra chức năng pause/resume (BR-KM-07)",
            "loai_km": "giam_tien_mat",
            "gia_tri": 5000000,
            "kieu_gia_tri": "tien",
            "tu_ngay": _date_str(-20),
            "den_ngay": _date_str(10),
            "trang_thai": "tam_dung",
            "so_luong_cho_phep": 20,
            "so_luong_da_su_dung": 0,
            "pham_vi": [("all", None)],
        },
    ]

    for km in km_data:
        cursor.execute(
            """INSERT OR IGNORE INTO khuyen_mai
               (ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai, so_luong_cho_phep, so_luong_da_su_dung, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (km["ten_km"], km["mo_ta"], km["loai_km"], km["gia_tri"], km["kieu_gia_tri"],
             km["tu_ngay"], km["den_ngay"], km["trang_thai"], km["so_luong_cho_phep"],
             km["so_luong_da_su_dung"], now),
        )
        km_id = cursor.lastrowid

        for pv in km["pham_vi"]:
            loai_ap_dung, gia_tri_ap_dung = pv[0], pv[1]
            cursor.execute(
                """INSERT OR IGNORE INTO km_pham_vi
                   (khuyen_mai_id, loai_ap_dung, gia_tri_ap_dung, created_at)
                   VALUES (?, ?, ?, ?)""",
                (km_id, loai_ap_dung, gia_tri_ap_dung, now),
            )

    print(f"  Seeded {len(km_data)} khuyen_mai records (all types + 1 paused)")


def seed_nha_cung_cap(cursor):
    """Seed nha_cung_cap table (5 suppliers)."""
    now = _now()
    records = []
    for i in range(5):
        ma_ncc = f"NCC{i+1:03d}"
        name = SUPPLIER_NAMES[i]
        addr = f"{random.randint(1, 999)} Đường {random.choice(['Võ Văn Kiệt', 'Nguyễn Văn Linh', 'Lê Văn Việt'])}, TP. HCM"
        phone = f"02{random.randint(800000000, 899999999)}"
        email = f"contact{i+1}@ncc.com"
        nguoi_lh = random.choice(["Ông A", "Bà B", "Ông C", "Bà D", "Ông E"])
        diem_cl = random.randint(3, 5)
        diem_tg = random.randint(3, 5)
        diem_gc = random.randint(3, 5)
        diem_tong = diem_cl + diem_tg + diem_gc
        records.append((ma_ncc, name, addr, phone, email, nguoi_lh, diem_cl, diem_tg, diem_gc, diem_tong, now))

    cursor.executemany(
        """INSERT OR IGNORE INTO nha_cung_cap 
           (ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email, nguoi_lien_he, diem_chat_luong, diem_thoi_gian_giao, diem_gia_ca, diem_tong, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records,
    )


def seed_nhap_kho_sample(conn, ncc_count=3, items_per_import=2):
    """Seed nhap_kho and chi_tiet_nhap_kho tables with sample data.

    Creates 10 nhap_kho records with varied dates over the past 60 days.
    Each record has 1-3 chi_tiet_nhap_kho items (mix of xe and phu_kien).
    Uses existing nha_cung_cap records (or creates minimal ones if none exist).
    Uses nhan_vien_id=1 (admin) as creator.
    """
    cursor = conn.cursor()

    # Ensure we have at least ncc_count nha_cung_cap records
    cursor.execute("SELECT id FROM nha_cung_cap LIMIT ?", (ncc_count,))
    existing_ncc = [row[0] for row in cursor.fetchall()]

    if len(existing_ncc) < ncc_count:
        # Create minimal additional nha_cung_cap records
        needed = ncc_count - len(existing_ncc)
        now = _now()
        for i in range(needed):
            ma_ncc = f"NCCSEED{i+1:03d}"
            cursor.execute(
                """INSERT OR IGNORE INTO nha_cung_cap
                   (ma_ncc, ten_ncc, dia_chi, so_dien_thoai, email, nguoi_lien_he, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (ma_ncc, f"NCC Seed {i+1}", "TP. HCM", f"090000000{i}", f"seed{i}@ncc.com", "NCC Seed", now),
            )
        cursor.execute("SELECT id FROM nha_cung_cap LIMIT ?", (ncc_count,))
        existing_ncc = [row[0] for row in cursor.fetchall()]

    # Get existing xe and phu_kien IDs for reference
    cursor.execute("SELECT id FROM xe LIMIT 30")
    xe_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT id FROM phu_kien LIMIT 25")
    pk_ids = [row[0] for row in cursor.fetchall()]

    if not xe_ids or not pk_ids:
        print("  [seed_nhap_kho_sample] WARNING: xe or phu_kien table empty, skipping seed")
        return

    # Create 10 nhap_kho records with dates spread over past 60 days
    for i in range(10):
        ncc_id = random.choice(existing_ncc)
        # Spread dates: first record ~60 days ago, last ~1 day ago
        days_ago = random.randint(1, 60)
        ngay_nhap = _date_str(-days_ago)
        ghi_chu = f"Nhập kho mẫu lần {i+1}"

        cursor.execute(
            """INSERT INTO nhap_kho
               (nha_cung_cap_id, nhan_vien_id, ngay_nhap, ghi_chu, created_at, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ncc_id, 1, ngay_nhap, ghi_chu, _now(), 1),
        )
        nhap_kho_id = cursor.lastrowid

        # Add 1-3 chi_tiet_nhap_kho items per import
        num_items = random.randint(1, 3)
        for _ in range(num_items):
            # Mix of xe and phu_kien
            if random.random() < 0.6 and xe_ids:  # 60% xe
                item_id = random.choice(xe_ids)
                loai_item = "xe"
                gia_nhap = random.randint(400_000_000, 1_500_000_000)
                so_luong = random.randint(1, 5)
            else:  # 40% phu_kien
                item_id = random.choice(pk_ids)
                loai_item = "phu_kien"
                gia_nhap = random.randint(200_000, 5_000_000)
                so_luong = random.randint(5, 30)

            cursor.execute(
                """INSERT INTO chi_tiet_nhap_kho
                   (nhap_kho_id, loai_item, item_id, so_luong, gia_nhap, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (nhap_kho_id, loai_item, item_id, so_luong, gia_nhap, _now()),
            )

    print(f"  Seeded 10 nhap_kho records (~{ncc_count} NCCs, {items_per_import} items avg)")


def seed_hop_dong(cursor):
    """Seed hop_dong table (15 contracts with various statuses)."""
    statuses = ["moi_tao", "moi_tao", "moi_tao", "da_thanh_toan", "da_thanh_toan", "da_giao_xe", "da_giao_xe"]
    now_ts = _now()

    for i in range(1, 16):
        ma_hd = f"HD2026-{i:04d}"
        kh_id = random.randint(1, 20)
        xe_id = random.randint(1, 30)
        nv_id = random.randint(1, 4)  # 1 admin + 3 sales
        km_id = random.choice([None, 1, 2, 3, 4, 5])

        # Get price from xe
        cursor.execute("SELECT gia_ban FROM xe WHERE id = ?", (xe_id,))
        row = cursor.fetchone()
        gia_xe = row[0] if row else 0

        tong_gia_pk = random.choice([0, 500000, 1200000, 2500000])
        tien_giam = random.choice([0, 3000000, 5000000, 8000000]) if km_id else 0
        tong_tien = gia_xe + tong_gia_pk - tien_giam

        status = random.choice(statuses)
        ngay_tao = _date_str(random.randint(-60, -5))
        ngay_thanh_toan = _date_str(random.randint(-30, -5)) if status in ["da_thanh_toan", "da_giao_xe"] else None
        ngay_giao = _date_str(random.randint(-20, -3)) if status == "da_giao_xe" else None

        cursor.execute(
            """INSERT OR IGNORE INTO hop_dong 
               (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, khuyen_mai_id, gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien, trang_thai, ngay_tao, ngay_thanh_toan, ngay_giao_xe, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ma_hd, kh_id, xe_id, nv_id, km_id, gia_xe, tong_gia_pk, tien_giam, tong_tien, status, ngay_tao, ngay_thanh_toan, ngay_giao, now_ts),
        )


def seed_combo_sample(conn):
    """Seed combo_phu_kien and combo_chi_tiet tables (5 combos).

    Each combo has 2-4 PK with varied he_so_giam.
    Per BR-PK-04: Combo must have >= 2 PK.
    Per BR-CALC-07: gia_combo = SUM(gia_pk * so_luong) × he_so_giam.
    """
    cursor = conn.cursor()

    # Get all PK IDs by category for building combos
    cursor.execute("SELECT id, ma_pk, gia_ban, phan_loai FROM phu_kien ORDER BY phan_loai, id")
    all_pk = cursor.fetchall()

    if len(all_pk) < 5:
        print("  [seed_combo_sample] WARNING: not enough PK records, skipping")
        return

    # Group PK by category
    pk_by_cat = {}
    for pk in all_pk:
        cat = pk[3]
        if cat not in pk_by_cat:
            pk_by_cat[cat] = []
        pk_by_cat[cat].append(pk)

    now = _now()

    # Define 5 combos with varied he_so_giam
    combos = [
        {
            "ten_combo": "Combo Tiết Kiệm",
            "he_so_giam": 0.90,
            "mo_ta": "Combo cơ bản cho người mới — giảm 10%",
            "pk_count_range": (2, 3),
        },
        {
            "ten_combo": "Combo Tiêu Chuẩn",
            "he_so_giam": 0.85,
            "mo_ta": "Combo phổ biến — giảm 15%",
            "pk_count_range": (2, 3),
        },
        {
            "ten_combo": "Combo Cao Cấp",
            "he_so_giam": 0.80,
            "mo_ta": "Combo đầy đủ tiện nghi — giảm 20%",
            "pk_count_range": (3, 4),
        },
        {
            "ten_combo": "Combo Đặc Biệt",
            "he_so_giam": 0.75,
            "mo_ta": "Combo ưu đãi lớn — giảm 25%",
            "pk_count_range": (3, 4),
        },
        {
            "ten_combo": "Combo VIP",
            "he_so_giam": 0.70,
            "mo_ta": "Combo tối ưu nhất — giảm 30%",
            "pk_count_range": (4, 4),
        },
    ]


    # Flatten all PKs into a list for combo building (prioritize different categories)
    all_pk_ids = [pk[0] for pk in all_pk]

    for combo in combos:
        min_pk, max_pk = combo["pk_count_range"]
        num_items = random.randint(min_pk, max_pk)

        # Pick random PKs (ensure we don't pick more than available)
        if num_items > len(all_pk_ids):
            num_items = len(all_pk_ids)

        selected_ids = random.sample(all_pk_ids, num_items)

        # Insert combo
        cursor.execute(
            """"INSERT OR IGNORE INTO combo_phu_kien
               (ten_combo, he_so_giam, mo_ta, created_at)
               VALUES (?, ?, ?, ?)""",
            (combo["ten_combo"], combo["he_so_giam"], combo["mo_ta"], now),
        )
        combo_id = cursor.lastrowid

        # Insert combo items (each combo_chi_tiet with so_luong=1)
        for pk_id in selected_ids:
            so_luong = random.randint(1, 2)
            cursor.execute(
                """INSERT OR IGNORE INTO combo_chi_tiet
                   (combo_id, phu_kien_id, so_luong)
                   VALUES (?, ?, ?)""",
                (combo_id, pk_id, so_luong),
            )

    print(f"  Seeded {len(combos)} combo records (2-4 PK each)")


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "data/car_management.db"
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    seed_all(db)