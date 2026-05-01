"""Unit tests for BaoCaoService - T-G5.4.TEST.01 & TEST.03.

Tests:
- TEST.01: revenue (4 group_by), top_xe (2), kpi_nv, vip_customers, warranty_cost
- TEST.03: Performance tests with 10,000 records (< 3s requirement)

References:
- BR-BC-01..05: Reporting requirements
- BR-CALC-01: Total calculation
- BR-CALC-05: Employee KPI formula
- BR-CALC-06: Conversion rate formula
- C-PERF-04: Query < 3s với 10,000 records
"""

import pytest
import sqlite3
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.application.services.bao_cao_service import (
    BaoCaoService,
    ValidationError,
)


# =============================================================================
# Fixtures
# =============================================================================

def _migrate(db_path):
    """Run migrations on database."""
    from app.infrastructure.database.migrations.runner import MigrationRunner
    runner = MigrationRunner(db_path)
    runner.run_pending()


def _create_base_schema(conn):
    """Create minimal schema for testing bao_cao_service."""
    conn.execute("PRAGMA foreign_keys = ON")

    # vai_tro
    conn.execute("""
        INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro)
        VALUES (1, 'admin', 'Quản trị viên'),
               (2, 'sales', 'Nhân viên bán hàng'),
               (3, 'tech', 'Kỹ thuật viên')
    """)

    # nhan_vien
    conn.execute("""
        INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai)
        VALUES (1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Admin User', 'admin@test.com', 1, 'active'),
               (2, 'sales1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Sales One', 'sales1@test.com', 2, 'active'),
               (3, 'sales2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Sales Two', 'sales2@test.com', 2, 'active'),
               (4, 'sales3', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Sales Three', 'sales3@test.com', 2, 'active'),
               (5, 'sales4', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Sales Four', 'sales4@test.com', 2, 'active')
    """)

    # khach_hang
    conn.execute("""
        INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email, dia_chi, phan_loai, tong_gia_tri_mua, so_xe_da_mua, ngay_sinh)
        VALUES (1, 'Khach Hang 1', '0909000001', 'kh1@test.com', '123 Test St', 'Thuong', 0, 0, '1990-05-15'),
               (2, 'Khach Hang 2', '0909000002', 'kh2@test.com', '456 Test St', 'VIP', 1500000000, 2, '1985-06-20'),
               (3, 'Khach Hang 3', '0909000003', 'kh3@test.com', '789 Test St', 'VIP', 2500000000, 3, '1988-03-10'),
               (4, 'Khach Hang 4', '0909000004', 'kh4@test.com', '101 Test St', 'Thuong', 500000000, 1, '1992-08-25'),
               (5, 'VIP Customer', '0909000005', 'vip@test.com', '202 VIP St', 'VIP', 3000000000, 4, '1980-12-01')
    """)

    # xe
    conn.execute("""
        INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, muc_toi_thieu, trang_thai)
        VALUES (1, 'XE001', 'Toyota', 'Camry', 2024, 'Den', 500000000, 5, 2, 'con_hang'),
               (2, 'XE002', 'Honda', 'Civic', 2024, 'Trang', 400000000, 3, 2, 'con_hang'),
               (3, 'XE003', 'Toyota', 'Vios', 2024, 'Do', 350000000, 2, 2, 'con_hang'),
               (4, 'XE004', 'BMW', 'X5', 2024, 'Den', 1500000000, 1, 1, 'con_hang'),
               (5, 'XE005', 'Honda', 'City', 2024, 'Bac', 380000000, 4, 2, 'con_hang'),
               (6, 'XE006', 'Mercedes', 'C200', 2024, 'Trang', 1200000000, 2, 1, 'con_hang'),
               (7, 'XE007', 'Toyota', 'Fortuner', 2024, 'Den', 800000000, 3, 2, 'con_hang'),
               (8, 'XE008', 'Honda', 'CR-V', 2024, 'Trang', 700000000, 2, 2, 'con_hang'),
               (9, 'XE009', 'BMW', 'X3', 2024, 'Do', 1100000000, 1, 1, 'con_hang'),
               (10, 'XE010', 'Mercedes', 'E200', 2024, 'Bac', 1300000000, 1, 1, 'con_hang'),
               (11, 'XE011', 'Toyota', 'Raize', 2024, 'Den', 300000000, 5, 2, 'con_hang'),
               (12, 'XE012', 'Honda', 'Accord', 2024, 'Trang', 650000000, 2, 2, 'con_hang'),
               (13, 'XE013', 'BMW', 'X1', 2024, 'Den', 900000000, 2, 1, 'con_hang'),
               (14, 'XE014', 'Mercedes', 'GLC', 2024, 'Trang', 1400000000, 1, 1, 'con_hang'),
               (15, 'XE015', 'Toyota', 'Alphard', 2024, 'Den', 2000000000, 1, 1, 'con_hang'),
               (16, 'XE016', 'Honda', 'Pilot', 2024, 'Bac', 850000000, 1, 1, 'con_hang'),
               (17, 'XE017', 'BMW', 'X7', 2024, 'Den', 2500000000, 1, 1, 'con_hang'),
               (18, 'XE018', 'Mercedes', 'S450', 2024, 'Trang', 3000000000, 1, 1, 'con_hang'),
               (19, 'XE019', 'Toyota', 'LandCruiser', 2024, 'Den', 3500000000, 1, 1, 'con_hang'),
               (20, 'XE020', 'Honda', 'HR-V', 2024, 'Bac', 450000000, 3, 2, 'con_hang')
    """)


