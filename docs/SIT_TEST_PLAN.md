# G6.1 SIT Test Plan — System Integration Testing

## 1. Mục đích

Tài liệu này đặc tả **Test Plan cho System Integration Testing (SIT)** của phần mềm Car-Management, tập trung vào **8 Workflow E2E** (WF-01..WF-08) và **Acceptance Criteria** (AC-XX-NN) trong BRD Mục 9.

---

## 2. Phạm vi

### 2.1 Test Objects

- 8 Workflow E2E: WF-01 (Nhập kho), WF-02 (Bán xe chuẩn), WF-03 (Bán trả góp), WF-04 (Bảo hành), WF-05 (Bảo dưỡng định kỳ), WF-06 (Xử lý khiếu nại), WF-07 (Marketing → Lead → KH), WF-08 (Hủy hợp đồng)
- Acceptance Criteria: AC-XE-01..03, AC-KH-01..03, AC-HD-01..05, AC-BH-01..02, AC-KM-01..02, AC-TG-01..02, AC-BC-01..02, AC-SEC-01..04

### 2.2 Roles tham gia

| Role | Mã | Quyền chính |
| --- | --- | --- |
| **Admin** | A-01 | Toàn quyền CRUD, hủy HĐ, quản lý NV |
| **Sales** | A-02 | Tạo HĐ, quản lý KH, tư vấn |
| **Kỹ thuật BH** | A-03 | Xử lý BH/BD, không tạo HĐ |

---

## 3. Ma trận Workflow × Role × Test Case

### WF-01: Nhập kho xe mới

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-01-01 | Admin tạo đơn đặt hàng NCC → trạng thái `nhap` | Admin | P1 | WF-01 |
| SIT-01-02 | Admin xác nhận giao hàng → tạo `nhap_kho`, tăng tồn kho xe | Admin | P1 | BR-NCC-05, BR-KHO-01 |
| SIT-01-03 | Xe `da_ban` nhập kho mới → tự chuyển về `con_hang` | Admin | P1 | BR-XE-05 |
| SIT-01-04 | Xem lịch sử nhập kho (filter NCC, ngày) | Admin | P2 | UC-KHO-03 |
| SIT-01-05 | Sales không có quyền nhập kho (chỉ xem) | Sales | P1 | Ma trận quyền |
| SIT-01-06 | Đơn `huy` → không tạo nhap_kho | Admin | P2 | BR-NCC-04 |

### WF-02: Bán xe (chuẩn)

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-02-01 | Tạo HĐ wizard 4 bước → lưu `moi_tao` | Sales | P1 | AC-HD-01 |
| SIT-02-02 | Chọn xe → snapshot `gia_xe` cố định | Sales | P1 | BR-HD-* snapshot |
| SIT-02-03 | Thêm PK vào HĐ → snapshot `gia_ban` PK | Sales | P1 | BR-PK-07 |
| SIT-02-04 | Áp dụng KM đúng phạm vi (BR-KM-04) | Sales | P1 | AC-KM-01 |
| SIT-02-05 | Tổng tiền tính đúng: `gia_xe + PK − KM` | Sales | P1 | AC-HD-02, BR-CALC-01 |
| SIT-02-06 | Thanh toán → trạng thái `da_thanh_toan` → giảm tồn kho | Sales | P1 | BR-HD-03, BR-KHO-03 |
| SIT-02-07 | Giao xe → `da_giao_xe` → tự sinh hồ sơ BH (24 tháng) | Sales | P1 | AC-BH-01 |
| SIT-02-08 | Giao xe → cập nhật KH: `tong_gia_tri_mua`, `so_xe_da_mua`, phân loại | Sales | P1 | BR-KH-03, AC-KH-01 |
| SIT-02-09 | Giao xe → tính KPI cho NV (BR-CALC-05) | Sales | P1 | BR-NV-03 |
| SIT-02-10 | In PDF HĐ đầy đủ thông tin (BR-HD-10) | Sales | P1 | AC-HD-04 |
| SIT-02-11 | Sales không sửa được HĐ đã thanh toán | Sales | P1 | BR-HD-09 |
| SIT-02-12 | Không cho chuyển `da_giao_xe` → `moi_tao` (reverse flow) | Sales | P1 | BR-FLOW (HĐ) |
| SIT-02-13 | Sửa giá xe gốc sau khi tạo HĐ → `gia_xe` trong HĐ không đổi | Admin | P1 | BR-HD-* snapshot |

