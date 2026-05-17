# KẾ HOẠCH KIỂM THỬ

## 1. Mục tiêu

Đảm bảo hệ thống Car Dealership Management hoạt động đúng theo nghiệp vụ, đáp ứng hiệu năng và không có lỗi bảo mật. Sử dụng pytest làm framework kiểm thử.

## 2. Phân loại kiểm thử

**Kiểm thử đơn vị (Unit Test):** Kiểm tra từng service riêng lẻ. File test tương ứng mỗi service trong thư mục tests/. Sử dụng fixture database SQLite in-memory. Chạy với `pytest tests/ -m "not perf"`.

**Kiểm thử tích hợp (Integration Test):** Kiểm tra luồng nghiệp vụ xuyên suốt. Tám workflow chính (wf01-wf08): Nhập kho, Bán xe chuẩn, Bán trả góp, Bảo hành, Bảo dưỡng, Khiếu nại, Marketing dẫn đến Khách hàng, Hủy hợp đồng. Chạy với `pytest tests/ -m wf04 -v` cho từng workflow.

**Kiểm thử hiệu năng (Performance Test):** Đo thời gian truy vấn. Ba mức: simple (<50ms), join_agg (<200ms), report (<500ms). Chạy với `pytest tests/ -m perf`.

**Kiểm thử chấp nhận (UAT):** Kịch bản kiểm thử thủ công trong test_uat_manual.py. Kiểm tra giao diện theo THIET_KE_GUI_CHI_TIET.md.

**Kiểm thử hồi quy (Regression):** Pre-commit hook tự động chạy flake8 + isort + black + pytest. Tất cả test phải pass trước mỗi lần commit.

## 3. Lệnh chạy

| Lệnh | Mục đích |
|------|----------|
| `pytest tests/ -v` | Chạy tất cả test |
| `pytest tests/path/to_file.py::Class::method -v` | Một test cụ thể |
| `pytest tests/ -m simple` | SELECT query (<50ms) |
| `pytest tests/ -m wf04 -v` | Workflow Bảo hành |
| `pytest tests/ -m perf` | Benchmark |
| `flake8 app tests --max-line-length=88` | Kiểm tra coding style |

## 4. Checklist chất lượng

80% code coverage cho application/services. Mỗi business rule (BR-CALC-*) có unit test riêng. Mỗi workflow có integration test. 100% migration được kiểm tra khả năng chạy xuôi và rollback. Ràng buộc CHECK và FOREIGN KEY được test trong fk_restrict và check_constraints.

## 5. Báo cáo

Kiểm thử được chạy tự động qua pre-commit. Kết quả hiển thị dưới dạng terminal output với pytest -v. Log lỗi ghi vào app/logs/ nếu có. Mọi test phải đạt trạng thái PASSED trước khi merge code.

---

*Ngày cập nhật: Tháng 5 năm 2026.*
