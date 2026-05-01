"""Tests for Marketing (ChienDichMk + Lead) services.

Test cases:
- TEST.01: Unit test convert_to_customer → KH được tạo + lead chuyển trạng thái
- TEST.02: Unit test calculate_conversion_rate (BR-CALC-06)
- TEST.03: Integration WF-07: tạo chiến dịch → thêm lead → chăm sóc → chuyển KH → tạo HĐ
- TEST.04: UAT theo AC-MK-* (manual test scenarios)
"""

import os
import sqlite3
import tempfile
from datetime import date, timedelta

import pytest

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.application.services.chien_dich_mk_service import (
    ChienDichMkService,
    ChienDichMkCreateData,
    ChienDichMkUpdateData,
    ChienDichMkNotFoundError,
    ValidationError,
)
from app.application.services.lead_service import (
    LeadService,
    LeadCreateData,
    LeadUpdateData,
    LeadNotFoundError,
    LeadConvertError,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def marketing_db():
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

    # Seed khach_hang (need for integration test)
    cursor.execute('SELECT COUNT(*) FROM khach_hang')
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email)
            VALUES (1, 'Khach Hang Test', '0909000001', 'kh1@test.com')
        """)

    conn.commit()
    yield conn
    conn.close()
    os.unlink(db_path)


@pytest.fixture
def campaign_service(marketing_db):
    """ChienDichMkService instance."""
    return ChienDichMkService(marketing_db)


@pytest.fixture
def lead_service(marketing_db):
    """LeadService instance."""
    return LeadService(marketing_db)


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def create_campaign(service, name="Test Campaign", status="dang_chay"):
    """Create a campaign with test data."""
    today = date.today()
    data = ChienDichMkCreateData(
        ten_chien_dich=name,
        kenh_tiep_thi="facebook",
        ngay_bat_dau=today.isoformat(),
        ngay_ket_thuc=(today + timedelta(days=30)).isoformat(),
        ngan_sach=50_000_000,
        muc_tieu="Test muc tieu",
        so_luong_lead_muc_tieu=20,
        created_by=1,
    )
    campaign = service.create(data)
    if status != "dang_chay":
        service.update(campaign["id"], ChienDichMkUpdateData(trang_thai=status))
        campaign = service.get_by_id(campaign["id"])
    return campaign


def create_lead(service, campaign_id=None, status="moi", ho_ten="Test Lead",
                so_dt="0909123456", email="lead@test.com", created_by=1):
    """Create a lead with test data."""
    data = LeadCreateData(
        chien_dich_id=campaign_id,
        ho_ten=ho_ten,
        so_dien_thoai=so_dt,
        email=email,
        nguon="facebook",
        nhu_cau="Can mua xe",
        created_by=created_by,
    )
    lead = service.create(data)
    if status != "moi":
        service.update_status(lead["id"], status)
        lead = service.get_by_id(lead["id"])
    return lead


# ─────────────────────────────────────────────────────────────────────────────
# TEST.01: Unit test convert_to_customer
# ─────────────────────────────────────────────────────────────────────────────

class TestLeadConvertToCustomer:
    """TEST.01: Lead convert_to_customer → KH được tạo + lead chuyển trạng thái."""

    def test_convert_to_customer_creates_khach_hang(self, lead_service, campaign_service):
        """Convert lead should create a new khach_hang record."""
        campaign = create_campaign(campaign_service)
        lead = create_lead(
            lead_service,
            campaign_id=campaign["id"],
            ho_ten="Nguyen Van Lead",
            so_dt="0909999999",
            email="lead.convert@test.com",
        )
        lead_id = lead["id"]

        result = lead_service.convert_to_customer(lead_id)

        # Verify lead now has khach_hang_id and status chuyen_doi
        assert result["khach_hang_id"] is not None, "khach_hang_id should be set"
        assert result["trang_thai"] == "chuyen_doi", "trang_thai should be chuyen_doi"

        # Verify khach_hang was created in database
        cursor = lead_service.conn.cursor()
        cursor.execute(
            "SELECT * FROM khach_hang WHERE id = ?",
            (result["khach_hang_id"],)
        )
        kh = cursor.fetchone()
        assert kh is not None, "khach_hang should exist"
        assert kh["ho_ten"] == "Nguyen Van Lead"
        assert kh["so_dien_thoai"] == "0909999999"
        assert kh["email"] == "lead.convert@test.com"

    def test_convert_to_customer_twice_fails(self, lead_service, campaign_service):
        """Converting same lead twice should raise error."""
        campaign = create_campaign(campaign_service)
        lead = create_lead(lead_service, campaign_id=campaign["id"])

        # First conversion
        lead_service.convert_to_customer(lead["id"])

        # Second conversion should fail
        with pytest.raises(LeadConvertError) as exc:
            lead_service.convert_to_customer(lead["id"])
        assert "đã được chuyển đổi" in str(exc.value)

    def test_convert_to_customer_already_has_khach_hang_fails(self, lead_service, campaign_service):
        """Lead already linked to khach_hang should fail on convert."""
        campaign = create_campaign(campaign_service)
        lead = create_lead(lead_service, campaign_id=campaign["id"])

        # Manually link to existing khach_hang
        lead_service._repo.update(lead["id"], {"khach_hang_id": 1})

        with pytest.raises(LeadConvertError) as exc:
            lead_service.convert_to_customer(lead["id"])
        assert "đã có khách hàng liên kết" in str(exc.value)

    def test_convert_nonexistent_lead_fails(self, lead_service):
        """Converting non-existent lead should raise error."""
        with pytest.raises(LeadNotFoundError):
            lead_service.convert_to_customer(999999)

    def test_convert_different_leads_creates_separate_kh(self, lead_service, campaign_service):
        """Each lead conversion creates separate khach_hang."""
        campaign = create_campaign(campaign_service)

        lead1 = create_lead(
            lead_service, campaign_id=campaign["id"],
            ho_ten="Lead One", so_dt="0909111111", email="one@test.com",
        )
        lead2 = create_lead(
            lead_service, campaign_id=campaign["id"],
            ho_ten="Lead Two", so_dt="0909222222", email="two@test.com",
        )

        result1 = lead_service.convert_to_customer(lead1["id"])
        result2 = lead_service.convert_to_customer(lead2["id"])

        # Should be different khach_hang records
        assert result1["khach_hang_id"] != result2["khach_hang_id"]

        cursor = lead_service.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM khach_hang WHERE id IN (?, ?)",
                       (result1["khach_hang_id"], result2["khach_hang_id"]))
        assert cursor.fetchone()["cnt"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# TEST.02: Unit test calculate_conversion_rate (BR-CALC-06)
# ─────────────────────────────────────────────────────────────────────────────

class TestCalculateConversionRate:
    """TEST.02: calculate_conversion_rate following BR-CALC-06."""

    def test_conversion_rate_zero_leads(self, campaign_service):
        """Campaign with no leads should have 0% conversion rate."""
        campaign = create_campaign(campaign_service)

        rate = campaign_service.calculate_conversion_rate(campaign["id"])

        assert rate == 0.0

    def test_conversion_rate_no_converted(self, campaign_service, lead_service):
        """Campaign with leads but none converted: 0% rate."""
        campaign = create_campaign(campaign_service)

        # Create 5 leads, none converted
        for i in range(5):
            create_lead(
                lead_service,
                campaign_id=campaign["id"],
                ho_ten=f"Lead {i}",
                so_dt=f"09090{i:05d}",
            )

        rate = campaign_service.calculate_conversion_rate(campaign["id"])

        assert rate == 0.0

    def test_conversion_rate_all_converted(self, campaign_service, lead_service):
        """Campaign with all leads converted: 100% rate."""
        campaign = create_campaign(campaign_service)

        # Create 4 leads, all converted
        for i in range(4):
            lead = create_lead(
                lead_service,
                campaign_id=campaign["id"],
                ho_ten=f"Lead {i}",
                so_dt=f"09090{i:05d}",
            )
            lead_service.update_status(lead["id"], "dang_cham_soc")
            lead_service.convert_to_customer(lead["id"])

        rate = campaign_service.calculate_conversion_rate(campaign["id"])

        assert rate == 100.0

    def test_conversion_rate_partial(self, campaign_service, lead_service):
        """Campaign with some leads converted: correct percentage."""
        campaign = create_campaign(campaign_service)

        # Create 10 leads, 3 converted
        for i in range(10):
            lead = create_lead(
                lead_service,
                campaign_id=campaign["id"],
                ho_ten=f"Lead {i}",
                so_dt=f"09090{i:05d}",
            )
            if i < 3:
                lead_service.update_status(lead["id"], "dang_cham_soc")
                lead_service.convert_to_customer(lead["id"])

        rate = campaign_service.calculate_conversion_rate(campaign["id"])

        assert rate == 30.0, f"Expected 30.0%, got {rate}%"

    def test_conversion_rate_nonexistent_campaign(self, campaign_service):
        """Non-existent campaign should raise error."""
        with pytest.raises(ChienDichMkNotFoundError):
            campaign_service.calculate_conversion_rate(999999)

    def test_conversion_rate_formula_br_calc_06(self, campaign_service, lead_service):
        """Verify BR-CALC-06 formula: rate = lead_chuyen_doi / tong_lead * 100."""
        campaign = create_campaign(campaign_service)

        # Create 8 leads, 2 converted
        for i in range(8):
            lead = create_lead(
                lead_service,
                campaign_id=campaign["id"],
                ho_ten=f"Lead {i}",
                so_dt=f"09090{i:05d}",
            )
            if i < 2:
                lead_service.update_status(lead["id"], "dang_cham_soc")
                lead_service.convert_to_customer(lead["id"])

        rate = campaign_service.calculate_conversion_rate(campaign["id"])

        # 2 / 8 * 100 = 25.0
        assert rate == 25.0


# ─────────────────────────────────────────────────────────────────────────────
# TEST.03: Integration WF-07
# ─────────────────────────────────────────────────────────────────────────────

class TestWF07Integration:
    """TEST.03: Integration WF-07 — tạo chiến dịch → thêm lead → chăm sóc → chuyển KH → tạo HĐ."""

    def test_wf07_full_flow(self, campaign_service, lead_service, marketing_db):
        """Full workflow: campaign → lead → caring → convert → create contract."""
        # Step 1: Create marketing campaign
        today = date.today()
        campaign = campaign_service.create(ChienDichMkCreateData(
            ten_chien_dich="Campaign WF-07 Test",
            kenh_tiep_thi="google_ads",
            ngay_bat_dau=today.isoformat(),
            ngay_ket_thuc=(today + timedelta(days=30)).isoformat(),
            ngan_sach=100_000_000,
            muc_tieu="Test WF-07",
            so_luong_lead_muc_tieu=5,
            created_by=1,
        ))
        assert campaign["id"] is not None

        # Step 2: Create lead from campaign
        lead = lead_service.create(LeadCreateData(
            chien_dich_id=campaign["id"],
            ho_ten="Khach Hang WF-07",
            so_dien_thoai="0909876543",
            email="wf07@test.com",
            nguon="google_ads",
            nhu_cau="Muon mua xe gia 500-800 tri",
            created_by=1,
        ))
        assert lead["trang_thai"] == "moi"

        # Step 3: Assign staff and update to dang_cham_soc
        lead_service.assign_to_nv(lead["id"], 2)  # sales1
        lead = lead_service.update_status(lead["id"], "dang_cham_soc")
        assert lead["trang_thai"] == "dang_cham_soc"
        assert lead["nhan_vien_phu_trach_id"] == 2

        # Step 4: Convert lead to customer
        converted = lead_service.convert_to_customer(lead["id"])
        assert converted["trang_thai"] == "chuyen_doi"
        assert converted["khach_hang_id"] is not None

        # Step 5: Verify campaign stats updated
        stats = campaign_service.get_campaign_summary(campaign["id"])
        assert stats["tong_lead"] == 1
        assert stats["lead_chuyen_doi"] == 1
        assert stats["ty_le_chuyen_doi"] == 100.0

        # Step 6: Create hop_dong for the new customer (integration check)
        kh_id = converted["khach_hang_id"]
        cursor = marketing_db.cursor()
        cursor.execute("""
            INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, gia_ban, so_luong_ton, trang_thai)
            VALUES (1, 'XE001', 'Toyota', 'Camry', 2024, 800_000_000, 5, 'con_hang')
        """)
        marketing_db.commit()

        cursor.execute("""
            INSERT INTO hop_dong (id, khach_hang_id, xe_id, ngay_hop_dong, tong_tien, trang_thai)
            VALUES (1, ?, 1, date('now'), 800_000_000, 'cho_xac_nhan')
        """, (kh_id,))
        marketing_db.commit()

        cursor.execute("SELECT * FROM hop_dong WHERE khach_hang_id = ?", (kh_id,))
        hd = cursor.fetchone()
        assert hd is not None, "Hop dong should be created for converted customer"

    def test_wf07_lead_status_transitions(self, campaign_service, lead_service):
        """Test valid lead status transitions according to BR-MK-02."""
        campaign = create_campaign(campaign_service)
        lead = create_lead(lead_service, campaign_id=campaign["id"])

        # moi → dang_cham_soc ✓
        lead = lead_service.update_status(lead["id"], "dang_cham_soc")
        assert lead["trang_thai"] == "dang_cham_soc"

        # dang_cham_soc → chuyen_doi ✓
        converted = lead_service.update_status(lead["id"], "chuyen_doi")
        assert converted["trang_thai"] == "chuyen_doi"

    def test_wf07_invalid_status_transition(self, lead_service, campaign_service):
        """Test invalid transition: moi → chuyen_doi should fail."""
        campaign = create_campaign(campaign_service)
        lead = create_lead(lead_service, campaign_id=campaign["id"])

        # moi → chuyen_doi is NOT valid (must go through dang_cham_soc first)
        with pytest.raises(Exception) as exc:
            lead_service.update_status(lead["id"], "chuyen_doi")
        assert "Không thể chuyển" in str(exc.value) or "VALID_STATUS_TRANSITIONS" in str(exc.value)


# ─────────────────────────────────────────────────────────────────────────────
# TEST.04: UAT theo AC-MK-*
# ─────────────────────────────────────────────────────────────────────────────

class TestUAT_AC_MK:
    """TEST.04: UAT scenarios based on AC-MK acceptance criteria.

    Note: These are automated reflections of UAT test scenarios.
    Manual verification steps noted in comments.
    """

    def test_ac_mk_01_campaign_creation(self, campaign_service):
        """AC-MK-01: Campaign can be created with valid data.

        Manual: Verify campaign appears in S-MK-01 list with correct info.
        """
        campaign = create_campaign(campaign_service, name="AC-MK-01 Test")
        assert campaign["ten_chien_dich"] == "AC-MK-01 Test"
        assert campaign["trang_thai"] == "dang_chay"

    def test_ac_mk_02_lead_creation(self, lead_service, campaign_service):
        """AC-MK-02: Lead can be created and tracked.

        Manual: Verify lead appears in S-MK-03 with 'moi' status.
        """
        campaign = create_campaign(campaign_service)
        lead = create_lead(
            lead_service,
            campaign_id=campaign["id"],
            ho_ten="AC-MK-02 Lead",
            so_dt="0909000202",
        )
        assert lead["trang_thai"] == "moi"
        assert lead["so_dien_thoai"] == "0909000202"

    def test_ac_mk_03_conversion_tracking(self, campaign_service, lead_service):
        """AC-MK-03: Lead conversion tracked correctly.

        Manual: Open S-MK-01 → click campaign → verify lead count and conversion rate.
        """
        campaign = create_campaign(campaign_service)

        # Create leads
        for i in range(5):
            create_lead(lead_service, campaign_id=campaign["id"], ho_ten=f"Lead {i}", so_dt=f"09090{i:04d}")

        # Convert 2 leads
        for i in range(2):
            lead = lead_service.get_all(limit=10)[i]
            lead_service.update_status(lead["id"], "dang_cham_soc")
            lead_service.convert_to_customer(lead["id"])

        # Verify campaign summary
        summary = campaign_service.get_campaign_summary(campaign["id"])
        assert summary["tong_lead"] == 5
        assert summary["lead_chuyen_doi"] == 2
        assert summary["ty_le_chuyen_doi"] == 40.0

    def test_ac_mk_04_campaign_budget_validation(self, campaign_service):
        """AC-MK-04: Campaign budget must be >= 0.

        Manual: Try creating campaign with negative budget → should be rejected.
        """
        today = date.today()
        with pytest.raises(ValidationError) as exc:
            campaign_service.create(ChienDichMkCreateData(
                ten_chien_dich="Budget Test",
                kenh_tiep_thi="facebook",
                ngay_bat_dau=today.isoformat(),
                ngay_ket_thuc=(today + timedelta(days=30)).isoformat(),
                ngan_sach=-1000000,  # Invalid negative
            ))
        assert "Ngân sách" in str(exc.value)

    def test_ac_mk_05_campaign_date_validation(self, campaign_service):
        """AC-MK-05: Campaign end date must be >= start date.

        Manual: Try creating campaign with end < start → should be rejected.
        """
        today = date.today()
        with pytest.raises(ValidationError) as exc:
            campaign_service.create(ChienDichMkCreateData(
                ten_chien_dich="Date Test",
                kenh_tiep_thi="facebook",
                ngay_bat_dau=today.isoformat(),
                ngay_ket_thuc=(today - timedelta(days=1)).isoformat(),  # Before start
                ngan_sach=0,
            ))
        assert "ngày kết thúc" in str(exc.value).lower() or "không hợp lệ" in str(exc.value).lower()

    def test_lead_assign_to_staff(self, lead_service, campaign_service):
        """AC-MK-06: Lead can be assigned to a staff member.

        Manual: In S-MK-03, select lead → click "Gán nhân viên" → verify NV name shows.
        """
        campaign = create_campaign(campaign_service)
        lead = create_lead(lead_service, campaign_id=campaign["id"])

        lead_service.assign_to_nv(lead["id"], 2)  # Assign to sales1

        updated = lead_service.get_by_id(lead["id"])
        assert updated["nhan_vien_phu_trach_id"] == 2

    def test_lead_status_workflow(self, lead_service, campaign_service):
        """AC-MK-07: Lead status follows BR-MK-02 workflow.

        Manual: In S-MK-03, update status and verify badge color changes.
        """
        campaign = create_campaign(campaign_service)
        lead = create_lead(lead_service, campaign_id=campaign["id"])

        assert lead["trang_thai"] == "moi"

        lead = lead_service.update_status(lead["id"], "dang_cham_soc")
        assert lead["trang_thai"] == "dang_cham_soc"

        lead = lead_service.update_status(lead["id"], "chuyen_doi")
        assert lead["trang_thai"] == "chuyen_doi"

        # Terminal state - cannot transition further
        with pytest.raises(Exception):
            lead_service.update_status(lead["id"], "tu_choi")
