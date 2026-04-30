"""Manual UAT tests for G2.3 - Main Window, Sidebar & Navigation.

This file documents manual test scenarios for UAT.
Run these manually to verify the main window navigation flow.

## Prerequisites
1. Application database must be seeded with test data
2. Default credentials: admin / Admin@123, sales01 / Admin@123, kythuat01 / Admin@123

## Test Scenarios

### TC-01: Login as Admin - Sidebar shows 15+ modules
1. Start application → Login screen
2. Enter username: `admin`, password: `Admin@123`
3. Click "Đăng nhập"
4. **Expected**: MainWindow appears with sidebar showing 15+ modules:
   - Dashboard 📊
   - Quản lý xe 🚗
   - Khách hàng 👥
   - Nhân viên 👤
   - Hợp đồng 📄
   - Kho hàng 📦
   - Phụ kiện 🔧
   - Khuyến mãi 🎁
   - Bảo hành 🛡️
   - Nhà cung cấp 🏭
   - Trả góp 💳
   - Bảo dưỡng 🔧
   - Cứu hộ 🚨
   - Marketing 📢
   - Khiếu nại ⚠️
   - Báo cáo 📈
   - Cài đặt ⚙️

### TC-02: Login as Sales - Sidebar shows limited modules
1. Logout or restart application
2. Login with username: `sales01`, password: `Admin@123`
3. **Expected**: MainWindow appears with sidebar showing limited modules:
   - Dashboard, Xe, Khách hàng, Hợp đồng, Kho, Phụ kiện, Khuyến mãi, Báo cáo
   - Should NOT see: Nhân viên, Bảo hành, Nhà cung cấp, Trả góp, Bảo dưỡng, Cứu hộ, Khiếu nại, Cài đặt

### TC-03: Login as Kỹ thuật - Sidebar shows 5 modules
1. Logout or restart application
2. Login with username: `kythuat01`, password: `Admin@123`
3. **Expected**: MainWindow appears with sidebar showing ~5 modules:
   - Dashboard, Bảo hành, Bảo dưỡng, Cứu hộ, Báo cáo

### TC-04: Click sidebar item - Content area changes
1. Login as admin
2. Click "Quản lý xe" in sidebar
3. **Expected**:
   - Sidebar item highlights with #f5f5f7 background
   - Content area shows placeholder for Xe module

### TC-05: TopBar user dropdown - Profile
1. Login as admin
2. Click user dropdown (▼) in top-right
3. Click "Hồ sơ"
4. **Expected**: Module changes to profile view

### TC-06: TopBar user dropdown - Change Password
1. Login as admin
2. Click user dropdown (▼) in top-right
3. Click "Đổi mật khẩu"
4. **Expected**: Change password dialog opens (S-AUTH-02)

### TC-07: TopBar user dropdown - Logout
1. Login as admin
2. Click user dropdown (▼) in top-right
3. Click "Đăng xuất"
4. **Expected**: 
   - MainWindow closes
   - Login screen appears

### TC-08: StatusBar - Time updates
1. Login as admin
2. Observe StatusBar at bottom
3. **Expected**: 
   - Time (HH:mm:ss) updates every second
   - User info displayed on left
   - Version (v1.0.0) displayed on right

### TC-09: Keyboard shortcut Ctrl+1..9 - Module switching
1. Login as admin
2. Press Ctrl+1
3. **Expected**: Dashboard module selected
4. Press Ctrl+2
5. **Expected**: Xe module selected

### TC-10: Keyboard shortcut Ctrl+L - Logout
1. Login as admin
2. Press Ctrl+L
3. **Expected**: 
   - MainWindow closes
   - Login screen appears

### TC-11: First login - Must change password
1. Create new user with must_change_password=True
2. Login with that user
3. **Expected**: 
   - Change password dialog appears immediately
   - Cannot skip or cancel
   - Must enter new password to proceed

### TC-12: Dealer name displayed correctly
1. Login as admin
2. **Expected**: TopBar shows "Đại lý xe hơi" (or configured dealer name)
3. Check StatusBar version display

## Expected Test Results

| Test Case | Result | Notes |
|-----------|--------|-------|
| TC-01 | PASS/FAIL | Admin should see 15+ modules |
| TC-02 | PASS/FAIL | Sales should see ~8 modules |
| TC-03 | PASS/FAIL | Kỹ thuật should see ~5 modules |
| TC-04 | PASS/FAIL | Sidebar highlight works |
| TC-05 | PASS/FAIL | Profile menu works |
| TC-06 | PASS/FAIL | Change password opens |
| TC-07 | PASS/FAIL | Logout works |
| TC-08 | PASS/FAIL | Time updates every second |
| TC-09 | PASS/FAIL | Ctrl+1..9 switches modules |
| TC-10 | PASS/FAIL | Ctrl+L logs out |
| TC-11 | PASS/FAIL | Force password change works |
| TC-12 | PASS/FAIL | Dealer name shows correctly |
"""


# This file is for documentation purposes
# Run manual tests according to the test cases above