# KẾ HOẠCH DỰ ÁN

**Phần mềm Quản lý Đại lý Xe hơi**

> Tài liệu kế hoạch chi tiết phục vụ việc xây dựng phần mềm quản lý đại lý xe hơi.
>
> **Tài liệu nguồn**:
>
> - `TECH_STACK.md` — stack kỹ thuật
> - `YEU_CAU_CHUC_NANG.md` — yêu cầu chức năng & phi chức năng
> - `LIST_CHUC_NANG.md` — 71 chức năng / 15 module
> - `BUSINESS_REQUIREMENTS.md` — **đặc tả nghiệp vụ chi tiết** (Business Rules, Use Cases, Workflow, Acceptance Criteria)
>
> **Vai trò của tài liệu này**: tổng hợp **kế hoạch tổng thể** (overview, stakeholder, database, UI/UX). Mọi quy tắc nghiệp vụ chi tiết nằm trong `BUSINESS_REQUIREMENTS.md`.

---

## 1. THÔNG TIN TỔNG QUAN DỰ ÁN

### 1.1 Tên dự án

Phần mềm Quản lý Đại lý Xe hơi (Car Dealership Management System).

### 1.2 Mục tiêu dự án

Xây dựng một ứng dụng desktop hỗ trợ đại lý xe hơi quản lý toàn diện hoạt động kinh doanh: từ quản lý xe, khách hàng, hợp đồng, kho, bảo hành cho đến báo cáo doanh thu và chăm sóc khách hàng sau bán hàng.

### 1.3 Phạm vi dự án

| Phạm vi | Bao gồm | Không bao gồm |
| --- | --- | --- |
| **Trong phạm vi** | 15 module nghiệp vụ (71 chức năng) theo `LIST_CHUC_NANG.md` | Bán hàng online (e-commerce, đặt xe qua web) |
| **Trong phạm vi** | Ứng dụng desktop chạy đơn lẻ, dữ liệu lưu SQLite | Đồng bộ đa chi nhánh real-time, multi-tenant |
| **Trong phạm vi** | Phân quyền **3 vai trò**: Admin, Sales, Kỹ thuật BH | Tích hợp cổng thanh toán, API ngân hàng tự động |
| **Trong phạm vi** | Xuất hợp đồng PDF (Jinja2 + WeasyPrint), báo cáo nội bộ | Ứng dụng mobile, web |
| **Trong phạm vi** | Tiếng Việt có dấu, đơn vị tiền VND | Đa ngôn ngữ, đa tiền tệ |
| **Trong phạm vi** | Bảo hành theo điều khoản chuẩn (BR-BH-01..10) | Tự động gửi email/SMS cho KH (mở rộng tương lai) |

> Tham chiếu chi tiết: `BUSINESS_REQUIREMENTS.md` mục **2.4 Phạm vi loại trừ** và **8. Ràng buộc & Giả định**.

### 1.4 Thông tin chung

| Hạng mục | Chi tiết |
| --- | --- |
| **Loại dự án** | Đồ án học phần Lập trình Python |
| **Loại sản phẩm** | Ứng dụng desktop một người dùng / mạng nội bộ nhỏ |
| **Tech stack** | Python 3.10+, PyQt6, SQLite, bcrypt, **Jinja2 + WeasyPrint** (PDF), **openpyxl** (Excel), pytest, PyInstaller |
| **Hệ điều hành** | Windows 10+, Linux (Ubuntu 20.04+), macOS 12+ |
| **Ngôn ngữ giao diện** | Tiếng Việt có dấu |
| **Quy mô dữ liệu** | ~10.000 bản ghi xe, hỗ trợ 50 người dùng đồng thời (mạng nội bộ) |

### 1.5 Nhóm thực hiện

| Thành viên | Vai trò | Trách nhiệm chính |
| --- | --- | --- |
| Nguyễn Văn Hiếu | Nhóm trưởng | Điều phối, kiến trúc, module hợp đồng & xe |
| Lê Minh Đạt | Thành viên | Module khách hàng, kho, phụ kiện, báo cáo |
| Nguyễn Hữu Hải | Thành viên | Module bảo hành, khuyến mãi, bảo mật, kiểm thử |

### 1.6 Lộ trình tổng quan (giai đoạn)

| Giai đoạn | Nội dung | Sản phẩm chính | Module BRD áp dụng |
| --- | --- | --- | --- |
| **G1 - Khởi tạo** | Thiết lập repo, môi trường, kiến trúc | Project skeleton, `requirements.txt`, README | - |
| **G2 - Nền tảng** | CSDL (24 bảng), đăng nhập, phân quyền, layout chính | Schema SQLite, `S-AUTH-01`, Main Window, audit log | NV, SEC |
| **G3 - Nghiệp vụ lõi** | Xe, KH, NV, Hợp đồng (wizard 4 bước), Kho | 5 module CRUD + hợp đồng PDF (Jinja2+WeasyPrint) | XE, KH, NV, HD, KHO |
| **G4 - Mở rộng** | Bảo hành, KM, Phụ kiện, NCC, Trả góp | 5 module nghiệp vụ phụ + WF-01..03 | BH, KM, PK, NCC, TG |
| **G5 - Bổ sung** | Hậu mãi, Marketing, Khiếu nại, Báo cáo (RP-01..07) | 4 module + Dashboard tổng hợp | HM, MK, KN, BC |
| **G6 - Hoàn thiện** | Kiểm thử, đóng gói, tài liệu | File `.exe`, hướng dẫn sử dụng, test report | Tất cả |

> Mỗi giai đoạn G2-G5 đều **kiểm thử theo Acceptance Criteria** (Mục 9 BRD) trước khi sang giai đoạn kế tiếp.

### 1.7 Mục tiêu nghiệp vụ (Business Objectives)

> Trích lược từ `BUSINESS_REQUIREMENTS.md` mục 2.2 — đây là kim chỉ nam đánh giá thành công của phần mềm.

