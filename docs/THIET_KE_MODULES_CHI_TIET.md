# MÔ TẢ THIẾT KẾ MODULES CHI TIẾT

---

## 1. Kiến trúc tổng thể hệ thống

Hệ thống được xây dựng theo mô hình Clean Architecture với bốn tầng rõ ràng. Tầng Presentation chứa toàn bộ giao diện PyQt6 bao gồm các màn hình chính, hộp thoại và widgets tái sử dụng. Tầng Application chứa các Service xử lý logic nghiệp vụ và là cầu nối giữa Presentation và Domain. Tầng Domain chứa các Entity được biểu diễn dưới dạng dataclass Python với các phương thức chuyển đổi dữ liệu. Tầng Infrastructure chứa các Repository truy cập cơ sở dữ liệu, các thư viện bên ngoài như PdfRenderer và ExcelExporter, cùng với các module bảo mật.

Dòng dữ liệu trong hệ thống tuân theo nguyên tắc phụ thuộc one-way: Presentation gọi Application, Application gọi Domain và Infrastructure, nhưng không theo chiều ngược lại. Điều này đảm bảo rằng tầng Domain và Infrastructure có thể hoạt động độc lập mà không phụ thuộc vào giao diện người dùng, giúp việc kiểm thử và bảo trì trở nên dễ dàng hơn.

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                    │
│  MainWindow, Sidebar, ContentArea, StatusBar             │
│  VehicleListScreen, ContractListScreen, BaoHanhScreen   │
└──────────────────────────┬──────────────────────────────┘
                           │ gọi
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                      │
│  XeService, HopDongService, BaoHanhService, AuthService  │
│  KhachHangService, BaoDuongService, KhieuNaiService      │
└──────────────────────────┬──────────────────────────────┘
                           │ gọi
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                        │
│  NhanVien, Xe, KhachHang, HopDong, BaoHanh, KhieuNai    │
│  BaseEntity (id, created_at, updated_at, created_by)     │
└──────────────────────────┬──────────────────────────────┘
                           │ gọi
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                    │
│  XeRepository, HopDongRepository, BaoHanhRepository     │
│  PasswordHasher (bcrypt), PdfRenderer, ExcelExporter     │
│  Database Connection (SQLite), MigrationRunner           │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Bảng tổng hợp cấu trúc các module

| Module              | Entity (Domain)        | Repository         | Service (Application)    | Screen chính                    |
| ------------------- | ---------------------- | ------------------ | ------------------------ | ------------------------------- |
| Xác thực & Phân quyền | NhanVien, VaiTro       | NhanVienRepository | AuthService              | LoginScreen, ChangePasswordDialog |
| Quản lý Xe          | Xe                     | XeRepository       | XeService                | VehicleListScreen, VehicleFormDialog |
| Quản lý Khách hàng  | KhachHang              | KhachHangRepository | KhachHangService         | CustomerListScreen, CustomerFormDialog |
| Quản lý Nhân viên   | NhanVien               | NhanVienRepository | NhanVienService          | EmployeeListScreen, EmployeeFormDialog |
| Quản lý Hợp đồng    | HopDong                | HopDongRepository  | HopDongService           | ContractListScreen, ContractDetailScreen, ContractWizardDialog |
| Quản lý Kho xe      | Xe                     | XeRepository       | KhoService               | InventoryOverviewScreen         |
| Quản lý Phụ kiện    | PhuKien, ComboPhuKien  | PhuKienRepository  | PhuKienService           | AccessoryListScreen, ComboManagerScreen |
| Quản lý Khuyến mãi  | KhuyenMai              | KhuyenMaiRepository | KhuyenMaiService         | PromoListScreen, PromoFormDialog |
| Quản lý Bảo hành    | BaoHanh                | BaoHanhRepository  | BaoHanhService           | WarrantyListScreen, WarrantyDetailScreen, WarrantyRequestFormDialog |
| Quản lý Bảo dưỡng   | BaoDuong               | BaoDuongRepository  | BaoDuongService          | MaintenanceScheduleScreen, MaintenanceFormDialog |
| Quản lý Trả góp     | TraGop                 | TraGopRepository   | TraGopService            | InstallmentListScreen, InstallmentCreateDialog |
| Quản lý Nhà cung cấp | NhaCungCap             | NhaCungCapRepository | NhaCungCapService       | SupplierListScreen, SupplierFormDialog |
| Quản lý Khiếu nại   | KhieuNai               | KhieuNaiRepository | KhieuNaiService          | ComplaintListScreen, ComplaintDetailScreen |
| Quản lý Marketing   | ChienDichMk, Lead      | LeadRepository     | ChienDichMkService, LeadService | MarketingScreen, LeadManagerScreen |
| Quản lý Bảo hiểm    | BaoHiem, CongTyBH      | BaoHiemRepository  | BaoHiemService           | BaoHiemListScreen, BaoHiemFormDialog |
| Báo cáo & Thống kê  | (nhiều entity)         | (nhiều repository) | BaoCaoService, DashboardService | ReportsHubScreen, RevenueReportScreen, TopVehiclesReportScreen |
| Hệ thống            | SystemSettings, AuditLog | (qua service)      | SystemSettingsService, AuditLogService | SystemSettingsScreen, AuditLogScreen |

