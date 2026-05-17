# GIỚI THIỆU CÁC CÔNG CỤ XÂY DỰNG HỆ THỐNG

---

## 1. Tổng quan về công nghệ

Hệ thống Quản lý Đại lý Xe hơi được xây dựng trên nền tảng Python phiên bản 3.10 trở lên với giao diện desktop sử dụng PyQt6. Toàn bộ dữ liệu được lưu trữ trong SQLite, bảo mật mật khẩu bằng bcrypt, và xuất báo cáo qua Jinja2 kết hợp WeasyPrint. Kiểm thử được thực hiện bằng pytest, và định dạng mã nguồn tuân theo Black và isort. Các công cụ này kết hợp tạo thành một hệ thống hoàn chỉnh từ giao diện người dùng, xử lý nghiệp vụ, lưu trữ dữ liệu đến xuất báo cáo và kiểm thử tự động.

---

## 2. Bảng tổng hợp công cụ theo mục đích sử dụng

| Mục đích            | Công cụ                        | Phiên bản    | Vai trò trong hệ thống                                        |
| ------------------- | ------------------------------ | ------------ | ------------------------------------------------------------- |
| Ngôn ngữ lập trình  | Python                         | 3.10+        | Ngôn ngữ nền tảng cho toàn bộ ứng dụng                         |
| Giao diện người dùng | PyQt6                          | 6.6.1        | Xây dựng giao diện desktop đa chức năng                       |
| Cơ sở dữ liệu       | SQLite                         | Tích hợp sẵn | Lưu trữ dữ liệu quan hệ, không cần máy chủ riêng              |
| Bảo mật mật khẩu    | bcrypt                         | 4.2.0        | Mã hóa và xác thực mật khẩu người dùng                         |
| Xuất PDF            | Jinja2 + WeasyPrint            | 3.1.4 / 68.1 | Tạo mẫu và chuyển đổi hợp đồng, báo cáo sang định dạng PDF    |
| Xuất Excel          | openpyxl                       | 3.1.5        | Xuất báo cáo dữ liệu dưới dạng bảng tính Excel                |
| Kiểm thử            | pytest                         | Tích hợp sẵn | Chạy các bài test đơn vị và tích hợp                           |
| Định dạng mã        | Black + isort                  | 24.8 / 5.13  | Tự động format mã nguồn theo chuẩn thống nhất                 |
| Kiểm tra mã         | flake8                         | 7.1.1        | Phát hiện lỗi style và lỗi tiềm ẩn trong mã nguồn             |
| Quản lý mã nguồn    | Git + GitHub                   | Tích hợp sẵn | Theo dõi thay đổi, quản lý nhánh và hợp nhất mã              |
| Đóng gói ứng dụng   | PyInstaller (tùy chọn)        | Tùy chọn     | Đóng gói thành file chạy .exe phân phối tại showroom          |

---

## 3. Chi tiết từng công cụ

### 3.1. Ngôn ngữ Python

Python là ngôn ngữ lập trình chính được sử dụng cho toàn bộ hệ thống, từ logic nghiệp vụ đến giao diện người dùng và truy xuất cơ sở dữ liệu. Phiên bản khuyến nghị là 3.10 hoặc 3.11 vì các phiên bản này cung cấp hiệu năng tốt và tương thích với hầu hết các thư viện trong hệ thống. Python được chọn vì cú pháp rõ ràng, dễ đọc, và có hệ sinh thái thư viện phong phú phù hợp với các yêu cầu nghiệp vụ của đề tài.

### 3.2. PyQt6 cho giao diện desktop

PyQt6 là thư viện tạo giao diện người dùng desktop mạnh mẽ, cho phép xây dựng các cửa sổ ứng dụng phức tạp với nhiều thành phần như bảng dữ liệu, biểu mẫu nhập liệu, hộp thoại, và thanh điều hướng. Trong hệ thống này, PyQt6 được sử dụng để xây dựng toàn bộ giao diện bao gồm màn hình đăng nhập, màn hình chính với sidebar và content area, các màn hình quản lý xe, khách hàng, hợp đồng, bảo hành, bảo dưỡng, khiếu nại và báo cáo. PyQt6 hỗ trợ tốt việc tạo các bảng dữ liệu với khả năng sắp xếp, lọc và phân trang, phù hợp với yêu cầu quản lý danh sách lớn trong nghiệp vụ đại lý xe.

### 3.3. SQLite cho lưu trữ dữ liệu

SQLite là hệ quản trị cơ sở dữ liệu quan hệ nhẹ, được tích hợp sẵn trong Python thông qua module sqlite3, không yêu cầu cài đặt máy chủ riêng biệt. Cơ sở dữ liệu được lưu trữ trong file data/car_management.db, phù hợp với quy mô dữ liệu của một đại lý xe và dễ dàng sao lưu bằng cách copy file. SQLite hỗ trợ đầy đủ các tính năng cần thiết bao gồm khóa ngoại, giao dịch (transaction), và các hàm tính toán tổng hợp phục vụ cho báo cáo.

### 3.4. bcrypt cho bảo mật mật khẩu