| Mã | Mục tiêu | KPI tham chiếu |
| --- | --- | --- |
| **BO-01** | Số hoá toàn bộ quy trình bán xe — không còn giấy tờ thủ công | 100% HĐ tạo qua hệ thống |
| **BO-02** | Quản lý kho chính xác, cảnh báo tồn kho thấp tự động | 0% sai lệch tồn kho thực tế ↔ hệ thống |
| **BO-03** | Theo dõi bảo hành chủ động, không bỏ sót khách hàng đến hạn | Cảnh báo BH 30 ngày trước hạn |
| **BO-04** | Đo lường hiệu quả khuyến mãi & marketing | Báo cáo `RP-06`, `RP-07` |
| **BO-05** | Theo dõi KPI nhân viên minh bạch, công bằng | Báo cáo `RP-03` real-time |
| **BO-06** | Cải thiện chăm sóc khách hàng, tăng tỷ lệ KH quay lại | KH `Than_thiet`/`VIP` ≥ 15% (BR-CALC-03) |
| **BO-07** | Đảm bảo bảo mật & truy vết hoạt động | Audit log đầy đủ; bcrypt cost ≥ 12 |

---

## 2. STAKEHOLDERS - NGƯỜI LIÊN QUAN

### 2.1 Phân loại stakeholder

Hệ thống có 3 nhóm:

1. **Actors (người dùng trực tiếp)**: đăng nhập và thao tác trên phần mềm — gắn với phân quyền `vai_tro`.
2. **Đối tượng dữ liệu**: được hệ thống quản lý nhưng không trực tiếp sử dụng (KH, NCC, Ngân hàng, Lead).
3. **Stakeholders dự án**: các bên liên quan đến quá trình xây dựng và vận hành phần mềm.

### 2.2 Actors — người dùng trực tiếp hệ thống

| Mã | Vai trò | Mô tả | Số người dự kiến | Module sử dụng |
| --- | --- | --- | --- | --- |
| **A-01** | **Quản trị viên (Admin)** | Người quản lý đại lý hoặc IT phụ trách hệ thống | 1-2 | Tất cả 15 module |
| **A-02** | **Nhân viên bán hàng (Sales)** | Người trực tiếp tư vấn & lập hợp đồng với khách | 5-20 | XE (R), KH, NV (cá nhân), HD, PK, KM, BH (C+R), HM, KN, MK, TG |
| **A-03** | **Nhân viên kỹ thuật / bảo hành** | Tiếp nhận và xử lý yêu cầu bảo hành, bảo dưỡng, cứu hộ | 2-5 | XE (R), KH (R), BH, HM, KN |

> Tham chiếu: `BUSINESS_REQUIREMENTS.md` mục **3.1 Actors hệ thống**.

### 2.3 Đối tượng dữ liệu (không trực tiếp dùng phần mềm)

| # | Đối tượng | Vai trò trong nghiệp vụ |
| --- | --- | --- |
| 1 | **Khách hàng** | Người mua xe; thông tin được lưu trong CSDL phục vụ hợp đồng, BH, hậu mãi |
| 2 | **Nhà cung cấp (NCC)** | Đối tác cung cấp xe & phụ kiện; được quản lý trong module NCC |
| 3 | **Ngân hàng** | Đối tác cho vay trả góp; thông tin lưu trong module Trả góp |
| 4 | **Lead (khách tiềm năng)** | Đối tượng chiến dịch marketing, chưa phải khách hàng chính thức |

### 2.4 Stakeholders dự án (xây dựng & sử dụng)

| Mã | Stakeholder | Quan tâm chính | Tần suất tương tác |
| --- | --- | --- | --- |
| **SH-01** | Giảng viên hướng dẫn | Đáp ứng yêu cầu đồ án, chất lượng mã nguồn & tài liệu | Theo lịch nộp |
| **SH-02** | Nhóm phát triển (3 sinh viên) | Hoàn thành đúng deadline, học được Python/PyQt6 | Hằng ngày |
| **SH-03** | Chủ đại lý (giả định) | ROI, doanh thu, tăng trưởng, tỷ lệ chuyển đổi | Hằng tháng/quý |
| **SH-04** | Quản lý đại lý (giả định) | Theo dõi KPI NV, kho, HĐ — vận hành trơn tru | Hằng ngày |
| **SH-05** | Kế toán (giả định) | Số liệu doanh thu chính xác, xuất Excel | Hằng tháng |
| **SH-06** | Hội đồng phản biện | Tính khả thi, tính học thuật, độ hoàn thiện | Buổi bảo vệ |
| **SH-07** | Khách hàng cuối (đại diện) | Trải nghiệm dịch vụ tại đại lý sau khi triển khai | Tại mỗi giao dịch |
| **SH-08** | Đối tác ngân hàng (giả định) | Số liệu hồ sơ trả góp đúng quy định | Hằng tháng |

> Tham chiếu: `BUSINESS_REQUIREMENTS.md` mục **3.2 Stakeholders & 3.3 Stakeholder map**.

### 2.5 Ma trận phân quyền

> Chi tiết đầy đủ tại `BUSINESS_REQUIREMENTS.md` mục **3.4 Ma trận quyền CRUD chi tiết**. Bảng dưới là tóm lược.
>
> Ký hiệu: **C**=Create, **R**=Read, **U**=Update, **D**=Delete, **`-`**=không có quyền

| Module / Chức năng | A-01 Admin | A-02 Sales | A-03 Kỹ thuật |
| --- | :---: | :---: | :---: |
| Quản lý nhân viên (CRUD) | CRUD | R (cá nhân) | R (cá nhân) |
| Quản lý xe (CRUD) | CRUD | R | R |
| Quản lý khách hàng | CRUD | CRU | R |
| Tạo hợp đồng | CRUD | CRU* | R |
| **Hủy hợp đồng** | **D** | **-** | **-** |
| Quản lý kho (nhập kho, xuất kho) | CRUD | R | - |
| Quản lý NCC, đơn đặt hàng | CRUD | R | - |
| Tạo & quản lý chương trình KM | CRUD | R | - |
| Áp dụng KM (khi tạo HĐ) | C | C | - |
| Tiếp nhận yêu cầu BH | CRUD | CR | CRU |
| Xử lý/cập nhật BH | CRUD | R | CRU |
| Bảo dưỡng, cứu hộ (Hậu mãi) | CRUD | C | CRU |
| Khiếu nại | CRUD | CRU | RU |
| Marketing & Lead | CRUD | RU | - |
| Trả góp | CRUD | CR | - |
| Báo cáo doanh thu / Top xe / VIP | R | - | - |
| KPI cá nhân (My Profile) | R | R | R |
| Audit log | R | - | - |
| Cài đặt hệ thống | CRUD | - | - |