---

## 3. Chi tiết thiết kế từng module

### 3.1. Module Xác thực và Phân quyền

Module xác thực và phân quyền là module nền tảng nhất của hệ thống, đảm bảo rằng chỉ những người dùng hợp lệ mới có thể truy cập vào phần mềm. Entity NhanVien lưu trữ thông tin đăng nhập bao gồm username, mat_khau_hash được mã hóa bằng bcrypt, ho_ten, email, so_dien_thoai và vai_tro_id tham chiếu đến bảng vai_tro. Entity VaiTro lưu trữ ba vai trò chính với ma_vai_tro là A-01 cho quản trị viên, A-02 cho nhân viên bán hàng và A-03 cho nhân viên kỹ thuật bảo hành.

Service AuthService xử lý toàn bộ logic liên quan đến đăng nhập và đăng xuất. Khi người dùng nhập tài khoản và mật khẩu, AuthService kiểm tra xem tài khoản có tồn tại hay không, kiểm tra trạng thái tài khoản có đang hoạt động hay không, kiểm tra xem tài khoản có bị khóa tạm thời do nhập sai mật khẩu nhiều lần hay không, và so sánh mật khẩu nhập vào với giá trị hash đã lưu trong cơ sở dữ liệu. Sau khi đăng nhập thành công, AuthService tạo một phiên làm việc (session) với thông tin người dùng và lưu trữ trong SessionManager. Phiên làm việc có thời hạn 30 phút và tự động hết hạn nếu người dùng không thao tác trong khoảng thời gian đó.

Repository NhanVienRepository kế thừa từ BaseRepository và cung cấp các thao tác CRUD tiêu chuẩn cùng với các phương thức tìm kiếm riêng như find_by_username để tìm nhân viên theo tên đăng nhập. Module cũng bao gồm PasswordHasher sử dụng bcrypt với chi phí tính toán là 12 để mã hóa mật khẩu, đảm bảo rằng ngay cả khi cơ sở dữ liệu bị lộ, mật khẩu gốc cũng không thể bị khôi phục.

**Sơ đồ luồng đăng nhập:**

```
Người dùng nhập username và password
           │
           ▼
AuthService.find_by_username(username)
           │
           ▼
Tài khoản tồn tại? ── Không ──► Trả về lỗi USER_NOT_FOUND
           │
           Có
           ▼
Tài khoản có trạng thái active? ── Không ──► Trả về lỗi ACCOUNT_INACTIVE
           │
           Có
           ▼
Tài khoản có bị khóa? ── Có ──► Kiểm tra thời gian khóa ── Còn khóa ──► Trả về lỗi ACCOUNT_LOCKED
           │                                                                    │
           │                                                           Hết khóa ──► Mở khóa tài khoản
           │                                                                │
           Không                                                         ▼
           ▼                                                        Tiếp tục kiểm tra
PasswordHasher.verify(password, hash)
           │
           ▼
Mật khẩu đúng? ── Không ──► Tăng lan_dang_nhap_sai ──► = 5? ──► Khóa tài khoản 15 phút ──► Trả về lỗi WRONG_PASSWORD
           │                                                                              │
           Có                                                                           Không
           ▼                                                                                  ▼
Đăng nhập thành công ──► Tạo CurrentSession ──► Ghi audit log ──► Chuyển đến MainWindow
```