def _seed_hop_dong(conn, year=2026, month=4, count=100, start_id=1):
    """Seed hop_dong records for testing.

    Args:
        conn: Database connection
        year, month: Target month for contracts
        count: Number of contracts to create
        start_id: Starting contract ID
    """
    now = datetime.now()
    base_date = datetime(year, month, 15)

    for i in range(count):
        # Distribute contracts across days
        day_offset = (i % 28) + 1
        contract_date = base_date.replace(day=min(day_offset, 28))
        date_str = contract_date.strftime("%Y-%m-%d")

        xe_id = (i % 20) + 1  # 20 different xe
        kh_id = (i % 5) + 1   # 5 different customers
        nv_id = (i % 5) + 1   # 5 different employees

        # Vary the total amount
        base_price = 400000000 + (i % 10) * 50000000
        tong_tien = base_price + (i * 1000000)

        status = 'da_giao_xe' if i % 3 == 0 else 'da_thanh_toan'

        conn.execute(f"""
            INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id,
                                  gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien,
                                  trang_thai, ngay_tao)
            VALUES ({start_id + i}, 'HD{start_id + i:06d}', {kh_id}, {xe_id}, {nv_id},
                    {base_price}, 0, 0, {tong_tien}, '{status}', '{date_str}')
        """)


