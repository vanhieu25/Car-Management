# MÔ TẢ THIẾT KẾ CƠ SỞ DỮ LIỆU

---

## 1. Tổng quan thiết kế

Cơ sở dữ liệu SQLite được thiết kế theo nguyên tắc chuẩn hóa cao nhằm tránh dư thừa dữ liệu và đảm bảo tính toàn vẹn thông qua khóa ngoại. Hệ thống gồm 30 bảng chính được tạo tuần tự thông qua MigrationRunner từ migration_001 đến migration_035, trong đó các migration từ 013 đến 035 bao gồm bổ sung chỉ mục, ràng buộc và cột cho các bảng đã có. File cơ sở dữ liệu nằm tại data/car_management.db. Mỗi bảng có id là khóa chính tự động tăng (INTEGER PRIMARY KEY AUTOINCREMENT), các cột created_at, updated_at và created_by được sử dụng để theo dõi lịch sử thao tác. Foreign key được bật theo mặc định trong mọi kết nối. Hệ thống sử dụng TEXT làm kiểu dữ liệu cho ngày giờ (SQLite không có kiểu DATETIME riêng), lưu theo định dạng ISO-8601. Các giá trị tiền tệ và số lượng sử dụng INTEGER (đơn vị nhỏ nhất, ví dụ VND).

Hệ thống cũng bao gồm 9 view hỗ trợ báo cáo và dashboard: view_revenue_by_month, view_top_xe_sold, view_kpi_nv, view_vip_customers, view_bh_cost, view_km_efficiency, view_mk_efficiency, view_dashboard_kpi và view_dashboard_alerts. Các view này được tạo trong migration_020 và migration_024.

---

## 2. Bảng cấu trúc hệ thống

### Bảng vai_tro

Vai trò người dùng trong hệ thống gồm ba giá trị: A-01 (quản trị viên), A-02 (nhân viên bán hàng), A-03 (nhân viên kỹ thuật). Mỗi vai trò có mã duy nhất và tên hiển thị.

| Cột         | Kiểu    | Ràng buộc                 | Ghi chú                       |
| ----------- | ------- | ------------------------- | ----------------------------- |
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT | Khóa chính                    |
| ma_vai_tro  | TEXT    | UNIQUE NOT NULL           | Mã vai trò (A-01, A-02, A-03) |
| ten_vai_tro | TEXT    | NOT NULL                  | Tên vai trò                   |
| mo_ta       | TEXT    |                           | Mô tả chi tiết                |
| created_at  | TEXT    | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo                 |

### Bảng nhan_vien

Nhân viên của hệ thống, mỗi nhân viên thuộc một vai trò và một đại lý. Tài khoản đăng nhập sử dụng username và mat_khah_hash (bcrypt). Hệ thống hỗ trợ khóa tài khoản sau 5 lần đăng nhập sai (khoa_den) và yêu cầu đổi mật khẩu lần đầu (must_change_password). Các cột so_hop_dong và doanh_thu được thêm ở migration_022 để phục vụ KPI nhân viên.

| Cột                  | Kiểu    | Ràng buộc                                | Ghi chú                   |
| -------------------- | ------- | ---------------------------------------- | ------------------------- |
| id                   | INTEGER | PRIMARY KEY AUTOINCREMENT                | Khóa chính                |
| username             | TEXT    | UNIQUE NOT NULL                          | Tên đăng nhập             |
| mat_khau_hash        | TEXT    | NOT NULL                                 | Mật khẩu mã hóa bcrypt    |
| ho_ten               | TEXT    | NOT NULL                                 | Họ và tên                 |
| email                | TEXT    | NOT NULL                                 | Email                     |
| so_dien_thoai        | TEXT    |                                          | Số điện thoại             |
| vai_tro_id           | INTEGER | NOT NULL FK → vai_tro(id)                | Khóa ngoại đến vai_tro    |
| trang_thai           | TEXT    | DEFAULT 'active' CHECK(active, inactive) | Trạng thái hoạt động      |
| lan_dang_nhap_sai    | INTEGER | DEFAULT 0                                | Số lần đăng nhập sai      |
| khoa_den             | TEXT    |                                          | Thời gian khóa đến        |
| must_change_password | INTEGER | DEFAULT 0                                | Cờ yêu cầu đổi mật khẩu   |
| password_min_length  | INTEGER | DEFAULT 8                                | Độ dài mật khẩu tối thiểu |
| last_password_change | TEXT    |                                          | Lần cuối đổi mật khẩu     |
| so_hop_dong          | INTEGER | DEFAULT 0                                | Số hợp đồng đã bán        |
| doanh_thu            | INTEGER | DEFAULT 0                                | Tổng doanh thu            |
| dai_ly_id            | INTEGER | FK → dai_ly(id)                          | Khóa ngoại đến đại lý     |
| created_by           | INTEGER | FK → nhan_vien(id)                       | Người tạo                 |
| created_at           | TEXT    | DEFAULT CURRENT_TIMESTAMP                | Thời gian tạo             |
| updated_at           | TEXT    |                                          | Thời gian cập nhật        |

### Bảng dai_ly

Đại lý phân phối. Mỗi nhân viên thuộc một đại lý. Đại lý mặc định DL001 được tạo khi seed dữ liệu.

| Cột           | Kiểu    | Ràng buộc                                             | Ghi chú            |
| ------------- | ------- | ----------------------------------------------------- | ------------------ |
| id            | INTEGER | PRIMARY KEY AUTOINCREMENT                             | Khóa chính         |
| ma_dai_ly     | TEXT    | UNIQUE NOT NULL                                       | Mã đại lý          |
| ten_dai_ly    | TEXT    | NOT NULL                                              | Tên đại lý         |
| dia_chi       | TEXT    |                                                       | Địa chỉ            |
| so_dien_thoai | TEXT    |                                                       | Số điện thoại      |
| email         | TEXT    |                                                       | Email              |
| trang_thai    | TEXT    | DEFAULT 'hoat_dong' CHECK(hoat_dong, khong_hoat_dong) | Trạng thái         |
| created_at    | TEXT    | DEFAULT CURRENT_TIMESTAMP                             | Thời gian tạo      |
| updated_at    | TEXT    |                                                       | Thời gian cập nhật |

---

## 3. Bảng nghiệp vụ cốt lõi

### Bảng xe

Danh mục xe với thông tin chi tiết về hãng, dòng xe, năm sản xuất, màu sắc và giá bán. Số lượng tồn kho được kiểm soát qua so_luong_ton và muc_toi_thieu để cảnh báo khi sắp hết hàng. Trạng thái xe gồm con_hang, da_ban và sap_ve.

| Cột                | Kiểu    | Ràng buộc                                          | Ghi chú            |
| ------------------ | ------- | -------------------------------------------------- | ------------------ |
| id                 | INTEGER | PRIMARY KEY AUTOINCREMENT                          | Khóa chính         |
| ma_xe              | TEXT    | UNIQUE NOT NULL                                    | Mã xe              |
| hang               | TEXT    | NOT NULL                                           | Hãng xe            |
| dong_xe            | TEXT    | NOT NULL                                           | Dòng xe            |
| nam_san_xuat       | INTEGER | NOT NULL CHECK(1990-2100)                          | Năm sản xuất       |
| mau_sac            | TEXT    |                                                    | Màu sắc            |
| gia_ban            | INTEGER | NOT NULL CHECK(≥0)                                 | Giá bán            |
| so_luong_ton       | INTEGER | DEFAULT 0 CHECK(≥0)                                | Số lượng tồn kho   |
| muc_toi_thieu      | INTEGER | DEFAULT 2                                          | Mức tồn tối thiểu  |
| trang_thai         | TEXT    | DEFAULT 'con_hang' CHECK(con_hang, da_ban, sap_ve) | Trạng thái         |
| ngay_nhap_dau_tien | TEXT    |                                                    | Ngày nhập đầu tiên |
| mo_ta              | TEXT    |                                                    | Mô tả thêm         |
| created_by         | INTEGER | FK → nhan_vien(id)                                 | Người tạo          |
| created_at         | TEXT    | DEFAULT CURRENT_TIMESTAMP                          | Thời gian tạo      |
| updated_at         | TEXT    |                                                    | Thời gian cập nhật |