> *Sales chỉ Update HĐ ở trạng thái `moi_tao` (BR-HD-09). HĐ `da_thanh_toan` chỉ Admin mới sửa được.*

---

## 3. BUSINESS REQUIREMENTS - TỔNG QUAN

> **Lưu ý quan trọng**: Mục này chỉ **tóm tắt cấu trúc Business Rules và liệt kê các điểm chính**. Đặc tả chi tiết đầy đủ — bao gồm Use Cases, Validation rules, Acceptance Criteria, Workflow E2E — nằm tại `BUSINESS_REQUIREMENTS.md`.

### 3.1 Hệ thống mã hoá Business Rules

`BUSINESS_REQUIREMENTS.md` sử dụng hệ thống mã hoá thống nhất:

| Tiền tố | Ý nghĩa | Ví dụ |
| --- | --- | --- |
| `BR-XX-NN` | Business Rule cho module XX, số NN | `BR-HD-02` (BR thứ 2 của module Hợp đồng) |
| `UC-XX-NN` | Use Case cho module XX | `UC-HD-01` (Tạo hợp đồng — wizard) |
| `AC-XX-NN` | Acceptance Criteria | `AC-HD-04` (PDF có đủ thông tin) |
| `WF-NN` | Workflow xuyên module | `WF-02` (Bán xe chuẩn) |
| `RP-NN` | Báo cáo (Report) | `RP-01` (Doanh thu) |
| `BO-NN` | Business Objective | `BO-01` (Số hoá quy trình) |

### 3.2 Tổng số quy tắc nghiệp vụ

| Loại | Số lượng | Vị trí trong BRD |
| --- | --- | --- |
| **BR tổng thể** (xuyên suốt) | ~58 | Mục 4 |
| **BR đặc thù module** | 124 | Mục 5.1 - 5.15 |
| **Use Cases** | ~50 (UC-XX-NN) | Mục 5 |
| **Workflow E2E** | 8 (WF-01..08) | Mục 6 |
| **Acceptance Criteria** | ~20+ (AC-XX-NN) | Mục 9 |
| **Báo cáo** | 7 (RP-01..07) | Mục 5.14, 7 |

### 3.3 Các nhóm Business Rules tổng thể (Mục 4 BRD)

| Nhóm | Số rule | Tóm tắt |
| --- | --- | --- |
| **BR-ID** (Định danh) | 6 | `ma_xe`, `so_dien_thoai`, `username`, `ma_hop_dong`, `ma_ncc`, `ma_km` đều UNIQUE & không sửa được sau khi tạo |
| **BR-DATA** (Dữ liệu) | 10 | Tiền VND ≥ 0; định dạng email/SĐT VN; ngày tháng `YYYY-MM-DD`; lãi suất ∈ [0, 30] |
| **BR-REF** (Toàn vẹn tham chiếu) | 7 | Không xoá xe/KH/NV/PK đã có HĐ — chuyển `inactive` thay vì xoá thật |
| **BR-FLOW** (Flow trạng thái) | 5 sơ đồ | HĐ, Xe, KM, Khiếu nại, ĐĐH NCC |
| **BR-CALC** (Công thức) | 7 | Tổng tiền HĐ, tiền giảm KM, phân loại KH, niên kim trả góp, KPI NV, tỷ lệ chuyển đổi, giá combo |
| **BR-TIME** (Thời gian) | 8 | BH 30 ngày, BD 7 ngày, trả góp chậm 5 ngày, sinh nhật ±7 ngày, session 30 phút |
| **BR-SEC** (Bảo mật) | 9 | bcrypt cost ≥ 12, mật khẩu ≥ 8 ký tự, khoá 5 lần sai/15 phút, audit log mọi CRUD |
| **BR-UI** (Hiển thị) | 6 | Format VND có dấu phẩy, ngày `dd/MM/yyyy`, badge có màu, dialog xác nhận hành động nguy hiểm |

### 3.4 Các công thức tính nghiệp vụ trọng yếu (BR-CALC)

> Đây là các công thức **bắt buộc viết unit test** để đảm bảo độ chính xác.

#### Công thức tổng tiền hợp đồng (BR-CALC-01)

```text
tong_tien = gia_xe + tong_gia_phu_kien − tien_giam_KM
```

#### Phân loại khách hàng tự động (BR-CALC-03)

| Phân loại | Điều kiện |
| --- | --- |
| `Thuong` | < 1 xe đã mua |
| `Than_thiet` | ≥ 1 xe HOẶC tổng giá trị mua ≥ 500 triệu |
| `VIP` | ≥ 3 xe HOẶC tổng giá trị mua ≥ 2 tỷ |

#### Niên kim trả góp (BR-CALC-04)

```text
M = P × r × (1 + r)^n / ((1 + r)^n − 1)
trong đó:
  P = số tiền vay
  r = lãi suất tháng (lai_suat_nam / 12 / 100)
  n = số kỳ (tháng)
```

#### KPI nhân viên (BR-CALC-05)

```text
KPI_nv(period) = {
  so_xe_ban    = COUNT(hop_dong WHERE nhan_vien_id = ? AND trang_thai = 'da_giao_xe' AND ngay_giao_xe ∈ period),
  doanh_thu    = SUM(tong_tien WHERE ...),
  ti_le_chot   = HĐ da_giao_xe / HĐ moi_tao
}
```

#### Tỷ lệ chuyển đổi marketing (BR-CALC-06)

```text
ti_le_chuyen_doi = (lead_chuyen_doi / tong_lead) × 100%
```

#### Giá combo phụ kiện (BR-CALC-07)

```text
gia_combo = SUM(phu_kien.gia_ban × so_luong) × he_so_giam
```

> Đầy đủ 7 công thức + ví dụ tính cụ thể: `BUSINESS_REQUIREMENTS.md` Mục 4.5.

### 3.5 Flow trạng thái (BR-FLOW) - tóm tắt

#### 3.5.1 Hợp đồng

```text
moi_tao ──► da_thanh_toan ──► da_giao_xe (TERMINAL)
   │              │
   ▼              ▼
   huy            huy        ◄── chỉ Admin có quyền
```

