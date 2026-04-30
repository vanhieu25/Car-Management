# TOÀN BỘ CHỨC NĂNG HỆ THỐNG QUẢN LÝ ĐẠI LÝ XE HƠI

Dựa trên yêu cầu được cung cấp, dưới đây là danh sách đầy đủ các chức năng mà hệ thống cần:

---

## 1. QUẢN LÝ THÔNG TIN XE

| STT | Chức năng           | Mô tả                                                                                  |
| --- | ------------------- | -------------------------------------------------------------------------------------- |
| 1.1 | Thêm mới xe         | Nhập thông tin: mã xe, hãng, dòng xe, năm sản xuất, màu sắc, giá bán, số lượng tồn kho |
| 1.2 | Chỉnh sửa xe        | Cập nhật thông tin xe (trừ mã xe)                                                      |
| 1.3 | Xóa xe              | Xóa khi chưa có hợp đồng liên quan                                                     |
| 1.4 | Tìm kiếm nâng cao   | Tìm kiếm theo nhiều tiêu chí kết hợp                                                   |
| 1.5 | Lọc theo trạng thái | Lọc: còn hàng / đã bán / sắp về                                                        |

---

## 2. QUẢN LÝ KHÁCH HÀNG

| STT | Chức năng             | Mô tả                                                 |
| --- | --------------------- | ----------------------------------------------------- |
| 2.1 | Thêm mới khách hàng   | Họ tên, SĐT, email (bắt buộc)                         |
| 2.2 | Cập nhật thông tin    | Chỉnh sửa thông tin khách hàng                        |
| 2.3 | Xem lịch sử giao dịch | Xem đầy đủ lịch sử mua hàng                           |
| 2.4 | Phân loại khách hàng  | Tự động phân loại dựa trên số lần mua và tổng giá trị |

---

## 3. QUẢN LÝ NHÂN VIÊN

| STT | Chức năng               | Mô tả                                     |
| --- | ----------------------- | ----------------------------------------- |
| 3.1 | Thêm nhân viên          | Quản trị viên thêm mới                    |
| 3.2 | Xóa nhân viên           | Quản trị viên xóa                         |
| 3.3 | Sửa thông tin nhân viên | Quản trị viên chỉnh sửa                   |
| 3.4 | Xem thông tin cá nhân   | Nhân viên bán hàng xem thông tin của mình |
| 3.5 | Theo dõi KPI            | Số xe bán, doanh thu tạo ra               |

---

## 4. QUẢN LÝ HỢP ĐỒNG BÁN XE

| STT | Chức năng           | Mô tả                                                     |
| --- | ------------------- | --------------------------------------------------------- |
| 4.1 | Tạo hợp đồng mới    | Tạo hợp đồng bán xe                                       |
| 4.2 | Tính toán giá trị   | Tự động tính toán giá hợp đồng                            |
| 4.3 | Thêm phụ kiện       | Bổ sung phụ kiện vào hợp đồng                             |
| 4.4 | Áp dụng khuyến mãi  | Tự động áp dụng KM nếu đủ điều kiện                       |
| 4.5 | Cập nhật trạng thái | Trạng thái: mới tạo / đã thanh toán / đã giao xe / đã hủy |
| 4.6 | In hợp đồng PDF     | Xuất hợp đồng dạng PDF chuyên nghiệp                      |

---

## 5. QUẢN LÝ KHO XE

| STT | Chức năng             | Mô tả                                |
| --- | --------------------- | ------------------------------------ |
| 5.1 | Cập nhật tồn kho      | Tự động cập nhật khi có hợp đồng mới |
| 5.2 | Cảnh báo tồn kho thấp | Cảnh báo khi dưới mức tối thiểu      |
| 5.3 | Lịch sử nhập kho      | Theo dõi nhập hàng từ nhà cung cấp   |

---

## 6. QUẢN LÝ BẢO HÀNH

| STT | Chức năng            | Mô tả                                  |
| --- | -------------------- | -------------------------------------- |
| 6.1 | Ghi nhận bảo hành    | Thời hạn (tháng), phạm vi bảo hành     |
| 6.2 | Theo dõi lịch sử BH  | Lịch sử bảo hành theo xe và khách hàng |
| 6.3 | Cảnh báo BH sắp hết  | Cảnh báo trước 30 ngày                 |
| 6.4 | Tiếp nhận yêu cầu BH | Ngày đến, nội dung sửa, chi phí        |
| 6.5 | Phân loại yêu cầu BH | Miễn phí / tính phí                    |
| 6.6 | In phiếu bảo hành    | In phiếu BH và biên lai sửa chữa       |
| 6.7 | Thống kê chi phí BH  | Báo cáo chi phí BH theo thời gian      |

---

## 7. QUẢN LÝ KHUYẾN MÃI

| STT | Chức năng            | Mô tả                                  |
| --- | -------------------- | -------------------------------------- |
| 7.1 | Tạo chương trình KM  | Tên, mô tả, thời gian áp dụng          |
| 7.2 | Loại khuyến mãi      | Giảm tiền / tặng PK / giảm lãi / combo |
| 7.3 | Phạm vi áp dụng      | Toàn bộ / hãng / dòng / xe tồn kho lâu |
| 7.4 | Mức giảm giá         | Số tiền cố định hoặc phần trăm         |
| 7.5 | Theo dõi hiệu quả KM | Số xe bán, doanh thu từ KM             |
| 7.6 | Tự động áp dụng KM   | Áp dụng tự động khi tạo hợp đồng       |
| 7.7 | Dừng/tạm dừng KM     | Quản lý trạng thái chương trình        |

---

## 8. QUẢN LÝ PHỤ KIỆN

