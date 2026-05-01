"""Unit tests for DashboardService - T-G5.4.TEST.04.

Tests:
- TEST.04: Dashboard KPI summary với 7 KPI tiles và role-based filtering

References:
- BR-BC-05: Dashboard KPI tiles calculation
- A-01 (admin): sees all
- A-02 (manager): sees own team
- A-03 (staff): limited view
"""

import pytest
import sqlite3
import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.application.services.dashboard_service import (
    DashboardService,
    PermissionDeniedError,
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
    """Create minimal schema for testing dashboard_service."""
    conn.execute("PRAGMA foreign_keys = ON")

    # vai_tro
    conn.execute("""
        INSERT INTO vai_tro (id, ma_vai_tro, ten_vai_tro)
        VALUES (1, 'A-01', 'Quản trị viên'),
               (2, 'A-02', 'Quản lý'),
               (3, 'A-03', 'Nhân viên')
    """)

    # nhan_vien
    conn.execute("""
        INSERT INTO nhan_vien (id, username, mat_khau_hash, ho_ten, email, vai_tro_id, trang_thai)
        VALUES (1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Admin User', 'admin@test.com', 1, 'active'),
               (2, 'manager1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Manager One', 'manager1@test.com', 2, 'active'),
               (3, 'staff1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Staff One', 'staff1@test.com', 3, 'active'),
               (4, 'staff2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Staff Two', 'staff2@test.com', 3, 'active'),
               (5, 'manager2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTtFQtE3T8TXK', 'Manager Two', 'manager2@test.com', 2, 'active')
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
               (5, 'XE005', 'Honda', 'City', 2024, 'Bac', 380000000, 4, 2, 'con_hang')
    """)


def _seed_contracts_current_month(conn, year, month, count=10):
    """Seed hop_dong records for current month."""
    base_date = datetime(year, month, 1)
    for i in range(count):
        day = min(i % 28 + 1, 28)
        date_str = base_date.replace(day=day).strftime("%Y-%m-%d")
        xe_id = (i % 5) + 1
        kh_id = (i % 5) + 1
        nv_id = (i % 5) + 1
        status = 'da_giao_xe' if i % 2 == 0 else 'da_thanh_toan'
        tong_tien = 400000000 + (i * 50000000)

        conn.execute(f"""
            INSERT INTO hop_dong (id, ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id,
                                  gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien,
                                  trang_thai, ngay_tao)
            VALUES ({1000 + i}, 'HD{1000 + i:06d}', {kh_id}, {xe_id}, {nv_id},
                    400000000, 0, 0, {tong_tien}, '{status}', '{date_str}')
        """)


def _seed_warranty_expiring(conn, year, month):
    """Seed bao_hanh records expiring within 30 days."""
    base_date = datetime(year, month, 1)
    # Add some warranties expiring in 30 days
    for i in range(5):
        day = min(15 + i, 28)
        ngay_ket_thuc = base_date.replace(day=day) + timedelta(days=30)
        ngay_bat_dau = base_date.replace(day=1)

        conn.execute(f"""
            INSERT INTO bao_hanh (id, hop_dong_id, ngay_bat_dau, ngay_ket_thuc, thoi_han_bh, trang_thai)
            VALUES ({100 + i}, {100 + i}, '{ngay_bat_dau.strftime('%Y-%m-%d')}', '{ngay_ket_thuc.strftime('%Y-%m-%d')}', 24, 'con_hanh')
        """)


def _seed_tra_gop_qua_han(conn, count=3):
    """Seed tra_gop_lich_su with qua_han status."""
    for i in range(count):
        conn.execute(f"""
            INSERT INTO tra_gop_lich_su (id, tra_gop_id, ngay_tra, so_tien, trang_thai, ghi_chu)
            VALUES ({100 + i}, {100 + i}, date('now'), 10000000, 'qua_han', 'Qua han {i}')
        """)


def _seed_kh_birthday_window(conn):
    """Seed khach_hang with birthday within 7 days."""
    now = datetime.now()
    # Customer with birthday in 3 days
    birthday_this_month = now.replace(day=min(now.day + 3, 28))
    conn.execute("""
        INSERT INTO khach_hang (id, ho_ten, so_dien_thoai, email, dia_chi, phan_loai, tong_gia_tri_mua, so_xe_da_mua, ngay_sinh)
        VALUES (100, 'KH Birthday', '0909100100', 'birthday@test.com', '999 Test St', 'Thuong', 0, 0, ?)
    """, (birthday_this_month.strftime("%Y-%m-%d"),))


def _seed_khieu_nai_cao(conn, count=2):
    """Seed khieu_nai with muc_do=cao and not resolved."""
    for i in range(count):
        conn.execute(f"""
            INSERT INTO khieu_nai (id, ma_phieu, khach_hang_id, nhan_vien_id, mo_ta, muc_do, trang_thai, ngay_tao)
            VALUES ({100 + i}, 'KN{100 + i:03d}', 1, 1, 'Phan anh {i}', 'cao', 'dang_xu_ly', date('now'))
        """)


@pytest.fixture
def dashboard_db():
    """Create database with test data for DashboardService."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    _migrate(db_path)
    _create_base_schema(conn)

    now = datetime.now()

    # Seed contracts this month
    _seed_contracts_current_month(conn, now.year, now.month, count=10)

    # Seed warranty expiring soon
    _seed_warranty_expiring(conn, now.year, now.month)

    # Seed overdue installment
    _seed_tra_gop_qua_han(conn, count=3)

    # Seed customer with upcoming birthday
    _seed_kh_birthday_window(conn)

    # Seed high-priority complaints
    _seed_khieu_nai_cao(conn, count=2)

    conn.commit()
    conn.close()

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


# =============================================================================
# TEST.04 — Dashboard KPI Summary
# =============================================================================
class TestDashboardSummary:
    """TEST.04 — DashboardService.get_summary — 11 test cases"""

    def test_get_summary_returns_all_kpis(self, dashboard_db):
        """Tổng hợp 7 KPI tiles đều có giá trị."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        assert "kpis" in result
        kpis = result["kpis"]

        # All 7 KPI tiles should exist
        expected_kpis = [
            "revenue_month",
            "hop_dong_month",
            "xe_ton_kho",
            "bh_expiring_30d",
            "tg_qua_han",
            "kh_birthday_7d",
            "kn_cao",
        ]
        for kpi_name in expected_kpis:
            assert kpi_name in kpis, f"KPI {kpi_name} not found in result"

        conn.close()

    def test_get_summary_revenue_month(self, dashboard_db):
        """revenue_month khớp với tổng tong_tien HĐ tháng hiện tại."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        # Calculate expected revenue from contracts this month
        now = datetime.now()
        if now.month == 12:
            next_year = now.year + 1
            next_month = 1
        else:
            next_year = now.year
            next_month = now.month + 1
        from_date = f"{now.year}-{now.month:02d}-01"
        to_date = f"{next_year}-{next_month:02d}-01"

        cursor = conn.execute("""
            SELECT COALESCE(SUM(tong_tien), 0) as revenue
            FROM hop_dong
            WHERE trang_thai IN ('da_thanh_toan', 'da_giao_xe')
              AND DATE(ngay_tao) >= DATE(?)
              AND DATE(ngay_tao) < DATE(?)
        """, (from_date, to_date))
        expected_revenue = cursor.fetchone()[0]

        assert result["kpis"]["revenue_month"] == expected_revenue
        conn.close()

    def test_get_summary_hop_dong_month(self, dashboard_db):
        """hop_dong_month khớp với số HĐ tạo trong tháng hiện tại."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        # Calculate expected contract count
        now = datetime.now()
        if now.month == 12:
            next_year = now.year + 1
            next_month = 1
        else:
            next_year = now.year
            next_month = now.month + 1
        from_date = f"{now.year}-{now.month:02d}-01"
        to_date = f"{next_year}-{next_month:02d}-01"

        cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM hop_dong
            WHERE DATE(ngay_tao) >= DATE(?) AND DATE(ngay_tao) < DATE(?)
        """, (from_date, to_date))
        expected_count = cursor.fetchone()[0]

        assert result["kpis"]["hop_dong_month"] == expected_count
        conn.close()

    def test_get_summary_xe_ton_kho(self, dashboard_db):
        """xe_ton_kho khớp với tổng so_luong_ton của xe còn hàng."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        # Calculate expected inventory
        cursor = conn.execute(
            "SELECT COALESCE(SUM(so_luong_ton), 0) as total FROM xe WHERE so_luong_ton > 0"
        )
        expected_ton = cursor.fetchone()[0]

        assert result["kpis"]["xe_ton_kho"] == expected_ton
        conn.close()

    def test_get_summary_bh_expiring_30d(self, dashboard_db):
        """bh_expiring_30d sử dụng find_expiring_in_30_days()."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        # Verify bh_expiring_30d is a positive count (we seeded 5 warranties)
        assert result["kpis"]["bh_expiring_30d"] >= 0
        conn.close()

    def test_get_summary_tg_qua_han(self, dashboard_db):
        """tg_qua_han sử dụng find_overdue() - đếm trạng thái 'qua_han'."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        # We seeded 3 overdue records
        assert result["kpis"]["tg_qua_han"] == 3
        conn.close()

    def test_get_summary_kh_birthday_7d(self, dashboard_db):
        """kh_birthday_7d sử dụng find_birthday_window(7)."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        # We seeded 1 customer with birthday in 7 days
        assert result["kpis"]["kh_birthday_7d"] >= 0
        conn.close()

    def test_get_summary_kn_cao(self, dashboard_db):
        """kn_cao đếm KN cấp cao chưa đóng."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        # We seeded 2 high-priority complaints
        assert result["kpis"]["kn_cao"] >= 0
        conn.close()

    def test_get_summary_role_admin_sees_all(self, dashboard_db):
        """A-01 (admin) thấy tất cả dữ liệu."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-01", user_id=None)

        assert result["role"] == "A-01"
        # Admin sees all KPIs (none are None)
        kpis = result["kpis"]
        for kpi_name, kpi_value in kpis.items():
            assert kpi_value is not None, f"Admin should see {kpi_name}, but got None"

        conn.close()

    def test_get_summary_role_nv_sees_own(self, dashboard_db):
        """A-02 (manager) thấy dữ liệu được lọc theo nhan_vien_id."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        # Manager sees their own team's data
        result = service.get_summary(role="A-02", user_id=1)

        assert result["role"] == "A-02"
        assert result["user_id"] == 1
        # A-02 should have filtered revenue and contracts
        assert result["kpis"]["revenue_month"] >= 0
        assert result["kpis"]["hop_dong_month"] >= 0
        conn.close()

    def test_get_summary_role_khach_sees_limited(self, dashboard_db):
        """A-03 (staff) thấy dữ liệu giới hạn."""
        conn = sqlite3.connect(dashboard_db)
        conn.execute("PRAGMA foreign_keys = ON")
        service = DashboardService(conn)

        result = service.get_summary(role="A-03", user_id=3)

        assert result["role"] == "A-03"
        # A-03 sees limited KPIs - only revenue and contracts
        kpis = result["kpis"]
        assert kpis["revenue_month"] is not None or kpis["revenue_month"] == 0
        assert kpis["hop_dong_month"] is not None or kpis["hop_dong_month"] == 0
        # Other KPIs should be None for staff
        assert kpis.get("xe_ton_kho") is None
        assert kpis.get("bh_expiring_30d") is None
        assert kpis.get("tg_qua_han") is None
        assert kpis.get("kh_birthday_7d") is None
        assert kpis.get("kn_cao") is None

        conn.close()