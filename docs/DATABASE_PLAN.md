## 4. DATABASE PLAN

### 4.1 Tổng quan thiết kế

- **Hệ quản trị**: SQLite (file `data/car_management.db`).
- **Bảng mã**: UTF-8.
- **Foreign key**: bật `PRAGMA foreign_keys = ON;` mỗi phiên kết nối.
- **Kiểu dữ liệu chính**: `INTEGER` (id, tiền VND, số lượng), `TEXT` (chuỗi, ngày tháng ISO `YYYY-MM-DD`), `REAL` (lãi suất, hệ số), `BLOB` (ảnh — không sử dụng giai đoạn đầu).
- **Quy ước đặt tên**: bảng dùng số nhiều, không dấu tiếng Việt (`xe`, `khach_hang`, `hop_dong`); cột dùng `snake_case`.
- **Khoá chính**: `id INTEGER PRIMARY KEY AUTOINCREMENT` cho mọi bảng (trừ bảng nối nhiều-nhiều).
- **Audit chung**: các bảng nghiệp vụ chính có `created_at`, `updated_at` (ISO datetime), `created_by`, `updated_by` (FK → `nhan_vien.id`).

### 4.2 Sơ đồ ERD (rút gọn)

```text
                                  ┌────────────────┐
                                  │   nhan_vien    │
                                  │  (sales/admin) │
                                  └───────┬────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
              ▼                           ▼                           ▼
   ┌────────────────┐         ┌────────────────────┐        ┌────────────────┐
   │     xe         │◄──────► │     hop_dong       │◄─────► │   khach_hang   │
   │                │         │ (master record)    │        │                │
   └────────┬───────┘         └─────────┬──────────┘        └────────┬───────┘
            │                           │                            │
            │                           ├──────► hop_dong_phu_kien   │
            │                           ├──────► bao_hanh ◄──────────┘
            │                           ├──────► tra_gop
            │                           └──────► khuyen_mai (FK)
            │
            ▼
   ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
   │  nhap_kho      │◄──────► │  nha_cung_cap  │────────►│ don_dat_hang   │
   └────────────────┘         └────────────────┘         └────────────────┘

   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
   │    phu_kien    │    │  combo_phu_kien│    │  khuyen_mai    │
   └────────────────┘    └────────────────┘    └────────────────┘

   ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
   │   bao_duong    │    │    khieu_nai   │    │  chien_dich_mk │
   └────────────────┘    └────────────────┘    └────────────────┘

   ┌────────────────┐    ┌────────────────┐
   │      lead      │    │  audit_log     │
   └────────────────┘    └────────────────┘
```

### 4.3 Danh sách bảng (25 bảng)

| # | Tên bảng | Mục đích | Module |
| --- | --- | --- | --- |
| 1 | `nhan_vien` | Tài khoản & thông tin nhân viên | NV, Bảo mật |
| 2 | `vai_tro` | Danh mục vai trò (admin/sales/ky_thuat) | NV, Bảo mật |
| 3 | `xe` | Thông tin xe & tồn kho | Xe, Kho |
| 4 | `khach_hang` | Thông tin khách hàng | KH |
| 5 | `hop_dong` | Hợp đồng bán xe | Hợp đồng |
| 6 | `phu_kien` | Danh mục phụ kiện | Phụ kiện |
| 7 | `combo_phu_kien` | Danh mục combo phụ kiện | Phụ kiện |
| 8 | `combo_chi_tiet` | Bảng nối combo ↔ phụ kiện | Phụ kiện |
| 9 | `hop_dong_phu_kien` | Bảng nối hợp đồng ↔ phụ kiện | Hợp đồng |
| 10 | `khuyen_mai` | Chương trình khuyến mãi | KM |
| 11 | `km_pham_vi` | Phạm vi áp dụng KM (hãng/dòng/xe) | KM |
| 12 | `bao_hanh` | Thông tin & hồ sơ bảo hành | BH |
| 13 | `bao_hanh_yeu_cau` | Yêu cầu BH (chi tiết sửa chữa) | BH |
| 14 | `bao_duong` | Lịch & lịch sử bảo dưỡng | Hậu mãi |
| 15 | `cuu_ho` | Yêu cầu cứu hộ | Hậu mãi |
| 16 | `nha_cung_cap` | Nhà cung cấp xe & PK | NCC |
| 17 | `nhap_kho` | Lịch sử nhập kho | Kho, NCC |
| 18 | `don_dat_hang` | Đơn đặt hàng từ NCC | NCC |
| 19 | `tra_gop` | Hợp đồng trả góp | Trả góp |
| 20 | `tra_gop_lich_su` | Lịch sử thanh toán theo kỳ | Trả góp |
| 21 | `chien_dich_mk` | Chiến dịch marketing | Marketing |
| 22 | `lead` | Khách hàng tiềm năng | Marketing |
| 23 | `khieu_nai` | Khiếu nại khách hàng | Khiếu nại |
| 24 | `audit_log` | Log hoạt động hệ thống | Bảo mật |
| 25 | `system_settings` | Cấu hình hệ thống (thời hạn BH, ngưỡng tồn kho mặc định, thông tin đại lý) | Bảo mật, Cài đặt |