### Bảng khach_hang

Khách hàng của hệ thống. Mỗi khách hàng có số điện thoại duy nhất. Phân loại khách hàng gồm Thuong, Than_thiet và VIP dựa trên tổng giá trị mua hàng và số xe đã mua. Cột trang_thai được thêm ở migration_034 phục vụ soft-delete.

| Cột              | Kiểu    | Ràng buộc                                       | Ghi chú                  |
| ---------------- | ------- | ----------------------------------------------- | ------------------------ |
| id               | INTEGER | PRIMARY KEY AUTOINCREMENT                       | Khóa chính               |
| ho_ten           | TEXT    | NOT NULL                                        | Họ và tên                |
| so_dien_thoai    | TEXT    | UNIQUE NOT NULL                                 | Số điện thoại            |
| email            | TEXT    | NOT NULL                                        | Email                    |
| dia_chi          | TEXT    |                                                 | Địa chỉ                  |
| ngay_sinh        | TEXT    |                                                 | Ngày sinh                |
| phan_loai        | TEXT    | DEFAULT 'Thuong' CHECK(Thuong, Than_thiet, VIP) | Phân loại khách hàng     |
| tong_gia_tri_mua | INTEGER | DEFAULT 0                                       | Tổng giá trị mua         |
| so_xe_da_mua     | INTEGER | DEFAULT 0                                       | Số xe đã mua             |
| trang_thai       | TEXT    | DEFAULT 'active' CHECK(active, inactive)        | Trạng thái (soft-delete) |
| created_by       | INTEGER | FK → nhan_vien(id)                              | Người tạo                |
| created_at       | TEXT    | DEFAULT CURRENT_TIMESTAMP                       | Thời gian tạo            |
| updated_at       | TEXT    |                                                 | Thời gian cập nhật       |

### Bảng hop_dong

Bảng trung tâm của hệ thống, ghi nhận mỗi giao dịch mua bán xe. Mỗi hợp đồng có mã duy nhất và lưu trữ thông tin khách hàng, xe, nhân viên bán, khuyến mãi áp dụng. Trạng thái hợp đồng gồm moi_tao, da_thanh_toan, da_giao_xe và huy. Cột da_thanh_toan được thêm ở migration_035 để theo dõi số tiền đã thanh toán. Các chỉ mục được tạo trên ma_hop_dong, trang_thai, ngay_tao, khach_hang_id, xe_id, nhan_vien_id và các tổ hợp (ngay_tao + trang_thai, trang_thai + nhan_vien_id).

| Cột               | Kiểu    | Ràng buộc                                                        | Ghi chú                   |
| ----------------- | ------- | ---------------------------------------------------------------- | ------------------------- |
| id                | INTEGER | PRIMARY KEY AUTOINCREMENT                                        | Khóa chính                |
| ma_hop_dong       | TEXT    | UNIQUE NOT NULL                                                  | Mã hợp đồng               |
| khach_hang_id     | INTEGER | NOT NULL FK → khach_hang(id)                                     | Khóa ngoại đến khách hàng |
| xe_id             | INTEGER | NOT NULL FK → xe(id)                                             | Khóa ngoại đến xe         |
| nhan_vien_id      | INTEGER | NOT NULL FK → nhan_vien(id)                                      | Khóa ngoại đến nhân viên  |
| khuyen_mai_id     | INTEGER | FK → khuyen_mai(id)                                              | Khóa ngoại đến khuyến mãi |
| gia_xe            | INTEGER | NOT NULL                                                         | Giá xe                    |
| tong_gia_phu_kien | INTEGER | DEFAULT 0                                                        | Tổng giá phụ kiện         |
| tien_giam_km      | INTEGER | DEFAULT 0                                                        | Tiền giảm khuyến mãi      |
| tong_tien         | INTEGER | NOT NULL                                                         | Tổng tiền                 |
| trang_thai        | TEXT    | DEFAULT 'moi_tao' CHECK(moi_tao, da_thanh_toan, da_giao_xe, huy) | Trạng thái hợp đồng       |
| ngay_tao          | TEXT    | DEFAULT CURRENT_TIMESTAMP                                        | Ngày tạo                  |
| ngay_thanh_toan   | TEXT    |                                                                  | Ngày thanh toán           |
| ngay_giao_xe      | TEXT    |                                                                  | Ngày giao xe              |
| ly_do_huy         | TEXT    |                                                                  | Lý do hủy                 |
| ghi_chu           | TEXT    |                                                                  | Ghi chú                   |
| da_thanh_toan     | INTEGER | DEFAULT 0                                                        | Số tiền đã thanh toán     |
| created_by        | INTEGER | FK → nhan_vien(id)                                               | Người tạo                 |
| created_at        | TEXT    | DEFAULT CURRENT_TIMESTAMP                                        | Thời gian tạo             |
| updated_at        | TEXT    |                                                                  | Thời gian cập nhật        |

### Bảng hop_dong_phu_kien

Bảng liên kết nhiều-nhiều giữa hop_dong và phu_kien. Một hợp đồng có thể mua nhiều phụ kiện, mỗi phụ kiện có số lượng và giá bán riêng. Khóa chính là tổ hợp hop_dong_id và phu_kien_id.

| Cột         | Kiểu    | Ràng buộc                     | Ghi chú                             |
| ----------- | ------- | ----------------------------- | ----------------------------------- |
| hop_dong_id | INTEGER | PRIMARY KEY FK → hop_dong(id) | Khóa chính, khóa ngoại đến hợp đồng |
| phu_kien_id | INTEGER | PRIMARY KEY FK → phu_kien(id) | Khóa chính, khóa ngoại đến phụ kiện |
| so_luong    | INTEGER | DEFAULT 1 CHECK(≥1)           | Số lượng                            |
| gia_ban     | INTEGER | NOT NULL                      | Giá bán                             |

---

## 4. Bảng quản lý phụ kiện

### Bảng phu_kien

Danh mục phụ kiện xe. Phân loại theo năm nhóm: noi_that, ngoai_that, dien_tu, bao_ve, trang_tri (cập nhật từ migration_016 theo BRD). Mỗi phụ kiện có mã duy nhất, giá bán và số lượng tồn kho.

| Cột        | Kiểu    | Ràng buộc                                                        | Ghi chú            |
| ---------- | ------- | ---------------------------------------------------------------- | ------------------ |
| id         | INTEGER | PRIMARY KEY AUTOINCREMENT                                        | Khóa chính         |
| ma_pk      | TEXT    | UNIQUE NOT NULL                                                  | Mã phụ kiện        |
| ten_pk     | TEXT    | NOT NULL                                                         | Tên phụ kiện       |
| phan_loai  | TEXT    | NOT NULL CHECK(noi_that, ngoai_that, dien_tu, bao_ve, trang_tri) | Phân loại          |
| gia_ban    | INTEGER | NOT NULL CHECK(≥0)                                               | Giá bán            |
| ton_kho    | INTEGER | DEFAULT 0 CHECK(≥0)                                              | Tồn kho            |
| mo_ta      | TEXT    |                                                                  | Mô tả              |
| created_by | INTEGER | FK → nhan_vien(id)                                               | Người tạo          |
| created_at | TEXT    | DEFAULT CURRENT_TIMESTAMP                                        | Thời gian tạo      |
| updated_at | TEXT    |                                                                  | Thời gian cập nhật |