### 3.2. Module Quản lý Xe

Entity Xe biểu diễn thông tin của từng chiếc xe trong kho đại lý với các thuộc tính bao gồm ma_xe là mã định danh duy nhất, hang là hãng sản xuất như Toyota, Honda, Ford, dong_xe là tên dòng xe cụ thể, nam_san_xuat, mau_sac, gia_ban, so_luong_ton và trang_thai có thể là con_hang, da_ban hoặc sap_ve. Entity cũng có muc_toi_thieu để đặt ngưỡng cảnh báo tồn kho thấp và ngay_nhap_dau_tien để theo dõi ngày nhập xe đầu tiên vào kho.

Repository XeRepository cung cấp các thao tác CRUD tiêu chuẩn và bổ sung các phương thức tìm kiếm nâng cao như find_by_hang để tìm xe theo hãng, find_available để tìm các xe còn hàng sẵn sàng bán, và find_low_stock để tìm các xe có số lượng tồn dưới mức tối thiểu. Service XeService xử lý logic nghiệp vụ bao gồm việc thêm xe mới vào kho, cập nhật thông tin xe, và quan trọng nhất là tự động cập nhật trạng thái xe khi có hợp đồng được tạo hoặc hủy bỏ.

Khi một hợp đồng bán xe được tạo thành công, XeService nhận được thông báo và giảm so_luong_ton của xe đó đi một đơn vị. Nếu so_luong_ton giảm xuống bằng hoặc thấp hơn muc_toi_thieu, hệ thống sẽ gửi cảnh báo cho quản lý biết để kịp thời nhập thêm xe. Khi một hợp đồng bị hủy, XeService hoàn trả xe về trạng thái con_hang và tăng so_luong_ton trở lại. Việc chỉnh sửa xe cho phép cập nhật mọi thông tin trừ ma_xe vì mã xe là định danh cố định không thay đổi theo thời gian. Khi xóa xe, hệ thống kiểm tra xem xe đó có hợp đồng liên quan hay không, nếu có thì từ chối xóa để bảo toàn dữ liệu lịch sử.

### 3.3. Module Quản lý Khách hàng

Entity KhachHang lưu trữ thông tin khách hàng bao gồm ho_ten, so_dien_thoai, email, dia_chi, ngay_sinh, phan_loai có thể là Thuong, Silver, Gold hoặc VIP dựa trên tổng giá trị mua hàng, tong_gia_tri_mua và so_xe_da_mua. Thuộc tính trang_thai cho phép đánh dấu khách hàng không còn hoạt động mà không xóa hẳn để giữ lại lịch sử giao dịch.

Repository KhachHangRepository cung cấp phương thức find_by_phone để tìm khách hàng theo số điện thoại vì số điện thoại là trường duy nhất trong hệ thống. Phương thức search cho phép tìm kiếm theo nhiều tiêu chí kết hợp. Service KhachHangService xử lý logic phân loại khách hàng tự động dựa trên tổng giá trị mua hàng tích lũy. Theo quy tắc BR-CALC-03, khách hàng được phân loại như sau: khách hàng thường (Tổng giá trị dưới 500 triệu), khách hàng bạc (Từ 500 triệu đến dưới 1 tỷ), khách hàng vàng (Từ 1 tỷ đến dưới 2 tỷ), và khách hàng VIP (Từ 2 tỷ trở lên). Mỗi khi có hợp đồng mới được tạo hoặc hủy bỏ, KhachHangService tự động cập nhật lại phân loại của khách hàng liên quan.