### 4.4 Đặc tả chi tiết các bảng cốt lõi

#### 4.4.1 `nhan_vien`

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | INTEGER | PK, AUTO | Khoá chính |
| `username` | TEXT | UNIQUE, NOT NULL | Tên đăng nhập |
| `mat_khau_hash` | TEXT | NOT NULL | Hash bcrypt |
| `ho_ten` | TEXT | NOT NULL | Họ tên đầy đủ |
| `email` | TEXT | NOT NULL | Email liên hệ |
| `so_dien_thoai` | TEXT | | SĐT |
| `vai_tro_id` | INTEGER | FK → `vai_tro.id` | Vai trò |
| `trang_thai` | TEXT | DEFAULT `active` | `active` / `inactive` |
| `lan_dang_nhap_sai` | INTEGER | DEFAULT 0 | Đếm sai mật khẩu |
| `khoa_den` | TEXT | NULLABLE | Thời điểm hết khoá |
| `created_at` | TEXT | DEFAULT CURRENT_TIMESTAMP | |
| `updated_at` | TEXT | | |

#### 4.4.2 `xe`

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | INTEGER | PK, AUTO | |
| `ma_xe` | TEXT | UNIQUE, NOT NULL | Mã xe (BR-ID-01); KHÔNG sửa được sau khi tạo |
| `hang` | TEXT | NOT NULL | Hãng xe |
| `dong_xe` | TEXT | NOT NULL | Dòng xe |
| `nam_san_xuat` | INTEGER | CHECK (nam_san_xuat ≥ 1990) | Năm SX |
| `mau_sac` | TEXT | | Màu |
| `gia_ban` | INTEGER | CHECK (≥0) | Giá bán (VND) |
| `so_luong_ton` | INTEGER | CHECK (≥0), DEFAULT 0 | Tồn kho |
| `muc_toi_thieu` | INTEGER | DEFAULT 2 | Ngưỡng cảnh báo |
| `trang_thai` | TEXT | DEFAULT `con_hang` | `con_hang`/`da_ban`/`sap_ve` |
| `ngay_nhap_dau_tien` | TEXT | | Phục vụ KM xe tồn lâu |
| `created_at` / `updated_at` | TEXT | | |

**Index**: `idx_xe_hang_dong` trên (`hang`, `dong_xe`); `idx_xe_trang_thai`.

#### 4.4.3 `khach_hang`

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | INTEGER | PK, AUTO | |
| `ho_ten` | TEXT | NOT NULL | |
| `so_dien_thoai` | TEXT | UNIQUE, NOT NULL | |
| `email` | TEXT | NOT NULL | |
| `dia_chi` | TEXT | | |
| `ngay_sinh` | TEXT | | Phục vụ chăm sóc KH |
| `phan_loai` | TEXT | DEFAULT `Thuong` | `Thuong`/`Than_thiet`/`VIP` |
| `tong_gia_tri_mua` | INTEGER | DEFAULT 0 | Cập nhật tự động |
| `so_xe_da_mua` | INTEGER | DEFAULT 0 | Cập nhật tự động |
| `created_at` / `updated_at` | TEXT | | |