def _seed_large_dataset(conn, num_records=10000):
    """Seed large dataset for performance testing.

    Creates contracts distributed across 12 months with various statuses.
    """
    conn.execute("DELETE FROM hop_dong")
    conn.execute("DELETE FROM nhan_vien")
    conn.execute("DELETE FROM xe")
    conn.execute("DELETE FROM khach_hang")

    # Insert employees
    for i in range(1, 21):  # 20 employees
        conn.execute(f"""
            INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai)
            VALUES ({i}, 'sales{i}', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK',
                    'Sales {i}', 'sales{i}@test.com', 2, 'active')
        """)

    # Insert customers
    for i in range(1, 101):  # 100 customers
        phan_loai = 'VIP' if i <= 20 else 'Thuong'
        tong_gia = i * 50000000
        so_xe = i // 10
        conn.execute(f"""
            INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email, dia_chi, phan_loai, tong_gia_tri_mua, so_xe_da_mua)
            VALUES ({i}, 'Khach Hang {i}', '0909{i:06d}', 'kh{i}@test.com', 'Addr {i}', '{phan_loai}', {tong_gia}, {so_xe})
        """)

    # Insert vehicles (20 types)
    hangs = ['Toyota', 'Honda', 'BMW', 'Mercedes']
    dong_xes = ['Camry', 'Civic', 'X5', 'C200', 'Vios', 'City', 'X3', 'E200', 'Fortuner', 'CR-V']
    for i in range(1, 21):
        hang = hangs[i % 4]
        dong_xe = dong_xes[i % 10]
        gia = 400000000 + (i * 50000000)
        conn.execute(f"""
            INSERT INTO xe (id, ma_xe, hang, dong_xe, nam_san_xuat, mau_sac, gia_ban, so_luong_ton, muc_toi_thieu, trang_thai)
            VALUES ({i}, 'XE{i:03d}', '{hang}', '{dong_xe}', 2024, 'Den', {gia}, 5, 2, 'con_hang')
        """)

    # Seed contracts distributed over 12 months
    base_date = datetime(2025, 1, 1)
    batch_size = 500

    for batch_start in range(0, num_records, batch_size):
        values = []
        for i in range(batch_start, min(batch_start + batch_size, num_records)):
            # Distribute across 12 months
            month_offset = (i * 7) % 12
            day_offset = (i * 13) % 28 + 1
            contract_date = base_date + relativedelta(months=month_offset)
            contract_date = contract_date.replace(day=min(day_offset, 28))
            date_str = contract_date.strftime("%Y-%m-%d")

            xe_id = (i % 20) + 1
            kh_id = (i % 100) + 1
            nv_id = (i % 20) + 1

            # Randomize status
            status_idx = i % 10
            if status_idx < 6:
                status = 'da_giao_xe'
            elif status_idx < 8:
                status = 'da_thanh_toan'
            else:
                status = 'moi_tao'

            tong_tien = 400000000 + (i % 50) * 10000000

            values.append(f"({i + 1}, 'HD{i + 1:06d}', {kh_id}, {xe_id}, {nv_id}, {400000000 + (i % 50) * 10000000}, 0, 0, {tong_tien}, '{status}', '{date_str}')")

        conn.execute("INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien, trang_thai, ngay_tao) VALUES " + ", ".join(values))

    conn.commit()


def _seed_warranty_data(conn, year=2026, month=4):
    """Seed bao_hanh and warranty requests for testing."""
    # Seed bao_hanh
    for i in range(1, 21):  # 20 warranties
        ngay_bat_dau = f"{year}-{month:02d}-15"
        ngay_ket_thuc = f"{year + 2}-{month:02d}-15"
        conn.execute(f"""
            INSERT INTO bao_hanh (id, hop_dong_id, ngay_bat_dau, ngay_ket_thuc, thoi_han_bh, trang_thai)
            VALUES ({i}, {i}, '{ngay_bat_dau}', '{ngay_ket_thuc}', 24, 'con_hanh')
        """)

    # Seed warranty requests (bao_hanh_yeu_cau)
    # Mix of mien_phi and tinh_phi
    for i in range(1, 31):  # 30 requests
        loai_phi = 'tinh_phi' if i % 3 == 0 else 'mien_phi'
        chi_phi = 500000 if i % 3 == 0 else 0
        ngay_yeu_cau = f"{year}-{month:02d}-{min(i % 28 + 1, 28):02d}"

        conn.execute(f"""
            INSERT INTO bao_hanh_yeu_cau (id, bao_hanh_id, nhan_vien_id, ngay_yeu_cau, mo_ta_tinh_trang, loai_yeu_cau, chi_phi, trang_thai)
            VALUES ({i}, {i % 20 + 1}, {i % 5 + 1}, '{ngay_yeu_cau}', 'Yeu cau bao hanh {i}', 'sua_chua', {chi_phi}, 'da_hoan_thanh')
        """)


@pytest.fixture
def bao_cao_db():
    """Create database with test data for BaoCaoService."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    _migrate(db_path)
    _create_base_schema(conn)

    # Seed 100 contracts for TEST.01
    _seed_hop_dong(conn, year=2026, month=4, count=100)

    # Seed warranty data
    _seed_warranty_data(conn, year=2026, month=4)

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def bao_cao_large_db():
    """Create database with 10,000 contracts for performance testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    _migrate(db_path)
    _create_base_schema(conn)

    # Seed 10,000 contracts
    _seed_large_dataset(conn, num_records=10000)

    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


