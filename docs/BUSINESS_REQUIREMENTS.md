# TÀI LIỆU YÊU CẦU NGHIỆP VỤ

**Phần mềm Quản lý Đại lý Xe hơi**

> **Business Requirements Document (BRD)** — phiên bản 1.0
>
> Tài liệu này đặc tả đầy đủ các yêu cầu nghiệp vụ (Business Requirements) làm cơ sở cho thiết kế kỹ thuật, phát triển và kiểm thử phần mềm.

---

## MỤC LỤC

1. [Giới thiệu](#1-giới-thiệu)
2. [Tổng quan nghiệp vụ](#2-tổng-quan-nghiệp-vụ)
3. [Stakeholders & Actors](#3-stakeholders--actors)
4. [Business Rules tổng thể](#4-business-rules-tổng-thể)
5. [Yêu cầu nghiệp vụ theo module](#5-yêu-cầu-nghiệp-vụ-theo-module)
6. [Quy trình nghiệp vụ End-to-End](#6-quy-trình-nghiệp-vụ-end-to-end)
7. [Báo cáo & KPI](#7-báo-cáo--kpi)
8. [Ràng buộc & Giả định](#8-ràng-buộc--giả-định)
9. [Tiêu chí nghiệm thu](#9-tiêu-chí-nghiệm-thu)
10. [Ma trận truy vết](#10-ma-trận-truy-vết)

---

## 1. GIỚI THIỆU

### 1.1 Mục đích tài liệu

Tài liệu Business Requirements này mô tả các yêu cầu nghiệp vụ của phần mềm quản lý đại lý xe hơi. Nó là cầu nối giữa **bên nghiệp vụ** (chủ đại lý, quản lý, nhân viên) và **đội phát triển**, đảm bảo:

- Mọi yêu cầu nghiệp vụ được ghi chép rõ ràng, không mơ hồ.
- Là cơ sở để thiết kế kỹ thuật (CSDL, kiến trúc, UI).
- Là cơ sở để xây dựng kịch bản kiểm thử.
- Là căn cứ nghiệm thu sản phẩm.

### 1.2 Phạm vi tài liệu

**Bao gồm**:

- Quy tắc nghiệp vụ (Business Rules).
- Use case chi tiết cho 15 module nghiệp vụ.
- Quy trình nghiệp vụ end-to-end.
- Ràng buộc dữ liệu, công thức tính toán, tiêu chí nghiệm thu.

**Không bao gồm**:

- Thiết kế giao diện chi tiết (xem `PLAN.md` mục 5).
- Đặc tả kỹ thuật CSDL chi tiết (xem `PLAN.md` mục 4).
- Lựa chọn công nghệ (xem `TECH_STACK.md`).

### 1.3 Đối tượng độc giả

| Đối tượng | Cách đọc tài liệu |
| --- | --- |
| **Chủ đại lý / Quản lý** | Đọc Mục 1, 2, 6, 7 để xác nhận đúng nghiệp vụ |
| **Nhóm phát triển** | Đọc toàn bộ, tập trung Mục 4, 5 |
| **Tester** | Đọc Mục 5, 6, 9 để viết test case |
| **Giảng viên** | Đọc toàn bộ để đánh giá độ đầy đủ của yêu cầu |

### 1.4 Tài liệu tham chiếu

| Mã | Tài liệu | Vai trò |
| --- | --- | --- |
| REF-01 | `README.md` | Giới thiệu dự án |
| REF-02 | `docs/TECH_STACK.md` | Tech stack |
| REF-03 | `docs/YEU_CAU_CHUC_NANG.md` | Yêu cầu chức năng & phi chức năng |
| REF-04 | `docs/LIST_CHUC_NANG.md` | Danh sách 71 chức năng |
| REF-05 | `docs/PLAN.md` | Kế hoạch tổng thể |
| REF-06 | `design/DESIGN-apple.md` | Design system |

### 1.5 Định nghĩa & viết tắt

| Thuật ngữ | Định nghĩa |
| --- | --- |
| **Đại lý** | Cửa hàng/showroom kinh doanh xe hơi sử dụng phần mềm |
| **HĐ** | Hợp đồng (mua bán xe) |
| **KH** | Khách hàng |
| **NV** | Nhân viên |
| **NCC** | Nhà cung cấp (xe & phụ kiện) |
| **PK** | Phụ kiện |
| **KM** | Khuyến mãi |
| **BH** | Bảo hành |
| **BD** | Bảo dưỡng |
| **VIP** | Khách hàng có tổng giá trị mua hoặc số xe đạt mức cao nhất |
| **KPI** | Chỉ số hiệu suất công việc (Key Performance Indicator) |
| **CRUD** | Create / Read / Update / Delete |
| **Lead** | Khách hàng tiềm năng (chưa phát sinh giao dịch) |
| **BR** | Business Rule (quy tắc nghiệp vụ) |
| **UC** | Use Case (trường hợp sử dụng) |
| **bcrypt** | Thuật toán băm mật khẩu một chiều |

### 1.6 Ký hiệu mã yêu cầu

| Tiền tố | Ý nghĩa | Ví dụ |
| --- | --- | --- |
| `BR-XX-NN` | Business Rule cho module XX, số thứ tự NN | `BR-HD-02` |
| `UC-XX-NN` | Use Case cho module XX | `UC-HD-01` |
| `AC-XX-NN` | Acceptance Criteria | `AC-HD-01` |
| `WF-NN` | Workflow (quy trình E2E) | `WF-01` |

Các mã module XX:

- `XE` (Xe), `KH` (Khách hàng), `NV` (Nhân viên), `HD` (Hợp đồng), `KHO` (Kho).
- `BH` (Bảo hành), `KM` (Khuyến mãi), `PK` (Phụ kiện), `HM` (Hậu mãi), `NCC` (Nhà cung cấp).
- `TG` (Trả góp), `MK` (Marketing), `KN` (Khiếu nại), `BC` (Báo cáo), `SEC` (Bảo mật).

---

## 2. TỔNG QUAN NGHIỆP VỤ

### 2.1 Bối cảnh kinh doanh

Một đại lý xe hơi điển hình tại Việt Nam thực hiện các hoạt động chính sau:

1. **Nhập xe** từ hãng/nhà phân phối, lưu kho.
2. **Tư vấn & bán xe** cho khách hàng, tạo hợp đồng.
3. **Cung cấp phụ kiện** đi kèm xe.
4. **Áp dụng khuyến mãi** để kích thích doanh số.
5. **Bảo hành & bảo dưỡng** xe sau khi bán.
6. **Hỗ trợ trả góp** thông qua đối tác ngân hàng.
7. **Marketing** thu hút khách hàng tiềm năng.
8. **Chăm sóc sau bán** (sinh nhật, ưu đãi tri ân, xử lý khiếu nại).

Trước khi có phần mềm, các đại lý thường dùng Excel rời rạc, dẫn đến: **mất dữ liệu, sai số liệu kế toán, khó tra cứu lịch sử bảo hành, không theo dõi được KPI nhân viên**. Phần mềm này giải quyết các vấn đề trên.

### 2.2 Mục tiêu nghiệp vụ

| Mã | Mục tiêu | Đo lường thành công |
| --- | --- | --- |
| BO-01 | Số hoá toàn bộ quy trình bán xe | 100% hợp đồng được tạo trên hệ thống, không còn dùng Excel |
| BO-02 | Theo dõi tồn kho chính xác theo thời gian thực | Sai lệch tồn kho thực tế ↔ hệ thống = 0 |
| BO-03 | Tăng tốc tra cứu thông tin khách hàng & xe | Mọi truy vấn ≤ 2 giây |
| BO-04 | Đảm bảo không bỏ sót lịch bảo hành/bảo dưỡng | Cảnh báo trước 30 ngày BH hết hạn, 7 ngày trước BD |
| BO-05 | Đo lường được hiệu suất nhân viên | Mỗi NV xem được KPI cá nhân; admin xem được toàn đại lý |
| BO-06 | Bảo mật dữ liệu khách hàng | Mật khẩu mã hoá bcrypt, audit log đầy đủ |
| BO-07 | Hỗ trợ ra quyết định kinh doanh | Có ≥ 4 báo cáo định kỳ (doanh thu, top xe, KPI NV, KH VIP) |

### 2.3 Phạm vi nghiệp vụ

```text
                  ┌────────────────────────────────────────┐
                  │       PHẦN MỀM QUẢN LÝ ĐẠI LÝ XE        │
                  ├────────────────────────────────────────┤
                  │                                         │
   ┌──────┐       │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │      ┌──────┐
   │ NCC  │──────►│  │  Kho    │──│   Xe    │──│   HĐ    │ │─────►│  KH  │
   └──────┘ Nhập  │  └─────────┘  └─────────┘  └────┬────┘ │ Bán  └───┬──┘
                  │                                  │      │          │
                  │              ┌────────────┬──────┤      │          │
                  │              ▼            ▼      ▼      │          │
                  │         ┌────────┐  ┌────────┐ ┌─────┐  │          │
                  │         │   PK   │  │   KM   │ │ BH  │◄─┼──────────┘
                  │         └────────┘  └────────┘ └─────┘  │   Bảo hành
                  │                                          │
                  │  ┌─────────┐  ┌──────────┐  ┌─────────┐ │
                  │  │ Trả góp │  │  Hậu mãi │  │ Khiếu  │ │
                  │  │         │  │  (BD)    │  │  nại   │ │
                  │  └─────────┘  └──────────┘  └─────────┘ │
                  │                                          │
                  │  ┌─────────┐  ┌──────────┐  ┌─────────┐ │
                  │  │   NV    │  │Marketing │  │ Báo cáo │ │
                  │  │  + KPI  │  │ + Lead   │  │         │ │
                  │  └─────────┘  └──────────┘  └─────────┘ │
                  │                                          │
                  │  ┌─────────────────────────────────────┐ │
                  │  │      Bảo mật & Audit Log            │ │
                  │  └─────────────────────────────────────┘ │
                  └─────────────────────────────────────────┘
```

### 2.4 Quy trình nghiệp vụ chính (high-level)

| Mã WF | Quy trình | Mô tả ngắn |
| --- | --- | --- |
| WF-01 | Nhập kho xe mới | NCC → đại lý nhập kho → cập nhật tồn |
| WF-02 | Bán xe (chuẩn) | KH liên hệ → tư vấn → tạo HĐ → thanh toán → giao xe |
| WF-03 | Bán xe trả góp | Như WF-02 + tạo hồ sơ trả góp với ngân hàng |
| WF-04 | Bảo hành | KH yêu cầu BH → kiểm tra → phân loại miễn phí/tính phí → sửa → bàn giao |
| WF-05 | Bảo dưỡng định kỳ | Hệ thống nhắc → KH đến → ghi nhận BD → thu phí |
| WF-06 | Xử lý khiếu nại | KH khiếu nại → phân công → xử lý → đóng → đánh giá |
| WF-07 | Marketing → Lead → KH | Chiến dịch → thu thập lead → chăm sóc → tạo HĐ |

> Chi tiết các workflow xem Mục 6.

### 2.5 Phạm vi loại trừ (Out of scope)

Phần mềm **KHÔNG** bao gồm:

- Bán hàng online / website e-commerce.
- Tích hợp cổng thanh toán (VNPay, Momo…).
- Đồng bộ đa chi nhánh real-time (chỉ chạy đơn lẻ hoặc mạng nội bộ).
- Tích hợp tự động với hệ thống ngân hàng (chỉ ghi nhận thông tin trả góp thủ công).
- Ứng dụng di động cho khách hàng.
- Hệ thống kế toán đầy đủ (chỉ có báo cáo doanh thu cơ bản).

---

## 3. STAKEHOLDERS & ACTORS

### 3.1 Phân loại

Tài liệu phân biệt rõ:

- **Stakeholders**: các bên có lợi ích liên quan đến phần mềm (chủ đại lý, quản lý, giảng viên…).
- **Actors**: các vai trò trực tiếp tương tác với phần mềm (Admin, Sales, Kỹ thuật BH).

### 3.2 Danh sách Actors chi tiết

#### A1 — Quản trị viên (Admin)

| Mục | Chi tiết |
| --- | --- |
| **Mô tả** | Người quản lý toàn bộ hệ thống, thường là chủ/quản lý đại lý hoặc IT |
| **Số lượng dự kiến** | 1-2 người |
| **Tần suất sử dụng** | Hàng ngày |
| **Mức độ thành thạo IT** | Trung bình - Khá |
| **Quyền** | Toàn quyền trên 15 module |
| **Trách nhiệm chính** | Cấu hình hệ thống, quản lý nhân viên, duyệt KM, xem báo cáo, kiểm tra audit log, sao lưu dữ liệu |

#### A2 — Nhân viên bán hàng (Sales)

| Mục | Chi tiết |
| --- | --- |
| **Mô tả** | Người trực tiếp tư vấn và bán xe cho khách |
| **Số lượng dự kiến** | 5-20 người |
| **Tần suất sử dụng** | Hàng ngày, nhiều lần/ngày |
| **Mức độ thành thạo IT** | Cơ bản |
| **Quyền** | Tạo/sửa HĐ, quản lý KH (CRUD), xem xe & PK, áp dụng KM, tạo BH, xem KPI cá nhân |
| **Trách nhiệm chính** | Tư vấn khách, tạo hợp đồng, theo dõi KH của mình, đạt KPI |

#### A3 — Nhân viên kỹ thuật bảo hành (Technician) *(tuỳ chọn)*

| Mục | Chi tiết |
| --- | --- |
| **Mô tả** | Người tiếp nhận và xử lý yêu cầu BH/BD |
| **Số lượng dự kiến** | 2-5 người |
| **Tần suất sử dụng** | Hàng ngày khi có yêu cầu BH/BD |
| **Quyền** | Ghi nhận yêu cầu BH, cập nhật tiến độ, in phiếu BH, ghi nhận BD/cứu hộ |
| **Trách nhiệm chính** | Sửa chữa, ghi log đầy đủ chi phí, bàn giao xe sau BH |

> **Lưu ý**: Trong giai đoạn đầu, nếu không có nhân viên kỹ thuật riêng, **Admin** có thể đảm nhận luôn vai trò này.

### 3.3 Danh sách Stakeholders

| Mã | Stakeholder | Vai trò trong dự án | Quan tâm chính |
| --- | --- | --- | --- |
| SH-01 | **Chủ đại lý** | Người ra quyết định mua/dùng phần mềm | ROI, doanh thu, hiệu suất NV |
| SH-02 | **Quản lý đại lý** | Người vận hành hệ thống | Tồn kho, hợp đồng, KPI |
| SH-03 | **Nhân viên** | Người dùng cuối | Dễ dùng, nhanh, không lỗi |
| SH-04 | **Khách hàng (cuối)** | Đối tượng dữ liệu | Bảo mật thông tin, nhận đúng BH/ưu đãi |
| SH-05 | **Nhà cung cấp** | Đối tác | Đặt hàng, thanh toán đúng hạn |
| SH-06 | **Ngân hàng đối tác** | Đối tác trả góp | Hồ sơ KH chính xác |
| SH-07 | **Nhóm phát triển** | Xây dựng phần mềm | Hoàn thành đúng deadline, học công nghệ |

### 3.4 Ma trận quyền chi tiết (theo CRUD)

Ký hiệu: `C` = Create, `R` = Read, `U` = Update, `D` = Delete, `-` = không có quyền.

| Module | Admin | Sales | Kỹ thuật BH |
| --- | :---: | :---: | :---: |
| Nhân viên (NV khác) | CRUD | - | - |
| Hồ sơ cá nhân | CRU | RU | RU |
| Xe | CRUD | R | R |
| Khách hàng | CRUD | CRU | R |
| Hợp đồng | CRUD | CRU | R |
| Hủy hợp đồng | D | - | - |
| Kho (nhập kho) | CRUD | R | - |
| Phụ kiện | CRUD | R | R |
| Combo phụ kiện | CRUD | R | - |
| Khuyến mãi (CRUD chương trình) | CRUD | R | - |
| Áp dụng KM cho HĐ | C | C | - |
| Bảo hành (hồ sơ) | CRUD | CR | CRU |
| Yêu cầu BH (chi tiết) | CRUD | C | CRU |
| Bảo dưỡng | CRUD | CR | CRU |
| Cứu hộ | CRUD | CR | CRU |
| Nhà cung cấp | CRUD | R | - |
| Đơn đặt hàng NCC | CRUD | - | - |
| Trả góp | CRUD | CR | - |
| Marketing & Lead | CRUD | RU | - |
| Khiếu nại | CRUD | CRU | RU |
| Báo cáo | R | R (cá nhân) | - |
| Audit log | R | - | - |
| Cài đặt hệ thống | CRUD | - | - |


## 4. BUSINESS RULES TỔNG THỂ

### 4.1 Quy tắc về định danh & duy nhất (BR-ID)

| Mã | Quy tắc | Ràng buộc kỹ thuật |
| --- | --- | --- |
| BR-ID-01 | Mỗi xe có `ma_xe` duy nhất, không thay đổi sau khi tạo | UNIQUE INDEX, không cho phép UPDATE field này |
| BR-ID-02 | Mỗi khách hàng định danh duy nhất bởi `so_dien_thoai` | UNIQUE INDEX trên `so_dien_thoai` |
| BR-ID-03 | Mỗi nhân viên có `username` duy nhất, không có khoảng trắng | UNIQUE INDEX, regex `^[a-zA-Z0-9_]+$` |
| BR-ID-04 | Mỗi hợp đồng có `ma_hop_dong` duy nhất, định dạng `HD{YYYY}-{NNNN}` | UNIQUE INDEX, sinh tự động khi tạo |
| BR-ID-05 | Mỗi NCC có `ma_ncc` duy nhất | UNIQUE INDEX |
| BR-ID-06 | Mỗi chương trình KM có `ten_km` duy nhất trong khoảng thời gian áp dụng | Constraint check khi tạo |

### 4.2 Quy tắc về dữ liệu (BR-DATA)

| Mã | Quy tắc | Validation |
| --- | --- | --- |
| BR-DATA-01 | Số tiền (giá xe, tổng HĐ, chi phí…) ≥ 0, đơn vị VND, kiểu integer | `CHECK (gia_ban >= 0)` |
| BR-DATA-02 | Số lượng (tồn kho, kỳ trả góp…) ≥ 0 | `CHECK (so_luong >= 0)` |
| BR-DATA-03 | Năm sản xuất xe trong [1990, năm hiện tại + 1] | Validate UI + DB |
| BR-DATA-04 | Email phải đúng định dạng `local@domain.tld` | Regex chuẩn RFC 5322 đơn giản |
| BR-DATA-05 | SĐT Việt Nam: 10 chữ số, bắt đầu bằng `0`, theo đầu số nhà mạng VN | Regex `^0[3-9][0-9]{8}$` |
| BR-DATA-06 | Ngày tháng dùng định dạng ISO `YYYY-MM-DD` (lưu trữ); hiển thị `dd/MM/yyyy` | Helper format |
| BR-DATA-07 | Ngày kết thúc ≥ ngày bắt đầu cho mọi cặp ngày (KM, BH, trả góp, chiến dịch…) | Validate UI + DB constraint |
| BR-DATA-08 | Phần trăm (%) phải nằm trong [0, 100] | `CHECK (phan_tram BETWEEN 0 AND 100)` |
| BR-DATA-09 | Lãi suất năm trong [0, 30] (đơn vị %) | Validate UI |
| BR-DATA-10 | Mã hợp đồng/mã xe/mã NCC: chỉ cho phép chữ, số, dấu gạch (`A-Z0-9-_`) | Regex |

### 4.3 Quy tắc về toàn vẹn tham chiếu (BR-REF)

| Mã | Quy tắc |
| --- | --- |
| BR-REF-01 | Không xoá xe khi xe đang có HĐ với trạng thái khác `huy` |
| BR-REF-02 | Không xoá NV khi NV đã tạo bất kỳ HĐ nào → đánh dấu `inactive` |
| BR-REF-03 | Không xoá KH khi KH có HĐ → đánh dấu `inactive` |
| BR-REF-04 | Không xoá phụ kiện khi PK xuất hiện trong HĐ chưa hủy |
| BR-REF-05 | Không xoá NCC khi có lịch sử nhập kho hoặc đơn đặt hàng |
| BR-REF-06 | Không xoá KM khi đã được áp dụng vào HĐ |
| BR-REF-07 | Khi xoá hợp đồng `huy`: phải hoàn lại tồn kho xe & PK |

### 4.4 Quy tắc về luồng trạng thái (BR-FLOW)

#### Trạng thái Hợp đồng

```text
   [moi_tao] ──► [da_thanh_toan] ──► [da_giao_xe]
       │                │
       └─────► [huy] ◄──┘
```

- Từ `moi_tao` chỉ có thể chuyển sang `da_thanh_toan` hoặc `huy`.
- Từ `da_thanh_toan` chỉ có thể chuyển sang `da_giao_xe` hoặc `huy`.
- `da_giao_xe` là trạng thái cuối, **không thể** quay lại hoặc hủy.
- `huy` là trạng thái cuối.

#### Trạng thái Xe

```text
   [con_hang] ──(tồn kho = 0)──► [da_ban]
        ▲
        │ (nhập kho mới)
        │
   [sap_ve] ──(nhập về kho)──────►
```

#### Trạng thái Khuyến mãi

```text
   [nhap] ──► [dang_chay] ◄──► [tam_dung]
                    │
                    └──(hết hạn hoặc admin dừng)──► [ket_thuc]
```

#### Trạng thái Khiếu nại

```text
   [moi] ──► [dang_xu_ly] ──► [da_giai_quyet] ──► [da_dong]
```

#### Trạng thái Đơn đặt hàng NCC

```text
   [nhap] ──► [da_gui] ──► [da_nhan]
       │           │
       └────► [huy] ◄
```

### 4.5 Quy tắc về tính toán (BR-CALC)

#### BR-CALC-01: Tổng tiền hợp đồng

```text
tong_tien = gia_xe + tong_gia_phu_kien − tien_giam_KM
```

Trong đó:

- `gia_xe`: giá xe tại thời điểm tạo hợp đồng (snapshot, không thay đổi khi giá xe sau này thay đổi).
- `tong_gia_phu_kien = SUM(hop_dong_phu_kien.so_luong * hop_dong_phu_kien.gia_ban)`.
- `tien_giam_KM`: số tiền giảm theo KM, tính theo BR-CALC-02.

#### BR-CALC-02: Tiền giảm KM

| Loại KM | Công thức |
| --- | --- |
| `giam_tien_mat` (kiểu `tien`) | `tien_giam = khuyen_mai.gia_tri` |
| `giam_tien_mat` (kiểu `phan_tram`) | `tien_giam = (gia_xe + tong_gia_phu_kien) * gia_tri / 100` |
| `tang_phu_kien` | Phụ kiện được tặng đưa vào HĐ với `gia_ban = 0`, `tien_giam = 0` |
| `giam_lai_suat` | Không ảnh hưởng `tong_tien`, ảnh hưởng module Trả góp |
| `combo` | Áp dụng theo điều kiện riêng của combo |

#### BR-CALC-03: Phân loại khách hàng

```text
IF so_xe_da_mua >= 3 OR tong_gia_tri_mua >= 2_000_000_000 THEN 'VIP'
ELSE IF so_xe_da_mua >= 1 OR tong_gia_tri_mua >= 500_000_000 THEN 'Than_thiet'
ELSE 'Thuong'
```

> Cập nhật phân loại tự động khi HĐ chuyển sang `da_giao_xe`.

#### BR-CALC-04: Số tiền trả góp hàng tháng (công thức niên kim)

```text
M = P × r × (1 + r)^n / ((1 + r)^n − 1)

Trong đó:
  M = số tiền trả mỗi tháng
  P = số tiền vay (gốc)
  r = lãi suất tháng = (lai_suat_nam / 12) / 100
  n = số kỳ trả (số tháng)
```

**Ví dụ**: Vay 500 triệu, lãi suất 8%/năm, 36 tháng:

- `r = 8/12/100 = 0.00667`
- `n = 36`
- `M = 500_000_000 × 0.00667 × (1.00667)^36 / ((1.00667)^36 − 1) ≈ 15_668_000 VND/tháng`

#### BR-CALC-05: KPI nhân viên

```text
KPI(NV, kỳ) = {
   so_xe_ban: COUNT(hop_dong WHERE nhan_vien_id = NV AND trang_thai = 'da_giao_xe' AND ngay_giao_xe IN ky),
   doanh_thu: SUM(hop_dong.tong_tien WHERE ...)
}
```

#### BR-CALC-06: Tỷ lệ chuyển đổi marketing

```text
ti_le_chuyen_doi = (so_lead_thanh_KH / tong_so_lead) × 100%
```

#### BR-CALC-07: Giá combo phụ kiện

```text
gia_combo = SUM(phu_kien.gia_ban * combo_chi_tiet.so_luong) × he_so_giam

Mặc định he_so_giam = 0.9 (giảm 10%)
```

### 4.6 Quy tắc về thời gian & cảnh báo (BR-TIME)

| Mã | Quy tắc | Tần suất kiểm tra |
| --- | --- | --- |
| BR-TIME-01 | Cảnh báo BH sắp hết hạn trước **30 ngày** | Mỗi lần mở Dashboard |
| BR-TIME-02 | Nhắc lịch BD trước **7 ngày** | Mỗi lần mở Dashboard |
| BR-TIME-03 | Cảnh báo trả góp chậm khi quá hạn ≥ **5 ngày** | Mỗi lần mở Dashboard |
| BR-TIME-04 | Cảnh báo tồn kho thấp khi `so_luong ≤ muc_toi_thieu` | Real-time |
| BR-TIME-05 | Sinh nhật KH: hiển thị trong **7 ngày** trước/sau ngày sinh | Mỗi lần mở Dashboard |
| BR-TIME-06 | KM tự động chuyển `ket_thuc` khi `den_ngay < hôm nay` | Khi mở module KM |
| BR-TIME-07 | Phiên đăng nhập hết hạn sau **30 phút** không thao tác | Timer ở UI |
| BR-TIME-08 | Khoá tài khoản **15 phút** sau 5 lần nhập sai mật khẩu | Khi xác thực |

### 4.7 Quy tắc về bảo mật (BR-SEC)

| Mã | Quy tắc |
| --- | --- |
| BR-SEC-01 | Mật khẩu lưu dưới dạng bcrypt hash, cost factor ≥ **12** |
| BR-SEC-02 | Mật khẩu mới phải có ≥ 8 ký tự, có ít nhất 1 chữ và 1 số |
| BR-SEC-03 | Không hiển thị mật khẩu plain text trong bất kỳ đâu (UI, log, file) |
| BR-SEC-04 | Mọi hành động CRUD trên dữ liệu quan trọng được ghi vào `audit_log` |
| BR-SEC-05 | Đăng nhập sai 5 lần → khoá tài khoản 15 phút (BR-TIME-08) |
| BR-SEC-06 | Phiên 30 phút không thao tác → tự đăng xuất, yêu cầu đăng nhập lại |
| BR-SEC-07 | Đổi mật khẩu yêu cầu nhập lại mật khẩu cũ |
| BR-SEC-08 | Sales chỉ xem được dữ liệu KPI của chính mình; không được xem KPI người khác |
| BR-SEC-09 | Audit log không thể bị xoá hoặc sửa qua UI |

### 4.8 Quy tắc về hiển thị (BR-UI)

| Mã | Quy tắc |
| --- | --- |
| BR-UI-01 | Số tiền hiển thị dạng có dấu phân cách hàng nghìn: `1,500,000 VND` |
| BR-UI-02 | Ngày hiển thị `dd/MM/yyyy`; ngày-giờ hiển thị `dd/MM/yyyy HH:mm` |
| BR-UI-03 | Trạng thái hiển thị bằng badge có màu: xanh = OK, vàng = cảnh báo, đỏ = nguy hiểm |
| BR-UI-04 | Nút action nguy hiểm (Xoá, Hủy HĐ) phải có dialog xác nhận |
| BR-UI-05 | Khi thao tác thành công, hiển thị toast thông báo trong 3 giây |
| BR-UI-06 | Tất cả thông điệp hệ thống bằng **tiếng Việt** có dấu |

---

## 5. YÊU CẦU NGHIỆP VỤ THEO MODULE

> Mỗi module được mô tả theo cấu trúc thống nhất:
>
> 1. **Mô tả & Mục tiêu**
> 2. **Actors**
> 3. **Business Rules đặc thù**
> 4. **Use Cases chi tiết** (precondition, main flow, alternative flows, postcondition)
> 5. **Validation rules cho dữ liệu**
> 6. **Lưu ý**

### 5.1 Module Quản lý Xe (XE)

#### 5.1.1 Mô tả & Mục tiêu

Quản lý toàn bộ thông tin xe có trong đại lý — từ nhập kho, hiển thị, tìm kiếm đến cập nhật trạng thái khi bán. Đây là module **trung tâm** vì xe là đối tượng kinh doanh chính.

#### 5.1.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | Chỉ xem (R) |
| Kỹ thuật BH | Chỉ xem (R) |

#### 5.1.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-XE-01 | Mã xe (`ma_xe`) không thể thay đổi sau khi tạo |
| BR-XE-02 | Không cho phép xoá xe đang xuất hiện trong HĐ trạng thái khác `huy` (BR-REF-01) |
| BR-XE-03 | Trạng thái xe có 3 giá trị cho phép: `con_hang`, `da_ban`, `sap_ve` |
| BR-XE-04 | Tự động chuyển `con_hang → da_ban` khi `so_luong_ton = 0` và xe có ít nhất 1 HĐ `da_giao_xe` |
| BR-XE-05 | Khi nhập kho thêm cho xe `da_ban` → tự chuyển về `con_hang` |
| BR-XE-06 | Tìm kiếm nâng cao hỗ trợ tổ hợp tiêu chí: hãng, dòng, năm, khoảng giá, màu, trạng thái |
| BR-XE-07 | Tìm kiếm theo từ khoá áp dụng cho cả `ma_xe`, `hang`, `dong_xe` (case-insensitive, có hỗ trợ tiếng Việt) |
| BR-XE-08 | Cảnh báo tồn kho thấp (BR-TIME-04, BR-KHO-02) |
| BR-XE-09 | `nam_san_xuat` ∈ [1990, năm hiện tại + 1] (BR-DATA-03) |

#### 5.1.4 Use Cases

##### UC-XE-01: Thêm mới xe

- **Actor chính**: Admin
- **Precondition**: Đã đăng nhập với quyền Admin
- **Main flow**:
  1. Admin mở màn hình "Quản lý Xe" → bấm "Thêm xe"
  2. Hệ thống hiển thị form trống
  3. Admin nhập: `ma_xe`, hãng, dòng xe, năm SX, màu, giá bán, tồn kho, mức tối thiểu
  4. Admin bấm "Lưu"
  5. Hệ thống validate (BR-DATA-01..03, BR-ID-01)
  6. Hệ thống lưu xe với trạng thái `con_hang`
  7. Hệ thống ghi audit log: `CREATE_XE`
  8. Hệ thống hiển thị toast "Đã thêm xe thành công"
- **Alternative flows**:
  - **A1**: `ma_xe` đã tồn tại → hiển thị lỗi inline, không lưu
  - **A2**: `nam_san_xuat` ngoài khoảng → hiển thị lỗi
  - **A3**: Người dùng bấm "Hủy" → đóng form, không lưu
- **Postcondition**: Xe mới có trong CSDL, hiển thị ở danh sách

##### UC-XE-02: Sửa thông tin xe

- **Actor chính**: Admin
- **Precondition**: Có xe tồn tại
- **Main flow**:
  1. Admin chọn xe → bấm "Sửa"
  2. Hệ thống hiển thị form điền sẵn dữ liệu, trường `ma_xe` ở chế độ disabled
  3. Admin chỉnh sửa các trường khác → "Lưu"
  4. Hệ thống validate & lưu
  5. Ghi audit log `UPDATE_XE` với diff nội dung
- **Alternative flows**:
  - **A1**: Validate sai → hiển thị lỗi, không lưu

##### UC-XE-03: Xoá xe

- **Actor chính**: Admin
- **Main flow**:
  1. Admin chọn xe → bấm "Xoá"
  2. Hệ thống hiển thị dialog xác nhận
  3. Admin xác nhận
  4. Hệ thống kiểm tra BR-XE-02
  5. Nếu OK → xoá khỏi CSDL, ghi audit log `DELETE_XE`
- **Alternative flows**:
  - **A1**: Xe đang có HĐ → hiển thị lỗi: "Không thể xoá xe đã phát sinh hợp đồng"
  - **A2**: Người dùng huỷ xác nhận → đóng dialog

##### UC-XE-04: Tìm kiếm nâng cao

- **Actor chính**: Admin, Sales, Kỹ thuật
- **Main flow**:
  1. Người dùng mở màn hình → mặc định hiển thị toàn bộ xe (phân trang)
  2. Người dùng nhập từ khoá vào search bar và/hoặc chọn các filter (hãng, dòng, năm, giá, màu, trạng thái)
  3. Hệ thống lọc và hiển thị kết quả ≤ 2 giây (yêu cầu phi chức năng)
  4. Người dùng có thể bấm "Reset" để xoá filter

##### UC-XE-05: Xem chi tiết xe

- **Main flow**: Bấm vào xe → mở tab Chi tiết với:
  - Tab "Thông tin": full thông tin xe
  - Tab "Lịch sử nhập kho": từ bảng `nhap_kho`
  - Tab "Hợp đồng đã bán": list HĐ liên quan
  - Tab "Khuyến mãi đang áp dụng": KM hiện hành cho xe này

#### 5.1.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `ma_xe` | Bắt buộc; 3-30 ký tự; chữ/số/dấu gạch; UNIQUE |
| `hang` | Bắt buộc; 1-50 ký tự |
| `dong_xe` | Bắt buộc; 1-100 ký tự |
| `nam_san_xuat` | Bắt buộc; integer; ∈ [1990, năm hiện tại + 1] |
| `mau_sac` | Tuỳ chọn; 1-30 ký tự |
| `gia_ban` | Bắt buộc; integer ≥ 0 |
| `so_luong_ton` | Bắt buộc; integer ≥ 0; mặc định 0 |
| `muc_toi_thieu` | Tuỳ chọn; integer ≥ 0; mặc định 2 |
| `trang_thai` | Bắt buộc; ∈ {`con_hang`, `da_ban`, `sap_ve`} |

#### 5.1.6 Lưu ý

- Khi xoá: ưu tiên cảnh báo Admin và đề xuất đánh dấu `inactive` (mở rộng tương lai) thay vì xoá thật.
- Tìm kiếm tiếng Việt: dùng `LIKE` với `COLLATE NOCASE`, hoặc chuẩn hoá Unicode về NFC.

---

### 5.2 Module Quản lý Khách hàng (KH)

#### 5.2.1 Mô tả & Mục tiêu

Lưu trữ thông tin khách hàng đã/đang giao dịch với đại lý, phân loại tự động và theo dõi lịch sử mua hàng.

#### 5.2.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | CRU (không xoá) |
| Kỹ thuật BH | R (xem khi xử lý BH) |

#### 5.2.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-KH-01 | Trường bắt buộc khi tạo: `ho_ten`, `so_dien_thoai`, `email` |
| BR-KH-02 | `so_dien_thoai` định danh duy nhất KH (BR-ID-02) |
| BR-KH-03 | Phân loại KH theo BR-CALC-03, cập nhật tự động khi HĐ chuyển `da_giao_xe` |
| BR-KH-04 | Lịch sử giao dịch hiển thị mọi HĐ, kể cả `huy`, sắp xếp theo ngày giảm dần |
| BR-KH-05 | Không cho phép xoá KH đã có HĐ → đánh dấu `inactive` (BR-REF-03) |
| BR-KH-06 | Email phải hợp lệ (BR-DATA-04); SĐT theo định dạng VN (BR-DATA-05) |
| BR-KH-07 | Lead khi tạo HĐ đầu tiên tự động chuyển thành KH với phân loại `Thuong` |

#### 5.2.4 Use Cases

##### UC-KH-01: Thêm mới khách hàng

- **Actor**: Admin, Sales
- **Main flow**:
  1. Mở "Khách hàng" → "Thêm KH"
  2. Nhập: họ tên, SĐT, email, địa chỉ, ngày sinh
  3. Lưu → hệ thống validate (BR-KH-01, 06; trùng SĐT)
  4. Tạo bản ghi với `phan_loai = Thuong`, `tong_gia_tri_mua = 0`, `so_xe_da_mua = 0`
  5. Audit log `CREATE_KH`
- **Alternative**:
  - **A1**: SĐT đã tồn tại → cảnh báo "KH đã có trong hệ thống. Mở chi tiết?"
  - **A2**: Email sai định dạng → lỗi inline

##### UC-KH-02: Cập nhật thông tin KH

- **Main flow**: Tương tự UC-KH-01 nhưng cho phép sửa mọi trường trừ `id`. Nếu đổi `so_dien_thoai`, kiểm tra lại tính duy nhất.

##### UC-KH-03: Xem lịch sử giao dịch

- **Main flow**:
  1. Mở chi tiết KH → tab "Lịch sử giao dịch"
  2. Hệ thống hiển thị bảng: mã HĐ, ngày tạo, xe, tổng tiền, trạng thái, NV phụ trách
  3. Cho phép bấm vào HĐ để mở chi tiết

##### UC-KH-04: Phân loại tự động

- **Trigger**: Mỗi khi HĐ chuyển sang `da_giao_xe`
- **Main flow** (hệ thống tự thực hiện):
  1. Cập nhật `khach_hang.tong_gia_tri_mua += hop_dong.tong_tien`
  2. Cập nhật `khach_hang.so_xe_da_mua += 1`
  3. Áp dụng BR-CALC-03 để cập nhật `phan_loai`
  4. Nếu `phan_loai` thay đổi (lên hạng) → ghi audit log `UPGRADE_KH`

#### 5.2.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `ho_ten` | Bắt buộc; 2-100 ký tự; cho phép tiếng Việt có dấu |
| `so_dien_thoai` | Bắt buộc; regex `^0[3-9][0-9]{8}$`; UNIQUE |
| `email` | Bắt buộc; định dạng email |
| `dia_chi` | Tuỳ chọn; ≤ 200 ký tự |
| `ngay_sinh` | Tuỳ chọn; ngày trong quá khứ; tuổi ≥ 18 |
| `phan_loai` | Hệ thống tự cập nhật; ∈ {`Thuong`, `Than_thiet`, `VIP`} |

#### 5.2.6 Lưu ý

- Bảo mật: SĐT và email là PII (Personally Identifiable Information). Cần che bớt khi hiển thị danh sách (ví dụ `0987***456`) — *(mở rộng tương lai)*.
- Khi xoá KH có HĐ: cấm hoàn toàn, đề xuất `inactive`.

---

### 5.3 Module Quản lý Nhân viên (NV)

#### 5.3.1 Mô tả & Mục tiêu

Quản lý tài khoản đăng nhập và thông tin cá nhân của nhân viên, kèm theo việc theo dõi KPI bán hàng cá nhân.

#### 5.3.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD nhân viên khác; xem mọi KPI |
| Sales | Xem & đổi thông tin/mật khẩu cá nhân; xem KPI cá nhân |
| Kỹ thuật BH | Tương tự Sales |

#### 5.3.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-NV-01 | Chỉ Admin được thêm/sửa/khoá nhân viên khác |
| BR-NV-02 | Sales/Kỹ thuật chỉ xem & cập nhật thông tin cá nhân của chính mình |
| BR-NV-03 | KPI tính theo BR-CALC-05, mặc định khoảng thời gian là tháng hiện tại |
| BR-NV-04 | Không xoá NV đã có HĐ → chuyển `trang_thai = inactive` (BR-REF-02) |
| BR-NV-05 | NV `inactive` không thể đăng nhập, không xuất hiện trong dropdown chọn NV ở HĐ mới |
| BR-NV-06 | Mỗi NV chỉ thuộc 1 vai trò (`admin`, `sales`, `ky_thuat`) tại một thời điểm |
| BR-NV-07 | Tài khoản admin đầu tiên (`username = admin`) không thể bị xoá hoặc khoá |
| BR-NV-08 | Mật khẩu mới sinh ngẫu nhiên 12 ký tự khi Admin thêm NV; gửi qua email/SMS *(mở rộng)* hoặc hiển thị 1 lần để Admin chuyển cho NV |

#### 5.3.4 Use Cases

##### UC-NV-01: Thêm nhân viên (Admin)

- **Main flow**:
  1. Admin mở "Quản lý Nhân viên" → "Thêm"
  2. Nhập username, họ tên, email, SĐT, vai trò
  3. Hệ thống sinh mật khẩu ngẫu nhiên, hash bằng bcrypt (BR-SEC-01)
  4. Lưu, audit log `CREATE_NV`
  5. Hiển thị mật khẩu plain text **1 lần duy nhất** trong dialog kết quả

##### UC-NV-02: Khoá / Mở khoá NV

- **Main flow**: Toggle `trang_thai` giữa `active`/`inactive`. Audit log.
- **Constraint**: Không cho phép khoá tài khoản `admin` gốc (BR-NV-07).

##### UC-NV-03: Xem KPI cá nhân (Sales)

- **Main flow**:
  1. Sales mở "Hồ sơ cá nhân" → tab KPI
  2. Mặc định hiển thị KPI tháng hiện tại
  3. Có thể đổi khoảng thời gian (tuần, tháng, quý, năm, tuỳ chỉnh)
  4. Hệ thống tính toán theo BR-CALC-05

##### UC-NV-04: Xem KPI toàn đội (Admin)

- **Main flow**: Admin mở "Báo cáo Hiệu suất NV" → bảng KPI toàn bộ NV.

##### UC-NV-05: Đổi mật khẩu cá nhân

- **Main flow**:
  1. NV mở "Đổi mật khẩu"
  2. Nhập mật khẩu cũ, mật khẩu mới (2 lần)
  3. Hệ thống xác thực mật khẩu cũ (BR-SEC-07)
  4. Validate mật khẩu mới (BR-SEC-02)
  5. Lưu hash mới, audit log `CHANGE_PASSWORD`
  6. Hết phiên hiện tại, yêu cầu đăng nhập lại

#### 5.3.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `username` | Bắt buộc; 3-30 ký tự; regex `^[a-zA-Z0-9_]+$`; UNIQUE |
| `mat_khau` (input) | Bắt buộc khi tạo; ≥ 8 ký tự; có ít nhất 1 chữ + 1 số |
| `ho_ten` | Bắt buộc; 2-100 ký tự |
| `email` | Bắt buộc; định dạng email |
| `vai_tro_id` | Bắt buộc; ∈ danh mục `vai_tro` |
| `trang_thai` | ∈ {`active`, `inactive`} |

---

### 5.4 Module Quản lý Hợp đồng (HD)

#### 5.4.1 Mô tả & Mục tiêu

Module **trung tâm nghiệp vụ** — nơi mọi giao dịch bán xe được ghi nhận. Có ảnh hưởng đến: kho, KH, KPI, KM, BH, trả góp.

#### 5.4.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ; duy nhất có quyền **hủy** HĐ |
| Sales | C, R (HĐ của mình), U (HĐ của mình, trạng thái `moi_tao`) |
| Kỹ thuật BH | R |

#### 5.4.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-HD-01 | Trạng thái theo flow trong BR-FLOW (Hợp đồng) |
| BR-HD-02 | Tổng tiền tính theo BR-CALC-01 |
| BR-HD-03 | Khi `moi_tao → da_thanh_toan`: giảm tồn kho xe & PK; ghi `ngay_thanh_toan = today()` |
| BR-HD-04 | Khi `da_thanh_toan → da_giao_xe`: ghi `ngay_giao_xe`; cập nhật KH (BR-KH-03); tính KPI (BR-NV-03); tự sinh hồ sơ BH (BR-BH-01) |
| BR-HD-05 | Khi `huy` (từ `moi_tao` hoặc `da_thanh_toan`): hoàn tồn kho; xoá hồ sơ BH nếu có; xoá hồ sơ trả góp nếu có |
| BR-HD-06 | `da_giao_xe` là trạng thái cuối — KHÔNG hủy được |
| BR-HD-07 | Mỗi HĐ chỉ áp dụng tối đa **1** chương trình KM tại thời điểm tạo |
| BR-HD-08 | Khi áp dụng KM: kiểm tra điều kiện (BR-KM-01, BR-KM-04) — nếu không thoả → reject |
| BR-HD-09 | Sales chỉ sửa được HĐ ở trạng thái `moi_tao`; HĐ đã thanh toán chỉ Admin được sửa |
| BR-HD-10 | Hợp đồng PDF phải có đủ: thông tin đại lý, KH, xe, PK, bảng giá, KM (nếu có), điều khoản BH, chữ ký 2 bên |
| BR-HD-11 | Mỗi xe trong HĐ phải có `so_luong_ton ≥ 1` tại thời điểm chuyển `da_thanh_toan` |
| BR-HD-12 | Mỗi PK trong HĐ phải có `ton_kho ≥ so_luong_yeu_cau` tại thời điểm chuyển `da_thanh_toan` |

#### 5.4.4 Use Cases

##### UC-HD-01: Tạo hợp đồng mới (Wizard 4 bước)

- **Actor**: Sales, Admin
- **Precondition**: Có ít nhất 1 KH và 1 xe `con_hang`
- **Main flow**:
  1. Mở "Hợp đồng" → "Tạo mới"
  2. **Bước 1 — Chọn khách hàng**:
     - Tìm KH hoặc tạo mới (gọi UC-KH-01)
  3. **Bước 2 — Chọn xe & phụ kiện**:
     - Chọn 1 xe; hệ thống snapshot `gia_xe` hiện tại
     - Có thể thêm nhiều phụ kiện hoặc combo
  4. **Bước 3 — Áp dụng khuyến mãi**:
     - Hệ thống tự đề xuất KM phù hợp (theo BR-KM-01, BR-KM-04)
     - User chọn 1 KM hoặc bỏ qua
     - Hệ thống tính `tien_giam_KM` (BR-CALC-02)
  5. **Bước 4 — Xác nhận**:
     - Hiển thị tổng tiền (BR-CALC-01), thông tin tóm tắt
     - User bấm "Lưu hợp đồng"
  6. Hệ thống sinh `ma_hop_dong` (định dạng `HD{YYYY}-{NNNN}`)
  7. Lưu HĐ với `trang_thai = moi_tao`
  8. Audit log `CREATE_HD`
- **Alternative flows**:
  - **A1**: Người dùng quay lại bước trước để sửa
  - **A2**: Người dùng huỷ wizard → không lưu
  - **A3**: Xe được chọn đã được HĐ khác giữ chỗ → cảnh báo

##### UC-HD-02: Chuyển trạng thái HĐ

- **Main flow**:
  1. Mở chi tiết HĐ → bấm "Xác nhận thanh toán" / "Xác nhận giao xe" / "Hủy"
  2. Hệ thống kiểm tra điều kiện theo BR-HD-01..06
  3. Cập nhật trạng thái + các tác vụ phụ (BR-HD-03..05)
  4. Audit log `UPDATE_HD_STATUS`
- **Alternative**: Trạng thái không hợp lệ → reject với thông báo

##### UC-HD-03: In hợp đồng PDF

- **Main flow**:
  1. Mở chi tiết HĐ → bấm "In PDF"
  2. Hệ thống render template PDF với dữ liệu HĐ
  3. Hiển thị preview
  4. User bấm "Tải xuống" / "In trực tiếp"
  5. Audit log `EXPORT_HD_PDF`

##### UC-HD-04: Hủy hợp đồng

- **Actor**: Admin (BR-HD-05, ma trận quyền)
- **Main flow**:
  1. Admin mở HĐ → "Hủy hợp đồng"
  2. Dialog xác nhận, yêu cầu nhập lý do hủy
  3. Hệ thống chuyển trạng thái → `huy`
  4. Hoàn tồn kho xe & PK
  5. Xoá hồ sơ BH/trả góp liên quan
  6. Audit log `CANCEL_HD` với lý do

#### 5.4.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `khach_hang_id` | Bắt buộc; tồn tại trong `khach_hang` |
| `xe_id` | Bắt buộc; tồn tại; `so_luong_ton ≥ 1` |
| `nhan_vien_id` | Bắt buộc; NV `active` |
| `gia_xe` | Snapshot tại thời điểm tạo, ≥ 0 |
| `tong_tien` | Hệ thống tính, ≥ 0 |
| `trang_thai` | Hệ thống quản lý theo flow |

#### 5.4.6 Lưu ý

- Snapshot `gia_xe`, `gia_ban` PK trong `hop_dong_phu_kien` để tránh lỗi khi đổi giá sau này.
- Sinh `ma_hop_dong`: format `HD{YYYY}-{NNNN}` với `NNNN` là số thứ tự trong năm, reset đầu năm.

---

### 5.5 Module Quản lý Kho (KHO)

#### 5.5.1 Mô tả & Mục tiêu

Theo dõi tồn kho xe & phụ kiện, ghi nhận lịch sử nhập từ NCC, cảnh báo khi tồn kho thấp.

#### 5.5.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | R |
| Kỹ thuật BH | - |

#### 5.5.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-KHO-01 | Tồn kho xe lưu trong `xe.so_luong_ton`; tồn kho PK lưu trong `phu_kien.ton_kho` |
| BR-KHO-02 | Cảnh báo tồn kho thấp khi `so_luong_ton ≤ muc_toi_thieu` (mặc định 2) |
| BR-KHO-03 | Tồn kho được giảm tự động khi HĐ chuyển `da_thanh_toan` (BR-HD-03) |
| BR-KHO-04 | Tồn kho được tăng tự động khi HĐ bị `huy` (BR-HD-05) |
| BR-KHO-05 | Mỗi lần nhập kho phải ghi: ngày nhập, NCC, xe/PK, số lượng, giá nhập, người nhập |
| BR-KHO-06 | Tổng giá trị tồn kho = `SUM(xe.so_luong_ton × xe.gia_ban) + SUM(phu_kien.ton_kho × phu_kien.gia_ban)` |
| BR-KHO-07 | Không cho phép `so_luong_ton < 0` ở mọi tình huống |

#### 5.5.4 Use Cases

##### UC-KHO-01: Nhập kho xe

- **Actor**: Admin
- **Main flow**:
  1. Mở "Kho" → "Nhập kho"
  2. Chọn loại nhập: xe / phụ kiện
  3. Chọn NCC (từ danh mục `nha_cung_cap`)
  4. Chọn xe (hoặc PK), nhập số lượng, giá nhập, ngày nhập
  5. Bấm "Lưu"
  6. Hệ thống:
     - Tăng `xe.so_luong_ton += so_luong`
     - Tạo bản ghi `nhap_kho`
     - Nếu xe đang `da_ban` và `so_luong_ton > 0` → chuyển `con_hang` (BR-XE-05)
  7. Audit log `IMPORT_STOCK`

##### UC-KHO-02: Xem tổng quan kho

- **Main flow**: Hiển thị bảng:
  - Cột: xe, hãng, dòng, tồn kho, mức tối thiểu, trạng thái cảnh báo
  - Highlight đỏ khi `so_luong_ton ≤ muc_toi_thieu`
  - Footer: tổng giá trị tồn kho

##### UC-KHO-03: Xem lịch sử nhập kho

- **Main flow**: Lọc theo NCC, ngày, loại; bảng `nhap_kho` sắp xếp giảm dần theo `ngay_nhap`.

#### 5.5.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `so_luong` (nhập) | ≥ 1 |
| `gia_nhap` | ≥ 0 |
| `ngay_nhap` | ≤ hôm nay |
| `nha_cung_cap_id` | Tồn tại; `trang_thai = active` |

#### 5.5.6 Lưu ý

- Có thể mở rộng: xuất kho khi điều chuyển nội bộ (giai đoạn sau).
- Backup snapshot tồn kho cuối ngày để phục vụ kiểm kê.

---

### 5.6 Module Quản lý Bảo hành (BH)

#### 5.6.1 Mô tả & Mục tiêu

Quản lý hồ sơ bảo hành theo từng xe đã bán, tiếp nhận yêu cầu bảo hành, phân loại miễn phí/tính phí, thống kê chi phí.

#### 5.6.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | C, R (tạo BH khi giao xe) |
| Kỹ thuật BH | C, R, U (xử lý yêu cầu BH) |

#### 5.6.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-BH-01 | Khi HĐ chuyển sang `da_giao_xe`, hệ thống tự sinh hồ sơ BH với `thoi_han_bh` mặc định 24 tháng (có thể cấu hình ở SystemSettings) |
| BR-BH-02 | `ngay_bat_dau` = ngày giao xe; `ngay_ket_thuc = ngay_bat_dau + thoi_han_bh` |
| BR-BH-03 | Cảnh báo BH sắp hết hạn trước **30 ngày** (BR-TIME-01); hiển thị ở Dashboard |
| BR-BH-04 | Phân loại yêu cầu BH: `mien_phi` nếu (BH còn hiệu lực + nội dung trong phạm vi) hoặc `tinh_phi` |
| BR-BH-05 | Yêu cầu BH có trạng thái: `tiep_nhan → dang_xu_ly → hoan_thanh` |
| BR-BH-06 | Khi `tinh_phi`, phải nhập `chi_phi` ≥ 0; khi `mien_phi`, `chi_phi = 0` |
| BR-BH-07 | Phiếu BH phải có: thông tin xe, KH, thời hạn, nội dung sửa, kỹ thuật phụ trách, tổng chi phí |
| BR-BH-08 | Một xe có thể có nhiều yêu cầu BH trong thời hạn |
| BR-BH-09 | Tổng chi phí BH theo tháng/quý hiển thị ở báo cáo |
| BR-BH-10 | Khi HĐ bị `huy`, hồ sơ BH liên quan cũng bị xoá (BR-HD-05) |

#### 5.6.4 Use Cases

##### UC-BH-01: Tự sinh hồ sơ BH

- **Trigger**: HĐ chuyển `da_giao_xe`
- **Main flow** (hệ thống tự thực hiện):
  1. Đọc `thoi_han_bh_default` từ SystemSettings (mặc định 24 tháng)
  2. Tạo bản ghi `bao_hanh` với:
     - `hop_dong_id`, `xe_id`, `khach_hang_id`
     - `ngay_bat_dau = ngay_giao_xe`
     - `ngay_ket_thuc = ngay_bat_dau + thoi_han_bh`
     - `pham_vi = "Bảo hành toàn diện theo điều khoản chuẩn"`
     - `trang_thai = con_hieu_luc`
  3. Audit log `CREATE_BH`

##### UC-BH-02: Tiếp nhận yêu cầu bảo hành

- **Actor**: Sales / Kỹ thuật BH
- **Main flow**:
  1. KH đến, kỹ thuật mở "Bảo hành" → tìm theo SĐT/biển số/mã HĐ
  2. Hệ thống hiển thị hồ sơ BH; báo nếu BH hết hạn
  3. Bấm "Tạo yêu cầu BH"
  4. Nhập: ngày đến, nội dung sửa, kỹ thuật phụ trách
  5. Hệ thống đề xuất phân loại (miễn phí/tính phí) dựa BR-BH-04
  6. Nếu `tinh_phi`, nhập `chi_phi`
  7. Lưu, audit log `CREATE_BH_REQUEST`
- **Alternative**:
  - **A1**: BH đã hết hạn → cho phép tiếp nhận nhưng bắt buộc `tinh_phi`
  - **A2**: Không tìm thấy hồ sơ → đề xuất tạo BH ngoài hệ thống (chỉ Admin)

##### UC-BH-03: Cập nhật trạng thái yêu cầu BH

- **Main flow**: Toggle `tiep_nhan → dang_xu_ly → hoan_thanh`. Mỗi bước ghi audit log.

##### UC-BH-04: In phiếu BH / biên lai

- **Main flow**: Tương tự UC-HD-03 nhưng template cho phiếu BH.

##### UC-BH-05: Cảnh báo BH sắp hết hạn

- **Trigger**: Mở Dashboard
- **Main flow**:
  1. Hệ thống tính: `bao_hanh` có `ngay_ket_thuc` trong khoảng [hôm nay, hôm nay + 30 ngày] và `trang_thai = con_hieu_luc`
  2. Hiển thị danh sách + đề xuất gọi điện báo KH

#### 5.6.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `thoi_han_bh` (tháng) | Bắt buộc; ≥ 1 |
| `ngay_bat_dau`, `ngay_ket_thuc` | BR-DATA-07 |
| `chi_phi` | ≥ 0; bắt buộc khi phân loại `tinh_phi` |
| `kỹ_thuat_phu_trach` | NV vai trò `ky_thuat` |

---

### 5.7 Module Quản lý Khuyến mãi (KM)

#### 5.7.1 Mô tả & Mục tiêu

Tạo và vận hành chương trình khuyến mãi, áp dụng tự động vào hợp đồng đủ điều kiện, theo dõi hiệu quả.

#### 5.7.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD chương trình KM |
| Sales | Áp dụng KM khi tạo HĐ |
| Kỹ thuật BH | - |

#### 5.7.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-KM-01 | KM chỉ áp dụng được khi `tu_ngay ≤ today() ≤ den_ngay` và `trang_thai = dang_chay` |
| BR-KM-02 | Một HĐ chỉ áp dụng tối đa **1** KM (BR-HD-07) |
| BR-KM-03 | Loại KM: `giam_tien_mat`, `tang_phu_kien`, `giam_lai_suat`, `combo` |
| BR-KM-04 | Phạm vi áp dụng: toàn bộ / theo hãng / theo dòng / theo xe cụ thể / xe tồn lâu (> 90 ngày) |
| BR-KM-05 | Khi tạo HĐ, hệ thống tự đề xuất KM phù hợp; user có thể chọn 1 hoặc bỏ qua |
| BR-KM-06 | Nếu nhiều KM phù hợp, ưu tiên KM có giá trị giảm cao nhất |
| BR-KM-07 | KM `tam_dung` không hiển thị trong dropdown chọn KM, nhưng giữ nguyên cho HĐ đã áp dụng |
| BR-KM-08 | Khi KM hết hạn (`den_ngay < today()`) → tự chuyển `ket_thuc` |
| BR-KM-09 | Hiệu quả KM = số HĐ áp dụng × tổng tiền các HĐ này |
| BR-KM-10 | Không xoá KM đã áp dụng vào HĐ (BR-REF-06) |

#### 5.7.4 Use Cases

##### UC-KM-01: Tạo chương trình KM

- **Actor**: Admin
- **Main flow**:
  1. Mở "Khuyến mãi" → "Tạo mới"
  2. Nhập: tên, mô tả, loại, giá trị, kiểu (tiền/%), thời gian, phạm vi
  3. Chọn phạm vi: toàn bộ / chọn hãng / chọn dòng / chọn xe cụ thể
  4. Lưu với `trang_thai = nhap` hoặc `dang_chay` (nếu khoảng thời gian đã bắt đầu)
  5. Audit log `CREATE_KM`

##### UC-KM-02: Sửa chương trình KM

- **Main flow**: Tương tự UC-KM-01.
- **Constraint**: Nếu KM đã được áp dụng cho HĐ, không cho sửa giá trị/kiểu — chỉ sửa được mô tả, thời gian (chỉ kéo dài, không rút ngắn).

##### UC-KM-03: Tạm dừng / Khôi phục KM

- **Main flow**: Toggle `dang_chay ⇄ tam_dung`. Audit log.

##### UC-KM-04: Áp dụng KM khi tạo HĐ

- Xem UC-HD-01, bước 3.

##### UC-KM-05: Báo cáo hiệu quả KM

- **Main flow**: Mở "Khuyến mãi" → "Báo cáo hiệu quả"
- Hiển thị bảng: KM, số HĐ áp dụng, tổng doanh thu, tổng tiền giảm
- Biểu đồ cột so sánh các KM

#### 5.7.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `ten_km` | Bắt buộc; 1-100 ký tự |
| `loai_km` | Bắt buộc; ∈ {`giam_tien_mat`, `tang_phu_kien`, `giam_lai_suat`, `combo`} |
| `gia_tri` | Bắt buộc; ≥ 0 |
| `kieu_gia_tri` | ∈ {`tien`, `phan_tram`}; nếu `phan_tram` thì `gia_tri ≤ 100` |
| `tu_ngay`, `den_ngay` | Bắt buộc; BR-DATA-07 |

---

### 5.8 Module Quản lý Phụ kiện (PK)

#### 5.8.1 Mô tả & Mục tiêu

Quản lý danh mục phụ kiện đi kèm xe, gồm phân loại, tồn kho, combo, và liên kết với HĐ.

#### 5.8.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | R; thêm PK vào HĐ |
| Kỹ thuật BH | R |

#### 5.8.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-PK-01 | PK được phân loại: `noi_that`, `ngoai_that`, `dien_tu`, `bao_ve`, `trang_tri` |
| BR-PK-02 | Combo PK: tập hợp nhiều PK với hệ số giảm (BR-CALC-07), mặc định 0.9 |
| BR-PK-03 | Tồn kho PK giảm tự động khi HĐ chuyển `da_thanh_toan` (BR-HD-03) |
| BR-PK-04 | Tồn kho PK được hoàn lại khi HĐ bị `huy` (BR-HD-05) |
| BR-PK-05 | Cảnh báo hết PK khi `ton_kho ≤ 0` |
| BR-PK-06 | Không xoá PK xuất hiện trong HĐ chưa hủy (BR-REF-04) |
| BR-PK-07 | Khi thêm PK vào HĐ: snapshot `gia_ban` tại thời điểm thêm; cho phép user override giá (cần Admin xác nhận nếu < giá gốc) |
| BR-PK-08 | Combo PK chỉ áp dụng nếu tồn kho của TẤT CẢ PK trong combo ≥ số lượng yêu cầu |

#### 5.8.4 Use Cases

##### UC-PK-01: CRUD phụ kiện

- Tương tự UC-XE-01..03 với các trường: tên, mô tả, phân loại, giá bán, tồn kho.

##### UC-PK-02: Tạo combo phụ kiện

- **Main flow**:
  1. Mở "Phụ kiện" → tab "Combo" → "Tạo combo"
  2. Nhập tên combo, mô tả
  3. Thêm các PK + số lượng
  4. Nhập hệ số giảm (mặc định 0.9)
  5. Hệ thống tự tính giá combo (BR-CALC-07), hiển thị preview
  6. Lưu

##### UC-PK-03: Thêm PK vào HĐ

- **Main flow**: Trong wizard tạo HĐ (bước 2):
  1. Bấm "Thêm phụ kiện"
  2. Tìm/lọc PK theo phân loại
  3. Chọn 1 hoặc nhiều PK + số lượng
  4. Hoặc chọn 1 combo (sẽ tự thêm các PK trong combo với giá ưu đãi)
  5. Hệ thống cập nhật `tong_gia_phu_kien` (BR-CALC-01)

#### 5.8.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `ten_pk` | Bắt buộc; 1-100 ký tự |
| `phan_loai` | ∈ 5 giá trị BR-PK-01 |
| `gia_ban` | ≥ 0 |
| `ton_kho` | ≥ 0 |
| `he_so_giam` (combo) | (0, 1] |

---

### 5.9 Module Dịch vụ Hậu mãi (HM)

#### 5.9.1 Mô tả & Mục tiêu

Cung cấp các dịch vụ sau bán hàng: bảo dưỡng định kỳ, cứu hộ, chăm sóc khách hàng.

#### 5.9.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | C, R (đặt lịch hộ KH) |
| Kỹ thuật BH | CRU (ghi nhận BD/cứu hộ) |

#### 5.9.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-HM-01 | Lịch BD định kỳ: mỗi 6 tháng hoặc 5.000 km, lấy mốc đến trước |
| BR-HM-02 | Hệ thống nhắc nhở trước **7 ngày** đến lịch BD (BR-TIME-02) |
| BR-HM-03 | Sinh nhật KH: hiển thị thông báo trong **7 ngày** trước/sau (BR-TIME-05) |
| BR-HM-04 | Yêu cầu cứu hộ ghi nhận: KH, xe, vị trí, mô tả, thời gian, chi phí, trạng thái |
| BR-HM-05 | Trạng thái cứu hộ: `tiep_nhan → dang_xu_ly → hoan_thanh` |
| BR-HM-06 | BD ghi nhận: ngày, KM xe, nội dung, chi phí, kỹ thuật phụ trách |
| BR-HM-07 | Chương trình chăm sóc: gợi ý gửi thiệp/ưu đãi cho KH có sinh nhật, KH VIP |

#### 5.9.4 Use Cases

##### UC-HM-01: Đặt lịch BD

- **Main flow**:
  1. Mở "Hậu mãi" → "Lịch BD" → "Đặt lịch"
  2. Chọn KH, xe (chỉ hiển thị xe của KH này)
  3. Nhập ngày dự kiến BD, ghi chú
  4. Lưu, hệ thống thêm vào calendar

##### UC-HM-02: Ghi nhận BD đã thực hiện

- **Actor**: Kỹ thuật BH
- **Main flow**:
  1. Mở lịch BD → chọn lịch
  2. Bấm "Ghi nhận đã thực hiện"
  3. Nhập KM xe hiện tại, nội dung BD, chi phí
  4. Lưu, audit log `RECORD_BD`

##### UC-HM-03: Tạo yêu cầu cứu hộ

- **Main flow**:
  1. KH gọi đến, NV mở "Cứu hộ" → "Tạo mới"
  2. Tìm KH/xe (hoặc tạo lead nếu KH chưa có trong hệ thống)
  3. Nhập: vị trí, mô tả, thời gian
  4. Hệ thống tạo bản ghi với `trang_thai = tiep_nhan`
  5. Khi xử lý xong, cập nhật chi phí và trạng thái

##### UC-HM-04: Danh sách KH có sinh nhật

- **Main flow**: Mở "Chăm sóc KH" → tab "Sinh nhật"
- Hiển thị danh sách KH có `ngay_sinh` trong [today() - 7d, today() + 7d]
- Mỗi KH có nút "Đề xuất quà tặng" (mở mẫu thiệp/ưu đãi)

#### 5.9.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `ngay_bao_duong` | Ngày BD ≥ ngày tạo |
| `km_xe` (BD) | integer ≥ 0 |
| `chi_phi` | ≥ 0 |

---

### 5.10 Module Quản lý Nhà cung cấp (NCC)

#### 5.10.1 Mô tả & Mục tiêu

Quản lý thông tin các nhà cung cấp xe & phụ kiện, theo dõi lịch sử nhập hàng, đánh giá NCC, tạo đơn đặt hàng.

#### 5.10.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ; tạo đơn đặt hàng |
| Sales | R |
| Kỹ thuật BH | - |

#### 5.10.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-NCC-01 | Mỗi NCC có `ma_ncc` duy nhất (BR-ID-05) |
| BR-NCC-02 | Đánh giá NCC theo 3 tiêu chí, mỗi tiêu chí thang 1-5 sao: chất lượng, thời gian giao, giá cả |
| BR-NCC-03 | Điểm NCC tổng = trung bình 3 tiêu chí (giúp xếp hạng NCC) |
| BR-NCC-04 | Đơn đặt hàng có trạng thái: `nhap → da_gui → da_nhan` (hoặc `huy`) |
| BR-NCC-05 | Khi đơn `da_nhan`: tự sinh bản ghi `nhap_kho` tương ứng |
| BR-NCC-06 | Không xoá NCC có lịch sử nhập kho (BR-REF-05) |

#### 5.10.4 Use Cases

##### UC-NCC-01: CRUD NCC

- Tương tự UC-XE-01..03 với các trường: mã, tên, địa chỉ, SĐT, email, người liên hệ.

##### UC-NCC-02: Đánh giá NCC

- **Actor**: Admin
- **Main flow**:
  1. Mở chi tiết NCC → tab "Đánh giá"
  2. Chấm 1-5 sao cho 3 tiêu chí
  3. Lưu, hệ thống tính điểm tổng

##### UC-NCC-03: Tạo đơn đặt hàng

- **Actor**: Admin
- **Main flow**:
  1. Mở "NCC" → "Đơn đặt hàng" → "Tạo mới"
  2. Chọn NCC
  3. Thêm các xe/PK + số lượng + giá thoả thuận
  4. Lưu với `trang_thai = nhap`
  5. Khi gửi cho NCC → bấm "Gửi" → `da_gui`
  6. Khi nhận hàng → bấm "Nhận hàng" → `da_nhan`, tự sinh `nhap_kho` (BR-NCC-05)

#### 5.10.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `ma_ncc` | Bắt buộc; UNIQUE |
| `ten_ncc` | Bắt buộc; 1-200 ký tự |
| `so_dien_thoai` | BR-DATA-05 |
| `email` | BR-DATA-04 |
| Sao đánh giá | integer ∈ [1, 5] |

---

### 5.11 Module Quản lý Trả góp (TG)

#### 5.11.1 Mô tả & Mục tiêu

Hỗ trợ KH mua xe trả góp thông qua đối tác ngân hàng: tính toán số tiền trả/tháng, theo dõi tiến độ trả, cảnh báo chậm trả.

#### 5.11.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | C, R (tạo hồ sơ khi tư vấn) |

#### 5.11.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-TG-01 | Hồ sơ trả góp phải gắn với 1 HĐ duy nhất; mỗi HĐ tối đa 1 hồ sơ trả góp |
| BR-TG-02 | Số tiền vay (`P`) ≤ `hop_dong.tong_tien` |
| BR-TG-03 | Lãi suất năm ∈ [0, 30] % (BR-DATA-09) |
| BR-TG-04 | Số kỳ trả ∈ [6, 84] tháng |
| BR-TG-05 | Số tiền trả/tháng tính theo BR-CALC-04 (công thức niên kim) |
| BR-TG-06 | Khi tạo hồ sơ → sinh tự động `n` bản ghi `tra_gop_lich_su` với `ngay_den_han` cách nhau 1 tháng |
| BR-TG-07 | Mỗi kỳ có trạng thái: `chua_tra`, `da_tra`, `qua_han` |
| BR-TG-08 | Cảnh báo chậm trả khi `today() - ngay_den_han ≥ 5 ngày` và trạng thái `chua_tra` (BR-TIME-03) |
| BR-TG-09 | Tự chuyển `chua_tra → qua_han` khi vượt 5 ngày chưa thanh toán |
| BR-TG-10 | Khi HĐ liên quan bị `huy` → xoá hồ sơ trả góp (BR-HD-05) |

#### 5.11.4 Use Cases

##### UC-TG-01: Tạo hồ sơ trả góp

- **Actor**: Sales / Admin
- **Precondition**: HĐ có `trang_thai ∈ {moi_tao, da_thanh_toan}`
- **Main flow**:
  1. Mở chi tiết HĐ → "Thiết lập trả góp"
  2. Nhập: ngân hàng, số tiền vay (`P`), lãi suất năm, số kỳ (`n`)
  3. Hệ thống tính `M` theo BR-CALC-04, hiển thị preview
  4. User xác nhận
  5. Hệ thống lưu hồ sơ + sinh `n` bản ghi `tra_gop_lich_su` (`ngay_den_han` cách nhau 1 tháng tính từ `ngay_giao_xe` hoặc `today()`)
  6. Audit log `CREATE_TG`

##### UC-TG-02: Ghi nhận thanh toán kỳ

- **Main flow**:
  1. Mở chi tiết hồ sơ trả góp → bảng các kỳ
  2. Bấm "Ghi nhận đã trả" trên kỳ tương ứng
  3. Nhập ngày thanh toán thực tế (mặc định `today()`)
  4. Hệ thống cập nhật trạng thái `da_tra`

##### UC-TG-03: Cảnh báo chậm trả

- **Trigger**: Mở Dashboard hoặc module trả góp
- **Main flow**: Hệ thống quét các kỳ `chua_tra` có `ngay_den_han + 5 ngày < today()` → đánh dấu `qua_han` và đưa vào danh sách cảnh báo

#### 5.11.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `so_tien_vay` | ≥ 0; ≤ `tong_tien` HĐ |
| `lai_suat_nam` | (0, 30] |
| `so_ky` | [6, 84] |
| `ngan_hang` | Bắt buộc; 1-100 ký tự |

---

### 5.12 Module Quản lý Marketing (MK)

#### 5.12.1 Mô tả & Mục tiêu

Quản lý các chiến dịch tiếp thị, theo dõi lead (khách hàng tiềm năng), đo lường hiệu quả chuyển đổi.

#### 5.12.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ |
| Sales | R, U (chăm sóc lead được giao) |

#### 5.12.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-MK-01 | Chiến dịch có trạng thái: `nhap → dang_chay → ket_thuc` |
| BR-MK-02 | Lead có trạng thái: `moi → dang_cham_soc → chuyen_doi → tu_choi` |
| BR-MK-03 | Khi lead `chuyen_doi` (tạo HĐ đầu tiên), tự chuyển thành KH với phân loại `Thuong` (BR-KH-07) |
| BR-MK-04 | Tỷ lệ chuyển đổi tính theo BR-CALC-06 |
| BR-MK-05 | Một lead có thể được phân công cho 1 NV phụ trách |
| BR-MK-06 | Một chiến dịch có thể có nhiều lead; mỗi lead thuộc tối đa 1 chiến dịch |
| BR-MK-07 | Hiệu quả chiến dịch = (số lead chuyển đổi / tổng lead) × 100% và doanh thu phát sinh từ các lead chuyển đổi |

#### 5.12.4 Use Cases

##### UC-MK-01: Tạo chiến dịch

- **Main flow**:
  1. Admin mở "Marketing" → "Tạo chiến dịch"
  2. Nhập: tên, ngân sách, thời gian, kênh tiếp thị, mục tiêu
  3. Lưu với `trang_thai = nhap` hoặc `dang_chay`

##### UC-MK-02: Thêm lead

- **Main flow**:
  1. Mở "Lead" → "Thêm lead" (có thể từ chiến dịch cụ thể)
  2. Nhập thông tin lead: họ tên, SĐT, email, nguồn (chiến dịch), nhu cầu
  3. Lưu với `trang_thai = moi`
  4. Có thể phân công NV phụ trách

##### UC-MK-03: Chuyển lead thành KH

- **Trigger**: Khi tạo HĐ với 1 lead làm khách hàng (chưa có KH tương ứng)
- **Main flow**:
  1. Trong wizard tạo HĐ (UC-HD-01), khi tìm KH → nếu nhập SĐT của lead, hệ thống đề xuất "Đây là lead. Chuyển thành KH?"
  2. User xác nhận → hệ thống:
     - Tạo `khach_hang` từ thông tin lead
     - Cập nhật `lead.trang_thai = chuyen_doi`
     - Cập nhật `lead.khach_hang_id`

##### UC-MK-04: Báo cáo hiệu quả chiến dịch

- **Main flow**: Mở "Marketing" → "Báo cáo"
- Hiển thị bảng: chiến dịch, ngân sách, số lead, tỷ lệ chuyển đổi, doanh thu phát sinh, ROI

#### 5.12.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `ten_chien_dich` | Bắt buộc; 1-200 ký tự |
| `ngan_sach` | ≥ 0 |
| `tu_ngay`, `den_ngay` | BR-DATA-07 |
| `kenh_tiep_thi` | ∈ {`facebook`, `google_ads`, `youtube`, `truyen_hinh`, `bao_chi`, `truyen_mieng`, `khac`} |

---

### 5.13 Module Quản lý Khiếu nại (KN)

#### 5.13.1 Mô tả & Mục tiêu

Tiếp nhận, phân công, xử lý khiếu nại của khách hàng và đo lường mức độ hài lòng sau xử lý.

#### 5.13.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | CRUD đầy đủ; phân công NV xử lý |
| Sales | C, R, U (ghi nhận & cập nhật khiếu nại của KH mình phụ trách) |
| Kỹ thuật BH | R, U (xử lý khiếu nại liên quan kỹ thuật) |

#### 5.13.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-KN-01 | Mức độ khiếu nại: `thap`, `trung_binh`, `cao` |
| BR-KN-02 | Trạng thái: `moi → dang_xu_ly → da_giai_quyet → da_dong` |
| BR-KN-03 | Khiếu nại `cao` được hiển thị nổi bật ở Dashboard với badge đỏ |
| BR-KN-04 | Sau khi `da_giai_quyet`, mời KH đánh giá hài lòng 1-5 sao trước khi đóng |
| BR-KN-05 | Mọi cập nhật trạng thái phải có ghi chú lý do |
| BR-KN-06 | Khiếu nại được phân loại theo nguồn: `chat_luong_xe`, `dich_vu`, `bao_hanh`, `khac` |
| BR-KN-07 | KPI giải quyết khiếu nại: thời gian từ `moi` đến `da_dong` ≤ 7 ngày (chỉ tiêu nội bộ) |

#### 5.13.4 Use Cases

##### UC-KN-01: Ghi nhận khiếu nại

- **Main flow**:
  1. Mở "Khiếu nại" → "Tạo mới"
  2. Chọn KH (hoặc nhập thông tin nếu là khách lạ)
  3. Nhập: nội dung, mức độ, phân loại
  4. Lưu với `trang_thai = moi`

##### UC-KN-02: Phân công xử lý

- **Actor**: Admin
- **Main flow**: Chọn NV phụ trách, lưu, audit log `ASSIGN_KN`

##### UC-KN-03: Cập nhật tiến độ

- **Main flow**: Cập nhật trạng thái + ghi chú lý do.

##### UC-KN-04: Đóng khiếu nại với đánh giá hài lòng

- **Main flow**:
  1. Khi `da_giai_quyet`, NV gọi điện xin đánh giá KH
  2. Nhập số sao (1-5)
  3. Bấm "Đóng khiếu nại" → `da_dong`

#### 5.13.5 Validation rules

| Trường | Quy tắc |
| --- | --- |
| `noi_dung` | Bắt buộc; 1-2000 ký tự |
| `muc_do` | ∈ {`thap`, `trung_binh`, `cao`} |
| `danh_gia_hai_long` | Tuỳ chọn; integer ∈ [1, 5] |

---

### 5.14 Module Báo cáo Thống kê (BC)

#### 5.14.1 Mô tả & Mục tiêu

Cung cấp các báo cáo kinh doanh phục vụ ra quyết định: doanh thu, top xe bán chạy, hiệu suất NV, KH VIP, BH, KM, Marketing.

#### 5.14.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | Xem mọi báo cáo |
| Sales | Xem KPI cá nhân |
| Kỹ thuật BH | - |

#### 5.14.3 Business Rules đặc thù

| Mã | Quy tắc |
| --- | --- |
| BR-BC-01 | Báo cáo doanh thu hỗ trợ filter: ngày / tháng / quý / năm + theo NV + theo dòng xe |
| BR-BC-02 | Top 10 xe = COUNT HĐ `da_giao_xe` GROUP BY xe trong khoảng thời gian |
| BR-BC-03 | KH VIP = sắp xếp `tong_gia_tri_mua` giảm dần |
| BR-BC-04 | KPI NV = BR-CALC-05 |
| BR-BC-05 | Mọi báo cáo có thể xuất ra Excel/CSV |
| BR-BC-06 | Báo cáo lấy dữ liệu real-time (trực tiếp từ CSDL), không cache để tránh sai số |
| BR-BC-07 | Báo cáo doanh thu chỉ tính HĐ `da_giao_xe` (HĐ chưa giao xe không tính) |

#### 5.14.4 Báo cáo cụ thể

| Mã báo cáo | Tên | Filter | Cột chính |
| --- | --- | --- | --- |
| RP-01 | Doanh thu theo thời gian | Ngày/tháng/quý/năm; NV; dòng xe | Ngày, số HĐ, doanh thu, % so kỳ trước |
| RP-02 | Top 10 xe bán chạy | Khoảng thời gian | Hãng, dòng, số xe bán, tổng doanh thu |
| RP-03 | Hiệu suất nhân viên | Khoảng thời gian | NV, số HĐ, doanh thu, % đạt KPI |
| RP-04 | Khách hàng VIP | Top N | KH, SĐT, số xe, tổng giá trị, phân loại |
| RP-05 | Chi phí bảo hành | Khoảng thời gian | Tháng, số yêu cầu, miễn phí, tính phí, tổng chi phí |
| RP-06 | Hiệu quả khuyến mãi | Khoảng thời gian | KM, số HĐ áp dụng, doanh thu, tiền giảm |
| RP-07 | Hiệu quả marketing | Theo chiến dịch | Chiến dịch, ngân sách, lead, chuyển đổi, ROI |

#### 5.14.5 Use Cases

##### UC-BC-01: Xem báo cáo

- **Main flow**:
  1. Mở "Báo cáo" → chọn loại báo cáo
  2. Cấu hình filter
  3. Bấm "Tạo báo cáo"
  4. Hệ thống truy vấn DB và hiển thị bảng + biểu đồ
  5. User có thể bấm "Xuất Excel" để tải xuống

##### UC-BC-02: Dashboard tổng quan

- **Main flow**: Mở Dashboard → hiển thị các KPI tile + biểu đồ doanh thu 12 tháng + danh sách cảnh báo.

#### 5.14.6 Lưu ý

- Có thể mở rộng: lập lịch tự động gửi email báo cáo tháng cho Admin (tương lai).

---

### 5.15 Module Bảo mật & Audit Log (SEC)

#### 5.15.1 Mô tả & Mục tiêu

Quản lý xác thực, phân quyền, ghi log hoạt động để đảm bảo an toàn dữ liệu.

#### 5.15.2 Actors

| Actor | Quyền |
| --- | --- |
| Admin | Xem log, cấu hình bảo mật |
| Sales / Kỹ thuật | Đăng nhập, đổi mật khẩu cá nhân |

#### 5.15.3 Business Rules đặc thù

(Tham chiếu BR-SEC-01..09 trong Mục 4.7 và BR-TIME-07, 08)

#### 5.15.4 Use Cases

##### UC-SEC-01: Đăng nhập

- **Main flow**:
  1. Mở app → màn hình đăng nhập
  2. Nhập username, password
  3. Hệ thống kiểm tra: NV tồn tại + `trang_thai = active` + bcrypt verify
  4. Nếu OK → tạo session 30 phút, mở Main Window
  5. Audit log `LOGIN_SUCCESS`
- **Alternative**:
  - **A1**: Sai mật khẩu → tăng `lan_dang_nhap_sai`; nếu ≥ 5 → khoá 15 phút (BR-SEC-05); audit log `LOGIN_FAIL`
  - **A2**: NV `inactive` → từ chối với thông báo "Tài khoản đã bị khoá"
  - **A3**: Trong thời gian khoá → từ chối với thông báo "Tài khoản đang bị khoá. Vui lòng thử lại sau"

##### UC-SEC-02: Đăng xuất

- **Main flow**: User bấm "Đăng xuất" hoặc session hết hạn → đóng Main Window, quay về login. Audit log `LOGOUT`.

##### UC-SEC-03: Xem audit log (Admin)

- **Main flow**:
  1. Admin mở "Audit Log"
  2. Filter theo: ngày, user, hành động, đối tượng
  3. Bảng hiển thị: thời gian, user, hành động, bảng ảnh hưởng, ID bản ghi, nội dung (JSON diff)
  4. Có thể xuất Excel

##### UC-SEC-04: Session timeout

- **Trigger**: 30 phút không thao tác (BR-TIME-07)
- **Main flow**: Hệ thống tự đăng xuất, quay về login, hiển thị thông báo "Phiên hết hạn".

#### 5.15.5 Validation rules

(Xem BR-SEC-01..09)

#### 5.15.6 Lưu ý

- File `audit_log` phải có cơ chế rotate khi quá lớn (mở rộng tương lai).
- Sao lưu DB hàng ngày tự động sang `data/backup/YYYY-MM-DD.db`.

---

## 6. QUY TRÌNH NGHIỆP VỤ END-TO-END

> Phần này mô tả các quy trình kinh doanh đi xuyên qua nhiều module, thể hiện cách các module phối hợp với nhau.

### 6.1 WF-01: Nhập kho xe mới

**Diễn viên**: Admin
**Module liên quan**: NCC → Kho → Xe

```text
   Admin            Hệ thống            CSDL
     │                  │                 │
     │ 1. Tạo đơn ĐH    │                 │
     │─────────────────►│                 │
     │                  │ Lưu don_dat_hang│
     │                  │────────────────►│
     │                  │                 │
     │ 2. NCC giao hàng │                 │
     │ 3. Bấm "Nhận"    │                 │
     │─────────────────►│                 │
     │                  │ Tự sinh nhap_kho│
     │                  │ Tăng so_luong_ton xe
     │                  │ Audit log       │
     │                  │────────────────►│
     │ 4. Toast thành công                │
     │◄─────────────────│                 │
```

**Tóm tắt**:

1. Admin tạo đơn đặt hàng (UC-NCC-03), trạng thái `nhap → da_gui`.
2. NCC giao hàng thực tế đến kho.
3. Admin bấm "Nhận hàng" → trạng thái `da_nhan`, hệ thống tự sinh `nhap_kho`, tăng tồn kho (BR-NCC-05, BR-KHO-01).
4. Nếu xe đang `da_ban` → tự chuyển `con_hang` (BR-XE-05).

### 6.2 WF-02: Bán xe (chuẩn — không trả góp)

**Diễn viên**: Sales (chính), Admin (duyệt nếu cần)
**Module liên quan**: KH → Xe → PK → KM → Hợp đồng → Kho → BH

```text
   1. Tư vấn KH ──► (Tạo lead nếu mới)
   2. KH đồng ý mua
   3. Sales mở "Tạo HĐ" (UC-HD-01)
        ├─ Bước 1: Chọn/Tạo KH
        ├─ Bước 2: Chọn xe + PK
        ├─ Bước 3: Áp dụng KM (nếu có)
        └─ Bước 4: Xác nhận tổng tiền
   4. Lưu HĐ với trạng thái = moi_tao
   5. KH thanh toán → Sales chuyển trạng thái → da_thanh_toan
        └─► Hệ thống: giảm tồn kho xe & PK
   6. Giao xe → chuyển trạng thái → da_giao_xe
        └─► Hệ thống:
            ├─ Tự sinh hồ sơ BH (BR-BH-01)
            ├─ Cập nhật KH: tong_gia_tri_mua, so_xe_da_mua
            ├─ Phân loại lại KH (BR-CALC-03)
            └─ Tính KPI cho NV
   7. In hợp đồng PDF (UC-HD-03)
   8. KH ra về với xe
```

**Business rules áp dụng**: BR-HD-01..06, BR-XE-04, BR-KHO-03, BR-KH-03, BR-BH-01, BR-NV-03.

### 6.3 WF-03: Bán xe trả góp

**Diễn viên**: Sales, Admin (xác nhận hồ sơ trả góp)
**Module liên quan**: WF-02 + Trả góp

```text
   1-4. Như WF-02 (đến tạo HĐ)
   5. Sales mở chi tiết HĐ → "Thiết lập trả góp" (UC-TG-01)
   6. Nhập: ngân hàng, số tiền vay, lãi suất, số kỳ
   7. Hệ thống:
        ├─ Tính M (BR-CALC-04)
        ├─ Sinh n bản ghi tra_gop_lich_su
        └─ Hiển thị bảng các kỳ
   8. KH ký giấy tờ trả góp với ngân hàng (offline)
   9. KH thanh toán đợt đầu (down payment) → HĐ chuyển da_thanh_toan
   10. Giao xe → da_giao_xe (như WF-02)
   11. Hàng tháng:
        ├─ KH trả ngân hàng (offline)
        ├─ Sales/Admin ghi nhận đã trả (UC-TG-02)
        └─ Cảnh báo nếu chậm trả ≥ 5 ngày (BR-TG-08)
```

### 6.4 WF-04: Bảo hành xe

**Diễn viên**: KH (tới đại lý), Sales/Kỹ thuật BH
**Module liên quan**: KH → BH → Xe (kiểm tra) → Báo cáo

```text
   1. KH gọi/đến yêu cầu BH
   2. NV mở "Bảo hành" → tìm theo SĐT hoặc mã HĐ
   3. Hệ thống hiển thị hồ sơ BH:
        ├─ Còn hiệu lực? (today() < ngay_ket_thuc)
        └─ Phạm vi BH
   4. Bấm "Tạo yêu cầu BH" (UC-BH-02)
        ├─ Nhập nội dung sửa
        ├─ Hệ thống đề xuất phân loại (mien_phi/tinh_phi)
        └─ Nếu tinh_phi → nhập chi_phi
   5. Kỹ thuật xử lý xe (offline)
        └─ Cập nhật trạng thái: tiep_nhan → dang_xu_ly → hoan_thanh
   6. KH nhận xe + biên lai (in từ UC-BH-04)
   7. Hệ thống cập nhật báo cáo chi phí BH (RP-05)
```

### 6.5 WF-05: Bảo dưỡng định kỳ

**Diễn viên**: KH, Sales (đặt lịch), Kỹ thuật BH (thực hiện)

```text
   1. Hệ thống nhắc nhở (Dashboard): "X xe sắp đến lịch BD"
   2. NV gọi điện cho KH, đặt lịch (UC-HM-01)
   3. KH đến đúng lịch
   4. Kỹ thuật ghi nhận BD (UC-HM-02): nội dung, KM xe, chi phí
   5. KH thanh toán
   6. Hệ thống tự lên lịch BD tiếp theo (BR-HM-01)
```

### 6.6 WF-06: Xử lý khiếu nại

**Diễn viên**: KH, Sales/Admin (tiếp nhận), NV phụ trách (xử lý)

```text
   1. KH khiếu nại
   2. NV ghi nhận (UC-KN-01): nội dung, mức độ, phân loại
        └─ Nếu mức độ = cao → hiển thị nổi bật ở Dashboard
   3. Admin phân công NV xử lý (UC-KN-02)
   4. NV xử lý:
        ├─ Liên hệ KH
        ├─ Phối hợp các bộ phận
        └─ Cập nhật trạng thái → da_giai_quyet
   5. NV xin đánh giá hài lòng từ KH (1-5 sao)
   6. Đóng khiếu nại → da_dong (UC-KN-04)
   7. Hệ thống cập nhật báo cáo KN
```

### 6.7 WF-07: Marketing → Lead → Khách hàng

**Diễn viên**: Admin (tạo chiến dịch), Sales (chăm sóc lead)

```text
   1. Admin tạo chiến dịch (UC-MK-01)
   2. Chiến dịch chạy (offline) — quảng cáo Facebook/Google/etc.
   3. Lead phát sinh:
        ├─ Form online (manual entry vào hệ thống) (UC-MK-02)
        ├─ Hoặc nhập từ tin nhắn/cuộc gọi
        └─ Lead có trạng thái = moi
   4. Admin phân công lead cho Sales
   5. Sales chăm sóc:
        ├─ Cập nhật trạng thái → dang_cham_soc
        └─ Ghi chú lịch sử tương tác
   6. Khi lead đồng ý mua → tạo HĐ (UC-HD-01)
        ├─ Hệ thống đề xuất chuyển lead → KH (UC-MK-03)
        └─ Lead.trang_thai → chuyen_doi
   7. Admin xem báo cáo hiệu quả (UC-MK-04, RP-07):
        ├─ Tỷ lệ chuyển đổi
        └─ ROI
```

### 6.8 WF-08: Hủy hợp đồng

**Diễn viên**: Admin (chỉ Admin mới được hủy)

```text
   1. KH yêu cầu hủy HĐ (lý do: không còn nhu cầu, đổi xe khác, …)
   2. Sales báo Admin
   3. Admin mở chi tiết HĐ → "Hủy hợp đồng" (UC-HD-04)
   4. Nhập lý do hủy
   5. Hệ thống:
        ├─ Chuyển trạng thái → huy
        ├─ Hoàn tồn kho xe & PK (BR-HD-05)
        ├─ Xoá hồ sơ BH liên quan (BR-BH-10)
        ├─ Xoá hồ sơ trả góp (BR-TG-10)
        └─ Audit log CANCEL_HD với lý do
   6. Nếu HĐ đã `da_thanh_toan`, NV xử lý hoàn tiền cho KH (offline)
```

> **Lưu ý**: HĐ `da_giao_xe` không thể hủy (BR-HD-06). Nếu KH yêu cầu trả xe, xử lý theo quy trình "thu hồi xe" (mở rộng tương lai, hiện chưa hỗ trợ).

---

## 7. BÁO CÁO & KPI

### 7.1 Danh sách báo cáo (tổng hợp)

Đã trình bày chi tiết tại Mục 5.14.4. Tóm lược:

| Mã | Tên báo cáo | Tần suất sử dụng | Người đọc chính |
| --- | --- | --- | --- |
| RP-01 | Doanh thu theo thời gian | Hàng tháng | Admin, Chủ đại lý |
| RP-02 | Top 10 xe bán chạy | Hàng tháng/quý | Admin, Marketing |
| RP-03 | Hiệu suất nhân viên | Hàng tháng | Admin, Quản lý |
| RP-04 | Khách hàng VIP | Hàng quý | Admin, Marketing |
| RP-05 | Chi phí bảo hành | Hàng tháng | Admin, Kỹ thuật |
| RP-06 | Hiệu quả khuyến mãi | Sau mỗi KM | Admin, Marketing |
| RP-07 | Hiệu quả marketing | Hàng tháng | Admin, Marketing |

### 7.2 KPI hệ thống cấp đại lý

| KPI | Định nghĩa | Mục tiêu (gợi ý) |
| --- | --- | --- |
| **Doanh thu tháng** | SUM(`hop_dong.tong_tien` `da_giao_xe` trong tháng) | Tăng so với cùng kỳ |
| **Số xe bán/tháng** | COUNT(HĐ `da_giao_xe`) | ≥ N (theo quy mô đại lý) |
| **Tỷ lệ HĐ hủy** | `huy / tổng HĐ tạo` | < 5% |
| **Tỷ lệ chuyển đổi marketing** | BR-CALC-06 | > 10% |
| **Tỷ lệ KH quay lại (repeat)** | KH có ≥ 2 HĐ / tổng KH | > 15% |
| **Tỷ lệ hài lòng khiếu nại** | Điểm trung bình `danh_gia_hai_long` | ≥ 4.0/5 |
| **Thời gian xử lý khiếu nại trung bình** | AVG(`ngay_dong - ngay_tao`) | ≤ 7 ngày |

### 7.3 KPI cá nhân (Sales)

| KPI | Định nghĩa | Cách tính |
| --- | --- | --- |
| **Số xe bán** | HĐ `da_giao_xe` của NV trong kỳ | BR-CALC-05 |
| **Doanh thu tạo ra** | SUM(`tong_tien`) | BR-CALC-05 |
| **Tỷ lệ chốt đơn** | HĐ `da_giao_xe` / HĐ `moi_tao` | % |
| **Số lead chăm sóc** | COUNT(`lead` được giao) | |
| **Tỷ lệ chuyển đổi cá nhân** | Lead `chuyen_doi` / lead được giao | % |

### 7.4 Quy tắc cập nhật KPI

- KPI tính real-time từ CSDL (BR-BC-06).
- Không lưu KPI snapshot, không cache.
- Mỗi NV xem được KPI cá nhân; Admin xem KPI toàn đội.

---

## 8. RÀNG BUỘC & GIẢ ĐỊNH

### 8.1 Ràng buộc kỹ thuật

| Mã | Ràng buộc |
| --- | --- |
| C-TECH-01 | Ngôn ngữ: Python 3.10+ |
| C-TECH-02 | UI: PyQt6 (desktop, không web) |
| C-TECH-03 | CSDL: SQLite (file đơn lẻ) — không hỗ trợ MySQL/PostgreSQL trong phạm vi này |
| C-TECH-04 | Bảo mật mật khẩu: thư viện `bcrypt` |
| C-TECH-05 | Hệ điều hành: Windows 10+, Linux Ubuntu 20.04+, macOS 12+ |
| C-TECH-06 | Đóng gói: PyInstaller (tuỳ chọn) |
| C-TECH-07 | Toàn bộ code & UI bằng tiếng Việt (có comment tiếng Việt) |

### 8.2 Ràng buộc nghiệp vụ

| Mã | Ràng buộc |
| --- | --- |
| C-BUS-01 | Đơn vị tiền tệ duy nhất: VND (không hỗ trợ đa tiền tệ) |
| C-BUS-02 | Phần mềm chỉ dùng cho 1 đại lý/cửa hàng (không multi-tenant) |
| C-BUS-03 | Một đại lý chạy đơn lẻ — không đồng bộ real-time đa chi nhánh |
| C-BUS-04 | Không tích hợp tự động với cổng thanh toán/ngân hàng |
| C-BUS-05 | Tài liệu hợp đồng PDF dùng template cố định, không cho phép thiết kế tuỳ ý qua UI |

### 8.3 Ràng buộc hiệu năng

| Mã | Ràng buộc |
| --- | --- |
| C-PERF-01 | Tìm kiếm xe ≤ 2 giây với 10.000 bản ghi |
| C-PERF-02 | Tải danh sách KH ≤ 1 giây |
| C-PERF-03 | Hỗ trợ tối đa 50 người dùng đồng thời (chế độ mạng nội bộ) |
| C-PERF-04 | Lỗi hệ thống < 0.1% |
| C-PERF-05 | Backup hàng ngày, phục hồi ≤ 15 phút |

### 8.4 Giả định

| Mã | Giả định |
| --- | --- |
| A-01 | Đại lý có máy tính cấu hình tối thiểu 2 cores, 4GB RAM |
| A-02 | Người dùng đã được đào tạo cơ bản về máy tính (mở app, gõ chữ, dùng chuột) |
| A-03 | Có ít nhất 1 quản trị viên am hiểu để cài đặt/khôi phục dữ liệu |
| A-04 | Khách hàng có SĐT chính chủ — SĐT là khoá định danh |
| A-05 | Mọi dữ liệu nhập vào (giá, số lượng) đều do NV nhập đúng — hệ thống chỉ validate format, không validate đúng/sai nghiệp vụ |
| A-06 | Đại lý có quy trình bán hàng tuyến tính (KH đến → tư vấn → ký HĐ → thanh toán → giao xe), không xử lý đặt cọc đa giai đoạn |
| A-07 | Bảo hành xe theo điều khoản chuẩn của hãng, không có điều khoản đặc biệt |
| A-08 | Lãi suất trả góp do ngân hàng quyết định — đại lý chỉ ghi nhận, không tính toán phức tạp khác |

### 8.5 Phụ thuộc bên ngoài

| Mã | Phụ thuộc |
| --- | --- |
| D-01 | Thư viện `PyQt6` (PyPI) |
| D-02 | Thư viện `bcrypt` (PyPI) |
| D-03 | Thư viện `reportlab` hoặc `weasyprint` (cho PDF) |
| D-04 | Thư viện `openpyxl` (cho xuất Excel) |
| D-05 | Thư viện `pytest` (test) |
| D-06 | Module `sqlite3` của Python (built-in) |

---

## 9. TIÊU CHÍ NGHIỆM THU

### 9.1 Tiêu chí nghiệm thu chung

Hệ thống được nghiệm thu khi đáp ứng đủ:

- ✅ **100% module** trong Mục 5 được triển khai đầy đủ các use case chính.
- ✅ **Tất cả Business Rules** trong Mục 4 được áp dụng và có thể kiểm chứng qua test.
- ✅ **Mọi yêu cầu phi chức năng** (Mục 8.3) đạt mục tiêu.
- ✅ **Có unit test** cho các hàm tính toán (BR-CALC-01..07).
- ✅ **Tài liệu hướng dẫn sử dụng** đầy đủ.
- ✅ **File `.exe`** đóng gói chạy được trên Windows.

### 9.2 Tiêu chí nghiệm thu chi tiết theo module

Ký hiệu `AC-XX-NN`: Acceptance Criteria cho module XX, số NN.

#### Module Xe (AC-XE)

- AC-XE-01: Có thể thêm/sửa/xóa xe theo UC-XE-01..03; xóa thất bại đúng theo BR-XE-02.
- AC-XE-02: Tìm kiếm với 10.000 xe trả kết quả ≤ 2 giây (C-PERF-01).
- AC-XE-03: Trạng thái xe tự cập nhật đúng theo BR-XE-04, 05.

#### Module KH (AC-KH)

- AC-KH-01: Phân loại KH tự cập nhật đúng BR-CALC-03.
- AC-KH-02: Trùng SĐT bị reject với thông báo rõ ràng.
- AC-KH-03: Lịch sử giao dịch hiển thị đầy đủ HĐ kể cả `huy`.

#### Module HD (AC-HD)

- AC-HD-01: Wizard 4 bước hoạt động trơn tru, có thể quay lại.
- AC-HD-02: Tổng tiền tính đúng theo BR-CALC-01 với mọi tổ hợp PK + KM.
- AC-HD-03: Chuyển trạng thái đúng theo BR-FLOW (Hợp đồng).
- AC-HD-04: PDF in ra có đủ thông tin theo BR-HD-10.
- AC-HD-05: Hủy HĐ hoàn lại tồn kho và xoá BH/Trả góp.

#### Module BH (AC-BH)

- AC-BH-01: Tự sinh hồ sơ BH khi HĐ → `da_giao_xe`.
- AC-BH-02: Cảnh báo BH sắp hết hạn 30 ngày hiển thị ở Dashboard.

#### Module KM (AC-KM)

- AC-KM-01: KM tự áp dụng đúng phạm vi (BR-KM-04).
- AC-KM-02: Tiền giảm tính đúng BR-CALC-02.

#### Module Trả góp (AC-TG)

- AC-TG-01: Số tiền trả/tháng tính đúng BR-CALC-04 (sai số ≤ 1 VND do làm tròn).
- AC-TG-02: Sinh đủ `n` kỳ trả với ngày cách nhau 1 tháng.

#### Module Báo cáo (AC-BC)

- AC-BC-01: 7 báo cáo (RP-01..07) đều xuất được Excel.
- AC-BC-02: Số liệu khớp với CSDL (sai số 0).

#### Module Bảo mật (AC-SEC)

- AC-SEC-01: Mật khẩu được hash bcrypt cost ≥ 12.
- AC-SEC-02: Đăng nhập sai 5 lần → khoá 15 phút.
- AC-SEC-03: Session timeout sau 30 phút.
- AC-SEC-04: Audit log đầy đủ với mọi CRUD quan trọng.

### 9.3 Quy trình nghiệm thu

1. **Test nội bộ**: Nhóm phát triển chạy unit test (`pytest`) đạt ≥ 80% coverage cho module nghiệp vụ.
2. **UAT (User Acceptance Test)**: Mô phỏng các workflow E2E (WF-01..08) trên dữ liệu seed.
3. **Demo với giảng viên**: Trình diễn các tính năng chính theo `LIST_CHUC_NANG.md`.
4. **Sản phẩm bàn giao** gồm: mã nguồn, file `.exe`, CSDL mẫu, tài liệu hướng dẫn.

---

## 10. MA TRẬN TRUY VẾT

> Ma trận liên kết Business Rules ↔ Use Cases ↔ Chức năng (`LIST_CHUC_NANG.md`) ↔ Màn hình (`PLAN.md` mục 5).

### 10.1 Ma trận BR ↔ Module ↔ Chức năng (rút gọn)

| Module | Số BR | Use Cases chính | Chức năng (`LIST_CHUC_NANG`) | Màn hình (`PLAN`) |
| --- | --- | --- | --- | --- |
| Xe | 9 (BR-XE-01..09) | UC-XE-01..05 | 1.1 - 1.5 | S-XE-01..03 |
| KH | 7 (BR-KH-01..07) | UC-KH-01..04 | 2.1 - 2.4 | S-KH-01..03 |
| NV | 8 (BR-NV-01..08) | UC-NV-01..05 | 3.1 - 3.5 | S-NV-01..03 |
| HD | 12 (BR-HD-01..12) | UC-HD-01..04 | 4.1 - 4.6 | S-HD-01..04 |
| Kho | 7 (BR-KHO-01..07) | UC-KHO-01..03 | 5.1 - 5.3 | S-KHO-01..02 |
| BH | 10 (BR-BH-01..10) | UC-BH-01..05 | 6.1 - 6.7 | S-BH-01..04 |
| KM | 10 (BR-KM-01..10) | UC-KM-01..05 | 7.1 - 7.7 | S-KM-01..03 |
| PK | 8 (BR-PK-01..08) | UC-PK-01..03 | 8.1 - 8.5 | S-PK-01..03 |
| HM | 7 (BR-HM-01..07) | UC-HM-01..04 | 9.1 - 9.4 | S-HM-01..04 |
| NCC | 6 (BR-NCC-01..06) | UC-NCC-01..03 | 10.1 - 10.4 | S-NCC-01..03 |
| TG | 10 (BR-TG-01..10) | UC-TG-01..03 | 11.1 - 11.4 | S-TG-01..03 |
| MK | 7 (BR-MK-01..07) | UC-MK-01..04 | 12.1 - 12.4 | S-MK-01..03 |
| KN | 7 (BR-KN-01..07) | UC-KN-01..04 | 13.1 - 13.5 | S-KN-01..02 |
| BC | 7 (BR-BC-01..07) | UC-BC-01..02 | 14.1 - 14.4 | S-BC-01..04 |
| SEC | 9 (BR-SEC-01..09) | UC-SEC-01..04 | 15.1 - 15.4 | S-AUTH-01..02, S-SYS-01 |

**Tổng số BR đặc thù module**: 124 BR (chưa kể BR tổng thể trong Mục 4).

### 10.2 Ma trận BR Tổng thể ↔ áp dụng

| BR Mục 4 | Module áp dụng |
| --- | --- |
| BR-ID-01..06 | XE, KH, NV, HD, NCC, KM |
| BR-DATA-01..10 | Tất cả module |
| BR-REF-01..07 | XE, KH, NV, HD, PK, NCC, KM |
| BR-FLOW (Hợp đồng) | HD, BH, TG, KHO |
| BR-FLOW (Xe) | XE, KHO |
| BR-FLOW (KM) | KM, HD |
| BR-FLOW (Khiếu nại) | KN |
| BR-FLOW (ĐĐH NCC) | NCC, KHO |
| BR-CALC-01..02 | HD, KM, PK |
| BR-CALC-03 | KH, HD |
| BR-CALC-04 | TG |
| BR-CALC-05 | NV, BC |
| BR-CALC-06 | MK, BC |
| BR-CALC-07 | PK |
| BR-TIME-01..08 | BH, HM, TG, XE, KH, KM, SEC |
| BR-SEC-01..09 | SEC, NV, tất cả module qua audit log |
| BR-UI-01..06 | Tất cả màn hình |

### 10.3 Test Plan tóm tắt

> Mỗi UC sẽ có ít nhất 1 happy-path test và ít nhất 1 alternative-flow test.

| Loại test | Phạm vi | Công cụ |
| --- | --- | --- |
| **Unit test** | Hàm tính BR-CALC-01..07; validation rules | pytest |
| **Integration test** | Workflow WF-01..08 | pytest + DB test |
| **UI test** | Các màn hình quan trọng (login, HĐ, BH) | (manual hoặc pytest-qt) |
| **Performance test** | Tìm kiếm 10.000 xe; mở danh sách KH | pytest-benchmark hoặc thủ công |
| **Security test** | bcrypt verify; session timeout; khoá tài khoản | pytest |

---

## PHỤ LỤC

### A. Lịch sử thay đổi tài liệu

| Phiên bản | Ngày | Người sửa | Ghi chú |
| --- | --- | --- | --- |
| 1.0 | 2026-04-30 | Nhóm phát triển | Phiên bản đầu tiên |

### B. Tài liệu liên quan

| Tài liệu | Mục đích |
| --- | --- |
| `README.md` | Giới thiệu dự án |
| `docs/TECH_STACK.md` | Stack kỹ thuật |
| `docs/YEU_CAU_CHUC_NANG.md` | Yêu cầu chức năng & phi chức năng |
| `docs/LIST_CHUC_NANG.md` | Danh sách 71 chức năng |
| `docs/PLAN.md` | Kế hoạch tổng thể (overview, DB, UI/UX) |
| `docs/BUSINESS_REQUIREMENTS.md` *(tài liệu này)* | Yêu cầu nghiệp vụ chi tiết |
| `design/DESIGN-apple.md` | Design system tham chiếu |

### C. Câu hỏi mở (cần xác nhận với stakeholder)

| Mã | Câu hỏi | Người trả lời |
| --- | --- | --- |
| Q-01 | Thời hạn BH mặc định 24 tháng có phù hợp với chính sách hãng xe không? | Chủ đại lý |
| Q-02 | Ngưỡng tồn kho cảnh báo mặc định 2 có phù hợp không? | Quản lý đại lý |
| Q-03 | Có cần lưu ảnh xe/khách hàng không? (Hiện chưa có trong scope) | Chủ đại lý |
| Q-04 | Lãi suất trả góp tối đa 30%/năm có hợp lý? | Quản lý |
| Q-05 | KPI mục tiêu cụ thể từng kỳ là gì? | Chủ đại lý |