### WF-03: Bán xe trả góp

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-03-01 | Thiết lập trả góp: nhập ngân hàng, số tiền vay, lãi suất, kỳ | Sales | P1 | WF-03 |
| SIT-03-02 | Tính tiền trả/tháng đúng công thức niên kim BR-CALC-04 | Sales | P1 | AC-TG-01 |
| SIT-03-03 | Sinh đủ `n` kỳ trả, mỗi kỳ cách 1 tháng | Sales | P1 | AC-TG-02 |
| SIT-03-04 | Down payment → thanh toán HĐ → giao xe | Sales | P1 | WF-03 |
| SIT-03-05 | Cảnh báo trả góp chậm ≥ 5 ngày (BR-TIME-03) | Sales | P2 | BR-TG-08 |
| SIT-03-06 | Hủy HĐ → xoá hồ sơ trả góp (BR-HD-05) | Admin | P1 | AC-HD-05 |

### WF-04: Bảo hành

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-04-01 | Tìm BH theo SĐT/mã HĐ → hiển thị thời hạn | Kỹ thuật | P1 | WF-04 |
| SIT-04-02 | Tạo yêu cầu BH: phân loại `mien_phi` vs `tinh_phi` | Kỹ thuật | P1 | BR-BH-04 |
| SIT-04-03 | Yêu cầu BH hết hạn → bắt buộc `tinh_phi` | Kỹ thuật | P1 | BR-BH-04 A1 |
| SIT-04-04 | Cập nhật trạng thái: `tiep_nhan → dang_xu_ly → hoan_thanh` | Kỹ thuật | P1 | BR-BH-05 |
| SIT-04-05 | In phiếu BH đầy đủ (BR-BH-07) | Kỹ thuật | P1 | WF-04 |
| SIT-04-06 | BH sắp hết hạn 30 ngày → cảnh báo Dashboard | Admin | P1 | AC-BH-02 |
| SIT-04-07 | Hủy HĐ → xoá hồ sơ BH liên quan | Admin | P1 | BR-BH-10, AC-HD-05 |
| SIT-04-08 | KH có nhiều yêu cầu BH trong thời hạn | Kỹ thuật | P2 | BR-BH-08 |

### WF-05: Bảo dưỡng định kỳ

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-05-01 | Dashboard nhắc lịch BD trước 7 ngày (BR-TIME-02) | Sales | P1 | WF-05 |
| SIT-05-02 | Đặt lịch BD cho KH → lưu thông tin | Sales | P1 | UC-HM-01 |
| SIT-05-03 | Ghi nhận BD: nội dung, chi phí, kỹ thuật phụ trách | Kỹ thuật | P1 | UC-HM-02 |
| SIT-05-04 | Cập nhật lịch BD tiếp theo tự động (BR-HM-01) | Kỹ thuật | P1 | BR-HM-01 |

### WF-06: Xử lý khiếu nại

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-06-01 | Ghi nhận khiếu nại → trạng thái `moi` | Sales | P1 | UC-KN-01 |
| SIT-06-02 | Admin phân công NV xử lý | Admin | P1 | UC-KN-02 |
| SIT-06-03 | Mức độ `cao` → hiển thị badge đỏ Dashboard | Admin | P1 | BR-KN-03 |
| SIT-06-04 | Cập nhật tiến độ kèm ghi chú lý do (BR-KN-05) | Sales | P1 | UC-KN-03 |
| SIT-06-05 | Đóng khiếu nại sau khi xin đánh giá 1-5 sao (BR-KN-04) | Sales | P1 | UC-KN-04 |
| SIT-06-06 | KPI xử lý ≤ 7 ngày (BR-KN-07) | Admin | P2 | BR-KN-07 |