- Mỗi bước có **side-effects** tự động: giảm/hoàn tồn kho, sinh BH, cập nhật phân loại KH, tính KPI.
- Chi tiết: `BUSINESS_REQUIREMENTS.md` Mục 4.4.1 và BR-HD-01..12.

#### 3.5.2 Khuyến mãi

```text
nhap ──► dang_chay ⇄ tam_dung ──► ket_thuc (TERMINAL)
```

#### 3.5.3 Yêu cầu BH / Khiếu nại / Cứu hộ (chung)

```text
tiep_nhan ──► dang_xu_ly ──► hoan_thanh / da_dong (TERMINAL)
```

> 5 sơ đồ flow chi tiết: `BUSINESS_REQUIREMENTS.md` Mục 4.4.

### 3.6 Bản đồ áp dụng BR vào 15 module

| Module | Số BR đặc thù | UC chính | Acceptance Criteria |
| --- | :---: | --- | --- |
| 1. Xe (XE) | 9 | UC-XE-01..05 | AC-XE-01..03 |
| 2. Khách hàng (KH) | 7 | UC-KH-01..04 | AC-KH-01..03 |
| 3. Nhân viên (NV) | 8 | UC-NV-01..05 | AC-NV-* |
| 4. **Hợp đồng (HD)** | **12** | **UC-HD-01..04** | **AC-HD-01..05** |
| 5. Kho (KHO) | 7 | UC-KHO-01..03 | AC-KHO-* |
| 6. **Bảo hành (BH)** | **10** | **UC-BH-01..05** | **AC-BH-01..02** |
| 7. Khuyến mãi (KM) | 10 | UC-KM-01..05 | AC-KM-01..02 |
| 8. Phụ kiện (PK) | 8 | UC-PK-01..03 | AC-PK-* |
| 9. Hậu mãi (HM) | 7 | UC-HM-01..04 | AC-HM-* |
| 10. NCC | 6 | UC-NCC-01..03 | AC-NCC-* |
| 11. **Trả góp (TG)** | **10** | **UC-TG-01..03** | **AC-TG-01..02** |
| 12. Marketing (MK) | 7 | UC-MK-01..04 | AC-MK-* |
| 13. Khiếu nại (KN) | 7 | UC-KN-01..04 | AC-KN-* |
| 14. Báo cáo (BC) | 7 | UC-BC-01..02 | AC-BC-01..02 |
| 15. Bảo mật (SEC) | 9 | UC-SEC-01..04 | AC-SEC-01..04 |
| **Tổng** | **124** | **~50 UC** | **~30+ AC** |

> Module **in đậm** = module quan trọng nhất, kiểm thử kỹ.

### 3.7 Yêu cầu phi chức năng (kế thừa từ `YEU_CAU_CHUC_NANG.md` & BRD Mục 8.3)

| Loại | Chỉ tiêu | Ràng buộc BRD |
| --- | --- | --- |
| Hiệu năng | Tìm kiếm xe ≤ 2s với 10.000 bản ghi; tải danh sách KH ≤ 1s | C-PERF-01, 02 |
| Đồng thời | Hỗ trợ tối đa 50 người dùng đồng thời (mạng nội bộ) | C-PERF-03 |
| Độ tin cậy | Lỗi hệ thống < 0.1%; backup hàng ngày; phục hồi ≤ 15 phút | C-PERF-04, 05 |
| Bảo mật | bcrypt cost ≥ 12; least privilege; audit trail; session 30 phút | BR-SEC-01..09 |
| Khả năng sử dụng | Đào tạo NV mới ≤ 2 giờ; thông điệp tiếng Việt có dấu | BR-UI-06 |
| Khả năng bảo trì | Comment tiếng Việt; kiến trúc module; coverage ≥ 80% | C-TECH-07 |
| Khả chuyển | Chạy được Windows / Linux / macOS | C-TECH-05 |

---

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

## 5. UI/UX PLAN - DANH SÁCH MÀN HÌNH

### 5.1 Triết lý thiết kế

- Tham chiếu tới `design/DESIGN-apple.md`: tone Apple-style, tối giản, photography-first, accent xanh `#0066cc`.
- Font hệ thống ưu tiên: SF Pro Display / SF Pro Text → fallback `system-ui`, `-apple-system`, `Segoe UI` (Windows).
- Chrome UI tối giản, đường viền mảnh `#e0e0e0`, phẳng (không bóng đổ trên card/button).
- Bo tròn: nút primary dùng pill (`9999px`), thẻ utility dùng `18px`.
- Thông điệp tiếng Việt rõ ràng, không viết tắt khó hiểu.
- Hỗ trợ thao tác bàn phím: phím tắt `Ctrl+N` (tạo mới), `Ctrl+F` (tìm kiếm), `F5` (refresh), `Esc` (đóng dialog).

### 5.2 Cấu trúc layout chung (Main Window)

```text
┌───────────────────────────────────────────────────────────────┐
│  Top bar (44px)  | Logo | Tên đại lý          | User · Logout │
├──────────────┬────────────────────────────────────────────────┤
│              │                                                │
│              │                                                │
│  Sidebar     │            Content Area                        │
│  (240px)     │       (màn hình nghiệp vụ)                     │
│              │                                                │
│  - Dashboard │                                                │
│  - Xe        │                                                │
│  - Khách hàng│                                                │
│  - Hợp đồng  │                                                │
│  - Kho       │                                                │
│  - ...       │                                                │
│              │                                                │
├──────────────┴────────────────────────────────────────────────┤
│  Status bar (28px) | Người dùng · Thời gian · Phiên bản       │
└───────────────────────────────────────────────────────────────┘
```

- **Top bar**: nền `#000` (theo Apple global-nav), text trắng, hiển thị tên đại lý, user hiện tại, nút đăng xuất.
- **Sidebar**: nền `#f5f5f7`, text `#1d1d1f`, item đang chọn highlight nhẹ, hiển thị icon + nhãn.
- **Content area**: nền `#ffffff`, padding 32px, có sub-header riêng cho mỗi màn hình.
- **Status bar**: hiển thị user, thời gian, version, trạng thái kết nối DB.

### 5.3 Tổng quan danh sách màn hình

Tổng cộng **42 màn hình** chia theo 5 nhóm:

