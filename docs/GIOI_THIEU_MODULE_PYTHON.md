# GIỚI THIỆU CÁC MODULE VÀ THƯ VIỆN PYTHON TRONG ĐỀ TÀI

---

## 1. Tổng quan

Đề tài Phần mềm Quản lý Đại lý Xe hơi sử dụng tổng cộng tám thư viện và module Python chính, mỗi thư viện phục vụ cho một nhóm nhiệm vụ riêng biệt trong hệ thống. Các thư viện này được chia thành ba nhóm theo chức năng: nhóm xây dựng giao diện và desktop, nhóm xử lý nghiệp vụ và dữ liệu, và nhóm xuất báo cáo. Mỗi thư viện đều đóng vai trò quan trọng và không thể thay thế trong kiến trúc tổng thể của hệ thống.

---

## 2. Bảng tổng hợp các module và thư viện

| Tên module/thư viện    | Phiên bản | Nhóm chức năng          | Nhiệm vụ chính trong đề tài                              |
| ---------------------- | --------- | ----------------------- | -------------------------------------------------------- |
| PyQt6                  | 6.6.1     | Giao diện desktop       | Xây dựng toàn bộ giao diện người dùng                    |
| PyQt6-WebEngine        | 6.11.0    | Giao diện web           | Hiển thị PDF preview trong ứng dụng                      |
| bcrypt                 | 4.2.0     | Bảo mật                 | Mã hóa và xác thực mật khẩu người dùng                   |
| Jinja2                 | 3.1.4     | Template               | Tạo mẫu HTML cho hợp đồng và phiếu bảo hành              |
| WeasyPrint             | 68.1      | Chuyển đổi PDF          | Chuyển đổi template HTML sang file PDF chuyên nghiệp    |
| openpyxl               | 3.1.5     | Xuất Excel              | Tạo và ghi file Excel cho báo cáo doanh thu và KPI       |
| Pillow                 | 10.4.0    | Xử lý hình ảnh          | Xử lý hình ảnh logo và biểu tượng trong ứng dụng         |
| python-dateutil        | 2.9.0     | Xử lý ngày tháng        | Tính toán ngày bảo hành, bảo dưỡng và hạn trả góp        |
| sqlite3 (built-in)     | Tích hợp  | Cơ sở dữ liệu           | Lưu trữ và truy vấn toàn bộ dữ liệu nghiệp vụ            |
| pytest (bên thứ ba)    | Tích hợp  | Kiểm thử                | Chạy unit test và integration test cho các module        |
| logging (built-in)      | Tích hợp  | Ghi log                 | Ghi log hệ thống, theo dõi hoạt động người dùng           |

---

## 3. Chi tiết từng module và thư viện

### 3.1. PyQt6 — Xây dựng giao diện desktop

PyQt6 là thư viện cốt lõi cho phần giao diện người dùng của toàn bộ hệ thống. Đây là bộ bindings Python cho Qt framework, cho phép tạo các ứng dụng desktop chuyên nghiệp với giao diện đồ họa phong phú. Trong đề tài này, PyQt6 được sử dụng để xây dựng hơn 50 màn hình và hộp thoại khác nhau, bao gồm màn hình đăng nhập, màn hình chính với thanh điều hướng sidebar, các màn hình danh sách xe, khách hàng, nhân viên, hợp đồng, bảo hành, bảo dưỡng, khiếu nại, và báo cáo. PyQt6 cung cấp các widget chuẩn như QTableView cho hiển thị danh sách dữ liệu có khả năng phân trang và sắp xếp, QDialog cho các hộp thoại modal, QFormLayout cho biểu mẫu nhập liệu, và QMessageBox cho các thông báo hệ thống. Kiến trúc Clean Architecture của đề tài cho phép tách biệt hoàn toàn phần giao diện (presentation layer) với phần logic nghiệp vụ (application layer), giúp việc bảo trì và mở rộng giao diện trở nên thuận tiện hơn.

### 3.2. PyQt6-WebEngine — Hiển thị nội dung PDF trong ứng dụng

PyQt6-WebEngine là thành phần bổ sung cho PyQt6, cho phép nhúng một trình duyệt web Chromium vào ứng dụng desktop. Trong đề tài này, PyQt6-WebEngine được sử dụng để hiển thị bản xem trước PDF trực tiếp trong ứng dụng thay vì mở một ứng dụng bên ngoài. Khi người dùng muốn xem hoặc in hợp đồng, hệ thống sử dụng WeasyPrint để tạo file PDF từ template, sau đó PyQt6-WebEngine tải và hiển thị file PDF đó trong một hộp thoại preview tích hợp trong ứng dụng. Người dùng có thể phóng to, thu nhỏ và cuộn trang mà không cần rời khỏi ứng dụng, tạo trải nghiệm liền mạch và chuyên nghiệp hơn so với việc mở PDF trong trình đọc mặc định của hệ điều hành.

### 3.3. bcrypt — Bảo mật mật khẩu người dùng