### WF-07: Marketing → Lead → Khách hàng

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-07-01 | Tạo chiến dịch marketing → trạng thái `dang_chay` | Admin | P1 | UC-MK-01 |
| SIT-07-02 | Thêm lead từ chiến dịch → trạng thái `moi` | Sales | P1 | UC-MK-02 |
| SIT-07-03 | Chuyển lead thành KH khi tạo HĐ đầu tiên (UC-MK-03) | Sales | P1 | BR-KH-07 |
| SIT-07-04 | Tính tỷ lệ chuyển đổi marketing (BR-CALC-06) | Admin | P1 | BR-MK-02 |
| SIT-07-05 | Báo cáo hiệu quả chiến dịch: chiến dịch, ngân sách, lead, ROI | Admin | P1 | UC-MK-04 |

### WF-08: Hủy hợp đồng

| Test Case | Mô tả | Role | Priority | AC Ref |
| --- | --- | --- | --- | --- |
| SIT-08-01 | Admin hủy HĐ `moi_tao` → hoàn tồn kho xe & PK | Admin | P1 | BR-HD-05, AC-HD-05 |
| SIT-08-02 | Admin hủy HĐ `da_thanh_toan` → hoàn tồn kho + xoá BH/TG | Admin | P1 | BR-HD-05, BR-BH-10, BR-TG-10 |
| SIT-08-03 | Không cho hủy HĐ `da_giao_xe` (BR-HD-06) | Admin | P1 | BR-HD-06 |
| SIT-08-04 | Hủy HĐ → ghi `ly_do_huy` ≥ 10 ký tự | Admin | P1 | UC-HD-04 |
| SIT-08-05 | Non-admin không thể hủy HĐ | Sales | P1 | Ma trận quyền |
| SIT-08-06 | Hủy HĐ → audit log `CANCEL_HD` | Admin | P1 | BR-SEC-09 |

---

## 4. Test Cases theo Acceptance Criteria

### AC-XE: Module Xe

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-XE-01 | Thêm xe mới: validate `ma_xe` UNIQUE, `nam_san_xuat` ≥ 1990 | P1 |
| SIT-XE-02 | Sửa xe: không cho sửa `ma_xe` (BR-XE-01) | P1 |
| SIT-XE-03 | Xoá xe đang có HĐ → reject (BR-XE-02, BR-REF-01) | P1 |
| SIT-XE-04 | Tìm kiếm 10.000 xe ≤ 2 giây (C-PERF-01) | P1 |
| SIT-XE-05 | Xe `so_luong_ton=0` + có HĐ `da_giao_xe` → tự chuyển `da_ban` (BR-XE-04) | P1 |
| SIT-XE-06 | Nhập kho xe `da_ban` → tự chuyển `con_hang` (BR-XE-05) | P1 |

### AC-KH: Module Khách hàng

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-KH-01 | Thêm KH mới: validate SĐT regex VN, email format | P1 |
| SIT-KH-02 | Trùng SĐT → reject với thông báo rõ (BR-KH-02) | P1 |
| SIT-KH-03 | Phân loại tự động: 499tr → Thuong, 500tr → Thân thiết, 2 tỷ → VIP (BR-CALC-03) | P1 |
| SIT-KH-04 | Lịch sử giao dịch hiển thị đầy đủ kể cả HĐ `huy` | P1 |
| SIT-KH-05 | Xoá KH đã có HĐ → reject (BR-REF-03) | P1 |

### AC-HD: Module Hợp đồng

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-HD-01 | Wizard 4 bước: quay lại và tiến tự do, không mất dữ liệu | P1 |
| SIT-HD-02 | Tổng tiền đúng: xe + PK − giảm KM, với mọi loại KM (4 loại) | P1 |
| SIT-HD-03 | Chuyển trạng thái chỉ đúng flow: `moi_tao → da_thanh_toan → da_giao_xe` | P1 |
| SIT-HD-04 | PDF in ra đủ: đại lý, KH, xe, PK, bảng giá, KM, BH, chữ ký 2 bên | P1 |
| SIT-HD-05 | Hủy HĐ: hoàn kho + xoá BH + xoá TG (AC-HD-05) | P1 |
| SIT-HD-06 | Áp dụng 2 KM cho 1 HĐ → reject (BR-HD-07) | P1 |
| SIT-HD-07 | Chuyển `da_thanh_toan` với xe `so_luong_ton=0` → reject (BR-HD-11) | P1 |
| SIT-HD-08 | Chuyển `da_thanh_toan` với PK `ton_kho < so_luong` → reject (BR-HD-12) | P1 |