| Nhóm | Số màn hình | Ghi chú |
| --- | --- | --- |
| A. Xác thực & Hệ thống | 3 | Đăng nhập, đổi mật khẩu, log |
| B. Dashboard & Cấu hình | 2 | Trang chủ, cài đặt |
| C. Nghiệp vụ lõi | 14 | Xe, KH, NV, HĐ, kho |
| D. Nghiệp vụ mở rộng | 16 | BH, KM, PK, NCC, trả góp, hậu mãi |
| E. Marketing, khiếu nại, báo cáo | 7 | MK, KN, báo cáo |

### 5.4 Chi tiết danh sách màn hình

#### A. Xác thực & Hệ thống

| ID | Màn hình | UC tham chiếu | Vai trò xem | Thành phần chính |
| --- | --- | --- | --- | --- |
| `S-AUTH-01` | **Đăng nhập** | UC-SEC-01 | Tất cả | Logo, ô `username`, ô `mật khẩu`, nút "Đăng nhập" (pill xanh), thông báo lỗi inline; áp dụng BR-SEC-05 (khoá 5 lần sai) |
| `S-AUTH-02` | **Đổi mật khẩu** | UC-NV-05 | Tất cả | Form: mật khẩu hiện tại / mới / xác nhận; điều kiện độ mạnh (BR-SEC-02) |
| `S-SYS-01` | **Nhật ký hoạt động (Audit Log)** | UC-SEC-03 | A-01 Admin | Bảng log: thời gian, user, hành động, bảng ảnh hưởng, JSON diff; filter ngày/user/hành động; xuất Excel |

#### B. Dashboard & Cấu hình

| ID | Màn hình | UC tham chiếu | Vai trò xem | Thành phần chính |
| --- | --- | --- | --- | --- |
| `S-DB-01` | **Dashboard tổng quan** | UC-BC-02 | A-01 (full) / A-02 (cá nhân) | KPI tiles: doanh thu tháng, số HĐ, số xe tồn, BH sắp hết hạn (BR-BH-03), cảnh báo chậm trả (BR-TG-08), sinh nhật KH (BR-HM-03), KN cấp độ cao (BR-KN-03); biểu đồ doanh thu 12 tháng |
| `S-CFG-01` | **Cài đặt hệ thống** | (cấu hình) | A-01 Admin | Cấu hình `system_settings`: logo, tên đại lý, địa chỉ, `thoi_han_bh_default` (24), `muc_toi_thieu_default` (2), đường dẫn backup |

#### C. Nghiệp vụ lõi

##### C.1 Quản lý xe

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-XE-01` | **Danh sách xe** | UC-XE-04 | Thanh tìm kiếm + bộ lọc (hãng, dòng, năm, giá, trạng thái) + nút "Thêm xe"; bảng (mã, hãng, dòng, năm, màu, giá, tồn kho, trạng thái); highlight tồn kho thấp (BR-XE-08); phân trang |
| `S-XE-02` | **Form thêm/sửa xe** | UC-XE-01, UC-XE-02 | Dialog: `ma_xe` (disable khi sửa — BR-XE-01), hãng, dòng, `nam_san_xuat` (validate BR-XE-09), màu, giá bán, tồn kho, mức tối thiểu |
| `S-XE-03` | **Chi tiết xe** | UC-XE-05 | Tab Thông tin · Lịch sử nhập kho · HĐ đã bán · KM đang áp dụng |

##### C.2 Quản lý khách hàng

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-KH-01` | **Danh sách khách hàng** | (R) | Tìm theo tên/SĐT/email; lọc `phan_loai` (Thường/Thân thiết/VIP); badge màu theo BR-CALC-03 |
| `S-KH-02` | **Form thêm/sửa khách hàng** | UC-KH-01, UC-KH-02 | Họ tên, SĐT, email, địa chỉ, ngày sinh; kiểm tra trùng SĐT (BR-KH-02), validate email (BR-DATA-04), SĐT VN (BR-DATA-05) |
| `S-KH-03` | **Chi tiết khách hàng** | UC-KH-03 | Tab Thông tin · Lịch sử giao dịch · Bảo hành · Khiếu nại; card tổng giá trị mua, số xe, phân loại (auto BR-KH-03) |

##### C.3 Quản lý nhân viên

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-NV-01` | **Danh sách nhân viên** *(A-01)* | UC-NV-01, UC-NV-02 | Bảng: username, họ tên, vai trò, email, KPI tháng, trạng thái; nút thêm/khoá/mở khoá; không được khoá tài khoản `admin` gốc (BR-NV-07) |
| `S-NV-02` | **Form thêm/sửa nhân viên** *(A-01)* | UC-NV-01 | Username, họ tên, email, SĐT, vai trò; **mật khẩu sinh ngẫu nhiên** 12 ký tự (BR-NV-08), hiển thị 1 lần |
| `S-NV-03` | **Hồ sơ cá nhân (My Profile)** *(A-02, A-03)* | UC-NV-03, UC-NV-05 | Thông tin cá nhân, đổi mật khẩu, KPI cá nhân (BR-CALC-05): số xe bán, doanh thu, tỷ lệ chốt |

##### C.4 Quản lý hợp đồng

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-HD-01` | **Danh sách hợp đồng** | (R) | Lọc trạng thái, ngày, KH, NV; bảng: mã HĐ (`HD2026-NNNN`), KH, xe, tổng tiền, trạng thái (badge BR-FLOW), ngày tạo |
| `S-HD-02` | **Wizard tạo/sửa HĐ** *(4 bước)* | UC-HD-01 | B1: Chọn/Tạo KH · B2: Chọn xe + PK (snapshot giá) · B3: Áp dụng KM (BR-KM-01..04) · B4: Xác nhận tổng tiền (BR-CALC-01) & lưu |
| `S-HD-03` | **Chi tiết hợp đồng** | UC-HD-02, UC-HD-04 | Thông tin đầy đủ; nút chuyển trạng thái (BR-FLOW); nút "Hủy HĐ" (chỉ A-01); nút in PDF; lịch sử trạng thái |
| `S-HD-04` | **Xem trước & In PDF** | UC-HD-03 | Preview PDF render bằng **Jinja2 + WeasyPrint** (BR-HD-10): thông tin đại lý, KH, xe, PK, bảng giá, KM, điều khoản BH, chữ ký 2 bên |