| STT | Chức năng            | Mô tả                                                |
| --- | -------------------- | ---------------------------------------------------- |
| 8.1 | Danh mục phụ kiện    | Tên, mô tả, giá, tồn kho                             |
| 8.2 | Phân loại PK         | Nội thất / ngoại thất / điện tử / bảo vệ / trang trí |
| 8.3 | Cảnh báo hết PK      | Cảnh báo khi tồn kho hết                             |
| 8.4 | Quản lý combo PK     | Gói PK với giá ưu đãi                                |
| 8.5 | Thêm PK vào hợp đồng | Tính giá riêng cho PK trong hợp đồng                 |

---

## 9. QUẢN LÝ DỊCH VỤ HẬU MÃI

| STT | Chức năng           | Mô tả                               |
| --- | ------------------- | ----------------------------------- |
| 9.1 | Đặt lịch bảo dưỡng  | Nhắc nhở theo km/tháng              |
| 9.2 | Ghi nhận lịch sử BD | Ngày, nội dung, chi phí bảo dưỡng   |
| 9.3 | Dịch vụ cứu hộ      | Ghi nhận yêu cầu, phản hồi, chi phí |
| 9.4 | Chăm sóc khách hàng | Thiệp sinh nhật, ưu đãi tri ân      |

---

## 10. QUẢN LÝ NHÀ CUNG CẤP

| STT  | Chức năng         | Mô tả                                   |
| ---- | ----------------- | --------------------------------------- |
| 10.1 | Thông tin NCC     | Tên, địa chỉ, SĐT, email, người liên hệ |
| 10.2 | Lịch sử nhập hàng | Ngày, số lượng, giá nhập                |
| 10.3 | Đánh giá NCC      | Chất lượng, thời gian giao, giá cả      |
| 10.4 | Tạo đơn đặt hàng  | Đặt xe/phụ kiện từ NCC                  |

---

## 11. QUẢN LÝ TRẢ GÓP

| STT  | Chức năng         | Mô tả                                      |
| ---- | ----------------- | ------------------------------------------ |
| 11.1 | Thông tin trả góp | Ngân hàng, số tiền vay, lãi suất, thời hạn |
| 11.2 | Tính toán trả góp | Tính số tiền trả hàng tháng                |
| 11.3 | Theo dõi tiến độ  | Số tiền còn nợ, số kỳ còn lại              |
| 11.4 | Cảnh báo chậm trả | Thông báo khi trả chậm                     |

---

## 12. QUẢN LÝ MARKETING

| STT  | Chức năng         | Mô tả                                    |
| ---- | ----------------- | ---------------------------------------- |
| 12.1 | Tạo chiến dịch    | Tên, ngân sách, thời gian, kênh tiếp thị |
| 12.2 | Theo dõi hiệu quả | Khách hàng tiềm năng, chuyển đổi         |
| 12.3 | Quản lý sự kiện   | Lái thử, triển lãm xe                    |
| 12.4 | Quản lý lead      | Khách hàng tiềm năng từ quảng cáo        |

---

## 13. QUẢN LÝ KHIẾU NẠI

| STT  | Chức năng          | Mô tả                                        |
| ---- | ------------------ | -------------------------------------------- |
| 13.1 | Ghi nhận khiếu nại | Nội dung, ngày, mức độ (thấp/trung bình/cao) |
| 13.2 | Phân công xử lý    | Giao cho nhân viên phụ trách                 |
| 13.3 | Theo dõi tiến độ   | Đang xử lý / đã giải quyết / đã đóng         |
| 13.4 | Đánh giá hài lòng  | Mức độ hài lòng sau xử lý                    |
| 13.5 | Báo cáo khiếu nại  | Thống kê theo loại, thời gian                |

---

## 14. BÁO CÁO THỐNG KÊ

| STT  | Chức năng                | Mô tả                          |
| ---- | ------------------------ | ------------------------------ |
| 14.1 | Doanh thu theo thời gian | Báo cáo theo ngày/tháng/năm    |
| 14.2 | Top 10 xe bán chạy       | Thống kê xe bán nhiều nhất     |
| 14.3 | Hiệu suất nhân viên      | KPI theo nhân viên             |
| 14.4 | Khách hàng VIP           | Xếp hạng theo tổng giá trị mua |

---

## 15. HỆ THỐNG BẢO MẬT

| STT  | Chức năng         | Mô tả                            |
| ---- | ----------------- | -------------------------------- |
| 15.1 | Đăng nhập         | Xác thực bằng tài khoản/mật khẩu |
| 15.2 | Mã hóa mật khẩu   | Mã hóa bcrypt                    |
| 15.3 | Ghi log hoạt động | Log mọi hoạt động quan trọng     |
| 15.4 | Session timeout   | Tự động đăng xuất sau 30 phút    |

---

## TỔNG KẾT

| Module                  | Số chức năng     |
| ----------------------- | ---------------- |
| 1. Quản lý thông tin xe | 5                |
| 2. Quản lý khách hàng   | 4                |
| 3. Quản lý nhân viên    | 5                |
| 4. Quản lý hợp đồng     | 6                |
| 5. Quản lý kho xe       | 3                |
| 6. Quản lý bảo hành     | 7                |
| 7. Quản lý khuyến mãi   | 7                |
| 8. Quản lý phụ kiện     | 5                |
| 9. Dịch vụ hậu mãi      | 4                |
| 10. Quản lý NCC         | 4                |
| 11. Quản lý trả góp     | 4                |
| 12. Quản lý marketing   | 4                |
| 13. Quản lý khiếu nại   | 5                |
| 14. Báo cáo thống kê    | 4                |
| 15. Hệ thống bảo mật    | 4                |
| **TỔNG CỘNG**           | **71 chức năng** |
