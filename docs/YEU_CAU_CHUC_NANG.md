# YÊU CẦU HỆ THỐNG

**Phần mềm quản lý đại lý xe hơi**

---

## 1. PHÂN TÍCH CHỨC NĂNG

### 1.1 Quản lý thông tin xe

**Mô tả**: Hệ thống cho phép quản lý toàn bộ thông tin về các dòng xe có trong đại lý

**Chi tiết**:

- Thêm mới xe với thông tin: mã xe, hãng, dòng xe, năm sản xuất, màu sắc, giá bán, số lượng tồn kho
- Chỉnh sửa thông tin xe (trừ mã xe)
- Xóa xe chỉ khi chưa có hợp đồng liên quan
- Tìm kiếm nâng cao theo nhiều tiêu chí kết hợp
- Lọc xe theo trạng thái: còn hàng / đã bán / sắp về

### 1.2 Quản lý khách hàng

**Mô tả**: Lưu trữ và quản lý thông tin khách hàng mua xe tại đại lý

**Chi tiết**:

- Thêm mới khách hàng với thông tin bắt buộc: họ tên, SĐT, email
- Cập nhật thông tin khách hàng
- Xem lịch sử giao dịch đầy đủ của từng khách hàng
- Phân loại tự động dựa trên số lần mua và tổng giá trị

### 1.3 Quản lý nhân viên

**Mô tả**: Quản lý thông tin và phân quyền cho nhân viên trong đại lý

**Chi tiết**:

- Quản trị viên có thể thêm/xóa/sửa mọi nhân viên
- Nhân viên bán hàng chỉ xem được thông tin của mình
- Theo dõi KPI: số xe bán được, doanh thu tạo ra

### 1.4 Quản lý hợp đồng bán xe

**Mô tả**: Tạo và quản lý hợp đồng bán xe giữa đại lý và khách hàng

**Chi tiết**:

- Tự động tính toán giá trị hợp đồng
- Hỗ trợ thêm phụ kiện và khuyến mãi
- Trạng thái hợp đồng: mới tạo / đã thanh toán / đã giao xe / đã hủy
- In hợp đồng dưới dạng PDF chuyên nghiệp

### 1.5 Quản lý kho xe

**Mô tả**: Theo dõi số lượng tồn kho và cảnh báo khi cần nhập hàng

**Chi tiết**:

- Cập nhật tồn kho tự động khi có hợp đồng mới
- Cảnh báo khi tồn kho dưới mức tối thiểu
- Lịch sử nhập kho từ nhà cung cấp

### 1.6 Báo cáo thống kê

**Mô tả**: Cung cấp các báo cáo kinh doanh theo nhiều chiều dữ liệu

**Chi tiết**:

- Doanh thu theo thời gian (ngày/tháng/năm)
- Top 10 xe bán chạy nhất
- Hiệu suất nhân viên theo KPI
- Khách hàng VIP theo tổng giá trị mua hàng

### 1.7 Hệ thống bảo mật

**Mô tả**: Đảm bảo an toàn thông tin và phân quyền truy cập

**Chi tiết**:

- Đăng nhập bằng tài khoản/mật khẩu
- Mã hóa mật khẩu theo chuẩn bcrypt
- Ghi log mọi hoạt động quan trọng
- Session timeout sau 30 phút không hoạt động

### 1.8 Quản lý Bảo hành

**Mô tả**: Theo dõi và quản lý thông tin bảo hành cho từng xe đã bán

**Chi tiết**:

- Ghi nhận thông tin bảo hành khi tạo hợp đồng: thời hạn bảo hành (tháng), phạm vi bảo hành
- Theo dõi lịch sử bảo hành của từng xe theo khách hàng
- Cảnh báo bảo hành sắp hết hạn (trước 30 ngày)
- Ghi nhận yêu cầu bảo hành: ngày đến bảo hành, nội dung sửa chữa, chi phí (nếu có)
- Phân loại yêu cầu bảo hành: bảo hành miễn phí / sửa chữa tính phí
- In phiếu bảo hành và biên lai sửa chữa
- Thống kê chi phí bảo hành theo thời gian

### 1.9 Quản lý Khuyến mãi

**Mô tả**: Tạo và quản lý các chương trình khuyến mãi cho xe

**Chi tiết**:

- Tạo chương trình khuyến mãi: tên KM, mô tả, thời gian áp dụng (từ ngày - đến ngày)
- Loại khuyến mãi: giảm giá tiền mặt / tặng phụ kiện / giảm lãi suất trả góp / combo
- Áp dụng KM cho: toàn bộ xe / hãng xe cụ thể / dòng xe cụ thể / xe tồn kho lâu
- Mức giảm giá: số tiền cố định hoặc phần trăm
- Theo dõi hiệu quả KM: số xe bán được với KM, doanh thu từ KM
- Tự động áp dụng KM khi tạo hợp đồng (nếu đủ điều kiện)
- Dừng/tạm dừng chương trình KM