##### C.5 Quản lý kho

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-KHO-01` | **Tổng quan kho** | UC-KHO-02 | Bảng tồn kho theo dòng xe; highlight đỏ khi `≤ muc_toi_thieu` (BR-KHO-02); footer: tổng giá trị (BR-KHO-06) |
| `S-KHO-02` | **Nhập kho** | UC-KHO-01 | Form: chọn NCC, xe/PK, số lượng (≥1), giá nhập, ngày nhập; bảng lịch sử nhập gần nhất (UC-KHO-03) |

#### D. Nghiệp vụ mở rộng

##### D.1 Quản lý bảo hành

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-BH-01` | **Danh sách bảo hành** | UC-BH-05 | Lọc trạng thái (còn HL / sắp hết / hết hạn); cảnh báo BH sắp hết 30 ngày (BR-BH-03, BR-TIME-01) |
| `S-BH-02` | **Chi tiết bảo hành** | (R) | Thông tin xe, KH, `thoi_han_bh`, `pham_vi`; danh sách yêu cầu BH đã tiếp nhận |
| `S-BH-03` | **Tạo yêu cầu bảo hành** | UC-BH-02, UC-BH-03 | Ngày đến, nội dung sửa, phân loại (BR-BH-04: miễn phí/tính phí), chi phí, kỹ thuật phụ trách |
| `S-BH-04` | **In phiếu BH / biên lai** | UC-BH-04 | Preview phiếu BH render bằng Jinja2 + WeasyPrint (BR-BH-07) |

##### D.2 Quản lý khuyến mãi

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-KM-01` | **Danh sách khuyến mãi** | UC-KM-03 | Badge trạng thái theo BR-FLOW (KM); nút tạm dừng/khôi phục (BR-KM-07) |
| `S-KM-02` | **Tạo/sửa khuyến mãi** | UC-KM-01, UC-KM-02 | Tên, mô tả, `loai_km` (4 loại BR-KM-03), `gia_tri`, `kieu_gia_tri` (tiền/%), thời gian, phạm vi multi-select (hãng/dòng/xe cụ thể/xe tồn lâu — BR-KM-04) |
| `S-KM-03` | **Báo cáo hiệu quả KM** | UC-KM-05 (RP-06) | Số HĐ áp dụng, doanh thu phát sinh, tổng tiền giảm (BR-KM-09); biểu đồ cột |

##### D.3 Quản lý phụ kiện

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-PK-01` | **Danh sách phụ kiện** | UC-PK-01 | Lọc theo `phan_loai` (5 loại BR-PK-01); hiển thị tồn kho + cảnh báo khi `≤ 0` (BR-PK-05) |
| `S-PK-02` | **Form thêm/sửa phụ kiện** | UC-PK-01 | Tên, mô tả, phân loại, giá bán, tồn kho |
| `S-PK-03` | **Quản lý combo phụ kiện** | UC-PK-02 | Tạo combo: tên, danh sách PK + số lượng, `he_so_giam` (mặc định 0.9); hiển thị giá ưu đãi tự tính (BR-CALC-07) |

##### D.4 Quản lý NCC

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-NCC-01` | **Danh sách NCC** | UC-NCC-01 | Bảng NCC + điểm đánh giá trung bình (BR-NCC-03); nút đánh giá nhanh |
| `S-NCC-02` | **Chi tiết NCC** | UC-NCC-02 | Thông tin liên hệ, lịch sử nhập hàng, đánh giá 3 tiêu chí (BR-NCC-02) sao 1-5 |
| `S-NCC-03` | **Đơn đặt hàng NCC** | UC-NCC-03 | Tạo đơn: chọn NCC, danh sách xe/PK, trạng thái đơn theo BR-FLOW (ĐĐH NCC); khi `da_nhan` tự sinh `nhap_kho` (BR-NCC-05) |

##### D.5 Quản lý trả góp

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-TG-01` | **Danh sách hồ sơ trả góp** | UC-TG-03 | Lọc theo ngân hàng, trạng thái; highlight đỏ khi có kỳ `qua_han` (BR-TG-08, 09) |
| `S-TG-02` | **Tạo hồ sơ trả góp** | UC-TG-01 | Liên kết HĐ; nhập ngân hàng, `so_tien_vay`, `lai_suat_nam` (∈[0,30]), `so_ky` (∈[6,84]); **tự tính** `M` theo BR-CALC-04 (niên kim) và sinh `n` kỳ |
| `S-TG-03` | **Theo dõi tiến độ trả góp** | UC-TG-02 | Bảng kỳ trả: số kỳ, `ngay_den_han`, `so_tien`, trạng thái (`chua_tra`/`da_tra`/`qua_han`); nút ghi nhận thanh toán |

##### D.6 Dịch vụ hậu mãi

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-HM-01` | **Lịch bảo dưỡng** | UC-HM-01 | Calendar view + list view; nhắc nhở 7 ngày trước lịch BD (BR-TIME-02) |
| `S-HM-02` | **Tạo phiếu bảo dưỡng** | UC-HM-02 | Chọn KH/xe, ngày, KM xe, nội dung, chi phí (BR-HM-06) |
| `S-HM-03` | **Yêu cầu cứu hộ** | UC-HM-03 | Ghi nhận: KH, xe, vị trí, mô tả, chi phí, trạng thái (BR-HM-04, 05) |
| `S-HM-04` | **Chăm sóc khách hàng** | UC-HM-04 | Danh sách KH có sinh nhật trong ±7 ngày (BR-TIME-05); gợi ý gửi thiệp/ưu đãi |

#### E. Marketing, Khiếu nại, Báo cáo

##### E.1 Marketing

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-MK-01` | **Danh sách chiến dịch** | UC-MK-01, UC-MK-04 | Bảng chiến dịch + ngân sách + tỷ lệ chuyển đổi (BR-CALC-06) |
| `S-MK-02` | **Tạo chiến dịch** | UC-MK-01 | Tên, ngân sách, thời gian, kênh tiếp thị (BR-MK validation), mục tiêu |
| `S-MK-03` | **Quản lý lead** | UC-MK-02, UC-MK-03 | Danh sách lead, trạng thái `moi/dang_cham_soc/chuyen_doi/tu_choi` (BR-MK-02); nút "Chuyển thành KH" (BR-MK-03) |

##### E.2 Khiếu nại