Thư viện bcrypt cung cấp thuật toán băm mật khẩu mạnh mẽ được thiết kế để chống lại các cuộc tấn công brute-force và rainbow table. Trong đề tài, bcrypt được sử dụng để mã hóa mật khẩu của tất cả nhân viên trước khi lưu vào cơ sở dữ liệu SQLite. Mỗi khi người dùng đăng nhập, mật khẩu họ nhập vào được băm bằng bcrypt và so sánh với giá trị đã lưu trong cơ sở dữ liệu. Thư viện này sử dụng chi phí tính toán (cost factor) là 12, nghĩa là mỗi lần băm mật khẩu cần thực hiện 2 mũ 12 (khoảng 4096) vòng tính toán. Điều này khiến việc thử tất cả các tổ hợp mật khẩu trở nên cực kỳ tốn thời gian, bảo vệ người dùng ngay cả khi cơ sở dữ liệu bị lộ hoàn toàn. Ngoài ra, bcrypt tự động thêm một giá trị salt ngẫu nhiên vào mỗi mật khẩu trước khi băm, đảm bảo rằng hai người dùng có cùng mật khẩu sẽ có các giá trị băm hoàn toàn khác nhau, ngăn chặn việc sử dụng rainbow table để giải mã hàng loạt mật khẩu cùng lúc.

### 3.4. Jinja2 — Tạo mẫu HTML cho tài liệu

Jinja2 là một template engine mạnh mẽ cho phép tách biệt phần thiết kế và phần dữ liệu của các tài liệu. Trong đề tài này, Jinja2 được sử dụng để thiết kế các template cho hợp đồng mua bán xe và phiếu bảo hành. Mỗi template là một file HTML chứa các placeholder như {{ ho_ten_khach }}, {{ ten_xe }}, {{ gia_ban }} và các cấu trúc logic như vòng lặp for để hiển thị danh sách phụ kiện hoặc khuyến mãi áp dụng. Khi hệ thống cần tạo một hợp đồng, dữ liệu thực tế từ cơ sở dữ liệu được truyền vào template, Jinja2 xử lý và sinh ra một file HTML hoàn chỉnh chứa đầy đủ thông tin của hợp đồng đó. Việc tách template ra khỏi mã Python cho phép nhóm phát triển dễ dàng chỉnh sửa định dạng tài liệu mà không cần thay đổi mã nguồn, và cho phép bộ phận khác có thể cập nhật mẫu hợp đồng mà không cần hiểu biết về lập trình.

### 3.5. WeasyPrint — Chuyển đổi HTML sang PDF

WeasyPrint là thư viện chuyển đổi HTML và CSS sang định dạng PDF với chất lượng in chuyên nghiệp. Trong đề tài, WeasyPrint nhận file HTML đã được Jinja2 điền đầy đủ dữ liệu và chuyển đổi thành file PDF để in hoặc gửi cho khách hàng. WeasyPrint hỗ trợ đầy đủ các thuộc tính CSS cho in ấn bao gồm page break, margin, header và footer cho mỗi trang, và tự động chia trang cho các nội dung dài. Điều này đảm bảo rằng hợp đồng và phiếu bảo hành được in ra có định dạng nhất quán với bố cục chuyên nghiệp, tương đương với việc sử dụng phần mềm Word để thiết kế nhưng có thể tự động hóa hoàn toàn từ dữ liệu trong cơ sở dữ liệu. Ngoài ra, WeasyPrint còn cho phép nhúng font tiếng Việt và hỗ trợ Unicode đầy đủ, đảm bảo các ký tự tiếng Việt trong hợp đồng hiển thị chính xác.

### 3.6. openpyxl — Xuất báo cáo Excel

Thư viện openpyxl cho phép tạo, đọc và chỉnh sửa các file Excel theo chuẩn OOXML (Office Open XML). Trong đề tài này, openpyxl được sử dụng để xuất các báo cáo doanh thu, báo cáo tồn kho, báo cáo KPI nhân viên và các báo cáo tổng hợp khác dưới dạng bảng tính Excel. Lớp ExcelExporter trong hệ thống sử dụng openpyxl để tạo các workbook với nhiều sheet, định dạng tiêu đề in đậm, cố định dòng tiêu đề khi cuộn, tự động điều chỉnh độ rộng cột, và định dạng số tiền VND với dấu phân cách hàng nghìn. File Excel được tạo ra có thể mở trực tiếp trong Microsoft Excel hoặc Google Sheets, cho phép quản lý phân tích chi tiết hơn bằng các công cụ quen thuộc hoặc chia sẻ với các bộ phận khác không sử dụng trực tiếp phần mềm quản lý đại lý.

### 3.7. Pillow — Xử lý hình ảnh trong ứng dụng

Pillow là thư viện xử lý hình ảnh mạnh mẽ, được sử dụng trong đề tài để xử lý các hình ảnh logo và biểu tượng hiển thị trong ứng dụng và trên các tài liệu PDF. Khi hệ thống khởi tạo, Pillow được dùng để tải và resize logo đại lý phù hợp với kích thước hiển thị trên giao diện và trên đầu trang hợp đồng PDF. Thư viện này hỗ trợ nhiều định dạng hình ảnh phổ biến như PNG, JPEG, BMP và GIF, cho phép hệ thống linh hoạt trong việc sử dụng logo ở nhiều định dạng khác nhau. Ngoài ra, Pillow còn được sử dụng để xử lý hình ảnh xe khi cần resize để hiển thị trong giao diện hoặc đính kèm vào báo cáo.