### 1.10 Quản lý Phụ kiện

**Mô tả**: Quản lý danh mục phụ kiện đi kèm xe

**Chi tiết**:

- Danh mục phụ kiện: tên PK, mô tả, giá bán, tồn kho PK
- Phân loại PK: nội thất / ngoại thất / điện tử / bảo vệ / trang trí
- Tồn kho PK và cảnh báo khi hết
- Combo PK: gói PK đi kèm với giá ưu đãi
- Thêm PK vào hợp đồng với giá tính toán riêng

### 1.11 Quản lý Dịch vụ hậu mãi

**Mô tả**: Các dịch vụ sau bán hàng cho khách hàng

**Chi tiết**:

- Đặt lịch bảo dưỡng định kỳ: nhắc nhở khách hàng đến bảo dưỡng theo km/tháng
- Ghi nhận lịch sử bảo dưỡng: ngày bảo dưỡng, nội dung, chi phí
- Dịch vụ cứu hộ: ghi nhận yêu cầu cứu hộ, phản hồi, chi phí
- Chương trình chăm sóc khách hàng: gửi thiệp sinh nhật, ưu đãi tri ân

### 1.12 Quản lý Nhà cung cấp

**Mô tả**: Quản lý thông tin các nhà cung cấp xe và phụ kiện

**Chi tiết**:

- Thông tin NCC: tên, địa chỉ, SĐT, email, người liên hệ
- Lịch sử nhập hàng từ NCC: ngày nhập, số lượng, giá nhập
- Đánh giá NCC: chất lượng, thời gian giao hàng, giá cả
- Đơn đặt hàng: tạo đơn đặt hàng xe/PK từ NCC

### 1.13 Quản lý Trả góp

**Mô tả**: Hỗ trợ quản lý thông tin trả góp cho khách hàng

**Chi tiết**:

- Thông tin trả góp: ngân hàng cho vay, số tiền vay, lãi suất, thời hạn
- Tính toán số tiền trả hàng tháng
- Theo dõi tiến độ trả góp: số tiền còn nợ, số kỳ còn lại
- Cảnh báo chậm trả

### 1.14 Quản lý Marketing

**Mô tả**: Các hoạt động tiếp thị và quảng cáo

**Chi tiết**:

- Chiến dịch marketing: tên chiến dịch, ngân sách, thời gian, kênh tiếp thị
- Theo dõi hiệu quả: số khách hàng tiềm năng, chuyển đổi thành khách mua
- Sự kiện: tổ chức sự kiện lái thử, triển lãm xe
- Quản lý lead: khách hàng tiềm năng từ quảng cáo

### 1.15 Quản lý Khiếu nại

**Mô tả**: Xử lý khiếu nại từ khách hàng

**Chi tiết**:

- Ghi nhận khiếu nại: nội dung, ngày khiếu nại, mức độ (thấp/trung bình/cao)
- Phân công xử lý cho nhân viên phụ trách
- Theo dõi tiến độ xử lý: đang xử lý / đã giải quyết / đã đóng
- Đánh giá mức độ hài lòng sau xử lý
- Báo cáo thống kê khiếu nại theo loại, thời gian

---

## 2. YÊU CẦU PHI CHỨC NĂNG

### 2.1 Hiệu năng

- Thời gian phản hồi tìm kiếm xe: ≤ 2 giây với cơ sở dữ liệu 10.000 bản ghi
- Thời gian tải danh sách khách hàng: ≤ 1 giây
- Hỗ trợ đồng thời 50 người dùng

### 2.2 Độ tin cậy

- Tỷ lệ lỗi hệ thống: < 0.1%
- Dữ liệu được backup tự động hàng ngày
- Khả năng phục hồi sau sự cố: ≤ 15 phút

### 2.3 Bảo mật

- Tuân thủ nguyên tắc least privilege (phân quyền tối thiểu)
- Mã hóa dữ liệu nhạy cảm khi lưu trữ
- Không lưu trữ mật khẩu dưới dạng plain text
- Audit trail cho mọi thay đổi dữ liệu quan trọng

### 2.4 Khả năng sử dụng

- Giao diện thân thiện, dễ sử dụng cho người không rành công nghệ
- Hỗ trợ thao tác bằng bàn phím và chuột
- Có hướng dẫn sử dụng tích hợp trong hệ thống
- Thời gian đào tạo nhân viên mới: ≤ 2 giờ

### 2.5 Khả năng bảo trì

- Mã nguồn được comment đầy đủ bằng tiếng Việt
- Kiến trúc module, dễ mở rộng tính năng
- Có unit test cho các hàm nghiệp vụ chính
- Tài liệu kỹ thuật đầy đủ

### 2.6 Tính khả chuyển

- Chạy được trên Windows, Linux, macOS
- Không phụ thuộc vào phiên bản hệ điều hành cụ thể
- Dễ dàng di chuyển cơ sở dữ liệu sang hệ thống khác