#### 4.4.4 `hop_dong`

| Cột | Kiểu | Ràng buộc | Mô tả |
| --- | --- | --- | --- |
| `id` | INTEGER | PK, AUTO | |
| `ma_hop_dong` | TEXT | UNIQUE, NOT NULL | VD: `HD2026-0001` |
| `khach_hang_id` | INTEGER | FK → `khach_hang.id` | |
| `xe_id` | INTEGER | FK → `xe.id` | |
| `nhan_vien_id` | INTEGER | FK → `nhan_vien.id` | Sales tạo HĐ |
| `khuyen_mai_id` | INTEGER | FK → `khuyen_mai.id`, NULL | KM áp dụng |
| `gia_xe` | INTEGER | NOT NULL | **Snapshot giá xe** tại thời điểm tạo HĐ (BR-HD §5.4.6) |
| `tong_gia_phu_kien` | INTEGER | DEFAULT 0 | Tổng tiền PK (đã snapshot) |
| `tien_giam_km` | INTEGER | DEFAULT 0 | Tiền giảm theo BR-CALC-02 |
| `tong_tien` | INTEGER | NOT NULL | Theo BR-CALC-01 |
| `trang_thai` | TEXT | DEFAULT `moi_tao` | Theo BR-FLOW (HĐ); xem BR-HD-01..06 |
| `ngay_tao` | TEXT | DEFAULT CURRENT_TIMESTAMP | |
| `ngay_thanh_toan` | TEXT | | Ghi khi chuyển `da_thanh_toan` (BR-HD-03) |
| `ngay_giao_xe` | TEXT | | Ghi khi chuyển `da_giao_xe` (BR-HD-04) |
| `ly_do_huy` | TEXT | NULLABLE | Bắt buộc khi `trang_thai = huy` (UC-HD-04) |
| `ghi_chu` | TEXT | | |

**Index**: `idx_hd_khach`, `idx_hd_xe`, `idx_hd_trang_thai`, `idx_hd_ngay_tao`.

> **Snapshot**: `gia_xe`, `tong_gia_phu_kien`, `tien_giam_km` đều được lưu cố định khi tạo HĐ — KHÔNG đồng bộ lại nếu giá gốc thay đổi sau này (đảm bảo HĐ in PDF luôn đúng số liệu lúc ký).

#### 4.4.5 `hop_dong_phu_kien` (bảng nối)

| Cột | Kiểu | Ràng buộc |
| --- | --- | --- |
| `hop_dong_id` | INTEGER | FK → `hop_dong.id` |
| `phu_kien_id` | INTEGER | FK → `phu_kien.id` |
| `so_luong` | INTEGER | DEFAULT 1, CHECK (≥ 1) |
| `gia_ban` | INTEGER | NOT NULL — **snapshot** giá PK lúc thêm vào HĐ (BR-PK-07) |
| **PK kép** | (`hop_dong_id`, `phu_kien_id`) | |

#### 4.4.6 `bao_hanh`

| Cột | Kiểu | Mô tả |
| --- | --- | --- |
| `id` | INTEGER PK | |
| `hop_dong_id` | INTEGER FK, UNIQUE | Mỗi HĐ có 1 hồ sơ BH (BR-BH-01) |
| `xe_id` | INTEGER FK | |
| `khach_hang_id` | INTEGER FK | |
| `thoi_han_bh` | INTEGER NOT NULL | Số tháng (mặc định 24, cấu hình tại SystemSettings) |
| `ngay_bat_dau` | TEXT | = `ngay_giao_xe` của HĐ |
| `ngay_ket_thuc` | TEXT | = `ngay_bat_dau` + `thoi_han_bh` (BR-BH-02) |
| `pham_vi` | TEXT | Mô tả phạm vi BH |
| `trang_thai` | TEXT | `con_hieu_luc` / `het_han` |

#### 4.4.7 `khuyen_mai`