### 3.8. python-dateutil — Tính toán ngày tháng phức tạp

Thư viện python-dateutil cung cấp các hàm tiện ích mở rộng cho việc xử lý ngày tháng trong Python. Trong đề tài, python-dateutil được sử dụng chủ yếu để tính toán các ngày liên quan đến bảo hành và bảo dưỡng xe. Cụ thể, khi một hợp đồng được tạo, hệ thống sử dụng relativedelta từ python-dateutil để tính ngày kết thúc bảo hành bằng cách cộng thêm số tháng bảo hành vào ngày mua xe. Tương tự, lịch bảo dưỡng định kỳ được tính toán bằng cách cộng thêm khoảng thời gian từ lần bảo dưỡng trước đó. python-dateutil đặc biệt hữu ích khi xử lý các trường hợp đặc biệt như tính số ngày giữa hai mốc thời gian có độ dài thay đổi (ví dụ từ ngày 31 tháng 1 đến ngày 28 tháng 2), hoặc cộng thêm một khoảng thời gian có tháng và năm vào một ngày cụ thể. Thư viện này cũng hỗ trợ phân tích chuỗi ngày tháng từ nhiều định dạng khác nhau, giảm thiểu lỗi khi xử lý dữ liệu đầu vào từ người dùng.

### 3.9. sqlite3 — Lưu trữ dữ liệu quan hệ

Module sqlite3 là thư viện Python tích hợp sẵn cho phép làm việc với cơ sở dữ liệu SQLite. Trong đề tài này, sqlite3 là module nền tảng cho toàn bộ việc lưu trữ và truy vấn dữ liệu nghiệp vụ. Tất cả các thông tin về xe, khách hàng, nhân viên, hợp đồng, bảo hành, bảo dưỡng, khiếu nại, khuyến mãi và đại lý đều được lưu trữ trong cơ sở dữ liệu SQLite nằm trong file data/car_management.db. Hệ thống sử dụng các câu lệnh SQL chuẩn để thực hiện các thao tác CRUD (Create, Read, Update, Delete) trên tất cả các bảng. Khóa ngoại (foreign key) được bật theo mặc định để đảm bảo tính toàn vẹn dữ liệu giữa các bảng có quan hệ với nhau. Cơ sở dữ liệu SQLite không yêu cầu cài đặt máy chủ riêng biệt, phù hợp với mô hình triển khai desktop tại một đại lý xe, và việc sao lưu chỉ đơn giản bằng thao tác copy file.

### 3.10. pytest — Kiểm thử tự động

pytest là framework kiểm thử được sử dụng để viết và chạy các bài test đơn vị và test tích hợp cho hệ thống. Trong đề tài, pytest được sử dụng để kiểm thử các nghiệp vụ quan trọng như tính giá trị hợp đồng, phân loại khách hàng dựa trên tổng giá trị mua hàng, tính toán số tiền trả góp hàng tháng, và các quy trình workflow từ đầu đến cuối như tạo hợp đồng mới, xử lý bảo hành, và hủy hợp đồng. Hệ thống sử dụng các marker của pytest để phân loại test, bao gồm marker simple cho các test truy vấn SELECT nhanh, marker join_agg cho các test truy vấn phức tạp với JOIN và tính toán tổng hợp, marker wf01 đến wf08 cho các test workflow nghiệp vụ, và marker perf cho các test đo hiệu năng. pytest hỗ trợ fixture cho phép chia sẻ dữ liệu test giữa nhiều test case và tích hợp tốt với các công cụ CI/CD để chạy test tự động mỗi khi có thay đổi trong mã nguồn.

---

## 4. Mối quan hệ giữa các thư viện trong một quy trình nghiệp vụ

Để minh họa cách các thư viện phối hợp trong thực tế, xét quy trình tạo hợp đồng bán xe và xuất PDF. Đầu tiên, PyQt6 hiển thị giao diện tạo hợp đồng cho nhân viên nhập thông tin. Khi nhân viên chọn xe và khách hàng, PyQt6 gọi đến service layer sử dụng sqlite3 để truy vấn dữ liệu từ cơ sở dữ liệu. Khi hợp đồng được lưu, hệ thống sử dụng bcrypt để băm mật khẩu nếu cần thay đổi thông tin người dùng, và python-dateutil để tính toán ngày kết thúc bảo hành. Khi nhân viên yêu cầu in hợp đồng, Jinja2 lấy dữ liệu hợp đồng và điền vào template HTML, WeasyPrint chuyển đổi HTML thành PDF, PyQt6-WebEngine hiển thị PDF preview trong ứng dụng, và openpyxl cho phép xuất báo cáo doanh thu từ hợp đồng đó ra Excel. Toàn bộ quy trình sử dụng logging để ghi lại mọi thao tác phục vụ cho việc kiểm toán và debug.

---

*Ngày cập nhật: Tháng 5 năm 2026*