### Bảng combo_phu_kien

Nhóm các phụ kiện thành gói combo với hệ số giảm giá (he_so_giam) từ 0 đến 1. Ví dụ he_so_giam = 0.15 tương ứng giảm 15% khi mua combo.

| Cột        | Kiểu    | Ràng buộc                          | Ghi chú            |
| ---------- | ------- | ---------------------------------- | ------------------ |
| id         | INTEGER | PRIMARY KEY AUTOINCREMENT          | Khóa chính         |
| ten_combo  | TEXT    | NOT NULL                           | Tên combo          |
| he_so_giam | REAL    | NOT NULL CHECK(0 < he_so_giam ≤ 1) | Hệ số giảm giá     |
| mo_ta      | TEXT    |                                    | Mô tả              |
| created_by | INTEGER | FK → nhan_vien(id)                 | Người tạo          |
| created_at | TEXT    | DEFAULT CURRENT_TIMESTAMP          | Thời gian tạo      |
| updated_at | TEXT    |                                    | Thời gian cập nhật |

### Bảng combo_chi_tiet

Bảng liên kết nhiều-nhiều giữa combo_phu_kien và phu_kien. Mỗi combo gồm nhiều phụ kiện với số lượng cụ thể. Khóa chính là tổ hợp combo_id và phu_kien_id.

| Cột         | Kiểu    | Ràng buộc                           | Ghi chú                             |
| ----------- | ------- | ----------------------------------- | ----------------------------------- |
| combo_id    | INTEGER | PRIMARY KEY FK → combo_phu_kien(id) | Khóa chính, khóa ngoại đến combo    |
| phu_kien_id | INTEGER | PRIMARY KEY FK → phu_kien(id)       | Khóa chính, khóa ngoại đến phụ kiện |
| so_luong    | INTEGER | DEFAULT 1 CHECK(≥1)                 | Số lượng                            |

---

## 5. Bảng khuyến mãi

### Bảng khuyen_mai

Chương trình khuyến mãi với năm loại: giam_tien_mat, giam_phan_tram, tang_phu_kien, giam_lai_suat và combo. Mỗi khuyến mãi có giá trị và kiểu giá trị (tien hoặc phan_tram). Trạng thái gồm nhap, dang_chay, tam_dung, ket_thuc. Thời gian áp dụng được giới hạn bởi tu_ngay và den_ngay.

| Cột                 | Kiểu    | Ràng buộc                                                                          | Ghi chú             |
| ------------------- | ------- | ---------------------------------------------------------------------------------- | ------------------- |
| id                  | INTEGER | PRIMARY KEY AUTOINCREMENT                                                          | Khóa chính          |
| ten_km              | TEXT    | NOT NULL                                                                           | Tên khuyến mãi      |
| mo_ta               | TEXT    |                                                                                    | Mô tả               |
| loai_km             | TEXT    | NOT NULL CHECK(giam_tien_mat, giam_phan_tram, tang_phu_kien, giam_lai_suat, combo) | Loại khuyến mãi     |
| gia_tri             | INTEGER | NOT NULL                                                                           | Giá trị             |
| kieu_gia_tri        | TEXT    | NOT NULL CHECK(tien, phan_tram)                                                    | Kiểu giá trị        |
| tu_ngay             | TEXT    | NOT NULL                                                                           | Ngày bắt đầu        |
| den_ngay            | TEXT    | NOT NULL                                                                           | Ngày kết thúc       |
| trang_thai          | TEXT    | DEFAULT 'dang_chay' CHECK(nhap, dang_chay, tam_dung, ket_thuc)                     | Trạng thái          |
| so_luong_cho_phep   | INTEGER |                                                                                    | Số lượng cho phép   |
| so_luong_da_su_dung | INTEGER | DEFAULT 0                                                                          | Số lượng đã sử dụng |
| created_by          | INTEGER | FK → nhan_vien(id)                                                                 | Người tạo           |
| created_at          | TEXT    | DEFAULT CURRENT_TIMESTAMP                                                          | Thời gian tạo       |
| updated_at          | TEXT    |                                                                                    | Thời gian cập nhật  |

### Bảng km_pham_vi

Phạm vi áp dụng của khuyến mãi, cho phép giới hạn đối tượng được hưởng khuyến mãi theo loại (all, hang, dong_xe, xe) và giá trị áp dụng tương ứng.

| Cột             | Kiểu    | Ràng buộc                              | Ghi chú                   |
| --------------- | ------- | -------------------------------------- | ------------------------- |
| id              | INTEGER | PRIMARY KEY AUTOINCREMENT              | Khóa chính                |
| khuyen_mai_id   | INTEGER | NOT NULL FK → khuyen_mai(id)           | Khóa ngoại đến khuyến mãi |
| loai_ap_dung    | TEXT    | NOT NULL CHECK(all, hang, dong_xe, xe) | Loại áp dụng              |
| gia_tri_ap_dung | TEXT    |                                        | Giá trị áp dụng           |
| created_at      | TEXT    | DEFAULT CURRENT_TIMESTAMP              | Thời gian tạo             |

---

## 6. Bảng quản lý kho và cung ứng

### Bảng nha_cung_cap

Nhà cung cấp xe và phụ kiện. Hệ thống đánh giá nhà cung cấp qua ba tiêu chí: chất lượng, thời gian giao hàng và giá cả, mỗi tiêu chí từ 0 đến 5. Điểm tổng (diem_tong) là tổng của ba tiêu chí.

| Cột                 | Kiểu    | Ràng buộc                 | Ghi chú             |
| ------------------- | ------- | ------------------------- | ------------------- |
| id                  | INTEGER | PRIMARY KEY AUTOINCREMENT | Khóa chính          |
| ma_ncc              | TEXT    | UNIQUE NOT NULL           | Mã nhà cung cấp     |
| ten_ncc             | TEXT    | NOT NULL                  | Tên nhà cung cấp    |
| dia_chi             | TEXT    |                           | Địa chỉ             |
| so_dien_thoai       | TEXT    |                           | Số điện thoại       |
| email               | TEXT    |                           | Email               |
| nguoi_lien_he       | TEXT    |                           | Người liên hệ       |
| diem_chat_luong     | INTEGER | DEFAULT 0 CHECK(0-5)      | Điểm chất lượng     |
| diem_thoi_gian_giao | INTEGER | DEFAULT 0 CHECK(0-5)      | Điểm thời gian giao |
| diem_gia_ca         | INTEGER | DEFAULT 0 CHECK(0-5)      | Điểm giá cả         |
| diem_tong           | INTEGER | DEFAULT 0                 | Điểm tổng           |
| created_by          | INTEGER | FK → nhan_vien(id)        | Người tạo           |
| created_at          | TEXT    | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo       |
| updated_at          | TEXT    |                           | Thời gian cập nhật  |

### Bảng nhap_kho

Phiếu nhập kho. Ghi nhận việc nhập xe hoặc phụ kiện từ nhà cung cấp. Mỗi phiếu nhập được thực hiện bởi một nhân viên và có thể ghi chú kèm theo.