Khi tạo mới khách hàng, hệ thống kiểm tra trường so_dien_thoai đã tồn tại trong cơ sở dữ liệu hay chưa để đảm bảo không có hai khách hàng cùng số điện thoại. Email được kiểm tra định dạng hợp lệ theo chuẩn BR-DATA-04 và số điện thoại phải theo định dạng Việt Nam theo BR-DATA-05. Khi xóa khách hàng, hệ thống kiểm tra xem khách hàng có hợp đồng liên quan hay không, nếu có thì chỉ cho phép đánh dấu trạng_thai thành inactive thay vì xóa hoàn toàn.

### 3.4. Module Quản lý Hợp đồng

Entity HopDong là một trong những entity phức tạp nhất của hệ thống, chứa đựng toàn bộ thông tin về giao dịch mua bán xe. Các thuộc tính bao gồm ma_hop_dong được định dạng tự động HD<YYYY>-<NNNN>, các khóa ngoại khach_hang_id, xe_id, nhan_vien_id và khuyen_mai_id, các trường tiền gia_xe, tong_gia_phu_kien, tien_giam_km và tong_tien để theo dõi giá trị hợp đồng, trang_thai có thể là moi_tao, da_thanh_toan, da_giao_xe hoặc huy, các trường ngày tháng ngay_tao, ngay_thanh_toan, ngay_giao_xe, và ly_do_huy để ghi nhận lý do hủy nếu có.

Repository HopDongRepository cung cấp phương thức find_by_ma_hop_dong để tìm hợp đồng theo mã, phương thức next_ma_hop_dong để tự động tạo mã hợp đồng mới kế tiếp, và phương thức search với bộ lọc theo trang_thai, ngày tạo, khách hàng, nhân viên và từ khóa. Service HopDongService xử lý logic tạo hợp đồng mới với quy trình nhiều bước bao gồm kiểm tra xe còn hàng hay không, kiểm tra khách hàng đã tồn tại hay cần tạo mới, tạo mã hợp đồng tự động, tính toán tổng giá trị bao gồm phụ kiện và khuyến mãi, và khởi tạo thông tin bảo hành nếu hợp đồng có hình thức thanh toán trả góp thì khởi tạo TraGop.

Khi hợp đồng được tạo với hình thức thanh toán trả góp, HopDongService gọi TraGopService để tạo thông tin trả góp bao gồm ngân hàng, số tiền vay, lãi suất năm và số kỳ thanh toán. Hệ thống tính toán số tiền trả hàng tháng theo công thức tính toán tài chính chuẩn. Khi hợp đồng chuyển trạng thái sang da_thanh_toan, hệ thống tự động cập nhật trạng thái xe sang da_ban và giảm số lượng tồn kho. Khi hợp đồng bị huy, hệ thống hoàn trả xe về trạng thái con_hang và hủy bỏ thông tin bảo hành đã tạo.

### 3.5. Module Quản lý Bảo hành

Entity BaoHanh lưu trữ thông tin bảo hành của mỗi xe đã bán, bao gồm hop_dong_id và xe_id để liên kết với hợp đồng và xe tương ứng, khach_hang_id để biết ai là chủ sở hữu, thoi_han_bh tính bằng tháng, ngay_bat_dau và ngay_ket_thuc được tính tự động bằng cách cộng thoi_han_bh vào ngay_bat_dau sử dụng relativedelta từ python-dateutil, pham_vi ghi nhận phạm vi bảo hành, trang_thai có thể là con_hieu_luc hoặc het_hieu_luc, và các thông tin bổ sung cho bảo hành ngoài như so_khung, so_may và is_external.

Repository BaoHanhRepository cung cấp phương thức find_by_hop_dong để tìm bảo hành theo hợp đồng, phương thức find_expiring để tìm các bảo hành sắp hết hạn trong vòng 30 ngày phục vụ cho việc gửi cảnh báo, và phương thức find_by_xe để tìm lịch sử bảo hành theo xe. Entity BaoHanhYeuCau lưu trữ các yêu cầu bảo hành riêng biệt với ngay_yeu_cau, loai_yeu_cau có thể là sua_chua hoặc thay_the, mo_ta_tinh_trang, phan_loai là mien_phi hoặc tinh_phi, chi_phi và nhan_vien_id của nhân viên xử lý.

