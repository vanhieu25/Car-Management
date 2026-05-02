# Hướng dẫn Cài đặt và Vận hành Database

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Cấu trúc Database](#2-cấu-trúc-database)
3. [Yêu cầu hệ thống](#3-yêu-cầu-hệ-thống)
4. [Cài đặt](#4-cài-đặt)
5. [Khởi tạo Database](#5-khởi-tạo-database)
6. [Chạy ứng dụng](#6-chạy-ứng-dụng)
7. [Cấu hình đường dẫn Database](#7-cấu-hình-đường-dẫn-database)
8. [Sao lưu và Phục hồi](#8-sao-lưu-và-phục-hồi)
9. [Cấu trúc bảng dữ liệu](#9-cấu-trúc-bảng-dữ-liệu)
10. [Xử lý sự cố](#10-xử-lý-sự-cố)

---

## 1. Giới thiệu

Phần mềm quản lý đại lý xe hơi sử dụng **SQLite** làm cơ sở dữ liệu. SQLite là database engine embeded, không cần cài đặt server riêng, phù hợp cho ứng dụng desktop.

**Đặc điểm:**
- File database nằm tại `data/car_management.db`
- Chế độ WAL (Write-Ahead Logging) được bật mặc định để tăng concurrency
- Foreign keys được enforce tự động
- Migrations được chạy tự động khi khởi động ứng dụng

---

## 2. Cấu trúc Database

```
data/
├── car_management.db          # Database chính (WAL mode)
├── car_management.db-shm       # Shared memory file (WAL)
├── car_management.db-wal      # Write-ahead log file (WAL)
└── backup/
    └── YYYY-MM-DD.db          # Các bản sao lưu theo ngày
```

---

## 3. Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|---|---|
| Python | 3.10+ |
| RAM | Tối thiểu 4GB |
| Disk | 500MB trống |
| OS | Windows / Linux / macOS |

---

## 4. Cài đặt

### 4.1. Clone repository

```bash
git clone <repo-url>
cd Car-Management
```

### 4.2. Tạo Virtual Environment

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (CMD)
python -m venv venv
venv\Scripts\activate.bat
```

### 4.3. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

---

## 5. Khởi tạo Database

### 5.1. Database được tạo tự động

Khi chạy `python main.py`, ứng dụng sẽ tự động:

1. **Kiểm tra và chạy migrations** — tạo tất cả các bảng nếu chưa tồn tại
2. **Seed dữ liệu mẫu** (nếu là lần đầu tiên hoặc database trống)

```
$ python main.py
14:39:44 - car_management - INFO - Migration runner finished. 0 migrations applied.
```

> **Lưu ý:** Nếu thấy log `0 migrations applied` mà bạn đã có dữ liệu từ trước, đó là vì tất cả migrations đã được áp dụng rồi.

### 5.2. Seed dữ liệu mẫu

Mặc định khi chạy lần đầu, hệ thống sẽ seed dữ liệu mẫu bao gồm:

| Bảng | Nội dung |
|---|---|
| `vai_tro` | 3 vai trò: admin, nhân viên kinh doanh, kế toán |
| `nhan_vien` | 5 nhân viên mẫu (password: `password123`) |
| `xe` | 10 xe các loại |
| `khach_hang` | 20 khách hàng mẫu |
| `phu_kien` | 15 phụ kiện các loại |
| `khuyen_mai` | 3 khuyến mãi mẫu |
| `nha_cung_cap` | 5 nhà cung cấp |
| `hop_dong` | 5 hợp đồng mẫu |

### 5.3. Chạy Migration thủ công

Nếu cần chạy migration thủ công (ví dụ: setup môi trường test):

```bash
cd Car-Management
source venv/bin/activate

python -c "
from app.infrastructure.database.migrations.runner import MigrationRunner
from app.infrastructure.database.seeds.dev_seed import seed_all

runner = MigrationRunner()
runner.run_pending()
seed_all()
print('Database initialized successfully!')
"
```

### 5.4. Thiết lập môi trường SIT

Để thiết lập database cho môi trường SIT (System Integration Testing):

```bash
python scripts/setup_sit_env.py
```

---

## 6. Chạy ứng dụng

### 6.1. Chạy bình thường

```bash
source venv/bin/activate
python main.py
```

### 6.2. Với Database cụ thể

```bash
python main.py --db-path data/test.db
```

### 6.3. Kiểm tra trạng thái Database

```bash
python -c "
from app.infrastructure.database.migrations.runner import MigrationRunner
runner = MigrationRunner()
status = runner.get_status()
print(f'Version: {status[\"current_version\"]}')
print(f'Migrations: {status[\"applied\"]}/{status[\"total_migrations\"]} applied')
print(f'Pending: {status[\"pending\"]}')
"
```

---

## 7. Cấu hình đường dẫn Database

### 7.1. Mặc định

Đường dẫn mặc định: `data/car_management.db`

### 7.2. Thay đổi qua code

```python
from app.infrastructure.database.connection import set_config, DatabaseConfig

# Đổi sang database khác
config = DatabaseConfig(db_path="data/my_database.db")
set_config(config)
```

### 7.3. Environment Variable

```bash
export CAR_DB_PATH="data/production.db"
python main.py
```

---

## 8. Sao lưu và Phục hồi

### 8.1. Sao lưu thủ công

```bash
# Tạo backup ngay lập tức
python scripts/backup_db.py

# Backup vào thư mục tùy chỉnh
python scripts/backup_db.py --output /path/to/backup/

# Backup nén (tiết kiệm dung lượng)
python scripts/backup_db.py --compress
```

### 8.2. Tự động sao lưu theo lịch (Linux)

```bash
# Thêm vào crontab
crontab -e

# Chạy backup hàng ngày lúc 2:00 sáng
0 2 * * * cd /path/to/Car-Management && /path/to/venv/bin/python scripts/backup_db.py
```

### 8.3. Phục hồi từ backup

```bash
# Copy backup thành database chính
cp data/backup/2026-05-01.db data/car_management.db
```

### 8.4. Xem lịch sử backup

```bash
ls -la data/backup/
```

---

## 9. Cấu trúc bảng dữ liệu

### 9.1. Danh sách bảng (23 bảng)

| Bảng | Mô tả |
|---|---|
| `schema_version` | Theo dõi phiên bản migration đã áp dụng |
| `vai_tro` | Vai trò người dùng (admin, nhân viên...) |
| `nhan_vien` | Nhân viên (username, password hash, thông tin) |
| `xe` | Xe (mã xe, hãng, dòng, giá, số lượng tồn) |
| `khach_hang` | Khách hàng (họ tên, SĐT, email, phân loại) |
| `hop_dong` | Hợp đồng mua bán xe |
| `phu_kien` | Phụ kiện (mã, tên, giá, tồn kho) |
| `combo_phu_kien` | Combo phụ kiện |
| `khuyen_mai` | Khuyến mãi |
| `bao_hanh` | Bảo hành |
| `bao_duong` | Bảo dưỡng |
| `cuu_ho` | Cứu hộ |
| `nha_cung_cap` | Nhà cung cấp |
| `nhap_kho` | Phiếu nhập kho |
| `chi_tiet_nhap_kho` | Chi tiết nhập kho |
| `don_dat_hang` | Đơn đặt hàng |
| `chi_tiet_don_dat` | Chi tiết đơn đặt hàng |
| `tra_gop` | Trả góp |
| `khieu_nai` | Khiếu nại |
| `chien_dich_mk` | Chiến dịch marketing |
| `lead` | Lead tiếp thị |
| `audit_log` | Nhật ký hành động người dùng |
| `system_settings` | Cấu hình hệ thống |

### 9.2. Các bảng quan trọng

#### `schema_version` — Theo dõi Migration

| Column | Kiểu | Mô tả |
|---|---|---|
| version | INTEGER | Số phiên bản migration |
| name | TEXT | Tên migration |
| applied_at | TEXT | Thời gian áp dụng |

#### `nhan_vien` — Nhân viên

| Column | Kiểu | Mô tả |
|---|---|---|
| username | TEXT | Tên đăng nhập (duy nhất) |
| mat_khau_hash | TEXT | Password đã hash bcrypt |
| ho_ten | TEXT | Họ tên đầy đủ |
| email | TEXT | Email |
| so_dien_thoai | TEXT | Số điện thoại |
| vai_tro_id | INTEGER | Foreign key → vai_tro |
| trang_thai | TEXT | active / inactive / locked |
| must_change_password | INTEGER | 1 = cần đổi password ở lần đầu |

**Tài khoản mặc định sau seed:**

| Username | Password | Vai trò |
|---|---|---|
| admin | password123 | Quản trị viên |
| nv001 | password123 | Nhân viên kinh doanh |
| nv002 | password123 | Nhân viên kinh doanh |
| ke_toan | password123 | Kế toán |

#### `xe` — Xe

| Column | Kiểu | Mô tả |
|---|---|---|
| ma_xe | TEXT | Mã xe (duy nhất) |
| hang | TEXT | Hãng xe (Toyota, Honda...) |
| dong_xe | TEXT | Dòng xe (Camry, Civic...) |
| nam_san_xuat | INTEGER | Năm sản xuất |
| mau_sac | TEXT | Màu sắc |
| gia_ban | INTEGER | Giá bán (VND) |
| so_luong_ton | INTEGER | Số lượng tồn kho |
| muc_toi_thieu | INTEGER | Mức tồn tối thiểu (cảnh báo) |
| trang_thai | TEXT | con_hang / da_ban / dang_vận_chuyển |

#### `khach_hang` — Khách hàng

| Column | Kiểu | Mô tả |
|---|---|---|
| ho_ten | TEXT | Họ tên |
| so_dien_thoai | TEXT | Số điện thoại |
| email | TEXT | Email |
| dia_chi | TEXT | Địa chỉ |
| ngay_sinh | TEXT | Ngày sinh |
| phan_loai | TEXT | Thuong / Than_thiet / VIP |

### 9.3. Sơ đồ quan hệ chính

```
nhan_vien ──(vai_tro_id)──> vai_tro
hop_dong ──(khach_hang_id)──> khach_hang
hop_dong ──(xe_id)──> xe
hop_dong ──(nhan_vien_id)──> nhan_vien
hop_dong ──(khuyen_mai_id)──> khuyen_mai (nullable)
bao_hanh ──(hop_dong_id)──> hop_dong
bao_hanh ──(xe_id)──> xe
bao_hanh ──(khach_hang_id)──> khach_hang
tra_gop ──(hop_dong_id)──> hop_dong
cuu_ho ──(khach_hang_id)──> khach_hang
cuu_ho ──(xe_id)──> xe
nhap_kho ──(nha_cung_cap_id)──> nha_cung_cap
nhap_kho ──(nhan_vien_id)──> nhan_vien
chi_tiet_nhap_kho ──(nhap_kho_id)──> nhap_kho
```

---

## 10. Xử lý sự cố

### 10.1. Lỗi "database is locked"

**Nguyên nhân:** Có connection chưa đóng hoặc đang có transaction dangling.

**Khắc phục:**
```bash
# Kill các process đang giữ database
lsof data/car_management.db

# Hoặc restart ứng dụng
pkill -f "python main.py"
```

### 10.2. Lỗi "no such table"

**Nguyên nhân:** Migration chưa chạy hoặc bị thiếu.

**Khắc phục:**
```bash
python -c "
from app.infrastructure.database.migrations.runner import MigrationRunner
runner = MigrationRunner()
runner.run_pending()
"
```

### 10.3. Lỗi "foreign key constraint failed"

**Nguyên nhân:** Đang cố xóa dữ liệu đang được tham chiếu bởi bảng khác.

**Khắc phục:** Xóa dữ liệu theo thứ tự ngược lại: xóa record con trước, record cha sau.

### 10.4. Reset Database hoàn toàn

⚠️ **Cảnh báo:** Xóa toàn bộ data, không thể khôi phục!

```bash
# Xóa database
rm data/car_management.db
rm data/car_management.db-shm
rm data/car_management.db-wal

# Chạy lại ứng dụng (sẽ tự tạo mới)
python main.py
```

### 10.5. Database bị corruption

**Dấu hiệu:** Ứng dụng crash, đọc/ghi lỗi bất thường.

**Khắc phục:**
```bash
# Khôi phục từ backup mới nhất
cp data/backup/YYYY-MM-DD.db data/car_management.db

# Nếu không có backup, export data thủ công rồi tạo lại DB
```

### 10.6. WAL file quá lớn

```bash
# Check size
ls -lh data/car_management.db*

# checkpoint WAL (đưa dữ liệu từ WAL về DB chính)
sqlite3 data/car_management.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

---

## Liên hệ hỗ trợ

Nếu gặp vấn đề không xử lý được, liên hệ nhóm phát triển:

| Thành viên | Email |
|---|---|
| Cao Văn Hiếu (Trưởng nhóm) | - |
| Lê Minh Đạt | - |
| Nguyễn Hữu Hải | - |
