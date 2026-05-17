# Mô Tả Cấu Trúc Mã Nguồn - Hệ Thống Quản Lý Đại Lý Ô Tô

## 1. Tổng Quan

Đây là ứng dụng desktop Python/PyQt6 quản lý đại lý ô tô, sử dụng Clean Architecture gồm 4 tầng: presentation, application, domain, infrastructure. Ngôn ngữ giao diện và tài liệu là tiếng Việt. Stack công nghệ gồm Python 3.10+, PyQt6, SQLite, bcrypt, Jinja2 + WeasyPrint (PDF), openpyxl (Excel), pytest.

## 2. Cấu Trúc Thư Mục

Thư mục chính `app/` chứa 4 thư mục con. Thư mục `presentation/` chứa giao diện PyQt6 với hai thành phần: `screens/` chứa các màn hình chính (list, detail, dialog) và `widgets/` chứa các thành phần UI dùng chung như top_bar, sidebar, content_area, status_bar, inputs, buttons, dialogs. Thư mục `application/` chứa nghiệp vụ với `services/` chứa logic nghiệp vụ và `validators/` chứa các quy tắc validation. Thư mục `domain/` chứa các entities dưới dạng dataclass. Thư mục `infrastructure/` chứa hạ tầng gồm `database/` cho kết nối DB và migrations, `repositories/` cho data access layer, `exporters/` cho export Excel/PDF, và `security/` cho password hashing.

## 3. Entry Point - main.py

File `main.py` là điểm khởi đầu của ứng dụng. Đầu tiên chạy `MigrationRunner.run_pending()` để thực hiện migration tự động khi khởi động. Sau đó gọi `seed_if_empty()` để seed dữ liệu mẫu nếu database trống. Cuối cùng khởi tạo `Application` để quản lý luồng đăng nhập và hiển thị MainWindow. Tài khoản mặc định là admin/password123.

## 4. Tầng Domain

File `domain/entities/__init__.py` định nghĩa tất cả entities bằng `@dataclass`. BaseEntity là class cơ sở cung cấp các trường id, created_at, updated_at, created_by cùng methods `to_dict()` và `from_row()`. Các entity chính gồm: NhanVien (nhân viên với username, mat_khau_hash, ho_ten, vai_tro_id, trang_thai), VaiTro (vai trò với ma_vai_tro, ten_vai_tro), Xe (xe với ma_xe, hang, dong_xe, gia_ban, so_luong_ton), KhachHang (khách hàng với ho_ten, phan_loai, tong_gia_tri_mua), HopDong (hợp đồng với ma_hop_dong, tong_tien, trang_thai), PhuKien, ComboPhuKien, KhuyenMai, BaoHanh, BaoHiem, TraGop, NhaCungCap, ChienDichMk, Lead, KhieuNai, BaoDuong, CuuHo, DaiLy, CongTyBH, AuditLog, SystemSettings.

## 5. Tầng Infrastructure

### 5.1 Database Connection

File `infrastructure/database/connection.py` cung cấp factory pattern cho SQLite connection. Hỗ trợ WAL mode, foreign_keys, busy_timeout 30s. Cung cấp context manager `get_connection_context()` và `transaction()` cho việc quản lý transaction.

### 5.2 Migrations

Thư mục `infrastructure/database/migrations/` chứa các file migration đánh số tuần tự từ 001 đến 023, tự động chạy trên startup. Mỗi migration có function `upgrade()` để tạo bảng và indexes tương ứng. File `runner.py` chứa MigrationRunner quản lý việc chạy các migration pending.

### 5.3 Seeds

File `infrastructure/database/seeds/dev_seed.py` tạo dữ liệu mẫu bao gồm admin user, các vai trò, xe mẫu. File `sit_seed.py` tạo dữ liệu cho SIT test.

### 5.4 Repositories

BaseRepository trong `infrastructure/repositories/base_repository.py` cung cấp CRUD chuẩn gồm find_by_id(), find_all(), create(), update(), delete(), count(), exists(). Các repository riêng cho từng entity kế thừa từ BaseRepository và thêm các method đặc thù.

### 5.5 Security và Exporters

File `infrastructure/security/password_hasher.py` cung cấp bcrypt hashing với cost >= 12. File `infrastructure/exporters/excel_exporter.py` cung cấp export Excel dùng openpyxl. File `infrastructure/pdf_renderer.py` cung cấp render PDF dùng Jinja2 templates + WeasyPrint.

## 6. Tầng Application

### 6.1 Services

