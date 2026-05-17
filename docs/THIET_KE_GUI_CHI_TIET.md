# MÔ TẢ THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG (GUI)

---

## 1. Cấu trúc bố cục chính

Giao diện chính của ứng dụng được thiết kế theo mô hình Apple-style layout với bố cục bốn vùng xếp dọc và ngang. Phía trên cùng là TopBar với chiều cao 44 pixel chứa logo đại lý, tên đại lý và thông tin người dùng kèm menu tùy chọn. Phía dưới TopBar là vùng nội dung chính được chia thành hai phần: Sidebar bên trái rộng 240 pixel chứa danh sách điều hướng các module, và ContentArea bên phải chiếm toàn bộ không gian còn lại hiển thị nội dung của module đang active. Phía dưới cùng là StatusBar với chiều cao 28 pixel hiển thị thông tin người dùng, thời gian hiện tại và trạng thái kết nối cơ sở dữ liệu. Kích thước tối thiểu của cửa sổ chính là 1280x720 pixel và kích thước mặc định khi khởi động là 1400x800 pixel.

```
┌───────────────────────────────────────────────────────────────┐
│  TOPBAR (44px)   │ Logo │ Dealer Name    │ User · Menu      │
├──────────────┬────────────────────────────────────────────────┤
│              │                                                │
│   SIDEBAR    │              CONTENTAREA                       │
│   (240px)    │           (QStackedWidget)                     │
│              │                                                │
├──────────────┴────────────────────────────────────────────────┤
│  STATUSBAR (28px)  │ User · Time · Version · DB Status       │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Các thành phần giao diện chính

TopBar được xây dựng từ widget TopBar chứa ba thành phần chính: nhóm bên trái gồm logo đại lý và tên đại lý, nhóm giữa là tiêu đề màn hình hiện tại, và nhóm bên phải chứa thông tin người dùng đang đăng nhập với avatar, tên và vai trò, cùng các nút thao tác đăng xuất, đổi mật khẩu và xem hồ sơ. Sidebar được xây dựng từ widget Sidebar hiển thị danh sách các module điều hướng dạng icon kèm nhãn, được nhóm theo danh mục và có mục active được highlight bằng màu nền #f5f5f7. Sidebar gửi signal module_selected khi người dùng click vào một mục menu, MainWindow nhận signal này và chuyển đổi màn hình trong ContentArea. ContentArea được xây dựng từ QStackedWidget cho phép chứa nhiều màn hình và chỉ hiển thị một màn hình tại một thời điểm, mỗi màn hình được đăng ký theo module_id và được quản lý thông qua phương thức register_screen và setCurrentWidget.

StatusBar hiển thị thông tin thời gian thực với username và vai trò của người dùng đang đăng nhập ở bên trái, phiên bản ứng dụng ở giữa và trạng thái kết nối cơ sở dữ liệu ở bên phải. Trạng thái kết nối cho biết cơ sở dữ liệu đang hoạt động bình thường hay có lỗi kết nối. StatusBar cũng hiển thị thời gian hiện tại và tự động cập nhật mỗi phút.

---

## 3. Các màn hình danh sách chính

Mỗi module trong hệ thống có một màn hình danh sách chính và các màn hình chi tiết hoặc hộp thoại đi kèm. Màn hình danh sách tiêu biểu bao gồm VehicleListScreen hiển thị danh sách xe với các cột thông tin và toolbar chức năng, CustomerListScreen hiển thị danh sách khách hàng, ContractListScreen hiển thị danh sách hợp đồng với bộ lọc trạng thái, WarrantyListScreen hiển thị danh sách bảo hành và cảnh báo sắp hết hạn. Các màn hình này đều có chung thiết kế với phần đầu chứa tiêu đề và các nút thao tác, phần thân chứa bảng dữ liệu QTableWidget với khả năng phân trang và sắp xếp, và phần cuối chứa tổng số bản ghi và các nút điều hướng phân trang. Toolbar phía trên bảng cho phép người dùng thực hiện các thao tác như thêm mới, tìm kiếm và xuất báo cáo.

---

## 4. Các hộp thoại và màn hình chi tiết

Hộp thoại (Dialog) được sử dụng cho các thao tác tạo mới và chỉnh sửa. VehicleFormDialog cho phép nhập thông tin xe mới hoặc chỉnh sửa thông tin xe hiện có với các trường nhập liệu được tổ chức theo nhóm và validate dữ liệu đầu vào. CustomerFormDialog cho phép tạo hoặc cập nhật thông tin khách hàng. ContractWizardDialog là một wizard gồm nhiều bước cho phép tạo hợp đồng mới với luồng chọn xe, nhập thông tin khách hàng, thêm phụ kiện và khuyến mãi, chọn hình thức thanh toán và xác nhận. WarrantyRequestFormDialog cho phép tiếp nhận yêu cầu bảo hành với các trường thông tin và phân loại tự động. Các hộp thoại đều có nút xác nhận và hủy bỏ, đóng gói validation và xử lý lỗi bên trong.

---

## 5. Phong cách thiết kế và màu sắc

Giao diện sử dụng phong cách thiết kế Apple với màu nền chính là trắng (#ffffff) và màu chữ là đen (#1d1d1f). Font chữ được sử dụng là hệ thống font tự nhiên của từng hệ điều hành thông qua thuộc tính font-family với giá trị fallback "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif". Màu nền hover của sidebar item là xám nhạt (#e8e8ed) và màu nền active là (#f5f5f7). Các nút bấm và input field sử dụng style sheet để đảm bảo tính nhất quán trên tất cả các hệ điều hành. Màu sắc cho các trạng thái được mã hóa cố định trong component StatusBadge với màu xanh lá cho trạng thái hoạt động, màu vàng cho trạng thái chờ và màu đỏ cho trạng thái cảnh báo hoặc hủy.

---

## 6. Luồng điều hướng và tương tác

Người dùng đăng nhập thành công sẽ được chuyển đến MainWindow với Sidebar hiển thị các module phù hợp với vai trò của người dùng. Khi click vào một mục trên Sidebar, signal module_selected được gửi đi kèm module_id, MainWindow nhận signal này và gọi NavigationRegistry để tìm screen class tương ứng, sau đó tạo instance của screen nếu chưa có hoặc chuyển đến screen đã tồn tại và hiển thị trong ContentArea bằng phương thức setCurrentWidget. Các signal quan trọng trong hệ thống bao gồm logout_requested được phát ra khi người dùng yêu cầu đăng xuất và module_changed được phát ra khi module active thay đổi. Ngoài ra, mỗi screen có thể phát signal để mở hộp thoại, ví dụ vehicle_list_screen phát signal để mở VehicleFormDialog khi người dùng click nút thêm mới hoặc chỉnh sửa.

---

*Ngày cập nhật: Tháng 5 năm 2026*