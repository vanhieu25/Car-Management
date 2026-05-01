"""Performance benchmarks for critical queries.

Tests query execution time against defined thresholds:
- Simple SELECT: < 50ms
- JOIN + aggregation: < 200ms
- Report query: < 500ms

Run via:
    pytest tests/perf/ -v
    pytest tests/perf/test_query_performance.py::test_xe_search_by_model -v
    pytest tests/perf/test_query_performance.py -v --benchmark  # with pytest-benchmark
"""

import pytest
import sqlite3
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.infrastructure.repositories.xe_repository import XeRepository, XeSearchFilter
from app.infrastructure.repositories.hop_dong_repository import HopDongRepository, HopDongSearchFilter
from app.infrastructure.repositories.khach_hang_repository import KhachHangRepository, KhachHangSearchFilter
from app.application.services.bao_cao_service import BaoCaoService
from app.application.services.kho_service import KhoService

from tests.perf.conftest import (
    benchmark,
    measure_query,
    BenchmarkResult,
    PERF_THRESHOLDS,
)


# =============================================================================
# Helper: Pretty print benchmark result
# =============================================================================

def print_benchmark(result: BenchmarkResult):
    """Print a single benchmark result with color-friendly formatting."""
    print(f"\n  {'✅ PASS' if result.passed else '❌ FAIL'} {result.query_name}")
    print(f"     Time: {result.elapsed_ms:.2f}ms | Threshold: {result.threshold_ms:.2f}ms")
    print(f"     Rows: {result.rows_returned}")


# =============================================================================
# WF-02 Related: Xe Search Queries
# =============================================================================