| Cột | Kiểu | Mô tả |
| --- | --- | --- |
| `id` | INTEGER PK | |
| `ten_km` | TEXT NOT NULL | |
| `mo_ta` | TEXT | |
| `loai_km` | TEXT | `giam_tien_mat`/`tang_phu_kien`/`giam_lai_suat`/`combo` |
| `gia_tri` | INTEGER | Số tiền hoặc % giảm |
| `kieu_gia_tri` | TEXT | `tien` / `phan_tram` |
| `tu_ngay` / `den_ngay` | TEXT | |
| `trang_thai` | TEXT | `dang_chay`/`tam_dung`/`ket_thuc` |

#### 4.4.8 `audit_log`

| Cột | Kiểu | Mô tả |
| --- | --- | --- |
| `id` | INTEGER PK | |
| `nhan_vien_id` | INTEGER FK | |
| `hanh_dong` | TEXT | `LOGIN`/`CREATE_HD`/`UPDATE_XE`/... |
| `bang_anh_huong` | TEXT | Tên bảng |
| `ban_ghi_id` | INTEGER | ID bản ghi liên quan |
| `noi_dung` | TEXT | JSON chi tiết thay đổi |
| `thoi_gian` | TEXT | DEFAULT CURRENT_TIMESTAMP |

> Các bảng còn lại (combo, NCC, nhập kho, trả góp, marketing, khiếu nại…) tuân theo cùng quy ước, sẽ được đặc tả đầy đủ ở tài liệu `DATABASE_DESIGN.md` trong giai đoạn G2.

### 4.5 Quan hệ chính

| Bảng cha | Bảng con | Loại | Ý nghĩa |
| --- | --- | --- | --- |
| `khach_hang` | `hop_dong` | 1 - N | Một KH có nhiều HĐ |
| `xe` | `hop_dong` | 1 - N | Một xe có nhiều HĐ |
| `nhan_vien` | `hop_dong` | 1 - N | Một NV tạo nhiều HĐ |
| `hop_dong` | `hop_dong_phu_kien` | 1 - N | HĐ có nhiều PK |
| `phu_kien` | `hop_dong_phu_kien` | 1 - N | PK xuất hiện trên nhiều HĐ |
| `hop_dong` | `bao_hanh` | 1 - 1 | Mỗi HĐ tạo 1 hồ sơ BH |
| `bao_hanh` | `bao_hanh_yeu_cau` | 1 - N | Một BH có nhiều yêu cầu sửa |
| `khuyen_mai` | `km_pham_vi` | 1 - N | Một KM áp dụng nhiều phạm vi |
| `nha_cung_cap` | `nhap_kho` | 1 - N | NCC có nhiều lần nhập |
| `nha_cung_cap` | `don_dat_hang` | 1 - N | NCC có nhiều đơn |
| `hop_dong` | `tra_gop` | 1 - 1 | Một HĐ có thể có 1 hồ sơ trả góp |
| `tra_gop` | `tra_gop_lich_su` | 1 - N | |
| `chien_dich_mk` | `lead` | 1 - N | |

### 4.6 Index & ràng buộc bổ sung

#### Index hiệu năng

Đặt index trên các cột tìm kiếm thường xuyên (đáp ứng C-PERF-01, 02 — tìm kiếm ≤ 2s với 10.000 bản ghi):

- `xe`: (`hang`, `dong_xe`), `trang_thai`, `gia_ban`
- `khach_hang`: `so_dien_thoai`, `email`, `phan_loai`
- `hop_dong`: `ngay_tao`, `trang_thai`, `nhan_vien_id`, `khach_hang_id`
- `bao_hanh`: `ngay_ket_thuc` (phục vụ cảnh báo BH 30 ngày)
- `tra_gop_lich_su`: `ngay_den_han`, `trang_thai` (cảnh báo chậm trả)
- `audit_log`: `thoi_gian`, `nhan_vien_id`, `hanh_dong`

#### Triggers / Side-effects (xử lý ở tầng Application Service hoặc DB Trigger)

