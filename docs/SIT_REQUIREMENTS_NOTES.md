# Sprint G6.1 REQ Analysis Notes

## Mục 6 — 8 Workflow E2E (Tóm tắt điểm test chính)

### WF-01: Nhập kho xe mới
- **Trigger**: Admin tạo đơn đặt hàng NCC → giao hàng → bấm "Nhận"
- **Kết quả**: `nhap_kho` được tạo, `xe.so_luong_ton` tăng, xe `da_ban` → `con_hang`
- **Điểm test chính**:
  - Admin tạo đơn đặt hàng (trạng thái `nhap → da_gui → da_nhan`)
  - Khi `da_nhan`: trigger tự tạo `nhap_kho` (BR-NCC-05)
  - Tồn kho tăng đúng số lượng
  - Xe `da_ban` nhập kho mới → tự chuyển `con_hang` (BR-XE-05)
  - Audit log `IMPORT_STOCK`

### WF-02: Bán xe (chuẩn)
- **Trigger**: Sales tạo HĐ wizard 4 bước → thanh toán → giao xe
- **Kết quả**: HĐ `da_giao_xe`, tồn kho giảm, KH cập nhật, BH tự sinh, KPI NV cập nhật
- **Điểm test chính**:
  - Wizard 4 bước: KH → Xe+PK → KM → Xác nhận
  - Snapshot giá: `gia_xe` và `gia_ban` PK cố định không đổi khi giá gốc thay đổi (BR-HD-* snapshot)
  - Áp dụng đúng 1 KM tối đa (BR-HD-07)
  - Tổng tiền: `gia_xe + PK − giảm_KM` (BR-CALC-01)
  - Thanh toán: giảm tồn kho xe & PK (BR-HD-03)
  - Giao xe: tự sinh BH 24 tháng (BR-BH-01), cập nhật KH (BR-KH-03), tính KPI (BR-NV-03)
  - Không cho hủy sau `da_giao_xe` (BR-HD-06)
  - In PDF đầy đủ (BR-HD-10)

### WF-03: Bán xe trả góp
- **Trigger**: Như WF-02 + thiết lập trả góp sau khi tạo HĐ
- **Kết quả**: Tính tiền trả/tháng đúng công thức niên kim, sinh đủ kỳ
- **Điểm test chính**:
  - Công thức: `M = P × r × (1+r)^n / ((1+r)^n − 1)` (BR-CALC-04)
  - Sinh đủ n kỳ trả, mỗi kỳ cách 1 tháng (AC-TG-02)
  - Cảnh báo trả góp chậm ≥ 5 ngày (BR-TIME-03, BR-TG-08)
  - Hủy HĐ → xoá hồ sơ trả góp (BR-HD-05, BR-TG-10)

### WF-04: Bảo hành
- **Trigger**: KH đến yêu cầu BH → NV tạo yêu cầu → xử lý → hoàn thành
- **Kết quả**: Yêu cầu BH được xử lý, cập nhật trạng thái, in phiếu
- **Điểm test chính**:
  - Tìm BH theo SĐT/mã HĐ → hiển thị hồ sơ đầy đủ (thời hạn, phạm vi)
  - BH còn hiệu lực → phân loại `mien_phi` (lỗi NSX)
  - BH hết hạn → bắt buộc `tinh_phi` (BR-BH-04 A1)
  - Trạng thái: `tiep_nhan → dang_xu_ly → hoan_thanh` (BR-BH-05)
  - Cảnh báo BH sắp hết hạn 30 ngày Dashboard (BR-BH-03, AC-BH-02)
  - In phiếu BH đầy đủ (BR-BH-07)
  - Hủy HĐ → xoá BH liên quan (BR-BH-10)

### WF-05: Bảo dưỡng định kỳ
- **Trigger**: Hệ thống nhắc → KH đến → ghi nhận BD → thanh toán
- **Kết quả**: Lịch BD được tạo, cập nhật lịch tiếp theo
- **Điểm test chính**:
  - Dashboard nhắc lịch BD trước 7 ngày (BR-TIME-02)
  - Ghi nhận BD: nội dung, chi phí, kỹ thuật phụ trách
  - Tự lên lịch BD tiếp theo (BR-HM-01)

### WF-06: Xử lý khiếu nại
- **Trigger**: KH khiếu nại → ghi nhận → phân công → xử lý → đóng
- **Kết quả**: Khiếu nại được xử lý, KH đánh giá hài lòng
- **Điểm test chính**:
  - Tạo khiếu nại → trạng thái `moi` (BR-FLOW Khiếu nại)
  - Mức độ `cao` → badge đỏ Dashboard (BR-KN-03)
  - Cập nhật trạng thái kèm ghi chú lý do (BR-KN-05)
  - Xin đánh giá 1-5 sao → đóng khiếu nại (BR-KN-04)
  - KPI: thời gian xử lý ≤ 7 ngày (BR-KN-07)

