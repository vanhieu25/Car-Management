"""Manual UAT tests - T-G2.2.TEST.06.

This file documents manual test scenarios for UAT.
Run these manually to verify the authentication flow.

## Prerequisites
1. Application database must be seeded with test data
2. Default credentials: admin / Admin@123

## Test Scenarios

### TC-01: Login thành công (Admin)
1. Mở ứng dụng → màn hình đăng nhập hiển thị
2. Nhập username: `admin`
3. Nhập password: `Admin@123`
4. Click "Đăng nhập"
5. **Kết quả mong đợi**: 
   - Đăng nhập thành công
   - Xuất hiện dialog "Đổi mật khẩu bắt buộc" (vì first login)
   - Hoặc hiển thị Main Window nếu đã đổi pass trước đó

### TC-02: Login thất bại - sai mật khẩu
1. Mở ứng dụng → màn hình đăng nhập
2. Nhập username: `admin`
3. Nhập password: `wrongpassword`
4. Click "Đăng nhập"
5. **Kết quả mong đợi**:
   - Thông báo lỗi màu đỏ: "Mật khẩu không đúng. Còn X lần thử."
   - Số lần thử giảm dần với mỗi lần sai

### TC-03: Login thất bại - tài khoản không tồn tại
1. Mở ứng dụng → màn hình đăng nhập
2. Nhập username: `nonexistent`
3. Nhập password: `anypassword`
4. Click "Đăng nhập"
5. **Kết quả mong đợi**:
   - Thông báo lỗi: "Tài khoản không tồn tại."

### TC-04: Tài khoản bị khóa sau 5 lần sai
1. Đăng nhập sai 5 lần với mật khẩu sai
2. **Kết quả mong đợi**:
   - Lần 5: Thông báo "Tài khoản bị khóa đến HH:mm"
   - Không thể đăng nhập trong thời gian khóa

### TC-05: Tài khoản khóa tự mở sau 15 phút
1. Đợi 15 phút sau khi bị khóa
2. Đăng nhập với mật khẩu đúng
3. **Kết quả mong đợi**:
   - Đăng nhập thành công (lockout đã hết hạn)

### TC-06: Đổi mật khẩu thành công
1. Đăng nhập → dialog đổi mật khẩu xuất hiện
2. Nhập mật khẩu cũ: `Admin@123`
3. Nhập mật khẩu mới: `NewPass@123`
4. Xác nhận mật khẩu mới: `NewPass@123`
5. Click "Xác nhận"
6. **Kết quả mong đợi**:
   - Toast "Đổi mật khẩu thành công!"
   - Chuyển sang Main Window

### TC-07: Đổi mật khẩu thất bại - mật khẩu mới quá ngắn
1. Đăng nhập → dialog đổi mật khẩu
2. Nhập mật khẩu cũ đúng
3. Nhập mật khẩu mới: `Short1` (dưới 8 ký tự)
4. **Kết quả mong đợi**:
   - Strength indicator màu đỏ
   - Thông báo lỗi khi click xác nhận: "Mật khẩu phải có ít nhất 8 ký tự"

### TC-08: Đổi mật khẩu thất bại - thiếu chữ cái
1. Dialog đổi mật khẩu
2. Mật khẩu mới: `12345678` (không có chữ cái)
3. **Kết quả mong đợi**:
   - Thông báo lỗi: "Mật khẩu phải chứa ít nhất 1 chữ"

### TC-09: Đổi mật khẩu thất bại - thiếu số
1. Dialog đổi mật khẩu
2. Mật khẩu mới: `PasswordOnly` (không có số)
3. **Kết quả mong đợi**:
   - Thông báo lỗi: "Mật khẩu phải chứa ít nhất 1 số"

### TC-10: Login với tài khoản Sales
1. Mở ứng dụng
2. Nhập username: `sales01`
3. Nhập password: `Admin@123`
4. Click "Đăng nhập"
5. **Kết quả mong đợi**:
   - Đăng nhập thành công
   - Role là "sales"

### TC-11: Login với tài khoản Kỹ thuật
1. Mở ứng dụng
2. Nhập username: `kythuat01`
3. Nhập password: `Admin@123`
4. Click "Đăng nhập"
5. **Kết quả mong đợi**:
   - Đăng nhập thành công
   - Role là "ky_thuat_bh"

### TC-12: Tài khoản inactive bị từ chối
1. (Cần admin update database: UPDATE nhan_vien SET trang_thai='inactive' WHERE username='sales01')
2. Thử đăng nhập với tài khoản inactive
3. **Kết quả mong đợi**:
   - Thông báo: "Tài khoản đã bị vô hiệu hóa"

## Expected Test Results

| Test Case | Kết quả | Ghi chú |
|-----------|---------|----------|
| TC-01 | ✅ PASS | |
| TC-02 | ✅ PASS | |
| TC-03 | ✅ PASS | |
| TC-04 | ✅ PASS | |
| TC-05 | ✅ PASS | Cần chờ 15 phút |
| TC-06 | ✅ PASS | |
| TC-07 | ✅ PASS | |
| TC-08 | ✅ PASS | |
| TC-09 | ✅ PASS | |
| TC-10 | ✅ PASS | |
| TC-11 | ✅ PASS | |
| TC-12 | ✅ PASS | Cần setup trước |
"""


# This file is for documentation purposes
# Run manual tests according to the test cases above
