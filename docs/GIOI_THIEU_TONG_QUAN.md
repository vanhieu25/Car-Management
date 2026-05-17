# GIỚI THIỆU TỔNG QUAN ĐỀ TÀI

## PHẦN MỀM QUẢN LÝ ĐẠI LÝ XE HƠI

---

### 1. Tổng quan dự án

Phần mềm Quản lý Đại lý Xe hơi là một ứng dụng desktop được phát triển nhằm hỗ trợ toàn diện các hoạt động kinh doanh của một đại lý xe hơi. Hệ thống được thiết kế để quản lý từ khâu nhập kho xe mới, bán xe có hoặc không trả góp, đến các dịch vụ hậu mãi như bảo hành, bảo dưỡng, và xử lý khiếu nại. Ngoài ra, phần mềm còn tích hợp các công cụ marketing, theo dõi khách hàng tiềm năng, và báo cáo doanh thu theo thời gian thực.

Dự án được xây dựng với mục tiêu số hóa quy trình quản lý đại lý, giảm thiểu thao tác thủ công, hạn chế sai sót trong tính toán, và cung cấp thông tin quản lý một cách nhanh chóng và chính xác.

---

### 2. Mục tiêu của đề tài

Mục tiêu chính của đề tài là xây dựng một hệ thống phần mềm cho phép nhân viên và quản lý đại lý xe hơi thực hiện các công việc hàng ngày một cách hiệu quả. Hệ thống giúp tự động hóa các quy trình nghiệp vụ, từ việc tạo hợp đồng mua bán xe, tính toán giá trị lắp đặt trả góp, đến việc quản lý tồn kho và theo dõi lịch bảo dưỡng định kỳ cho khách hàng.

Một mục tiêu quan trọng khác là đảm bảo tính bảo mật và phân quyền rõ ràng giữa các vai trò người dùng. Hệ thống phân biệt giữa ba vai trò chính: quản trị viên có toàn quyền quản lý nhân viên và hệ thống, nhân viên bán hàng thực hiện các nghiệp vụ liên quan đến hợp đồng và khách hàng, và nhân viên kỹ thuật xử lý các công việc bảo hành, bảo dưỡng.

---

### 3. Các module chínc của hệ thống

Hệ thống bao gồm nhiều module phục vụ cho từng lĩnh vực nghiệp vụ cụ thể. Module quản lý kho xe cho phép theo dõi số lượng xe tồn kho, cập nhật trạng thái xe khi có hợp đồng mới, và cảnh báo khi tồn kho giảm xuống dưới mức tối thiểu. Module quản lý hợp đồng hỗ trợ tạo mới hợp đồng mua bán xe với các hình thức thanh toán khác nhau, bao gồm thanh toán một lần và trả góp qua ngân hàng hoặc công ty tài chính.

Module quản lý bảo hành cho phép tiếp nhận yêu cầu bảo hành từ khách hàng, phân loại miễn phí hoặc tính phí dựa trên điều kiện bảo hành, và theo dõi chi phí bảo hành theo từng thời kỳ. Module quản lý bảo dưỡng giúp lập lịch bảo dưỡng định kỳ và gửi nhắc nhở cho khách hàng trước khi đến hạn. Module quản lý khiếu nại xử lý các phản ánh của khách hàng về chất lượng sản phẩm hoặc dịch vụ.

Module marketing hỗ trợ tạo và quản lý các chiến dịch khuyến mãi, theo dõi hiệu quả của từng chương trình, và quản lý khách hàng tiềm năng từ nhiều nguồn khác nhau. Module báo cáo cung cấp các báo cáo tổng hợp về doanh thu, KPI nhân viên, top xe bán chạy, và tình trạng tồn kho.

---

### 4. Công nghệ sử dụng

Hệ thống được xây dựng trên nền tảng Python phiên bản 3.10 trở lên, kết hợp với PyQt6 để tạo giao diện người dùng desktop trực quan và thân thiện. Dữ liệu được lưu trữ trong SQLite, một hệ quản trị cơ sở dữ liệu quan hệ nhẹ và không yêu cầu cài đặt máy chủ riêng biệt.

Bảo mật mật khẩu được xử lý bằng thuật toán bcrypt với chi phí tính toán cao, đảm bảo mật khẩu không thể bị giải mã ngay cả khi bị lộ database. Việc xuất báo cáo PDF sử dụng Jinja2 làm công cụ tạo mẫu kết hợp với WeasyPrint để chuyển đổi sang định dạng PDF chuyên nghiệp. Dữ liệu Excel được xuất ra bằng thư viện openpyxl.

Mã nguồn tuân thủ kiến trúc Clean Architecture với bốn tầng chính: presentation cho giao diện người dùng, application cho logic nghiệp vụ, domain cho các đối tượng và quy tắc nghiệp vụ, và infrastructure cho việc truy cập dữ liệu. Kiến trúc này giúp mã nguồn dễ bảo trì, mở rộng và kiểm thử.

---

### 5. Đối tượng sử dụng

Hệ thống phục vụ bao gồm ba nhóm đối tượng chính. Quản trị viên là người có toàn quyền quản lý hệ thống, quản lý thông tin nhân viên, cấu hình các tham số nghiệp vụ, và xem các báo cáo tổng hợp. Nhân viên bán hàng sử dụng hệ thống để tạo hợp đồng, quản lý thông tin khách hàng, và theo dõi tình trạng thanh toán của các hợp đồng. Nhân viên kỹ thuật và bảo hành sử dụng hệ thống để tiếp nhận yêu cầu bảo hành, cập nhật lịch sử sửa chữa, và quản lý lịch bảo dưỡng cho khách hàng.

---

### 6. Quy trình nghiệp vụ chính

Quy trình nhập kho xe mới bắt đầu khi nhân viên tạo phiếu nhập kho với thông tin xe được cung cấp từ nhà cung cấp. Hệ thống tự động cập nhật số lượng tồn kho và ghi nhận lịch sử nhập hàng.

Quy trình bán xe chuẩn bao gồm các bước: chọn xe từ kho, nhập thông tin khách hàng, tạo hợp đồng với giá trị tự động tính toán bao gồm phụ kiện và khuyến mãi áp dụng, cập nhật trạng thái xe sang đã bán, và in hợp đồng PDF cho khách hàng.

Quy trình bán xe trả góp phức tạp hơn khi bao gồm thêm việc tính toán số tiền trả góp hàng tháng dựa trên lãi suất và thời hạn vay, theo dõi tiến độ thanh toán của khách hàng, và cảnh báo khi có khoản thanh toán trễ hạn.

Quy trình bảo hành được kích hoạt khi khách hàng yêu cầu bảo hành, hệ thống kiểm tra điều kiện bảo hành dựa trên thời hạn và loại sự cố, sau đó tạo phiếu bảo hành và cập nhật chi phí phát sinh.

---

### 7. Kết quả dự kiến

Hệ thống hoàn thiện sẽ cho phép quản lý toàn bộ hoạt động kinh doanh đại lý xe hơi từ một giao diện duy nhất. Các thông tin về xe, khách hàng, hợp đồng, bảo hành và bảo dưỡng được quản lý tập trung và cập nhật tự động. Quy trình nghiệp vụ được số hóa giúp giảm thiểu sai sót và tiết kiệm thời gian xử lý. Hệ thống báo cáo cung cấp cho quản lý cái nhìn tổng quan về tình trạng kinh doanh và hỗ trợ ra quyết định dựa trên dữ liệu thực tế.

---

*Ngày cập nhật: Tháng 5 năm 2026*