Service BaoHanhService xử lý logic phân loại yêu cầu bảo hành. Theo nguyên tắc BR-BH-04, hệ thống tự động phân loại yêu cầu thành miễn phí nếu nguyên nhân nằm trong lỗi của nhà sản xuất và tính phí nếu nguyên nhân do lỗi của khách hàng. Danh sách CUSTOMER_FAULT_KEYWORDS trong service bao gồm các từ khóa như va đập, ngập nước, tai nạn, sử dụng sai, không bảo dưỡng, tự sửa và rơi để hệ thống tự động nhận biết và phân loại. Khi có yêu cầu bảo hành mới, service kiểm tra xem xe còn trong thời hạn bảo hành hay không và sự cố có nằm trong phạm vi bảo hành hay không trước khi tiếp nhận.

**Sơ đồ luồng xử lý yêu cầu bảo hành:**

```
Khách hàng mang xe đến bảo hành
            │
            ▼
Nhân viên nhập thông tin yêu cầu BH
            │
            ▼
BaoHanhService.kiem_tra_dieu_kien_bh(xe_id, noi_dung)
            │
            ▼
Xe còn trong thời hạn BH? ── Không ──► Từ chối tiếp nhận ──► Thông báo cho khách hàng
            │
            Có
            ▼
Noi dung co trong pham vi BH? ── Không ──► Phân loại tinh_phi ──► Báo giá cho khách hàng
            │
            Có
            ▼
Duyệt từ khóa trong noi_dung_su_co
            │
            ▼
Khớp với CUSTOMER_FAULT_KEYWORDS? ── Có ──► Phân loại tinh_phi
            │
            Không
            ▼
Phân loại mien_phi
            │
            ▼
Tạo BaoHanhYeuCau ──► Ghi nhận chi phí (nếu có) ──► Cập nhật trạng thái xe
            │
            ▼
Hoàn tất tiếp nhận
```

### 3.6. Module Quản lý Khuyến mãi

Entity KhuyenMai lưu trữ thông tin chương trình khuyến mãi với ten_km, mo_ta, loai_km có thể là giam_tien_mat, giam_phan_tram, tang_phu_kien, giam_lai_suat hoặc combo, gia_tri là số tiền hoặc phần trăm giảm tùy theo kieu_gia_tri, tu_ngay và den_ngay xác định thời gian áp dụng, trang_thai có thể là nhap, dang_chay, tam_dung hoặc ket_thuc, và các trường so_luong_cho_phep và so_luong_da_su_dung để kiểm soát số lượng khuyến mãi có thể áp dụng.

Service KhuyenMaiService cung cấp logic tự động áp dụng khuyến mãi khi tạo hợp đồng. Khi HopDongService gọi đến để kiểm tra khuyến mãi áp dụng cho một xe cụ thể, KhuyenMaiService duyệt qua tất cả các chương trình khuyến mãi đang trong trạng thái dang_chay và kiểm tra xem xe có thỏa mãn điều kiện phạm vi áp dụng hay không. Phạm vi áp dụng có thể là toàn bộ xe, chỉ hãng nhất định, chỉ dòng xe nhất định, hoặc chỉ xe tồn kho lâu ngày (xe có ngay_nhap_dau_tien cách ngày hiện tại hơn một ngưỡng định sẵn). Hệ thống chọn khuyến mãi có lợi nhất cho khách hàng (ưu tiên khuyến mãi giảm nhiều nhất về số tiền) và tự động áp dụng vào hợp đồng.

### 3.7. Module Quản lý Trả góp

Entity TraGop lưu trữ thông tin trả góp của hợp đồng với hop_dong_id liên kết với hợp đồng, ngan_hang là tên ngân hàng hoặc công ty tài chính, so_tien_vay là số tiền khách hàng vay, lai_suat_nam là lãi suất hàng năm, so_ky là tổng số kỳ thanh toán, so_tien_tra_thang là số tiền phải trả mỗi tháng đã được tính toán, và trang_thai có thể là dang_tra hoặc da_tat_toan.