### WF-07: Marketing → Lead → KH
- **Trigger**: Tạo chiến dịch → thu thập lead → chăm sóc → tạo HĐ
- **Kết quả**: Lead chuyển thành KH, tính ROI chiến dịch
- **Điểm test chính**:
  - Tạo chiến dịch → trạng thái `dang_chay`
  - Lead `moi` → `dang_cham_soc` → `chuyen_doi`
  - Khi tạo HĐ cho lead: hệ thống đề xuất chuyển lead → KH (UC-MK-03, BR-KH-07)
  - Tỷ lệ chuyển đổi = lead chuyển đổi / tổng lead (BR-CALC-06)
  - Báo cáo ROI: chiến dịch, ngân sách, lead, chuyển đổi

### WF-08: Hủy hợp đồng
- **Trigger**: Admin hủy HĐ → nhập lý do → hệ thống xử lý
- **Kết quả**: HĐ → `huy`, hoàn tồn kho, xoá BH/TG
- **Điểm test chính**:
  - Chỉ Admin được hủy (BR-HD-05)
  - `moi_tao` → hủy: chỉ hoàn tồn kho
  - `da_thanh_toan` → hủy: hoàn tồn kho + xoá BH + xoá TG (BR-HD-05)
  - Không cho hủy `da_giao_xe` (BR-HD-06)
  - Lý do hủy ≥ 10 ký tự (BR-UI-04)
  - Audit log `CANCEL_HD` với lý do

---

## Mục 9 — Acceptance Criteria (điểm test chính)

### AC-XE-01..03
- Thêm/sửa/xóa xe theo UC-XE-01..03
- Xóa thất bại khi xe có HĐ chưa hủy (BR-XE-02, BR-REF-01)
- Tìm kiếm ≤ 2 giây với 10.000 xe (C-PERF-01)
- Trạng thái tự cập nhật: `con_hang → da_ban` khi tồn = 0 + HĐ `da_giao_xe` (BR-XE-04)

### AC-KH-01..03
- Phân loại tự động: `Thuong < 500tr ≤ Thân thiết < 2 tỷ ≤ VIP` (BR-CALC-03)
- Trùng SĐT → reject với thông báo "KH đã có trong hệ thống" (BR-KH-02)
- Lịch sử giao dịch hiển thị đầy đủ kể cả HĐ `huy` (BR-KH-04)

### AC-HD-01..05
- Wizard 4 bước hoạt động trơn tru, quay lại không mất dữ liệu
- Tổng tiền đúng với mọi tổ hợp PK + KM (BR-CALC-01, 02)
- Chuyển trạng thái đúng BR-FLOW: `moi_tao → da_thanh_toan → da_giao_xe`
- PDF in đầy đủ (BR-HD-10): đại lý, KH, xe, PK, bảng giá, KM, điều khoản BH, chữ ký
- Hủy: hoàn tồn kho + xoá BH + xoá TG (AC-HD-05)

### AC-BH-01..02
- Tự sinh hồ sơ BH khi HĐ `da_giao_xe` (BR-BH-01)
  - `ngay_bat_dau = ngay_giao_xe`
  - `ngay_ket_thuc = ngay_bat_dau + thoi_han_bh` (default 24 tháng)
- Dashboard cảnh báo BH sắp hết hạn 30 ngày (BR-BH-03)

### AC-KM-01..02
- KM đúng phạm vi: hãng/dòng/xe cụ thể/xe tồn lâu > 90 ngày (BR-KM-04)
- Tiền giảm đúng: tiền mặt / phần trăm (BR-CALC-02)

### AC-TG-01..02
- Tiền trả/tháng đúng công thức niên kim (BR-CALC-04)
- Sinh đủ n kỳ trả, ngày cách nhau 1 tháng

### AC-BC-01..02
- 7 báo cáo (RP-01..07) xuất Excel (BR-BC-05)
- Số liệu khớp CSDL (sai số 0) (BR-BC-06)

### AC-SEC-01..04
- Mật khẩu bcrypt cost ≥ 12 (BR-SEC-01)
- Đăng nhập sai 5 lần → khoá 15 phút (BR-SEC-05)
- Session timeout 30 phút (BR-TIME-07)
- Audit log đầy đủ (BR-SEC-09)