| ID | Màn hình | UC tham chiếu | Thành phần chính |
| --- | --- | --- | --- |
| `S-KN-01` | **Danh sách khiếu nại** | UC-KN-01 | Lọc theo mức độ (`thap/trung_binh/cao`) và trạng thái; KN `cao` hiển thị nổi bật (BR-KN-03) |
| `S-KN-02` | **Chi tiết & xử lý khiếu nại** | UC-KN-02, UC-KN-03, UC-KN-04 | Nội dung, phân công (A-01), cập nhật trạng thái + ghi chú lý do (BR-KN-05); đánh giá hài lòng 1-5 sao trước khi đóng (BR-KN-04) |

##### E.3 Báo cáo

| ID | Màn hình | UC / Report | Thành phần chính |
| --- | --- | --- | --- |
| `S-BC-01` | **Báo cáo doanh thu** | UC-BC-01, **RP-01** | Filter ngày/tháng/quý/năm + NV + dòng xe (BR-BC-01); biểu đồ cột + đường; xuất Excel (openpyxl) |
| `S-BC-02` | **Top 10 xe bán chạy** | UC-BC-01, **RP-02** | Bảng + biểu đồ cột ngang; filter khoảng thời gian (BR-BC-02) |
| `S-BC-03` | **Hiệu suất nhân viên** | UC-BC-01, **RP-03** | Bảng KPI NV (BR-CALC-05): số HĐ, doanh thu, tỷ lệ chốt; biểu đồ so sánh |
| `S-BC-04` | **Khách hàng VIP** | UC-BC-01, **RP-04** | Danh sách KH theo `tong_gia_tri_mua` giảm dần (BR-BC-03); xuất Excel |

> Ngoài 4 màn hình trên, các báo cáo `RP-05` (chi phí BH), `RP-06` (hiệu quả KM), `RP-07` (hiệu quả marketing) được nhúng tại `S-KM-03`, `S-MK-01` và một tab báo cáo BH tại `S-BH-01`.

### 5.5 Sơ đồ điều hướng (User Flow chính)

```text
[Đăng nhập] ──► [Dashboard]
                   │
                   ├──► Xe ──► Danh sách ──► Chi tiết / Form
                   ├──► KH  ──► Danh sách ──► Chi tiết / Form
                   ├──► HĐ  ──► Danh sách ──► Wizard tạo HĐ ──► PDF
                   ├──► Kho ──► Tổng quan ──► Nhập kho
                   ├──► BH  ──► Danh sách ──► Chi tiết ──► Tạo yêu cầu
                   ├──► KM, PK, NCC, Trả góp, Hậu mãi ...
                   ├──► Marketing, Khiếu nại
                   └──► Báo cáo (4 màn hình)
```

### 5.6 Workflow End-to-End (cross-module)

> Các workflow xuyên qua nhiều màn hình & module được đặc tả chi tiết tại `BUSINESS_REQUIREMENTS.md` Mục 6 (WF-01..08). Bảng dưới ánh xạ với màn hình tương ứng.

| Mã | Workflow | Actor chính | Màn hình tham gia |
| --- | --- | --- | --- |
| **WF-01** | Nhập kho xe mới | A-01 Admin | `S-NCC-03` → `S-KHO-02` → `S-XE-01` |
| **WF-02** | Bán xe chuẩn (không trả góp) | A-02 Sales | `S-KH-01/02` → `S-HD-02` (wizard) → `S-HD-03` → `S-HD-04` (PDF) → `S-BH-01` (auto) |
| **WF-03** | Bán xe trả góp | A-02 Sales + A-01 Admin | WF-02 + `S-TG-02` → `S-TG-03` |
| **WF-04** | Bảo hành xe | A-02 / A-03 | `S-BH-01` → `S-BH-02` → `S-BH-03` → `S-BH-04` |
| **WF-05** | Bảo dưỡng định kỳ | A-03 Kỹ thuật | `S-DB-01` (cảnh báo) → `S-HM-01` → `S-HM-02` |
| **WF-06** | Xử lý khiếu nại | A-02 / A-01 / A-03 | `S-KN-01` → `S-KN-02` |
| **WF-07** | Marketing → Lead → KH | A-01 + A-02 | `S-MK-02` → `S-MK-03` → `S-HD-02` (wizard, chuyển lead) |
| **WF-08** | Hủy hợp đồng | A-01 Admin | `S-HD-03` → confirm dialog → audit log |

### 5.7 Component Library tái sử dụng (PyQt6)

| Component | Mô tả | BR liên quan |
| --- | --- | --- |
| `PrimaryButton` | Pill xanh (`#0066cc`), text trắng, padding 11×22, dùng cho action chính | - |
| `SecondaryButton` | Pill viền xanh, nền trắng | - |
| `DangerButton` | Pill đỏ — dùng cho action phá huỷ (xoá, hủy HĐ) | BR-UI-04 |
| `DataTable` | QTableView + model có sort/filter/phân trang | C-PERF-01 |
| `SearchBar` | Pill input với icon kính lúp leading | - |
| `FilterChip` | Pill toggle dùng trong thanh filter | - |
| `KpiCard` | Card hiển thị KPI: tiêu đề + số liệu lớn + delta | RP-* |
| `StatusBadge` | Badge bo tròn hiển thị trạng thái với màu khác nhau | BR-UI-03 |
| `MoneyLabel` | Hiển thị tiền VND có dấu phẩy (`1,500,000 VND`) | BR-UI-01 |
| `DateLabel` | Hiển thị ngày `dd/MM/yyyy` | BR-UI-02 |
| `FormDialog` | Modal form chuẩn cho thêm/sửa với validate inline | BR-UI-04 |
| `ConfirmDialog` | Modal xác nhận xoá/hủy với input lý do | BR-UI-04 |
| `ToastNotification` | Thông báo nhanh ở góc dưới phải, hiển thị 3 giây | BR-UI-05 |
| `PdfRenderer` | Wrapper Jinja2 + WeasyPrint để render HĐ/phiếu BH/báo cáo | BR-HD-10, BR-BH-07 |
| `ExcelExporter` | Wrapper openpyxl để xuất báo cáo (RP-01..07) | BR-BC-05 |

### 5.8 Trạng thái màn hình & xử lý ngoại lệ