# =============================================================================
# TEST.01 — revenue (4 group_by variants)
# =============================================================================
class TestRevenueReport:
    """TEST.01 — BaoCaoService.revenue — 7 test cases"""

    def test_revenue_group_by_day(self, bao_cao_db):
        """Báo cáo doanh thu theo ngày với 100 HĐ phân bố trong tháng."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.revenue("2026-04-01", "2026-04-30", group_by="day")

        assert "breakdown" in result
        assert result["total_contracts"] > 0
        assert result["total_revenue"] > 0
        # Each day should have some contracts
        assert len(result["breakdown"]) > 0
        conn.close()

    def test_revenue_group_by_month(self, bao_cao_db):
        """Báo cáo doanh thu theo tháng với 100 HĐ."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.revenue("2026-01-01", "2026-12-31", group_by="month")

        assert "breakdown" in result
        assert len(result["breakdown"]) > 0
        # April 2026 should be in the breakdown
        periods = [item["period"] for item in result["breakdown"]]
        assert "2026-04" in periods
        conn.close()

    def test_revenue_group_by_quarter(self, bao_cao_db):
        """Báo cáo doanh thu theo quý với 100 HĐ."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.revenue("2026-01-01", "2026-12-31", group_by="quarter")

        assert "breakdown" in result
        assert len(result["breakdown"]) > 0
        # Q2 2026 should be present
        quarters = [item["period"] for item in result["breakdown"]]
        assert any("Q2" in q for q in quarters)
        conn.close()

    def test_revenue_group_by_year(self, bao_cao_db):
        """Báo cáo doanh thu theo năm với 100 HĐ."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.revenue("2025-01-01", "2027-12-31", group_by="year")

        assert "breakdown" in result
        assert len(result["breakdown"]) > 0
        periods = [item["period"] for item in result["breakdown"]]
        assert "2026" in periods
        conn.close()

    def test_revenue_filter_by_nhan_vien(self, bao_cao_db):
        """Báo cáo doanh thu lọc theo nhan_vien_id = 1."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.revenue("2026-04-01", "2026-04-30", group_by="day", nhan_vien_id=1)

        assert result["filters"]["nhan_vien_id"] == 1
        assert result["total_revenue"] > 0
        conn.close()

    def test_revenue_filter_by_dong_xe(self, bao_cao_db):
        """Báo cáo doanh thu lọc theo dong_xe = 'Toyota'."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.revenue("2026-04-01", "2026-04-30", group_by="day", dong_xe="Toyota")

        assert result["filters"]["dong_xe"] == "Toyota"
        conn.close()

    def test_revenue_invalid_date_range(self, bao_cao_db):
        """Báo cáo doanh thu với from_date > to_date phải raise ValidationError."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        with pytest.raises(ValidationError):
            service.revenue("2026-05-01", "2026-04-01", group_by="day")
        conn.close()


# =============================================================================
# TEST.01 — top_xe
# =============================================================================
class TestTopXeReport:
    """TEST.01 — BaoCaoService.top_xe — 2 test cases"""

    def test_top_xe(self, bao_cao_db):
        """Báo cáo top 10 xe bán chạy với 100 HĐ phân bố 20 xe."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.top_xe(from_date="2026-04-01", to_date="2026-04-30", top=10)

        assert len(result) <= 10
        # Verify sorted by doanh_thu descending
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i]["doanh_thu"] >= result[i + 1]["doanh_thu"]
        conn.close()

    def test_top_xe_custom_top(self, bao_cao_db):
        """Báo cáo top 5 xe bán chạy với top=5."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.top_xe(from_date="2026-04-01", to_date="2026-04-30", top=5)

        assert len(result) <= 5
        conn.close()


# =============================================================================
# TEST.01 — kpi_nv
# =============================================================================
class TestKPINhanVienReport:
    """TEST.01 — BaoCaoService.kpi_nv — 1 test case"""

    def test_kpi_nv(self, bao_cao_db):
        """Báo cáo KPI nhân viên tháng 4/2026 với 50 HĐ phân bố 5 nhân viên."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        # Seed additional contracts for KPI testing (50 across 5 employees)
        for i in range(50):
            xe_id = (i % 20) + 1
            kh_id = (i % 5) + 1
            nv_id = (i % 5) + 1
            status = 'da_giao_xe' if i % 2 == 0 else 'da_thanh_toan'
            tong_tien = 400000000 + (i * 5000000)
            conn.execute(f"""
                INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id,
                                      gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien,
                                      trang_thai, ngay_tao)
                VALUES ({1000 + i}, 'HD{1000 + i:06d}', {kh_id}, {xe_id}, {nv_id},
                        400000000, 0, 0, {tong_tien}, '{status}', '2026-04-{min(i % 28 + 1, 28):02d}')
            """)
        conn.commit()

        result = service.kpi_nv("2026-04")

        assert len(result) > 0
        # Check KPI structure
        for item in result:
            assert "nhan_vien_id" in item
            assert "ho_ten" in item
            assert "so_hop_dong_moi_tao" in item
            assert "so_hop_dong_da_thanh_toan" in item
            assert "doanh_thu" in item
            assert "ti_le_chot" in item

        conn.close()