### AC-BH: Module Bảo hành

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-BH-01 | HĐ `da_giao_xe` → tự sinh hồ sơ BH đúng `thoi_han_bh=24` tháng | P1 |
| SIT-BH-02 | Dashboard cảnh báo BH sắp hết hạn trong 30 ngày | P1 |
| SIT-BH-03 | BH hết hạn → tiếp nhận yêu cầu bắt buộc `tinh_phi` | P1 |

### AC-KM: Module Khuyến mãi

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-KM-01 | KM chỉ áp dụng khi `dang_chay` + `tu_ngay ≤ today ≤ den_ngay` | P1 |
| SIT-KM-02 | Tiền giảm tính đúng cho 4 loại KM (BR-CALC-02) | P1 |
| SIT-KM-03 | KM `tam_dung` không hiển thị trong dropdown chọn (BR-KM-07) | P1 |
| SIT-KM-04 | KM hết hạn → tự chuyển `ket_thuc` (BR-KM-08) | P1 |

### AC-TG: Module Trả góp

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-TG-01 | Tính tiền trả/tháng đúng công thức niên kim (BR-CALC-04) | P1 |
| SIT-TG-02 | Sinh đủ `n` kỳ trả, ngày cách nhau 1 tháng | P1 |
| SIT-TG-03 | Cảnh báo trả góp quá hạn ≥ 5 ngày (BR-TIME-03) | P1 |

### AC-BC: Module Báo cáo

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-BC-01 | 7 báo cáo (RP-01..07) đều xuất được Excel | P1 |
| SIT-BC-02 | Số liệu báo cáo khớp CSDL (sai số 0) | P1 |

### AC-SEC: Module Bảo mật

| Test Case | Mô tả | Priority |
| --- | --- | --- |
| SIT-SEC-01 | Mật khẩu hash bcrypt cost ≥ 12 | P1 |
| SIT-SEC-02 | Đăng nhập sai 5 lần → khoá 15 phút (BR-SEC-05) | P1 |
| SIT-SEC-03 | Session timeout sau 30 phút không thao tác (BR-TIME-07) | P1 |
| SIT-SEC-04 | Mọi CRUD quan trọng → ghi audit_log (BR-SEC-09) | P1 |

---

## 5. Test Environment Setup

### 5.1 Database Configuration

- **Development DB**: `data/car_management.db` — dùng cho development
- **SIT DB**: `data/car_management_sit.db` — database riêng cho SIT, không ảnh hưởng dev
- Cấu hình qua `scripts/setup_sit_env.py`

### 5.2 Test Users

| Username | Role | Password | Mục đích |
| --- | --- | --- | --- |
| `admin` | Admin | `Admin@123` | Test full permissions |
| `nv01` | Sales | `Admin@123` | Test CRUD HĐ, KH |
| `kt01` | Kỹ thuật BH | `Admin@123` | Test WF-04, WF-05 |

### 5.3 Test Data Requirements

- 1000 KH (faker) — performance test
- 5000 HĐ (faker) — performance test
- 100 NCC (faker)
- 200 BH records (faker)
- 30 xe seed + faker cho perf test
- 25 PK + 5 combo

---

## 6. Test Execution Checklist

### Pre-test
- [ ] Setup SIT DB: `python scripts/setup_sit_env.py`
- [ ] Seed test data: `python scripts/seed_sit.py`
- [ ] Backup clean SIT DB: `python scripts/backup_sit_db.py`

### Per Workflow
- [ ] Run Happy path test cases
- [ ] Run Alternative/Edge cases
- [ ] Log all findings

### Post-test
- [ ] Collect test results
- [ ] Document bugs → GitHub Issues
- [ ] Backup clean SIT DB lại

---

## 7. Risk & Mitigation

| Risk | Impact | Mitigation |
| --- | --- | --- |
| DB state contamination between tests | High | Use isolated SIT DB per test run |
| Performance test data generation slow | Medium | Run seed with batching |
| WF-08 (hủy) destroy test data | High | Backup before WF-08 tests |
| Role permission matrix complex | Medium | Test each role separately first |