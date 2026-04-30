
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