# =============================================================================
# TEST.01 — vip_customers
# =============================================================================
class TestVIPCustomerReport:
    """TEST.01 — BaoCaoService.vip_customers — 1 test case"""

    def test_vip_customers(self, bao_cao_db):
        """Báo cáo VIP customers sắp xếp theo tong_gia_tri_mua giảm dần."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.vip_customers(top=20)

        assert len(result) > 0
        # Verify sorted by tong_gia_tri_mua descending
        for i in range(len(result) - 1):
            assert result[i]["tong_gia_tri_mua"] >= result[i + 1]["tong_gia_tri_mua"]

        # Verify VIP customers have high purchase value
        vip_customers = [r for r in result if r.get("phan_loai") == "VIP"]
        assert len(vip_customers) > 0
        conn.close()


# =============================================================================
# TEST.01 — warranty_cost
# =============================================================================
class TestWarrantyCostReport:
    """TEST.01 — BaoCaoService.warranty_cost — 1 test case"""

    def test_warranty_cost(self, bao_cao_db):
        """Báo cáo chi phí bảo hành theo loại (mien_phi/tinh_phi)."""
        conn = sqlite3.connect(bao_cao_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        result = service.warranty_cost("2026-04-01", "2026-04-30")

        assert "breakdown" in result
        assert "total_cost" in result
        assert len(result["breakdown"]) > 0

        # Verify breakdown by loai_phi
        loai_phis = [item["loai_phi"] for item in result["breakdown"]]
        assert "mien_phi" in loai_phis or "tinh_phi" in loai_phis
        conn.close()


# =============================================================================
# TEST.03 — Performance tests
# =============================================================================
class TestPerformance:
    """TEST.03 — Performance tests: 10,000 records < 3 seconds"""

    def test_revenue_performance_10k_records(self, bao_cao_large_db):
        """Revenue query với 10,000 HĐ phải hoàn thành trong < 3 giây."""
        conn = sqlite3.connect(bao_cao_large_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        start_time = time.time()
        result = service.revenue("2025-01-01", "2025-12-31", group_by="month")
        elapsed = time.time() - start_time

        assert elapsed < 3.0, f"Revenue query took {elapsed:.2f}s, expected < 3s"
        assert result["total_revenue"] > 0
        conn.close()

    def test_top_xe_performance_10k_records(self, bao_cao_large_db):
        """Top xe query với 10,000 HĐ phải hoàn thành trong < 3 giây."""
        conn = sqlite3.connect(bao_cao_large_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = BaoCaoService(conn)

        start_time = time.time()
        result = service.top_xe(from_date="2025-01-01", to_date="2025-12-31", top=10)
        elapsed = time.time() - start_time

        assert elapsed < 3.0, f"Top xe query took {elapsed:.2f}s, expected < 3s"
        assert len(result) > 0
        conn.close()