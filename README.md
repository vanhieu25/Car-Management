# Phần mềm Quản lý Đại lý Xe Hơi

> Ứng dụng desktop quản lý toàn diện hoạt động kinh doanh ô tô cho đại lý.

---

## 1. Mô tả dự án

Đồ án học phần **Lập trình Python** với mục tiêu xây dựng phần mềm quản lý đại lý xe hơi. Phần mềm hỗ trợ:

- Quản lý thông tin xe, khách hàng, nhân viên
- Quản lý hợp đồng mua bán, bảo hành, bảo dưỡng
- Báo cáo thống kê doanh thu và hiệu suất kinh doanh
- Quản lý kho xe, phụ kiện, khuyến mãi
- Hỗ trợ trả góp và chăm sóc khách hàng sau bán hàng

---

## 2. Nhóm thực hiện

| Thành viên          | Vai trò         |
| ------------------- | --------------- |
| Nguyễn Văn Hiếu     | Nhóm trưởng     |
| Lê Minh Đạt        | Thành viên      |
| Nguyễn Hữu Hải     | Thành viên      |

---

## 3. Tech Stack

| Thành phần       | Công nghệ              | Mô tả                        |
| ---------------- | ---------------------- | ---------------------------- |
| Ngôn ngữ         | Python 3.10+           | Ngôn ngữ chính, xử lý nghiệp vụ |
| Giao diện        | PyQt6                  | Desktop UI framework         |
| Cơ sở dữ liệu   | SQLite                 | Lưu trữ dữ liệu nội bộ      |
| Bảo mật          | bcrypt                 | Mã hóa mật khẩu             |
| Kiểm thử         | pytest                 | Unit test                    |
| Đóng gói         | PyInstaller (tuỳ chọn) | Build file .exe              |

---

## 4. Tính năng chính

### 4.1 Quản lý xe
- Thêm/sửa/xoá thông tin xe (mã xe, hãng, dòng, năm, màu, giá, tồn kho)
- Tìm kiếm và lọc xe theo nhiều tiêu chí
- Trạng thái: còn hàng / đã bán / sắp về

### 4.2 Quản lý khách hàng
- Lưu thông tin khách hàng (họ tên, SĐT, email)
- Phân loại khách hàng tự động theo lịch sử mua hàng
- Xem lịch sử giao dịch

### 4.3 Quản lý nhân viên
- Phân quyền: quản trị viên vs nhân viên bán hàng
- Theo dõi KPI: số xe bán, doanh thu

### 4.4 Quản lý hợp đồng
- Tạo hợp đồng mua bán xe
- Tự động tính giá trị, áp dụng khuyến mãi/phụ kiện
- Trạng thái: mới tạo / đã thanh toán / đã giao / đã hủy
- In hợp đồng PDF

### 4.5 Quản lý kho
- Cập nhật tồn kho tự động theo hợp đồng
- Cảnh báo khi tồn kho dưới mức tối thiểu

### 4.6 Báo cáo thống kê
- Doanh thu theo ngày/tháng/năm
- Top 10 xe bán chạy
- Hiệu suất nhân viên
- Khách hàng VIP

### 4.7 Bảo hành
- Theo dõi bảo hành theo xe và khách hàng
- Cảnh báo bảo hành sắp hết hạn (30 ngày trước)
- Phân loại: bảo hành miễn phí / sửa chữa tính phí
- In phiếu bảo hành

### 4.8 Khuyến mãi
- Tạo chương trình KM theo thời gian
- Loại: giảm giá / tặng phụ kiện / giảm lãi suất / combo
- Áp dụng theo hãng, dòng xe hoặc xe tồn kho lâu

### 4.9 Quản lý phụ kiện
- Danh mục phụ kiện, phân loại (nội thất/ngoại thất/điện tử...)
- Combo phụ kiện, cảnh báo hết hàng

### 4.10 Dịch vụ hậu mãi
- Đặt lịch bảo dưỡng định kỳ
- Dịch vụ cứu hộ
- Chương trình chăm sóc khách hàng (sinh nhật, tri ân)

### 4.11 Quản lý nhà cung cấp
- Thông tin nhà cung cấp (tên, địa chỉ, SĐT)
- Lịch sử nhập hàng, đánh giá chất lượng
- Tạo đơn đặt hàng

### 4.12 Quản lý trả góp
- Thông tin ngân hàng, lãi suất, thời hạn
- Tính toán số tiền trả hàng tháng
- Theo dõi tiến độ, cảnh báo chậm trả

### 4.13 Quản lý marketing
- Chiến dịch quảng cáo, ngân sách
- Quản lý lead (khách hàng tiềm năng)
- Sự kiện lái thử, triển lãm

### 4.14 Quản lý khiếu nại
- Ghi nhận và phân công xử lý
- Theo dõi tiến độ, đánh giá mức độ hài lòng
- Thống kê báo cáo

---

## 5. Yêu cầu hệ thống

| Yêu cầu       | Chi tiết                                      |
| ------------- | --------------------------------------------- |
| CPU           | Tối thiểu 2 cores                             |
| RAM           | Tối thiểu 4 GB                                |
| Dung lượng    | ~200 MB cho ứng dụng và dữ liệu SQLite       |
| Hệ điều hành  | Windows 10+, Linux (Ubuntu 20.04+), macOS 12+ |

---

## 6. Cài đặt và chạy

```bash
# Clone repository
git clone <repository-url>
cd Car-Management

# Cài đặt dependencies
pip install -r requirements.txt  # PyQt6, bcrypt, pytest

# Chạy ứng dụng
python main.py
```

---

## 7. Liên hệ

| Thành viên          | GitHub           |
| ------------------- | ---------------- |
| Nguyễn Văn Hiếu     | vanhieu25        |
| Lê Minh Đạt        | leminhdat8386    |
| Nguyễn Hữu Hải     | huuhai22 |