"""Tests for KhieuNai (Complaint) Service.

Test cases:
- TEST.01: Unit test update_status → reject nếu thiếu ly_do (BR-KN-05)
- TEST.02: Unit test close → reject nếu chưa có satisfaction (BR-KN-04)
- TEST.03: Integration WF-06: tạo KN → A-01 phân công → A-02 xử lý → đánh giá → đóng
- TEST.04: UAT theo AC-KN-*
"""

import os
import sqlite3
import tempfile
from datetime import date, timedelta

import pytest

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.application.services.khieu_nai_service import (
    KhieuNaiService,
    KhieuNaiCreateData,
    KhieuNaiUpdateData,
    KhieuNaiNotFoundError,
    ValidationError,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def khieunai_db():
    """Create a temporary database with all migrations applied."""
    db_path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Run migrations using path
    runner = MigrationRunner(db_path)
    runner.run_pending()

    # Seed required data
    cursor = conn.cursor()

    # Seed vai_tro (migration already seeds, check first)
    cursor.execute('SELECT COUNT(*) FROM vai_tro')
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro)
            VALUES (1, 'A-01', 'Admin'), (2, 'A-02', 'Sales'), (3, 'A-03', 'KyThuat')
        """)

    # Seed nhan_vien
    cursor.execute('SELECT COUNT(*) FROM nhan_vien')
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai)
            VALUES (1, 'admin', '$2b$12$dummy', 'Nguyen Van A', 'admin@test.com', 1, 'active'),
                   (2, 'sales1', '$2b$12$dummy', 'Tran Van B', 'sales1@test.com', 2, 'active'),
                   (3, 'sales2', '$2b$12$dummy', 'Le Thi C', 'sales2@test.com', 2, 'active')
        """)

    # Seed khach_hang
    cursor.execute('SELECT COUNT(*) FROM khach_hang')
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email)
            VALUES (1, 'Khach Hang Test', '0909000001', 'kh1@test.com'),
                   (2, 'Khach Hang 2', '0909000002', 'kh2@test.com')
        """)

    # Seed hop_dong (for optional link)
    cursor.execute('SELECT COUNT(*) FROM xe')
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, gia_ban, so_luong_ton, trang_thai)
            VALUES (1, 'XE001', 'Toyota', 'Camry', 2024, 800000000, 5, 'con_hang')
        """)
    cursor.execute('SELECT COUNT(*) FROM hop_dong')
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, ngay_tao, gia_xe, tong_tien, trang_thai)
            VALUES (1, 'HD001', 1, 1, 1, date('now'), 800000000, 800000000, 'moi_tao')
        """)

    conn.commit()
    yield conn
    conn.close()
    os.unlink(db_path)


@pytest.fixture
def kn_service(khieunai_db):
    """KhieuNaiService instance."""
    return KhieuNaiService(khieunai_db)


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def create_kn(service, kh_id=1, hd_id=None, tieu_de="Test KN",
              noi_dung="Noi dung test", muc_do="trung_binh", nguon_goc="khac",
              created_by=1):
    """Create a complaint with test data."""
    data = KhieuNaiCreateData(
        khach_hang_id=kh_id,
        hop_dong_id=hd_id,
        tieu_de=tieu_de,
        noi_dung=noi_dung,
        muc_do=muc_do,
        nguon_goc=nguon_goc,
        created_by=created_by,
    )
    return service.create(data)


# ─────────────────────────────────────────────────────────────────────────────
# TEST.01: Unit test update_status → reject nếu thiếu ly_do (BR-KN-05)
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateStatusRequireLyDo:
    """TEST.01: BR-KN-05 — ly_do is REQUIRED when updating status."""

    def test_update_status_without_ly_do_fails(self, kn_service):
        """update_status without ly_do should raise ValidationError."""
        kn = create_kn(kn_service, tieu_de="KN test ly do")

        with pytest.raises(ValidationError) as exc:
            kn_service.update_status(kn["id"], "dang_xu_ly", ly_do=None)
        assert "lý do" in str(exc.value).lower() or "BR-KN-05" in str(exc.value)

    def test_update_status_with_empty_ly_do_fails(self, kn_service):
        """update_status with empty ly_do should raise ValidationError."""
        kn = create_kn(kn_service, tieu_de="KN test ly do rong")

        with pytest.raises(ValidationError) as exc:
            kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="   ")
        assert "lý do" in str(exc.value).lower()

    def test_update_status_with_whitespace_ly_do_fails(self, kn_service):
        """update_status with whitespace-only ly_do should fail."""
        kn = create_kn(kn_service)

        with pytest.raises(ValidationError):
            kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="  \n\t  ")

    def test_update_status_with_valid_ly_do_succeeds(self, kn_service):
        """update_status with valid ly_do should succeed."""
        kn = create_kn(kn_service, tieu_de="KN valid ly do")

        result = kn_service.update_status(
            kn["id"],
            "dang_xu_ly",
            ly_do="Da tiep nhan va bat dau xu ly"
        )

        assert result["trang_thai"] == "dang_xu_ly"
        assert result["ly_do"] == "Da tiep nhan va bat dau xu ly"

    def test_update_status_reopen_without_ly_do_fails(self, kn_service):
        """Reopening a complaint also requires ly_do."""
        kn = create_kn(kn_service, tieu_de="KN reopen")
        kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Dang xu ly")
        kn_service.update_status(kn["id"], "da_giai_quyet", ly_do="Da giai quyet xong")

        # Try to reopen without ly_do
        with pytest.raises(ValidationError):
            kn_service.update_status(kn["id"], "dang_xu_ly", ly_do=None)

    def test_multiple_status_updates_each_require_ly_do(self, kn_service):
        """Each status update requires its own ly_do."""
        kn = create_kn(kn_service, tieu_de="KN multi update")

        # First update
        result = kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Lan 1")
        assert result["trang_thai"] == "dang_xu_ly"

        # Second update without ly_do should fail
        with pytest.raises(ValidationError):
            kn_service.update_status(kn["id"], "da_giai_quyet", ly_do=None)

        # Second update with ly_do should succeed
        result = kn_service.update_status(kn["id"], "da_giai_quyet", ly_do="Lan 2")
        assert result["trang_thai"] == "da_giai_quyet"


# ─────────────────────────────────────────────────────────────────────────────
# TEST.02: Unit test close → reject nếu chưa có satisfaction (BR-KN-04)
# ─────────────────────────────────────────────────────────────────────────────

class TestCloseRequireSatisfaction:
    """TEST.02: BR-KN-04 — danh_gia_hai_long (1-5) required before closing."""

    def test_close_without_satisfaction_fails(self, kn_service):
        """close() without danh_gia_hai_long should raise ValidationError."""
        kn = create_kn(kn_service, tieu_de="KN close without rating")

        with pytest.raises(ValidationError) as exc:
            kn_service.close(kn["id"], danh_gia_hai_long=None)
        assert "1-5" in str(exc.value) or "BR-KN-04" in str(exc.value)

    def test_close_with_zero_rating_fails(self, kn_service):
        """close() with rating=0 should fail."""
        kn = create_kn(kn_service, tieu_de="KN zero rating")

        with pytest.raises(ValidationError):
            kn_service.close(kn["id"], danh_gia_hai_long=0)

    def test_close_with_six_rating_fails(self, kn_service):
        """close() with rating=6 should fail."""
        kn = create_kn(kn_service, tieu_de="KN rating 6")

        with pytest.raises(ValidationError):
            kn_service.close(kn["id"], danh_gia_hai_long=6)

    def test_close_with_negative_rating_fails(self, kn_service):
        """close() with negative rating should fail."""
        kn = create_kn(kn_service, tieu_de="KN negative rating")

        with pytest.raises(ValidationError):
            kn_service.close(kn["id"], danh_gia_hai_long=-1)

    def test_close_with_valid_rating_1_succeeds(self, kn_service):
        """close() with rating=1 (很不满意) should succeed."""
        kn = create_kn(kn_service, tieu_de="KN rating 1")
        kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Dang xu ly")

        result = kn_service.close(kn["id"], danh_gia_hai_long=1)

        assert result["trang_thai"] == "da_dong"
        assert result["danh_gia_hai_long"] == 1
        assert result["ngay_dong"] is not None

    def test_close_with_valid_rating_5_succeeds(self, kn_service):
        """close() with rating=5 (非常满意) should succeed."""
        kn = create_kn(kn_service, tieu_de="KN rating 5")
        kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Dang xu ly")

        result = kn_service.close(kn["id"], danh_gia_hai_long=5)

        assert result["trang_thai"] == "da_dong"
        assert result["danh_gia_hai_long"] == 5

    def test_close_from_da_giai_quyet_status_succeeds(self, kn_service):
        """close() from 'da_giai_quyet' status should work."""
        kn = create_kn(kn_service, tieu_de="KN from resolved")
        kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Dang xu ly")
        kn_service.update_status(kn["id"], "da_giai_quyet", ly_do="Da xu ly xong")

        result = kn_service.close(kn["id"], danh_gia_hai_long=4)

        assert result["trang_thai"] == "da_dong"
        assert result["danh_gia_hai_long"] == 4

    def test_close_from_moi_status_fails(self, kn_service):
        """close() directly from 'moi' status should fail."""
        kn = create_kn(kn_service, tieu_de="KN from moi")

        with pytest.raises(ValidationError) as exc:
            kn_service.close(kn["id"], danh_gia_hai_long=3)
        assert "trạng thái" in str(exc.value).lower()

    def test_close_from_da_dong_status_fails(self, kn_service):
        """close() when already closed should fail."""
        kn = create_kn(kn_service, tieu_de="KN double close")
        kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Dang xu ly")
        kn_service.close(kn["id"], danh_gia_hai_long=3)

        with pytest.raises(ValidationError):
            kn_service.close(kn["id"], danh_gia_hai_long=5)


# ─────────────────────────────────────────────────────────────────────────────
# TEST.03: Integration WF-06
# ─────────────────────────────────────────────────────────────────────────────

class TestWF06Integration:
    """TEST.03: Integration WF-06 — tạo KN → A-01 phân công → A-02 xử lý → đánh giá → đóng."""

    def test_wf06_full_flow(self, kn_service):
        """Full workflow: create → assign → process → close."""
        # Step 1: Create complaint (customer files complaint)
        kn = create_kn(
            kn_service,
            kh_id=1,
            hd_id=1,
            tieu_de="WF-06 Full Test",
            noi_dung="Xe co van de chat luong, can duoc xu ly ngay",
            muc_do="cao",
            nguon_goc="chat_luong_xe",
        )
        assert kn["trang_thai"] == "moi"
        assert kn["muc_do"] == "cao"
        kn_id = kn["id"]

        # Step 2: A-01 assigns to staff (sales1 = A-02)
        kn = kn_service.assign(kn_id, nv_id=2)  # sales1
        assert kn["trang_thai"] == "dang_xu_ly"
        assert kn["nhan_vien_xu_ly_id"] == 2

        # Step 3: Staff updates status to "da_giai_quyet" with ly_do
        kn = kn_service.update_status(
            kn_id,
            "da_giai_quyet",
            ly_do="Da lien he KH, gap nhuoc diem, de xuat doi tra mot phan"
        )
        assert kn["trang_thai"] == "da_giai_quyet"
        assert kn["ly_do"] == "Da lien he KH, gap nhuoc diem, de xuat doi tra mot phan"

        # Step 4: Close complaint with satisfaction rating
        kn = kn_service.close(kn_id, danh_gia_hai_long=4)
        assert kn["trang_thai"] == "da_dong"
        assert kn["danh_gia_hai_long"] == 4
        assert kn["ngay_dong"] is not None

    def test_wf06_priority_caos_tracking(self, kn_service):
        """BR-KN-03: High priority (cao) should be tracked and displayed first."""
        # Create 3 complaints with different priorities
        kn1 = create_kn(kn_service, tieu_de="KN thap", muc_do="thap")
        kn2 = create_kn(kn_service, tieu_de="KN cao", muc_do="cao")
        kn3 = create_kn(kn_service, tieu_de="KN trung binh", muc_do="trung_binh")

        # Get all ordered by priority
        all_kn = kn_service.get_all(limit=10)
        muc_dos = [k["muc_do"] for k in all_kn]

        # 'cao' should appear first in the sorted list
        assert muc_dos[0] == "cao", "BR-KN-03: Priority 'cao' should be first"

    def test_wf06_assign_only_admin(self, kn_service):
        """BR-KN-02: Only A-01 can assign - but this is enforced at permission level.
        
        Note: Service layer assigns without permission check (done in UI layer).
        This test verifies the assignment flow works.
        """
        kn = create_kn(kn_service, tieu_de="KN assign test")

        # Assign to staff 2 (sales1)
        result = kn_service.assign(kn["id"], nv_id=2)
        assert result["nhan_vien_xu_ly_id"] == 2
        assert result["trang_thai"] == "dang_xu_ly"

    def test_wf06_reopen_after_close_fails(self, kn_service):
        """After closing, complaint cannot be reopened (da_dong is terminal)."""
        kn = create_kn(kn_service, tieu_de="KN reopen test")
        kn_service.assign(kn["id"], nv_id=2)
        kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Dang xu ly")
        kn_service.update_status(kn["id"], "da_giai_quyet", ly_do="Da xong")
        kn_service.close(kn["id"], danh_gia_hai_long=3)

        # Try to reopen - should fail (da_dong is terminal)
        with pytest.raises(ValidationError):
            kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Thu reopen")


# ─────────────────────────────────────────────────────────────────────────────
# TEST.04: UAT theo AC-KN-*
# ─────────────────────────────────────────────────────────────────────────────

class TestUAT_AC_KN:
    """TEST.04: UAT scenarios based on AC-KN acceptance criteria."""

    def test_ac_kn_01_create_complaint(self, kn_service):
        """AC-KN-01: Customer can create a complaint.

        Manual: Open S-KN-01 → click "Tạo khiếu nại" → fill form → save
        """
        kn = create_kn(
            kn_service,
            kh_id=1,
            hd_id=1,
            tieu_de="AC-KN-01 Test",
            noi_dung="Test noi dung cho AC-KN-01",
            muc_do="cao",
            nguon_goc="dich_vu",
        )
        assert kn["id"] is not None
        assert kn["tieu_de"] == "AC-KN-01 Test"
        assert kn["trang_thai"] == "moi"

    def test_ac_kn_02_complaint_list_prioritized(self, kn_service):
        """AC-KN-02: Complaint list shows high-priority (cao) first.

        Manual: Open S-KN-01 → verify 'cao' badges appear at top
        """
        create_kn(kn_service, tieu_de="Low prio", muc_do="thap")
        create_kn(kn_service, tieu_de="High prio", muc_do="cao")
        create_kn(kn_service, tieu_de="Med prio", muc_do="trung_binh")

        kns = kn_service.get_all(limit=10)

        # First should be 'cao'
        assert kns[0]["muc_do"] == "cao", "BR-KN-03: 'cao' must be first"

    def test_ac_kn_03_assign_requires_reason(self, kn_service):
        """AC-KN-03: Assigning complaint requires status update with ly_do.

        Manual: In S-KN-02 → Phân công → select NV → verify status changes
        """
        kn = create_kn(kn_service, tieu_de="KN assign test")

        # assign() changes status to 'dang_xu_ly'
        result = kn_service.assign(kn["id"], nv_id=2)
        assert result["trang_thai"] == "dang_xu_ly"

        # Verify ly_do is NOT required for assign() (it's for status updates)
        # But subsequent status update WOULD require ly_do
        with pytest.raises(ValidationError):
            kn_service.update_status(kn["id"], "da_giai_quyet", ly_do=None)

    def test_ac_kn_04_close_requires_satisfaction(self, kn_service):
        """AC-KN-04: Closing complaint requires 1-5 satisfaction rating.

        Manual: In S-KN-02 → Đóng KN → select stars → confirm
        """
        kn = create_kn(kn_service, tieu_de="AC-KN-04 Test")
        kn_service.assign(kn["id"], nv_id=2)

        # Without rating
        with pytest.raises(ValidationError):
            kn_service.close(kn["id"], danh_gia_hai_long=None)

        # With valid rating
        result = kn_service.close(kn["id"], danh_gia_hai_long=4)
        assert result["trang_thai"] == "da_dong"
        assert result["danh_gia_hai_long"] == 4

    def test_ac_kn_05_muc_do_validation(self, kn_service):
        """AC-KN-05: Mức độ chỉ chấp nhận: thap, trung_binh, cao.

        Manual: Try creating KN with invalid muc_do → should be rejected
        """
        with pytest.raises(ValidationError) as exc:
            create_kn(kn_service, muc_do="ratcao")
        assert "mức độ" in str(exc.value).lower()

    def test_ac_kn_06_nguon_goc_validation(self, kn_service):
        """AC-KN-06: Nguồn gốc chỉ chấp nhận: chat_luong_xe, dich_vu, bao_hanh, khac.
        """
        kn = create_kn(kn_service, nguon_goc="bao_hanh")
        assert kn["nguon_goc"] == "bao_hanh"

        with pytest.raises(ValidationError):
            create_kn(kn_service, nguon_goc="khong_hop_le")

    def test_ac_kn_07_status_transitions(self, kn_service):
        """AC-KN-07: Trạng thái tuân theo BR-KN-01 flow.

        moi → dang_xu_ly → da_giai_quyet/da_dong
        """
        kn = create_kn(kn_service, tieu_de="AC-KN-07 Test")
        assert kn["trang_thai"] == "moi"

        # moi → dang_xu_ly OK
        kn = kn_service.update_status(kn["id"], "dang_xu_ly", ly_do="Nhan vien nhan xu ly")
        assert kn["trang_thai"] == "dang_xu_ly"

        # dang_xu_ly → da_giai_quyet OK
        kn = kn_service.update_status(kn["id"], "da_giai_quyet", ly_do="Da xu ly xong")
        assert kn["trang_thai"] == "da_giai_quyet"

    def test_ac_kn_08_invalid_status_transition(self, kn_service):
        """AC-KN-08: moi → da_giai_quyet (skip dang_xu_ly) is not allowed."""
        kn = create_kn(kn_service, tieu_de="AC-KN-08 Test")

        # Cannot skip dang_xu_ly
        with pytest.raises(ValidationError) as exc:
            kn_service.update_status(kn["id"], "da_giai_quyet", ly_do="Thu skip")
        assert "Không thể chuyển" in str(exc.value)

    def test_ac_kn_09_delete_only_moi_status(self, kn_service):
        """AC-KN-09: Chỉ xóa được khiếu nại ở trạng thái 'moi'.

        Manual: In S-KN-01 → select 'moi' KN → delete → confirm
        """
        kn = create_kn(kn_service, tieu_de="KN delete test")

        # Delete 'moi' status → OK
        result = kn_service.delete(kn["id"])
        assert result is True

        # Create another and change status
        kn2 = create_kn(kn_service, tieu_de="KN cant delete")
        kn_service.assign(kn2["id"], nv_id=2)

        # Cannot delete 'dang_xu_ly'
        with pytest.raises(ValidationError) as exc:
            kn_service.delete(kn2["id"])
        assert "mới" in str(exc.value)

    def test_ac_kn_10_customer_history(self, kn_service):
        """AC-KN-10: View complaint history by customer.

        Manual: Open customer detail → view complaint history
        """
        # Create 3 complaints for same customer
        for i in range(3):
            create_kn(kn_service, kh_id=1, tieu_de=f"KN cua KH {i}")

        history = kn_service.get_by_khach_hang(1)
        assert len(history) >= 3
        assert all(k["khach_hang_id"] == 1 for k in history)

    def test_ac_kn_11_stats_summary(self, kn_service):
        """AC-KN-11: Dashboard shows complaint statistics.

        Manual: Open dashboard → verify KN stats tiles
        """
        create_kn(kn_service, muc_do="cao")
        create_kn(kn_service, muc_do="cao")
        create_kn(kn_service, muc_do="trung_binh")

        stats = kn_service.get_stats_summary()

        assert stats["tong_khieu_nai"] >= 3
        assert stats["cao"] >= 2
        assert stats["trung_binh"] >= 1
