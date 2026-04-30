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