class TestXeSearchPerformance:
    """Performance tests for vehicle search queries (WF-02 related)."""

    def test_xe_search_by_hang(self, perf_conn):
        """Simple SELECT: search xe by hang (single filter)."""
        with benchmark("xe_search_by_hang", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                "SELECT * FROM xe WHERE hang = 'Toyota' LIMIT 50"
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed, f"Query exceeded threshold: {result.elapsed_ms:.2f}ms"

    def test_xe_search_by_model_and_year(self, perf_conn):
        """Simple SELECT with 2 conditions: hang + nam_san_xuat."""
        with benchmark("xe_search_model_year", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM xe
                   WHERE hang = 'Toyota' AND nam_san_xuat = 2024
                   LIMIT 50"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_xe_search_by_price_range(self, perf_conn):
        """Simple SELECT with price range."""
        with benchmark("xe_search_price_range", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM xe
                   WHERE gia_ban BETWEEN 500000000 AND 1000000000
                   LIMIT 50"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_xe_search_multi_condition(self, perf_conn):
        """JOIN-like query: xe search with multiple conditions + sort."""
        with benchmark("xe_search_multi_condition", threshold_ms=100) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM xe
                   WHERE hang = 'Toyota'
                     AND nam_san_xuat >= 2022
                     AND gia_ban BETWEEN 400000000 AND 800000000
                     AND trang_thai = 'con_hang'
                   ORDER BY gia_ban ASC
                   LIMIT 50"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_xe_search_with_pagination(self, perf_conn):
        """Simple SELECT with OFFSET pagination (page 10, 50 per page)."""
        offset = 9 * 50  # page 10 (0-indexed)
        with benchmark("xe_search_pagination", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM xe
                   WHERE trang_thai = 'con_hang'
                   ORDER BY id LIMIT 50 OFFSET ?""",
                (offset,)
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed


# =============================================================================
# WF-02/03 Related: Contract (HĐ) Queries
# =============================================================================

class TestHopDongPerformance:
    """Performance tests for contract queries (WF-02, WF-03 related)."""

    def test_hd_filter_by_status(self, perf_conn):
        """Simple SELECT: filter hop_dong by trang_thai."""
        with benchmark("hd_filter_by_status", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM hop_dong
                   WHERE trang_thai = 'da_giao_xe'
                   LIMIT 100"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_hd_filter_by_status_and_date(self, perf_conn):
        """Simple SELECT with 2 conditions: trang_thai + date range."""
        today = datetime.now()
        thirty_days_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        with benchmark("hd_filter_status_date", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM hop_dong
                   WHERE trang_thai = 'da_giao_xe'
                     AND DATE(ngay_tao) >= DATE(?)
                   LIMIT 100""",
                (thirty_days_ago,)
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_hd_filter_pagination(self, perf_conn):
        """Simple SELECT with pagination (page 20 of 100 results)."""
        page_size = 100
        offset = 19 * page_size
        with benchmark("hd_filter_pagination", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM hop_dong
                   WHERE trang_thai = 'da_giao_xe'
                   ORDER BY id LIMIT ? OFFSET ?""",
                (page_size, offset)
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_hd_join_kh_xe_count(self, perf_conn):
        """JOIN + aggregation: count contracts per KH who has bought."""
        with benchmark("hd_join_kh_count", threshold_ms=200) as result:
            cursor = perf_conn.execute(
                """SELECT kh.id, kh.ho_ten, COUNT(hd.id) as so_hop_dong
                   FROM khach_hang kh
                   JOIN hop_dong hd ON kh.id = hd.khach_hang_id
                   WHERE hd.trang_thai = 'da_giao_xe'
                   GROUP BY kh.id, kh.ho_ten
                   HAVING so_hop_dong >= 1
                   LIMIT 100"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed


# =============================================================================
# Revenue Report Queries
# =============================================================================

class TestRevenueReportPerformance:
    """Performance tests for revenue report queries (RP-01)."""

    def test_bh_report_monthly(self, perf_conn):
        """Report query: monthly revenue breakdown (aggregation + GROUP BY)."""
        with benchmark("bh_report_monthly", threshold_ms=500) as result:
            cursor = perf_conn.execute(
                """SELECT
                       strftime('%Y-%m', ngay_tao) as thang,
                       COUNT(*) as so_hop_dong,
                       SUM(tong_tien) as doanh_thu
                   FROM hop_dong
                   WHERE trang_thai IN ('da_thanh_toan', 'da_giao_xe')
                     AND ngay_tao >= DATE('now', '-12 months')
                   GROUP BY strftime('%Y-%m', ngay_tao)
                   ORDER BY thang DESC
                   LIMIT 12"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_bh_report_quarterly(self, perf_conn):
        """Report query: quarterly revenue breakdown."""
        with benchmark("bh_report_quarterly", threshold_ms=500) as result:
            cursor = perf_conn.execute(
                """SELECT
                       strftime('%Y', ngay_tao) as year,
                       (CAST(strftime('%m', ngay_tao) AS INTEGER) + 2) / 3 as quy,
                       COUNT(*) as so_hop_dong,
                       SUM(tong_tien) as doanh_thu
                   FROM hop_dong
                   WHERE trang_thai IN ('da_thanh_toan', 'da_giao_xe')
                     AND ngay_tao >= DATE('now', '-24 months')
                   GROUP BY year, quy
                   ORDER BY year DESC, quy DESC"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_bh_report_yearly(self, perf_conn):
        """Report query: yearly revenue breakdown."""
        with benchmark("bh_report_yearly", threshold_ms=500) as result:
            cursor = perf_conn.execute(
                """SELECT
                       strftime('%Y', ngay_tao) as year,
                       COUNT(*) as so_hop_dong,
                       SUM(tong_tien) as doanh_thu
                   FROM hop_dong
                   WHERE trang_thai IN ('da_thanh_toan', 'da_giao_xe')
                   GROUP BY strftime('%Y', ngay_tao)
                   ORDER BY year DESC"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed


# =============================================================================
# VIP Customer Queries
# =============================================================================

class TestVIPCustomerPerformance:
    """Performance tests for VIP customer and purchase history queries."""

    def test_kh_vip_list(self, perf_conn):
        """Simple SELECT: find VIP customers."""
        with benchmark("kh_vip_list", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT * FROM khach_hang
                   WHERE phan_loai = 'VIP'
                   LIMIT 100"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_kh_vip_with_purchase_history(self, perf_conn):
        """JOIN: VIP customers with purchase history (count + total spend)."""
        with benchmark("kh_vip_purchase_history", threshold_ms=200) as result:
            cursor = perf_conn.execute(
                """SELECT
                       kh.id, kh.ho_ten, kh.so_dien_thoai,
                       kh.tong_gia_tri_mua, kh.so_xe_da_mua,
                       COUNT(hd.id) as hd_count,
                       SUM(hd.tong_tien) as total_spent
                   FROM khach_hang kh
                   LEFT JOIN hop_dong hd
                      ON kh.id = hd.khach_hang_id AND hd.trang_thai = 'da_giao_xe'
                   WHERE kh.phan_loai = 'VIP'
                   GROUP BY kh.id
                   ORDER BY kh.tong_gia_tri_mua DESC
                   LIMIT 50"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_kh_top_by_spending(self, perf_conn):
        """Aggregation: top 20 customers by total spending."""
        with benchmark("kh_top_by_spending", threshold_ms=100) as result:
            cursor = perf_conn.execute(
                """SELECT ho_ten, so_dien_thoai, phan_loai,
                          tong_gia_tri_mua, so_xe_da_mua
                   FROM khach_hang
                   WHERE so_xe_da_mua > 0
                   ORDER BY tong_gia_tri_mua DESC
                   LIMIT 20"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed


# =============================================================================
# Warehouse (Kho) Queries
# =============================================================================

class TestKhoPerformance:
    """Performance tests for warehouse/inventory queries."""

    def test_kho_ton_kho_by_pk(self, perf_conn):
        """Simple SELECT: inventory stock by phu_kien."""
        with benchmark("kho_ton_kho_by_pk", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT ma_pk, ten_pk, phan_loai, gia_ban, ton_kho
                   FROM phu_kien
                   WHERE ton_kho > 0
                   ORDER BY ten_pk
                   LIMIT 100"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_kho_xe_ton_kho(self, perf_conn):
        """Simple SELECT: vehicle stock by status."""
        with benchmark("kho_xe_ton_kho", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT hang, dong_xe, nam_san_xuat,
                          SUM(so_luong_ton) as tong_ton
                   FROM xe
                   WHERE trang_thai = 'con_hang'
                   GROUP BY hang, dong_xe, nam_san_xuat
                   ORDER BY tong_ton DESC"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_kho_nhap_xuat_report(self, perf_conn):
        """Report query: inventory receipt/expenditure summary."""
        with benchmark("kho_nhap_xuat_report", threshold_ms=500) as result:
            cursor = perf_conn.execute(
                """SELECT
                       DATE(nk.ngay_nhap) as ngay,
                       ncc.ten_ncc,
                       COUNT(DISTINCT nk.id) as so_lan_nhap,
                       SUM(ctnk.so_luong) as tong_so_luong,
                       SUM(ctnk.gia_nhap * ctnk.so_luong) as tong_gia_tri
                   FROM nhap_kho nk
                   JOIN chi_tiet_nhap_kho ctnk ON nk.id = ctnk.nhap_kho_id
                   JOIN nha_cung_cap ncc ON nk.nha_cung_cap_id = ncc.id
                   WHERE nk.ngay_nhap >= DATE('now', '-30 days')
                   GROUP BY DATE(nk.ngay_nhap), ncc.ten_ncc
                   ORDER BY ngay DESC"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed

    def test_kho_low_stock_xe(self, perf_conn):
        """Simple SELECT + aggregate: vehicles below minimum stock threshold."""
        with benchmark("kho_low_stock_xe", threshold_ms=50) as result:
            cursor = perf_conn.execute(
                """SELECT ma_xe, hang, dong_xe, so_luong_ton, muc_toi_thieu
                   FROM xe
                   WHERE so_luong_ton < muc_toi_thieu
                      OR (trang_thai = 'con_hang' AND so_luong_ton <= 2)
                   ORDER BY so_luong_ton ASC
                   LIMIT 20"""
            )
            rows = cursor.fetchall()
            result.rows_returned = len(rows)

        print_benchmark(result)
        assert result.passed


# =============================================================================
# Combined Workflow: Full WF-02 Search
# =============================================================================

class TestFullWorkflowPerformance:
    """End-to-end performance tests simulating full workflow queries."""

    def test_wf02_create_contract_lookup(self, perf_conn):
        """Simulate WF-02: search xe + KH before creating contract."""
        results = []

        # 1. Search available xe
        r = measure_query(
            perf_conn,
            """SELECT * FROM xe
               WHERE trang_thai = 'con_hang'
                 AND so_luong_ton > 0
               ORDER BY gia_ban ASC
               LIMIT 20""",
            query_name="wf02_xe_available",
            threshold_ms=50,
        )
        results.append(r)
        print_benchmark(r)

        # 2. Search VIP KH
        r = measure_query(
            perf_conn,
            """SELECT * FROM khach_hang
               WHERE phan_loai = 'VIP'
               ORDER BY tong_gia_tri_mua DESC
               LIMIT 20""",
            query_name="wf02_kh_vip",
            threshold_ms=50,
        )
        results.append(r)
        print_benchmark(r)

        # 3. Search promotions
        r = measure_query(
            perf_conn,
            """SELECT * FROM khuyen_mai
               WHERE trang_thai = 'dang_chay'
                 AND den_ngay >= DATE('now')
               ORDER BY gia_tri DESC
               LIMIT 10""",
            query_name="wf02_km_active",
            threshold_ms=50,
        )
        results.append(r)
        print_benchmark(r)

        # All individual queries should pass
        assert all(res.passed for res in results)

    def test_wf04_warranty_lookup(self, perf_conn):
        """Simulate WF-04: warranty lookup by phone/contract code."""
        # 1. Find warranty by contract
        r = measure_query(
            perf_conn,
            """SELECT bh.*, hd.ma_hop_dong, kh.ho_ten, kh.so_dien_thoai
               FROM bao_hanh bh
               JOIN hop_dong hd ON bh.hop_dong_id = hd.id
               JOIN khach_hang kh ON bh.khach_hang_id = kh.id
               WHERE bh.trang_thai = 'con_hieu_luc'
               ORDER BY bh.ngay_ket_thuc ASC
               LIMIT 50""",
            query_name="wf04_bh_lookup",
            threshold_ms=200,
        )
        print_benchmark(r)
        assert r.passed

    def test_wf03_installment_summary(self, perf_conn):
        """Simulate WF-03: installment plan summary for a KH."""
        r = measure_query(
            perf_conn,
            """SELECT
                   tg.id, tg.ngan_hang, tg.so_tien_vay,
                   tg.lai_suat_nam, tg.so_ky, tg.trang_thai,
                   hd.ma_hop_dong, kh.ho_ten,
                   (SELECT COUNT(*) FROM tra_gop_lich_su tls
                    WHERE tls.tra_gop_id = tg.id AND tls.trang_thai = 'da_tra')
                     as so_ky_da_tra
               FROM tra_gop tg
               JOIN hop_dong hd ON tg.hop_dong_id = hd.id
               JOIN khach_hang kh ON hd.khach_hang_id = kh.id
               ORDER BY tg.id DESC
               LIMIT 50""",
            query_name="wf03_tg_summary",
            threshold_ms=200,
        )
        print_benchmark(r)
        assert r.passed
