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

    print("Seeding khuyen_mai...")
    seed_khuyen_mai(cursor)

    print("Seeding nha_cung_cap...")
    seed_nha_cung_cap(cursor)

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
    """Seed khuyen_mai table (5 promotions - one of each type)."""
    now = _date_str()
    promotions = [
        ("Khuyến mãi giảm giá tiền mặt", "Giảm 5 triệu cho tất cả xe", "giam_tien_mat", 5000000, "tien", _date_str(-10), _date_str(20), "dang_chay"),
        ("Giảm 10% cho xe Toyota", "Áp dụng giảm 10% giá xe Toyota", "giam_phan_tram", 10, "phan_tram", _date_str(-5), _date_str(30), "dang_chay"),
        ("Tặng phụ kiện khi mua xe", "Tặng camera hành trình trị giá 2 triệu", "tang_phu_kien", 1, "tien", _date_str(-3), _date_str(15), "dang_chay"),
        ("Giảm lãi suất trả góp", "Giảm 2% lãi suất khi trả góp 60 tháng", "giam_lai_suat", 2, "phan_tram", _date_str(-7), _date_str(25), "dang_chay"),
        ("Combo bảo dưỡng", "Gói bảo dưỡng 5 lần giảm 30%", "combo", 30, "phan_tram", _date_str(-2), _date_str(60), "dang_chay"),
    ]
    now_ts = _now()
    records = [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], 100, 0, now_ts) for p in promotions]
    cursor.executemany(
        """INSERT OR IGNORE INTO khuyen_mai 
           (ten_km, mo_ta, loai_km, gia_tri, kieu_gia_tri, tu_ngay, den_ngay, trang_thai, so_luong_cho_phep, so_luong_da_su_dung, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records,
    )


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


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "data/car_management.db"
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    seed_all(db)