| Cột             | Kiểu    | Ràng buộc                      | Ghi chú                     |
| --------------- | ------- | ------------------------------ | --------------------------- |
| id              | INTEGER | PRIMARY KEY AUTOINCREMENT      | Khóa chính                  |
| nha_cung_cap_id | INTEGER | NOT NULL FK → nha_cung_cap(id) | Khóa ngoại đến nhà cung cấp |
| nhan_vien_id    | INTEGER | NOT NULL FK → nhan_vien(id)    | Khóa ngoại đến nhân viên    |
| ngay_nhap       | TEXT    | DEFAULT CURRENT_TIMESTAMP      | Ngày nhập                   |
| ghi_chu         | TEXT    |                                | Ghi chú                     |
| created_by      | INTEGER | FK → nhan_vien(id)             | Người tạo                   |
| created_at      | TEXT    | DEFAULT CURRENT_TIMESTAMP      | Thời gian tạo               |

### Bảng chi_tiet_nhap_kho

Chi tiết từng mặt hàng trong phiếu nhập kho. Mỗi dòng ghi nhận loại item (xe hoặc phu_kien), id của item, số lượng và giá nhập.

| Cột         | Kiểu    | Ràng buộc                    | Ghi chú                   |
| ----------- | ------- | ---------------------------- | ------------------------- |
| id          | INTEGER | PRIMARY KEY AUTOINCREMENT    | Khóa chính                |
| nhap_kho_id | INTEGER | NOT NULL FK → nhap_kho(id)   | Khóa ngoại đến phiếu nhập |
| loai_item   | TEXT    | NOT NULL CHECK(xe, phu_kien) | Loại mặt hàng             |
| item_id     | INTEGER | NOT NULL                     | ID mặt hàng               |
| so_luong    | INTEGER | NOT NULL CHECK(>0)           | Số lượng                  |
| gia_nhap    | INTEGER | NOT NULL CHECK(≥0)           | Giá nhập                  |
| created_at  | TEXT    | DEFAULT CURRENT_TIMESTAMP    | Thời gian tạo             |

### Bảng don_dat_hang

Đơn đặt hàng gửi đến nhà cung cấp. Mỗi đơn hàng có mã duy nhất, trạng thái (nhap, da_gui, da_nhan, huy) và ngày giao dự kiến.

| Cột             | Kiểu    | Ràng buộc                                        | Ghi chú                     |
| --------------- | ------- | ------------------------------------------------ | --------------------------- |
| id              | INTEGER | PRIMARY KEY AUTOINCREMENT                        | Khóa chính                  |
| nha_cung_cap_id | INTEGER | NOT NULL FK → nha_cung_cap(id)                   | Khóa ngoại đến nhà cung cấp |
| nhan_vien_id    | INTEGER | NOT NULL FK → nhan_vien(id)                      | Khóa ngoại đến nhân viên    |
| ma_don          | TEXT    | UNIQUE NOT NULL                                  | Mã đơn hàng                 |
| ngay_dat        | TEXT    | DEFAULT CURRENT_TIMESTAMP                        | Ngày đặt                    |
| trang_thai      | TEXT    | DEFAULT 'nhap' CHECK(nhap, da_gui, da_nhan, huy) | Trạng thái                  |
| ngay_giao       | TEXT    |                                                  | Ngày giao                   |
| ghi_chu         | TEXT    |                                                  | Ghi chú                     |
| created_by      | INTEGER | FK → nhan_vien(id)                               | Người tạo                   |
| created_at      | TEXT    | DEFAULT CURRENT_TIMESTAMP                        | Thời gian tạo               |
| updated_at      | TEXT    |                                                  | Thời gian cập nhật          |

### Bảng chi_tiet_don_dat

Chi tiết từng mặt hàng trong đơn đặt hàng, tương tự chi_tiet_nhap_kho nhưng dành cho đơn đặt hàng.

| Cột             | Kiểu    | Ràng buộc                      | Ghi chú                     |
| --------------- | ------- | ------------------------------ | --------------------------- |
| id              | INTEGER | PRIMARY KEY AUTOINCREMENT      | Khóa chính                  |
| don_dat_hang_id | INTEGER | NOT NULL FK → don_dat_hang(id) | Khóa ngoại đến đơn đặt hàng |
| loai_item       | TEXT    | NOT NULL CHECK(xe, phu_kien)   | Loại mặt hàng               |
| item_id         | INTEGER | NOT NULL                       | ID mặt hàng                 |
| so_luong        | INTEGER | NOT NULL CHECK(>0)             | Số lượng                    |
| gia_don         | INTEGER | NOT NULL CHECK(≥0)             | Giá đặt hàng                |
| created_at      | TEXT    | DEFAULT CURRENT_TIMESTAMP      | Thời gian tạo               |

---

## 7. Bảng bảo hành và dịch vụ

### Bảng bao_hanh

Thông tin bảo hành cho mỗi hợp đồng. Mỗi hợp đồng có tối đa một bảo hành chính (hop_dong_id là UNIQUE). Hỗ trợ cả bảo hành nội bộ (is_external = 0) và bảo hiểm ngoài (is_external = 1) với thông tin số khung, số máy. Các cột loai_bh, dai_ly_ban_id, so_policy, phi_bh được thêm ở migration_025.

| Cột           | Kiểu    | Ràng buộc                                                            | Ghi chú                   |
| ------------- | ------- | -------------------------------------------------------------------- | ------------------------- |
| id            | INTEGER | PRIMARY KEY AUTOINCREMENT                                            | Khóa chính                |
| hop_dong_id   | INTEGER | UNIQUE FK → hop_dong(id)                                             | Khóa ngoại đến hợp đồng   |
| xe_id         | INTEGER | FK → xe(id)                                                          | Khóa ngoại đến xe         |
| khach_hang_id | INTEGER | NOT NULL FK → khach_hang(id)                                         | Khóa ngoại đến khách hàng |
| thoi_han_bh   | INTEGER | NOT NULL                                                             | Thời hạn bảo hành (tháng) |
| ngay_bat_dau  | TEXT    | NOT NULL                                                             | Ngày bắt đầu              |
| ngay_ket_thuc | TEXT    | NOT NULL CHECK(≥ngay_bat_dau)                                        | Ngày kết thúc             |
| pham_vi       | TEXT    |                                                                      | Phạm vi bảo hành          |
| trang_thai    | TEXT    | DEFAULT 'con_hieu_luc' CHECK(con_hieu_luc, het_han)                  | Trạng thái                |
| loai_bh       | TEXT    | DEFAULT 'bao_hanh' CHECK(bao_hanh, tnds, tai_nan, chao_no, that_lac) | Loại bảo hiểm             |
| dai_ly_ban_id | INTEGER | FK → nhan_vien(id)                                                   | Đại lý bán bảo hiểm       |
| so_policy     | TEXT    |                                                                      | Số policy                 |
| phi_bh        | INTEGER | DEFAULT 0                                                            | Phí bảo hiểm              |
| so_khung      | TEXT    |                                                                      | Số khung                  |
| so_may        | TEXT    |                                                                      | Số máy                    |
| is_external   | INTEGER | DEFAULT 0                                                            | Bảo hành ngoài (0/1)      |
| created_by    | INTEGER | FK → nhan_vien(id)                                                   | Người tạo                 |
| created_at    | TEXT    | DEFAULT CURRENT_TIMESTAMP                                            | Thời gian tạo             |
| updated_at    | TEXT    |                                                                      | Thời gian cập nhật        |

### Bảng bao_hanh_yeu_cau