Service TraGopService xử lý logic tính toán số tiền trả hàng tháng theo công thức tài chính chuẩn. Công thức tính toán bao gồm phần gốc và phần lãi trong mỗi kỳ thanh toán, với số tiền gốc trả tăng dần theo thời gian và số tiền lãi giảm dần. Service cũng theo dõi tiến độ thanh toán và so sánh ngày thanh toán thực tế với ngày đến hạn. Nếu khách hàng thanh toán trễ hơn 5 ngày so với ngày đến hạn, hệ thống gửi cảnh báo để nhân viên chủ động liên hệ nhắc nhở. Khi tất cả các kỳ đã được thanh toán, trạng_thai của TraGop chuyển sang da_tat_toan.

### 3.8. Module Báo cáo và Dashboard

Module báo cáo và dashboard tổng hợp dữ liệu từ nhiều module khác nhau để cung cấp cái nhìn tổng quan về tình trạng kinh doanh của đại lý. Service DashboardService truy vấn dữ liệu tổng hợp từ các repository khác nhau để tính toán các chỉ số như tổng doanh thu trong ngày, tháng hoặc năm, số xe đã bán, số hợp đồng đang xử lý, và top nhân viên bán hàng. Service BaoCaoService cung cấp các báo cáo chi tiết theo yêu cầu bao gồm báo cáo doanh thu theo thời gian, báo cáo top xe bán chạy, báo cáo KPI nhân viên và báo cáo khách hàng VIP.

Repository trong module báo cáo sử dụng các truy vấn SQL phức tạp với JOIN và aggregation để tổng hợp dữ liệu. Ví dụ, báo cáo doanh thu theo tháng sử dụng GROUP BY theo tháng và SUM để tính tổng doanh thu. Báo cáo top xe sử dụng JOIN giữa bảng xe và bảng hợp đồng để đếm số lượng xe đã bán của từng dòng xe và sắp xếp giảm dần. Tất cả các báo cáo đều có thể xuất ra định dạng Excel thông qua ExcelExporter sử dụng thư viện openpyxl.

### 3.9. Module Quản lý Khiếu nại

Entity KhieuNai lưu trữ thông tin khiếu nại từ khách hàng bao gồm khach_hang_id, hop_dong_id tùy chọn để liên kết với hợp đồng liên quan, nhan_vien_xu_ly_id để phân công nhân viên xử lý, tieu_de và noi_dung mô tả nội dung khiếu nại, muc_do có thể là thap, trung_binh hoặc cao, nguon_goc cho biết khiếu nại đến từ đâu như khach_hang, nhan_vien hoặc khac, trang_thai có thể là moi, dang_xu_ly hoặc da_dong, và các trường ngay_xu_ly, ngay_dong để theo dõi tiến độ.

Service KhieuNaiService xử lý luồng xử lý khiếu nại từ khi tiếp nhận đến khi đóng. Khi tiếp nhận khiếu nại mới, service gán trạng_thai là moi và muc_do dựa trên nội dung. Quản lý có thể phân công khiếu nại cho nhân viên phụ trách và theo dõi tiến độ xử lý. Khi khiếu nại được giải quyết xong, nhân viên cập nhật ngay_xu_ly và trang_thai sang da_dong, đồng thời ghi nhận ly_do và danh_gia_hai_long từ khách hàng. Báo cáo khiếu nại thống kê theo loại và theo thời gian giúp đại lý nhận diện các vấn đề phổ biến.

### 3.10. Module Quản lý Phụ kiện và Combo

Entity PhuKien lưu trữ thông tin phụ kiện với ma_pk, ten_pk, phan_loai để phân loại thành nội thất, ngoại thất, điện tử, bảo vệ hoặc trang trí, gia_ban, ton_kho và mo_ta. Entity ComboPhuKien cho phép nhóm nhiều phụ kiện lại với nhau thành một gói combo có ten_combo và he_so_giam để áp dụng giảm giá cho cả gói thay vì từng phụ kiện riêng lẻ.