| Trạng thái | Hiển thị | Áp dụng cho | BR |
| --- | --- | --- | --- |
| **Empty state** | Icon + dòng "Chưa có dữ liệu" + nút tạo mới | Danh sách trống | - |
| **Loading state** | Skeleton hoặc spinner ở giữa | Khi tải danh sách lớn | C-PERF-01, 02 |
| **Error state** | Banner đỏ + nút "Thử lại" | Lỗi DB/IO | - |
| **Permission denied** | Icon khoá + thông báo "Bạn không có quyền" | Khi A-02/A-03 mở màn hình A-01 | Mục 2.5 |
| **Form validation** | Border đỏ + caption đỏ dưới input | Khi nhập sai định dạng | BR-DATA-* |
| **Confirm before destructive** | Dialog xác nhận yêu cầu nhập lý do | Hủy HĐ, xoá NV/xe/KH | BR-UI-04 |
| **Session timeout** | Modal "Phiên hết hạn" → quay về login | 30 phút không thao tác | BR-TIME-07 |

### 5.9 Wireframe ưu tiên (xây dựng trước trong G2-G3)

| Thứ tự | Màn hình | Lý do ưu tiên |
| --- | --- | --- |
| 1 | `S-AUTH-01` Đăng nhập | Cần thiết để vào hệ thống |
| 2 | `S-DB-01` Dashboard | Trang chủ, thử nghiệm sớm KPI tiles |
| 3 | `S-XE-01`, `S-XE-02` Xe | Module nền (tham chiếu rộng) |
| 4 | `S-KH-01`, `S-KH-02` Khách hàng | Module nền (tham chiếu rộng) |
| 5 | `S-HD-01`, `S-HD-02` HĐ wizard | Module nghiệp vụ trọng tâm |
| 6 | `S-HD-04` Xem trước PDF | Xác minh tích hợp Jinja2+WeasyPrint sớm |
| 7 | `S-KHO-01` Tổng quan kho | Phục vụ kiểm tra side-effect tồn kho |
| 8 | `S-NV-01` Quản lý NV | Cần cho test phân quyền |

---

## 6. PHỤ LỤC - LIÊN KẾT TÀI LIỆU

### 6.1 Bộ tài liệu dự án

| Tài liệu | Vai trò | Quan hệ với `PLAN.md` |
| --- | --- | --- |
| `README.md` | Giới thiệu dự án, hướng dẫn cài đặt & chạy | Cấp 0 (tổng quan) |
| `docs/TECH_STACK.md` | Chi tiết tech stack: PyQt6, SQLite, bcrypt, **Jinja2+WeasyPrint**, **openpyxl**, pytest, PyInstaller | `PLAN.md` Mục 1.4 tham chiếu |
| `docs/YEU_CAU_CHUC_NANG.md` | Yêu cầu chức năng & phi chức năng (theo chuẩn IEEE 830) | `PLAN.md` Mục 3.7 tham chiếu |
| `docs/LIST_CHUC_NANG.md` | Danh sách 71 chức năng — 15 module | `PLAN.md` Mục 5 (mã `S-*`) ánh xạ |
| **`docs/BUSINESS_REQUIREMENTS.md`** | **Đặc tả nghiệp vụ chi tiết**: 124 BR module + ~58 BR tổng thể, ~50 UC, 8 Workflow, ~30 AC, 7 Báo cáo, ma trận truy vết | **`PLAN.md` Mục 3 tham chiếu nguồn; Mục 5 dùng UC-XX-NN** |
| `docs/PLAN.md` *(tài liệu này)* | Kế hoạch tổng thể: tổng quan, stakeholder, BR tóm tắt, DB, UI/UX | Trung tâm, link mọi tài liệu khác |
| `design/DESIGN-apple.md` | Design system tham chiếu (Apple, tone tối giản) | `PLAN.md` Mục 5.1 tham chiếu |

### 6.2 Sơ đồ phụ thuộc tài liệu

```text
                        README.md
                            │
                            ▼
                        PLAN.md  (tài liệu này)
                       ╱   │   ╲
                      ▼    ▼    ▼
        TECH_STACK.md    YEU_CAU_  LIST_CHUC_NANG.md
                         CHUC_NANG.md      │
                            │              │
                            ▼              ▼
                  BUSINESS_REQUIREMENTS.md ◄─┐
                  (đặc tả chi tiết — chuẩn   │
                   IEEE 830 + Use Cases +   │
                   Acceptance Criteria)     │
                            │               │
                            ▼               │
                       (Code & Test) ───────┘
```

### 6.3 Quy ước cập nhật tài liệu

- Mọi thay đổi nghiệp vụ **ưu tiên cập nhật trong `BUSINESS_REQUIREMENTS.md`** trước, sau đó mới đồng bộ về `PLAN.md` và `LIST_CHUC_NANG.md`.
- Mỗi cập nhật ghi vào "Phụ lục A. Lịch sử thay đổi" của BRD với phiên bản tăng dần.
- Khi xung đột giữa `PLAN.md` và `BUSINESS_REQUIREMENTS.md` → **lấy BRD làm nguồn chính**.

### 6.4 Thuật ngữ chung

> Đầy đủ tại `BUSINESS_REQUIREMENTS.md` Mục 1.4. Trích lược các thuật ngữ thường dùng trong kế hoạch:

| Thuật ngữ | Ý nghĩa |
| --- | --- |
| **HĐ** | Hợp đồng (`hop_dong`) |
| **KH** | Khách hàng (`khach_hang`) |
| **NV** | Nhân viên (`nhan_vien`) |
| **NCC** | Nhà cung cấp (`nha_cung_cap`) |
| **PK** | Phụ kiện (`phu_kien`) |
| **BH** | Bảo hành (`bao_hanh`) |
| **KM** | Khuyến mãi (`khuyen_mai`) |
| **TG** | Trả góp (`tra_gop`) |
| **MK** | Marketing |
| **KN** | Khiếu nại (`khieu_nai`) |
| **HM** | Hậu mãi (bảo dưỡng, cứu hộ) |
| **KPI** | Key Performance Indicator (chỉ số đánh giá) |
| **CRUD** | Create / Read / Update / Delete |
| **A-NN** | Mã actor (A-01 Admin, A-02 Sales, A-03 Kỹ thuật) |
| **S-XXX-NN** | Mã màn hình UI |
| **WF-NN** | Mã workflow xuyên module |
| **RP-NN** | Mã báo cáo |