Yêu cầu bảo hành phát sinh trong thời gian bảo hành. Mỗi yêu cầu thuộc về một bảo hành và được xử lý bởi một nhân viên. Loại yêu cầu gồm bao_duong, sua_chua và thay_the. Cột phan_loai (mien_phi hoặc tinh_phi) được thêm ở migration_023.

| Cột              | Kiểu    | Ràng buộc                                                           | Ghi chú                        |
| ---------------- | ------- | ------------------------------------------------------------------- | ------------------------------ |
| id               | INTEGER | PRIMARY KEY AUTOINCREMENT                                           | Khóa chính                     |
| bao_hanh_id      | INTEGER | NOT NULL FK → bao_hanh(id)                                          | Khóa ngoại đến bảo hành        |
| nhan_vien_id     | INTEGER | NOT NULL FK → nhan_vien(id)                                         | Khóa ngoại đến nhân viên xử lý |
| ngay_yeu_cau     | TEXT    | DEFAULT CURRENT_TIMESTAMP                                           | Ngày yêu cầu                   |
| mo_ta_tinh_trang | TEXT    | NOT NULL                                                            | Mô tả tình trạng               |
| loai_yeu_cau     | TEXT    | NOT NULL CHECK(bao_duong, sua_chua, thay_the)                       | Loại yêu cầu                   |
| chi_phi          | INTEGER | DEFAULT 0 CHECK(≥0)                                                 | Chi phí                        |
| phan_loai        | TEXT    | DEFAULT 'mien_phi' CHECK(mien_phi, tinh_phi)                        | Phân loại phí                  |
| trang_thai       | TEXT    | DEFAULT 'dang_xu_ly' CHECK(moi, dang_xu_ly, da_hoan_thanh, da_dong) | Trạng thái                     |
| ngay_hoan_thanh  | TEXT    |                                                                     | Ngày hoàn thành                |
| ghi_chu          | TEXT    |                                                                     | Ghi chú                        |
| created_by       | INTEGER | FK → nhan_vien(id)                                                  | Người tạo                      |
| created_at       | TEXT    | DEFAULT CURRENT_TIMESTAMP                                           | Thời gian tạo                  |
| updated_at       | TEXT    |                                                                     | Thời gian cập nhật             |

### Bảng bao_duong

Lịch bảo dưỡng định kỳ cho xe. Mỗi lịch bảo dưỡng ghi nhận khách hàng, xe, nhân viên phụ trách, ngày dự kiến, số km và nội dung bảo dưỡng. Trạng thái gồm cho_xac_nhan, da_xac_nhan, dang_thuc_hien, da_hoan_thanh và huy.

| Cột           | Kiểu    | Ràng buộc                                                                                   | Ghi chú                   |
| ------------- | ------- | ------------------------------------------------------------------------------------------- | ------------------------- |
| id            | INTEGER | PRIMARY KEY AUTOINCREMENT                                                                   | Khóa chính                |
| khach_hang_id | INTEGER | NOT NULL FK → khach_hang(id)                                                                | Khóa ngoại đến khách hàng |
| xe_id         | INTEGER | NOT NULL FK → xe(id)                                                                        | Khóa ngoại đến xe         |
| nhan_vien_id  | INTEGER | FK → nhan_vien(id)                                                                          | Khóa ngoại đến nhân viên  |
| ngay_du_kien  | TEXT    | NOT NULL                                                                                    | Ngày dự kiến              |
| ngay_thuc_te  | TEXT    |                                                                                             | Ngày thực tế              |
| km_xe         | INTEGER | CHECK(≥0)                                                                                   | Số km xe                  |
| noi_dung      | TEXT    |                                                                                             | Nội dung                  |
| chi_phi       | INTEGER | DEFAULT 0 CHECK(≥0)                                                                         | Chi phí                   |
| trang_thai    | TEXT    | DEFAULT 'cho_xac_nhan' CHECK(cho_xac_nhan, da_xac_nhan, dang_thuc_hien, da_hoan_thanh, huy) | Trạng thái                |
| ghi_chu       | TEXT    |                                                                                             | Ghi chú                   |
| created_by    | INTEGER | FK → nhan_vien(id)                                                                          | Người tạo                 |
| created_at    | TEXT    | DEFAULT CURRENT_TIMESTAMP                                                                   | Thời gian tạo             |
| updated_at    | TEXT    |                                                                                             | Thời gian cập nhật        |

### Bảng cuu_ho

Yêu cầu cứu hộ khẩn cấp. Ghi nhận vị trí, mô tả sự cố và thời gian xử lý. Trạng thái gồm tiep_nhan, dang_xu_ly, hoan_thanh, huy và tu_choi (cập nhật từ migration_032).

| Cột               | Kiểu    | Ràng buộc                                                                  | Ghi chú                   |
| ----------------- | ------- | -------------------------------------------------------------------------- | ------------------------- |
| id                | INTEGER | PRIMARY KEY AUTOINCREMENT                                                  | Khóa chính                |
| khach_hang_id     | INTEGER | NOT NULL FK → khach_hang(id)                                               | Khóa ngoại đến khách hàng |
| xe_id             | INTEGER | NOT NULL FK → xe(id)                                                       | Khóa ngoại đến xe         |
| nhan_vien_id      | INTEGER | FK → nhan_vien(id)                                                         | Khóa ngoại đến nhân viên  |
| vi_tri            | TEXT    | NOT NULL                                                                   | Vị trí                    |
| mo_ta             | TEXT    |                                                                            | Mô tả                     |
| thoi_gian_yeu_cau | TEXT    | DEFAULT CURRENT_TIMESTAMP                                                  | Thời gian yêu cầu         |
| thoi_gian_xu_ly   | TEXT    |                                                                            | Thời gian xử lý           |
| trang_thai        | TEXT    | DEFAULT 'tiep_nhan' CHECK(tiep_nhan, dang_xu_ly, hoan_thanh, huy, tu_choi) | Trạng thái                |
| chi_phi           | INTEGER | DEFAULT 0 CHECK(≥0)                                                        | Chi phí                   |
| ghi_chu           | TEXT    |                                                                            | Ghi chú                   |
| created_by        | INTEGER | FK → nhan_vien(id)                                                         | Người tạo                 |
| created_at        | TEXT    | DEFAULT CURRENT_TIMESTAMP                                                  | Thời gian tạo             |
| updated_at        | TEXT    |                                                                            | Thời gian cập nhật        |

---

## 8. Bảng tài chính

### Bảng tra_gop

Thông tin trả góp cho hợp đồng. Mỗi hợp đồng có tối đa một gói trả góp (hop_dong_id là UNIQUE). Lưu trữ thông tin ngân hàng, số tiền vay, lãi suất năm (tối đa 30%), số kỳ thanh toán (6 đến 84 tháng) và số tiền trả mỗi tháng. Cột trang_thai (dang_tra hoặc hoan_thanh) được thêm ở migration_023.

| Cột               | Kiểu    | Ràng buộc                                      | Ghi chú                 |
| ----------------- | ------- | ---------------------------------------------- | ----------------------- |
| id                | INTEGER | PRIMARY KEY AUTOINCREMENT                      | Khóa chính              |
| hop_dong_id       | INTEGER | UNIQUE NOT NULL FK → hop_dong(id)              | Khóa ngoại đến hợp đồng |
| ngan_hang         | TEXT    | NOT NULL                                       | Ngân hàng               |
| so_tien_vay       | INTEGER | NOT NULL CHECK(≥0)                             | Số tiền vay             |
| lai_suat_nam      | REAL    | NOT NULL CHECK(0-30)                           | Lãi suất năm (%)        |
| so_ky             | INTEGER | NOT NULL CHECK(6-84)                           | Số kỳ (tháng)           |
| so_tien_tra_thang | INTEGER | NOT NULL                                       | Số tiền trả tháng       |
| trang_thai        | TEXT    | DEFAULT 'dang_tra' CHECK(dang_tra, hoan_thanh) | Trạng thái gói trả góp  |
| created_by        | INTEGER | FK → nhan_vien(id)                             | Người tạo               |
| created_at        | TEXT    | DEFAULT CURRENT_TIMESTAMP                      | Thời gian tạo           |
| updated_at        | TEXT    |                                                | Thời gian cập nhật      |