Thư mục `application/services/` chứa các service xử lý logic nghiệp vụ. SessionManager trong `session.py` là singleton quản lý phiên đăng nhập với timeout 30 phút theo BR-SEC-06. AuthService xác thực đăng nhập và lockout sau 5 lần sai theo BR-SEC-05. XeService xử lý nghiệp vụ xe. HopDongService tạo hợp đồng, tính tổng tiền theo BR-CALC-01, áp dụng khuyến mãi. KhuyenMaiService quản lý khuyến mãi và tìm khuyến mãi tối ưu. TraGopService tính toán số tiền trả góp theo BR-CALC-03 và theo dõi thanh toán trễ 5 ngày theo BR-TIME-06. BaoHanhService quản lý bảo hành với cảnh báo hết hạn 30 ngày theo BR-TIME-04. BaoDuongService quản lý lịch bảo dưỡng với nhắc nhở 7 ngày theo BR-TIME-05. Các service khác gồm KhachHangService, NhanVienService, KhieuNaiService, CuuHoService, LeadService, DashboardService, AuditLogService, BaoHiemService, NhaCungCapService, PhuKienService, ComboService, DonDatHangService, NhapKhoService, KhoService, ChienDichMkService, SystemSettingsService, SidebarService, PermissionService. Hai service đặc biệt là KhuyenMaiScheduler và TraGopScheduler tự động chạy để cập nhật trạng thái khuyến mãi hết hạn và kiểm tra thanh toán trễ.

### 6.2 Validators

Thư mục `application/validators/` chứa các quy tắc validation cho khách hàng (khach_hang_validator.py) và xe (xe_validator.py).

## 7. Tầng Presentation

### 7.1 Screens

Thư mục `presentation/screens/` chứa khoảng 70 file screens và dialogs được phân theo module. Màn hình chính gồm main_window.py (cửa sổ chính với TopBar, Sidebar, ContentArea, StatusBar), login_screen.py (đăng nhập), change_password_dialog.py (đổi password). Module xe gồm vehicle_list_screen.py, vehicle_form_dialog.py, vehicle_detail_screen.py, vehicle_delete_dialog.py. Module khách hàng gồm customer_list_screen.py, customer_form_dialog.py, customer_detail_screen.py. Module hợp đồng gồm contract_list_screen.py, contract_wizard_dialog.py, contract_detail_screen.py, payment_contract_screen.py. Module trả góp gồm installment_list_screen.py, installment_create_dialog.py, installment_progress_screen.py. Module bảo hành gồm warranty_list_screen.py, warranty_detail_screen.py, warranty_request_form_dialog.py, warranty_request_list_screen.py, internal_warranty_form_dialog.py, external_warranty_form_dialog.py, warranty_print_dialog.py. Module bảo hiểm gồm bao_hiem_list_screen.py, bao_hiem_form_dialog.py, bao_hiem_detail_screen.py, payment_insurance_screen.py. Module bảo dưỡng gồm maintenance_schedule_screen.py, maintenance_form_dialog.py, maintenance_status_dialog.py. Module khiếu nại gồm complaint_list_screen.py, complaint_form_dialog.py, complaint_detail_screen.py. Module marketing gồm campaign_list_screen.py, campaign_form_dialog.py, lead_manager_screen.py, lead_form_dialog.py, lead_assign_dialog.py, lead_status_dialog.py. Module khuyến mãi gồm promo_list_screen.py, promo_form_dialog.py, promo_effectiveness_screen.py. Module nhân viên gồm employee_list_screen.py, employee_form_dialog.py, employee_profile_screen.py, employee_kpi_report_screen.py. Module nhà cung cấp gồm supplier_list_screen.py, supplier_form_dialog.py, supplier_detail_screen.py, supplier_rating_dialog.py. Module kho gồm inventory_overview_screen.py, stock_in_form_dialog.py, order_list_screen.py, order_form_dialog.py. Module cứu hộ gồm rescue_request_list_screen.py, rescue_request_form_dialog.py. Module phụ kiện gồm accessory_list_screen.py, accessory_form_dialog.py, combo_manager_screen.py. Module báo cáo gồm reports_hub_screen.py, revenue_report_screen.py, top_vehicles_report_screen.py, vip_customer_report_screen.py, customer_care_screen.py. Module hệ thống gồm dashboard_screen.py, audit_log_screen.py, system_settings_screen.py.

### 7.2 Widgets

Thư mục `presentation/widgets/` chứa các thành phần UI dùng chung. Top_bar.py là thanh trên cùng hiển thị logo, tên đại lý, user menu, đăng xuất. Sidebar.py là thanh bên trái với menu điều hướng theo vai trò người dùng. Content_area.py là vùng nội dung chính dạng QStackedWidget. Status_bar.py là thanh dưới hiển thị user, thời gian, phiên bản, trạng thái DB. Inputs.py chứa các component nhập liệu như Input, Select, DatePicker, TextArea. Buttons.py chứa các nút bấm định dạng sẵn. Dialogs.py chứa các dialog dùng chung như ConfirmDialog, AlertDialog.

## 8. Tầng Shared

Thư mục `app/shared/` chứa các utility dùng chung. File `constants.py` định nghĩa các hằng số business như trạng thái, mã vai trò, thời gian. File `logger.py` cấu hình logging. File `db_utils.py` cung cấp các database utilities.

## 9. Luồng Hoạt Động Chính

### 9.1 Khởi động

Ứng dụng khởi động từ main.py, chạy migration tự động, seed dữ liệu mẫu nếu cần, sau đó hiển thị LoginScreen. Khi đăng nhập thành công, SessionManager.login() được gọi và MainWindow được hiển thị với Sidebar và ContentArea. Nếu cần đổi password bắt buộc, ChangePasswordDialog được hiển thị trước.