Service PhuKienService xử lý logic quản lý combo phụ kiện. Khi tạo hợp đồng, nhân viên có thể thêm phụ kiện vào đơn hàng với giá tính riêng cho từng sản phẩm hoặc chọn một combo để áp dụng giảm giá tự động cho toàn bộ gói. Hệ thống theo dõi tồn kho phụ kiện và cảnh báo khi tồn kho cạn kiệt. Khi phụ kiện được thêm vào hợp đồng, service tự động giảm ton_kho tương ứng.

---

## 4. Thiết kế cơ sở dữ liệu

Cơ sở dữ liệu SQLite với 35 bảng chính được thiết kế theo nguyên tắc chuẩn hóa để tránh dư thừa dữ liệu. Mỗi bảng có cột id là khóa chính tự động tăng, các cột created_at, updated_at và created_by để theo dõi thông tin quản lý. Khóa ngoại được sử dụng để liên kết các bảng có quan hệ với nhau và đảm bảo tính toàn vẹn dữ liệu. Cơ sở dữ liệu hỗ trợ các migration để cập nhật cấu trúc khi cần mở rộng.

**Sơ đồ quan hệ bảng chính:**

```
vai_tro (1) ────────< nhan_vien (N)
                         │
                         │
nha_cung_cap (1) ────────< nhap_kho (N)
                              │
                              │
khach_hang (1) ────────< hop_dong (N) ────────> xe (N)
                         │                         │
                         │                         │
                         ├──────< hop_dong_phu_kien (N) >── phu_kien (N)
                         │
                         │
                         ├──────< tra_gop (1)
                         │
                         │
                         └──────< bao_hanh (1)
                                    │
                                    │
                                    └──────< bao_hanh_yeu_cau (N)
```

---

## 5. Luồng điều hướng của ứng dụng

Ứng dụng được điều khiển thông qua NavigationRegistry và ModuleId. NavigationRegistry lưu trữ ánh xạ từ module ID đến class màn hình tương ứng, cho phép điều hướng động dựa trên lựa chọn của người dùng trên sidebar. MainWindow chứa QStackedWidget trong ContentArea để chứa các màn hình, khi người dùng click vào một mục menu sidebar, MainWindow sẽ tìm màn hình tương ứng và hiển thị trong ContentArea thay vì tạo mới hoàn toàn.

**Sơ đồ luồng điều hướng:**

```
Người dùng đăng nhập thành công
              │
              ▼
MainWindow hiển thị với Sidebar và ContentArea
              │
              ▼
Người dùng click vào mục menu Sidebar
              │
              ▼
NavigationRegistry.get_screen(module_id)
              │
              ▼
Tìm thấy screen_class? ── Không ──► Hiển thị thông báo "Chức năng đang phát triển"
              │
              Có
              ▼
ContentArea.setCurrentWidget(screen_instance)
              │
              ▼
Screen được hiển thị và sẵn sàng tương tác
```

---

## 6. Xử lý ngoại lệ và ghi log

Mỗi service định nghĩa các exception class riêng kế thừa từ base exception để xử lý các trường hợp lỗi cụ thể. Ví dụ, BaoHanhService có BaoHanhNotFoundError, InvalidStateTransitionError và ValidationError. Khi có lỗi xảy ra, service sẽ raise exception tương ứng và tầng presentation sẽ catch và hiển thị thông báo phù hợp cho người dùng.

AuditLogService ghi lại tất cả các hoạt động quan trọng trong hệ thống bao gồm đăng nhập, đăng xuất, tạo mới, chỉnh sửa và xóa dữ liệu. Mỗi audit log chứa nhan_vien_id của người thực hiện, hanh_dong mô tả hành động, bang_anh_huong cho biết bảng dữ liệu bị ảnh hưởng, ban_ghi_id của bản ghi liên quan, noi_dung chi tiết về thay đổi và thoi_gian là thời điểm thực hiện. Điều này tạo cơ sở để kiểm toán và truy vết khi có sự cố hoặc nghi ngờ về việc truy cập trái phép.

---

*Ngày cập nhật: Tháng 5 năm 2026*