### Bảng tra_gop_lich_su

Lịch sử thanh toán từng kỳ của gói trả góp. Mỗi kỳ có ngày đến hạn, số tiền phải trả và trạng thái (chua_tra, da_tra, qua_han). Hệ thống tự động cảnh báo khi kỳ thanh toán quá hạn 5 ngày.

| Cột              | Kiểu    | Ràng buộc                                           | Ghi chú                 |
| ---------------- | ------- | --------------------------------------------------- | ----------------------- |
| id               | INTEGER | PRIMARY KEY AUTOINCREMENT                           | Khóa chính              |
| tra_gop_id       | INTEGER | NOT NULL FK → tra_gop(id)                           | Khóa ngoại đến trả góp  |
| ky_thu           | INTEGER | NOT NULL                                            | Kỳ thứ                  |
| ngay_den_han     | TEXT    | NOT NULL                                            | Ngày đến hạn            |
| so_tien_phai_tra | INTEGER | NOT NULL                                            | Số tiền phải trả        |
| ngay_thuc_te     | TEXT    |                                                     | Ngày thực tế thanh toán |
| trang_thai       | TEXT    | DEFAULT 'chua_tra' CHECK(chua_tra, da_tra, qua_han) | Trạng thái              |
| ghi_chu          | TEXT    |                                                     | Ghi chú                 |
| created_at       | TEXT    | DEFAULT CURRENT_TIMESTAMP                           | Thời gian tạo           |

---

## 9. Bảng marketing

### Bảng chien_dich_mk

Chiến dịch marketing. Ghi nhận kênh tiếp thị (facebook, google_ads, youtube, truyen_hinh, bao_chi, truyen_mieng, khac), ngân sách, mục tiêu và số lượng lead mục tiêu. Trạng thái gồm nhap, dang_chay và ket_thuc.

| Cột                    | Kiểu    | Ràng buộc                                                                               | Ghi chú                |
| ---------------------- | ------- | --------------------------------------------------------------------------------------- | ---------------------- |
| id                     | INTEGER | PRIMARY KEY AUTOINCREMENT                                                               | Khóa chính             |
| ten_chien_dich         | TEXT    | NOT NULL                                                                                | Tên chiến dịch         |
| kenh_tiep_thi          | TEXT    | NOT NULL CHECK(facebook, google_ads, youtube, truyen_hinh, bao_chi, truyen_mieng, khac) | Kênh tiếp thị          |
| ngay_bat_dau           | TEXT    | NOT NULL                                                                                | Ngày bắt đầu           |
| ngay_ket_thuc          | TEXT    | NOT NULL                                                                                | Ngày kết thúc          |
| ngan_sach              | INTEGER | DEFAULT 0 CHECK(≥0)                                                                     | Ngân sách              |
| muc_tieu               | TEXT    |                                                                                         | Mục tiêu               |
| so_luong_lead_muc_tieu | INTEGER | DEFAULT 0                                                                               | Số lượng lead mục tiêu |
| trang_thai             | TEXT    | DEFAULT 'nhap' CHECK(nhap, dang_chay, ket_thuc)                                         | Trạng thái             |
| created_by             | INTEGER | FK → nhan_vien(id)                                                                      | Người tạo              |
| created_at             | TEXT    | DEFAULT CURRENT_TIMESTAMP                                                               | Thời gian tạo          |
| updated_at             | TEXT    |                                                                                         | Thời gian cập nhật     |

### Bảng lead

Khách hàng tiềm năng thu thập từ các chiến dịch marketing. Mỗi lead có thể được chăm sóc bởi một nhân viên phụ trách và chuyển đổi thành khách hàng thực tế (khach_hang_id). Trạng thái gồm moi, dang_cham_soc, chuyen_doi và tu_choi.

| Cột                    | Kiểu    | Ràng buộc                                                    | Ghi chú                                    |
| ---------------------- | ------- | ------------------------------------------------------------ | ------------------------------------------ |
| id                     | INTEGER | PRIMARY KEY AUTOINCREMENT                                    | Khóa chính                                 |
| chien_dich_id          | INTEGER | FK → chien_dich_mk(id)                                       | Khóa ngoại đến chiến dịch                  |
| ho_ten                 | TEXT    | NOT NULL                                                     | Họ và tên                                  |
| so_dien_thoai          | TEXT    | NOT NULL                                                     | Số điện thoại                              |
| email                  | TEXT    |                                                              | Email                                      |
| nguon                  | TEXT    |                                                              | Nguồn gốc                                  |
| nhu_cau                | TEXT    |                                                              | Nhu cầu                                    |
| nhan_vien_phu_trach_id | INTEGER | FK → nhan_vien(id)                                           | Nhân viên phụ trách                        |
| trang_thai             | TEXT    | DEFAULT 'moi' CHECK(moi, dang_cham_soc, chuyen_doi, tu_choi) | Trạng thái                                 |
| khach_hang_id          | INTEGER | FK → khach_hang(id)                                          | Khóa ngoại đến khách hàng (khi chuyển đổi) |
| ghi_chu                | TEXT    |                                                              | Ghi chú                                    |
| created_by             | INTEGER | FK → nhan_vien(id)                                           | Người tạo                                  |
| created_at             | TEXT    | DEFAULT CURRENT_TIMESTAMP                                    | Thời gian tạo                              |
| updated_at             | TEXT    |                                                              | Thời gian cập nhật                         |

---

## 10. Bảng khiếu nại

### Bảng khieu_nai

Khiếu nại của khách hàng. Hỗ trợ bốn mức độ (thap, trung_binh, cao) và bốn nguồn gốc (chat_luong_xe, dich_vu, bao_hanh, khac). Mỗi khiếu nại được xử lý bởi một nhân viên, có đánh giá hài lòng từ 1 đến 5 sau khi giải quyết. Trạng thái gồm moi, dang_xu_ly, da_giai_quyet và da_dong.

| Cột                | Kiểu    | Ràng buộc                                                    | Ghi chú                   |
| ------------------ | ------- | ------------------------------------------------------------ | ------------------------- |
| id                 | INTEGER | PRIMARY KEY AUTOINCREMENT                                    | Khóa chính                |
| khach_hang_id      | INTEGER | NOT NULL FK → khach_hang(id)                                 | Khóa ngoại đến khách hàng |
| hop_dong_id        | INTEGER | FK → hop_dong(id)                                            | Khóa ngoại đến hợp đồng   |
| nhan_vien_xu_ly_id | INTEGER | FK → nhan_vien(id)                                           | Nhân viên xử lý           |
| tieu_de            | TEXT    | NOT NULL                                                     | Tiêu đề                   |
| noi_dung           | TEXT    | NOT NULL                                                     | Nội dung                  |
| muc_do             | TEXT    | DEFAULT 'trung_binh' CHECK(thap, trung_binh, cao)            | Mức độ                    |
| nguon_goc          | TEXT    | CHECK(chat_luong_xe, dich_vu, bao_hanh, khac)                | Nguồn gốc                 |
| trang_thai         | TEXT    | DEFAULT 'moi' CHECK(moi, dang_xu_ly, da_giai_quyet, da_dong) | Trạng thái                |
| ngay_tao           | TEXT    | DEFAULT CURRENT_TIMESTAMP                                    | Ngày tạo                  |
| ngay_xu_ly         | TEXT    |                                                              | Ngày xử lý                |
| ngay_dong          | TEXT    |                                                              | Ngày đóng                 |
| danh_gia_hai_long  | INTEGER | CHECK(1-5)                                                   | Đánh giá hài lòng         |
| ly_do              | TEXT    |                                                              | Lý do                     |
| created_by         | INTEGER | FK → nhan_vien(id)                                           | Người tạo                 |
| created_at         | TEXT    | DEFAULT CURRENT_TIMESTAMP                                    | Thời gian tạo             |
| updated_at         | TEXT    |                                                              | Thời gian cập nhật        |