### 9.2 Bán xe (Workflow 02)

ContractWizardDialog hướng dẫn người dùng qua các bước: chọn xe với XeService.kiem_tra_ton_kho(), chọn khách hàng, chọn phụ kiện optional, áp dụng khuyến mãi tối ưu từ KhuyenMaiService, tính tổng tiền theo công thức BR-CALC-01, và tạo hợp đồng. Hệ thống tự động cập nhật tồn kho xe, số xe đã mua và tổng giá trị mua của khách hàng, đồng thời phân loại khách hàng thành VIP nếu tổng giá trị mua vượt 500 triệu.

### 9.3 Trả góp (Workflow 03)

Sau khi tạo hợp đồng, InstallmentCreateDialog cho phép tạo trả góp. TraGopService.tinh_so_tien_tra_thang() tính số tiền trả hàng tháng theo công thức tài chính BR-CALC-03: A = P * r * (1+r)^n / ((1+r)^n - 1). TraGopScheduler kiểm tra thanh toán hàng ngày và gửi cảnh báo nếu khách hàng trễ hơn 5 ngày.

### 9.4 Bảo hành (Workflow 04)

WarrantyListScreen hiển thị danh sách bảo hành. Khi tạo yêu cầu bảo hành, BaoHanhService kiểm tra xe còn trong thời hạn và tạo yêu cầu. BaoHanhScheduler cảnh báo các bảo hành sắp hết hạn trước 30 ngày.

## 10. Quy Ước Đặt Tên

Về file names, service đặt theo pattern {module}_service.py (xe_service.py, hop_dong_service.py), repository đặt theo pattern {entity}_repository.py (xe_repository.py), list screen đặt theo pattern {module}_list_screen.py (vehicle_list_screen.py), detail screen đặt theo pattern {module}_detail_screen.py, form dialog đặt theo pattern {module}_form_dialog.py, entity đặt theo CamelCase (KhachHang, BaoHanh).

Về mã vai trò, A-01 là Admin với toàn quyền, A-02 là Sales với quyền Xe, Khách hàng, Hợp đồng, Marketing, A-03 là Kỹ thuật với quyền Bảo hành, Bảo dưỡng, Cứu hộ.

Về trạng thái hợp đồng theo flow: moi_tao -> da_thanh_toan -> da_giao_xe, hoặc huy nếu hủy. Trạng thái bảo hành gồm con_hieu_luc, het_hieu_luc, tam_dung.

## 11. Business Rules Reference

BR-CALC-01 tính tổng tiền hợp đồng: gia_xe + tong_gia_phu_kien - tien_giam_km. BR-CALC-02 phân loại khách hàng VIP khi tong_gia_tri_mua > 500 triệu. BR-CALC-03 công thức trả góp: A = P * r * (1+r)^n / ((1+r)^n - 1). BR-SEC-05 lockout 5 lần đăng nhập sai. BR-SEC-06 session timeout 30 phút. BR-SEC-07 audit log cho tất cả thao tác. BR-TIME-04 cảnh báo bảo hành hết hạn trước 30 ngày. BR-TIME-05 nhắc bảo dưỡng trước 7 ngày. BR-TIME-06 cảnh báo thanh toán trễ 5 ngày. BR-NV-08 bắt buộc đổi password lần đầu.

## 12. Database

File database là data/car_management.db dạng SQLite. Migrations tự động chạy trên startup từ migration_001 đến migration_023. Seeds tạo dữ liệu mẫu nếu bảng nhan_vien trống. Các bảng chính gồm nhan_vien, vai_tro, xe, khach_hang, hop_dong, phu_kien, combo_phu_kien, khuyen_mai, bao_hanh, bao_hiem, bao_duong, cuu_ho, tra_gop, nha_cung_cap, dai_ly, nhap_kho, don_dat_hang, tra_lich, chien_dich_mk, lead, khieu_nai, audit_log, system_settings. Các bảng trung gian gồm hop_dong_phu_kien và bao_hanh_yeu_cau.

## 13. Testing

Pytest sử dụng các markers để phân loại tests: simple cho SELECT < 50ms, join_agg cho JOIN/AGG < 200ms, report cho reports < 500ms, perf cho performance benchmarks. Các workflow markers gồm wf01 (Nhập kho), wf02 (Bán xe chuẩn), wf03 (Bán trả góp), wf04 (Bảo hành), wf05 (Bảo dưỡng), wf06 (Khiếu nại), wf07 (Marketing -> Lead -> Khách hàng), wf08 (Hủy hợp đồng). Chạy tests với lệnh pytest tests/ -v, pytest tests/ -m simple cho tests nhanh, pytest tests/ -m wf04 -v cho workflow 04.

## 14. Tổng Kết

Hệ thống có khoảng 70+ screens/dialogs, 27 services, 21 entities, và 23 migrations. Mã nguồn được tổ chức theo Clean Architecture với sự phân tách rõ ràng giữa các tầng presentation, application, domain, infrastructure, giúp dễ bảo trì và mở rộng.