Thư viện bcrypt được sử dụng để mã hóa mật khẩu người dùng trước khi lưu vào cơ sở dữ liệu. bcrypt sử dụng thuật toán băm có chi phí tính toán cao, khiến việc brute-force hoặc rainbow table attack trở nên không khả thi ngay cả khi cơ sở dữ liệu bị lộ. Điều này đảm bảo rằng ngay cả quản trị viên cơ sở dữ liệu cũng không thể đọc được mật khẩu gốc của người dùng.

### 3.5. Jinja2 và WeasyPrint cho xuất PDF

Jinja2 là công cụ tạo mẫu (template engine) cho phép thiết kế các mẫu HTML có cấu trúc rõ ràng, sau đó điền dữ liệu động vào để tạo nội dung hoàn chỉnh. WeasyPrint chuyển đổi HTML thành PDF với chất lượng in chuyên nghiệp. Trong hệ thống, hai công cụ này kết hợp để xuất hợp đồng mua bán xe và phiếu bảo hành dưới dạng PDF, đảm bảo định dạng nhất quán và chuyên nghiệp như khi in từ phần mềm Word.

### 3.6. openpyxl cho xuất Excel

Thư viện openpyxl cho phép tạo và ghi các tệp Excel với định dạng bảng tính bao gồm ô, cột, hàng, và các công thức tính toán. Hệ thống sử dụng openpyxl để xuất các báo cáo như báo cáo doanh thu, báo cáo tồn kho, và báo cáo KPI nhân viên dưới dạng tệp Excel mà người quản lý có thể mở và phân tích thêm trong Microsoft Excel hoặc Google Sheets.

### 3.7. pytest cho kiểm thử

pytest là framework kiểm thử phổ biến trong cộng đồng Python, cho phép viết và chạy các bài test đơn vị và test tích hợp. Hệ thống sử dụng pytest với các marker để phân loại test theo loại, bao gồm test nhanh cho truy vấn SELECT, test workflow cho các quy trình nghiệp vụ từ đầu đến cuối, và test hiệu năng cho các truy vấn phức tạp. Các test workflow đặc biệt quan trọng vì chúng mô phỏng các quy trình nghiệp vụ thực tế như nhập kho xe mới, tạo hợp đồng bán xe, xử lý bảo hành, và hủy hợp đồng.

### 3.8. Black và isort cho định dạng mã nguồn

Black là công cụ tự động định dạng mã Python theo chuẩn thống nhất, giúp loại bỏ các tranh luận về style code trong nhóm phát triển. isort tự động sắp xếp các câu lệnh import theo thứ tự chuẩn, giúp mã nguồn dễ đọc và nhất quán hơn. Hai công cụ này được tích hợp vào pre-commit để tự động chạy mỗi khi lập trình viên commit mã, đảm bảo chất lượng mã nguồn trước khi đưa vào repository.

### 3.9. flake8 cho kiểm tra mã

flake8 là công cụ linting giúp phát hiện các lỗi về style, các vấn đề tiềm ẩn như biến không được sử dụng, import không cần thiết, và các anti-pattern trong mã nguồn. flake8 được cấu hình với độ dài dòng tối đa 88 ký tự, phù hợp với cài đặt của Black, giúp duy trì mã nguồn sạch và giảm thiểu các lỗi có thể phát sinh do style không nhất quán.

---

## 4. Quy trình phát triển tích hợp các công cụ

Trong quá trình phát triển, các công cụ được tích hợp theo quy trình sau đây. Khi lập trình viên viết mã mới, mã được định dạng tự động bằng Black và isort trước khi commit thông qua pre-commit hook. Sau khi commit, flake8 kiểm tra lại mã lần cuối để phát hiện các vấn đề còn sót. CI/CD (nếu được thiết lập) sẽ chạy pytest để đảm bảo tất cả các test đều passed trước khi mã được merge vào nhánh chính. Khi cần phát hành, PyInstaller đóng gói toàn bộ ứng dụng thành file .exe để triển khai tại showroom hoặc cài đặt trên máy tính của nhân viên.

---

## 5. Lý do chọn các công cụ này

Các công cụ được chọn dựa trên nguyên tắc tối giản và phù hợp với quy mô dự án. Python với PyQt6 là sự kết hợp mạnh mẽ cho ứng dụng desktop có giao diện phức tạp. SQLite không yêu cầu cài đặt máy chủ riêng, phù hợp với đại lý xe có quy mô vừa và nhỏ, không cần đầu tư hạ tầng cơ sở dữ liệu phức tạp. bcrypt đảm bảo mật khẩu được bảo vệ theo tiêu chuẩn hiện đại. Jinja2 và WeasyPrint cung cấp giải pháp xuất PDF chuyên nghiệp mà không cần sử dụng phần mềm đắt tiền. pytest, Black, isort và flake8 là các công cụ kiểm thử và định dạng phổ biến, dễ tích hợp và có cộng đồng hỗ trợ mạnh.

Tất cả các công cụ này đều miễn phí và mã nguồn mở, giảm thiểu chi phí license cho dự án. Đồng thời chúng đều có tài liệu phong phú và được sử dụng rộng rãi trong ngành phần mềm, giúp việc tìm kiếm hỗ trợ khi gặp vấn đề trở nên dễ dàng hơn.

---

*Ngày cập nhật: Tháng 5 năm 2026*