---

## 11. Bảng bảo hiểm

### Bảng cong_ty_bh

Công ty bảo hiểm đối tác. Mỗi công ty có mã duy nhất và trạng thái hoạt động.

| Cột           | Kiểu    | Ràng buộc                                             | Ghi chú            |
| ------------- | ------- | ----------------------------------------------------- | ------------------ |
| id            | INTEGER | PRIMARY KEY AUTOINCREMENT                             | Khóa chính         |
| ma_cty        | TEXT    | UNIQUE NOT NULL                                       | Mã công ty         |
| ten_cty       | TEXT    | NOT NULL                                              | Tên công ty        |
| dia_chi       | TEXT    |                                                       | Địa chỉ            |
| so_dien_thoai | TEXT    |                                                       | Số điện thoại      |
| email         | TEXT    |                                                       | Email              |
| trang_thai    | TEXT    | DEFAULT 'hoat_dong' CHECK(hoat_dong, khong_hoat_dong) | Trạng thái         |
| created_at    | TEXT    | DEFAULT CURRENT_TIMESTAMP                             | Thời gian tạo      |
| updated_at    | TEXT    |                                                       | Thời gian cập nhật |

### Bảng bao_hiem

Hợp đồng bảo hiểm liên kết với bảo hành. Hỗ trợ năm loại bảo hiểm: tnds, tai_nan, chao_no, that_lac và khac. Lưu trữ số policy, ngày mua, ngày hiệu lực, ngày hết hạn, phí bảo hiểm, giá trị bảo hiểm và thông tin đại lý bán. Các cột cong_ty_bh_id, ngay_hieu_luc, xe_id, hop_dong_id được thêm ở migration_029. Cột gia_tri_bh được thêm ở migration_031.

| Cột           | Kiểu    | Ràng buộc                                                               | Ghi chú                         |
| ------------- | ------- | ----------------------------------------------------------------------- | ------------------------------- |
| id            | INTEGER | PRIMARY KEY AUTOINCREMENT                                               | Khóa chính                      |
| bao_hanh_id   | INTEGER | NOT NULL FK → bao_hanh(id)                                              | Khóa ngoại đến bảo hành         |
| loai_bh       | TEXT    | NOT NULL DEFAULT 'tnds' CHECK(tnds, tai_nan, chao_no, that_lac, khac)   | Loại bảo hiểm                   |
| so_policy     | TEXT    |                                                                         | Số policy                       |
| ngay_mua      | TEXT    | NOT NULL                                                                | Ngày mua                        |
| ngay_hieu_luc | TEXT    |                                                                         | Ngày hiệu lực                   |
| ngay_het_han  | TEXT    | NOT NULL                                                                | Ngày hết hạn                    |
| phi_bh        | INTEGER | DEFAULT 0                                                               | Phí bảo hiểm                    |
| gia_tri_bh    | INTEGER | DEFAULT 0                                                               | Giá trị bảo hiểm                |
| dai_ly_ban_id | INTEGER | FK → nhan_vien(id)                                                      | Đại lý bán                      |
| trang_thai    | TEXT    | DEFAULT 'con_hieu_luc' CHECK(con_hieu_luc, het_han, huy, da_thanh_toan) | Trạng thái                      |
| xe_id         | INTEGER | FK → xe(id)                                                             | Khóa ngoại đến xe               |
| hop_dong_id   | INTEGER | FK → hop_dong(id)                                                       | Khóa ngoại đến hợp đồng         |
| cong_ty_bh_id | INTEGER | FK → cong_ty_bh(id)                                                     | Khóa ngoại đến công ty bảo hiểm |
| ghi_chu       | TEXT    |                                                                         | Ghi chú                         |
| created_by    | INTEGER | FK → nhan_vien(id)                                                      | Người tạo                       |
| created_at    | TEXT    | DEFAULT CURRENT_TIMESTAMP                                               | Thời gian tạo                   |
| updated_at    | TEXT    |                                                                         | Thời gian cập nhật              |

---

## 13. Chỉ mục

Hệ thống sử dụng các chỉ mục sau để tối ưu hiệu năng truy vấn, được tạo qua các migration 001-021:

| Bảng             | Chỉ mục                         | Cột                                                  | Loại   |
| ---------------- | ------------------------------- | ---------------------------------------------------- | ------ |
| vai_tro          | idx_vai_tro_ma                  | ma_vai_tro                                           | UNIQUE |
| nhan_vien        | idx_nv_username                 | username                                             | UNIQUE |
| nhan_vien        | idx_nv_vai_tro                  | vai_tro_id                                           |        |
| khach_hang       | idx_kh_so_dien_thoai            | so_dien_thoai                                        | UNIQUE |
| khach_hang       | idx_kh_phan_loai                | phan_loai                                            |        |
| khach_hang       | idx_kh_tong_gia_tri             | tong_gia_tri_mua DESC                                |        |
| khach_hang       | idx_kh_ngay_sinh                | ngay_sinh                                            |        |
| khach_hang       | idx_kh_ngay_sinh_not_null       | ngay_sinh WHERE NOT NULL                             |        |
| xe               | idx_xe_hang_dong                | hang, dong_xe                                        |        |
| xe               | idx_xe_trang_thai               | trang_thai                                           |        |
| xe               | idx_xe_ma_xe                    | ma_xe                                                | UNIQUE |
| xe               | idx_xe_ton_low                  | so_luong_ton, muc_toi_thieu WHERE con_hang           |        |
| phu_kien         | idx_pk_ma                       | ma_pk                                                | UNIQUE |
| phu_kien         | idx_pk_phan_loai                | phan_loai                                            |        |
| phu_kien         | idx_pk_ton_kho                  | ton_kho                                              |        |
| hop_dong         | idx_hd_ma                       | ma_hop_dong                                          | UNIQUE |
| hop_dong         | idx_hd_trang_thai               | trang_thai                                           |        |
| hop_dong         | idx_hd_ngay_tao                 | ngay_tao                                             |        |
| hop_dong         | idx_hd_khach                    | khach_hang_id                                        |        |
| hop_dong         | idx_hd_xe                       | xe_id                                                |        |
| hop_dong         | idx_hd_nv                       | nhan_vien_id                                         |        |
| hop_dong         | idx_hd_nv_ngay                  | nhan_vien_id, ngay_tao                               |        |
| hop_dong         | idx_hd_tong_tien                | tong_tien                                            |        |
| hop_dong         | idx_hop_dong_ngay_trang_thai    | ngay_tao, trang_thai                                 |        |
| hop_dong         | idx_hop_dong_trang_thai_nv      | trang_thai, nhan_vien_id                             |        |
| hop_dong         | idx_hop_dong_khach_hang         | khach_hang_id                                        |        |
| hop_dong         | idx_hop_dong_ngay_nv            | ngay_tao, nhan_vien_id                               |        |
| hop_dong         | idx_hd_giao_ngay_status         | ngay_giao_xe, trang_thai WHERE da_giao_xe            |        |
| nha_cung_cap     | idx_ncc_ma                      | ma_ncc                                               | UNIQUE |
| nha_cung_cap     | idx_ncc_ten                     | ten_ncc                                              |        |
| bao_hanh         | idx_bh_hop_dong                 | hop_dong_id                                          |        |
| bao_hanh         | idx_bh_xe                       | xe_id                                                |        |
| bao_hanh         | idx_bh_ngay_ket_thuc            | ngay_ket_thuc                                        |        |
| bao_hanh         | idx_bh_trang_thai               | trang_thai                                           |        |
| bao_hanh         | idx_bh_dai_ly_ban               | dai_ly_ban_id                                        |        |
| bao_hanh         | idx_bh_ngay_ket_thuc_trang_thai | ngay_ket_thuc, trang_thai                            |        |
| bao_hanh         | idx_bh_expiring_30days          | ngay_ket_thuc, trang_thai WHERE con_hieu_luc         |        |
| bao_hanh         | idx_bh_so_khung                 | so_khung                                             |        |
| bao_hanh         | idx_bh_so_may                   | so_may                                               |        |
| bao_hanh         | idx_bh_is_external              | is_external                                          |        |
| bao_hanh_yeu_cau | idx_bhyc_bao_hanh               | bao_hanh_id                                          |        |
| bao_hanh_yeu_cau | idx_bhyc_trang_thai             | trang_thai                                           |        |
| bao_duong        | idx_bd_khach                    | khach_hang_id                                        |        |
| bao_duong        | idx_bd_xe                       | xe_id                                                |        |
| bao_duong        | idx_bd_ngay                     | ngay_du_kien                                         |        |
| bao_duong        | idx_bd_trang_thai               | trang_thai                                           |        |
| bao_duong        | idx_bd_ngay_du_kien_7days       | ngay_du_kien WHERE cho_xac_nhan                      |        |
| cuu_ho           | idx_cuu_ho_khach                | khach_hang_id                                        |        |
| cuu_ho           | idx_cuu_ho_xe                   | xe_id                                                |        |
| cuu_ho           | idx_cuu_ho_trang_thai           | trang_thai                                           |        |
| tra_gop          | idx_tg_hop_dong                 | hop_dong_id                                          |        |
| tra_gop          | idx_tg_ngan_hang                | ngan_hang                                            |        |
| tra_gop_lich_su  | idx_tgls_tra_gop                | tra_gop_id                                           |        |
| tra_gop_lich_su  | idx_tgls_ngay_den_han           | ngay_den_han                                         |        |
| tra_gop_lich_su  | idx_tgls_trang_thai             | trang_thai                                           |        |
| tra_gop_lich_su  | idx_tgls_qua_han                | trang_thai, ngay_den_han                             |        |
| tra_gop_lich_su  | idx_tgls_chua_tra_den_han       | ngay_den_han, trang_thai WHERE chua_tra              |        |
| tra_gop_lich_su  | idx_tgls_ngay_den_han_v2        | ngay_den_han                                         |        |
| tra_gop_lich_su  | idx_tgls_trang_thai_v2          | trang_thai                                           |        |
| khuyen_mai       | idx_km_trang_thai               | trang_thai                                           |        |
| khuyen_mai       | idx_km_ngay                     | tu_ngay, den_ngay                                    |        |
| khuyen_mai       | idx_km_loai                     | loai_km                                              |        |
| km_pham_vi       | idx_kmp_km                      | khuyen_mai_id                                        |        |
| chien_dich_mk    | idx_cd_trang_thai               | trang_thai                                           |        |
| chien_dich_mk    | idx_cd_ngay                     | ngay_bat_dau, ngay_ket_thuc                          |        |
| lead             | idx_lead_chien_dich             | chien_dich_id                                        |        |
| lead             | idx_lead_trang_thai             | trang_thai                                           |        |
| lead             | idx_lead_nv                     | nhan_vien_phu_trach_id                               |        |
| lead             | idx_lead_so_dt                  | so_dien_thoai                                        |        |
| lead             | idx_lead_chuyen_doi             | trang_thai, chien_dich_id                            |        |
| khieu_nai        | idx_kn_khach                    | khach_hang_id                                        |        |
| khieu_nai        | idx_kn_hop_dong                 | hop_dong_id                                          |        |
| khieu_nai        | idx_kn_nv_xu_ly                 | nhan_vien_xu_ly_id                                   |        |
| khieu_nai        | idx_kn_trang_thai               | trang_thai                                           |        |
| khieu_nai        | idx_kn_muc_do                   | muc_do                                               |        |
| khieu_nai        | idx_kn_ngay_tao                 | ngay_tao                                             |        |
| khieu_nai        | idx_kn_priority                 | muc_do DESC, ngay_tao ASC                            |        |
| khieu_nai        | idx_kn_nguon_goc                | nguon_goc                                            |        |
| khieu_nai        | idx_kn_status_muc_do            | trang_thai, muc_do                                   |        |
| khieu_nai        | idx_kn_kh_open                  | khach_hang_id, trang_thai WHERE moi, dang_xu_ly      |        |
| khieu_nai        | idx_kn_nv_open                  | nhan_vien_xu_ly_id, trang_thai WHERE moi, dang_xu_ly |        |
| audit_log        | idx_al_nv                       | nhan_vien_id                                         |        |
| audit_log        | idx_al_bang                     | bang_anh_huong                                       |        |
| audit_log        | idx_al_thoi_gian                | thoi_gian                                            |        |
| audit_log        | idx_al_thoi_gian_hanh_dong      | thoi_gian, hanh_dong                                 |        |
| bao_hiem         | idx_bao_hiem_bao_hanh           | bao_hanh_id                                          |        |
| bao_hiem         | idx_bao_hiem_xe                 | xe_id                                                |        |
| bao_hiem         | idx_bao_hiem_trang_thai         | trang_thai                                           |        |
| bao_hiem         | idx_bhiem_so_policy             | so_policy                                            |        |
| bao_hiem         | idx_bhiem_dai_ly                | dai_ly_ban_id                                        |        |
| bao_hiem         | idx_bhiem_ngay_het_han          | ngay_het_han                                         |        |

---

## 14. Sơ đồ quan hệ tổng thể

```
vai_tro ────────────────< nhan_vien >────── dai_ly
                              │
khach_hang <─────── hop_dong >────────────── xe
                 │   │
                 │   ├──< hop_dong_phu_kien >── phu_kien
                 │   │
                 │   ├── bao_hanh >────── bao_hanh_yeu_cau
                 │   │
                 │   ├── tra_gop >─────── tra_gop_lich_su
                 │   │
                 │   └── bao_hiem ──────── cong_ty_bh
                 │
                 ├──< bao_duong
                 ├──< cuu_ho
                 ├──< khieu_nai
                 └──< lead >───────────── chien_dich_mk

nha_cung_cap >── nhap_kho >── chi_tiet_nhap_kho
don_dat_hang >── chi_tiet_don_dat
phu_kien >── combo_chi_tiet >── combo_phu_kien

bao_hanh >── bao_hiem >── cong_ty_bh
```

---

_Ngày cập nhật: Tháng 5 năm 2026. Tổng số: 30 bảng, 9 view, 82 chỉ mục._