> Các side-effect này có thể implement bằng **SQLite trigger** hoặc **Application Service** (khuyến nghị: Application Service để dễ test & log).

| Mã | Trigger | Khi nào | Hành động | BR áp dụng |
| --- | --- | --- | --- | --- |
| **TRG-01** | `on_hd_thanh_toan` | HĐ `moi_tao → da_thanh_toan` | Giảm `xe.so_luong_ton`, `phu_kien.ton_kho`; ghi `ngay_thanh_toan` | BR-HD-03, BR-KHO-03 |
| **TRG-02** | `on_hd_giao_xe` | HĐ `da_thanh_toan → da_giao_xe` | Tự sinh `bao_hanh`; cập nhật `khach_hang` (tổng giá trị, số xe, phân loại); cập nhật KPI NV; ghi `ngay_giao_xe` | BR-HD-04, BR-BH-01, BR-CALC-03, BR-CALC-05 |
| **TRG-03** | `on_hd_huy` | HĐ → `huy` | Hoàn tồn kho xe & PK; xoá `bao_hanh` & `tra_gop` liên quan | BR-HD-05, BR-BH-10, BR-TG-10 |
| **TRG-04** | `on_xe_ton_kho_zero` | `xe.so_luong_ton = 0` & có HĐ `da_giao_xe` | Chuyển `xe.trang_thai → da_ban` | BR-XE-04 |
| **TRG-05** | `on_xe_nhap_kho` | Tăng `xe.so_luong_ton` từ 0 → > 0 cho xe `da_ban` | Chuyển `xe.trang_thai → con_hang` | BR-XE-05 |
| **TRG-06** | `on_km_het_han` | Cron daily, `khuyen_mai.den_ngay < today()` | Chuyển `trang_thai → ket_thuc` | BR-KM-08 |
| **TRG-07** | `on_tra_gop_qua_han` | Cron daily, `tra_gop_lich_su.ngay_den_han + 5d < today()` & `trang_thai = chua_tra` | Chuyển `trang_thai → qua_han` | BR-TG-08, 09 |
| **TRG-08** | `on_audit_any_crud` | Mọi CRUD trên bảng nghiệp vụ | Insert vào `audit_log` (user, action, JSON diff) | BR-SEC-09 |

#### Ràng buộc bổ sung (CHECK / FOREIGN KEY)

- `xe.so_luong_ton ≥ 0`, `phu_kien.ton_kho ≥ 0` (BR-KHO-07).
- `hop_dong.trang_thai IN ('moi_tao', 'da_thanh_toan', 'da_giao_xe', 'huy')`.
- `bao_hanh.ngay_ket_thuc ≥ ngay_bat_dau` (BR-DATA-07).
- `khuyen_mai.den_ngay ≥ tu_ngay`.
- `tra_gop.lai_suat_nam` ∈ [0, 30] (BR-DATA-09).
- ON DELETE: `RESTRICT` cho mọi FK quan trọng (xe, KH, NV, PK) để ngăn xoá dữ liệu có ràng buộc (BR-REF-01..07).

#### Backup & phục hồi

- File SQLite được copy hàng ngày sang `data/backup/YYYY-MM-DD.db` (BR-SEC trong BRD).
- Phục hồi ≤ 15 phút (C-PERF-05).
- Lưu giữ tối thiểu 30 ngày backup.

### 4.7 Dữ liệu seed cho phát triển/kiểm thử

| Bảng | Số bản ghi seed | Ghi chú |
| --- | --- | --- |
| `vai_tro` | 3 | `admin`, `sales`, `ky_thuat` |
| `nhan_vien` | 5 | 1 admin + 3 sales + 1 kỹ thuật |
| `xe` | 30 | 5 hãng × 3 dòng × 2 phiên bản |
| `khach_hang` | 20 | Đa dạng phân loại |
| `phu_kien` | 25 | 5 nhóm phân loại |
| `khuyen_mai` | 5 | Mỗi loại 1 chương trình |
| `nha_cung_cap` | 5 | |
| `hop_dong` | 15 | Đủ trạng thái khác nhau |

---

