"""Performance test fixtures for Car-Management.

Provides:
- perf_db: Connection to SIT DB seeded with 1000 KH, 5000 HĐ
- benchmark: Context manager / decorator to measure execution time

Target thresholds:
- Simple SELECT: < 50ms
- JOIN + aggregation: < 200ms
- Report query: < 500ms
"""

import os
import sys
import sqlite3
import tempfile
import time
import shutil
from pathlib import Path
from typing import Callable, Optional
from contextlib import contextmanager
from dataclasses import dataclass

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.infrastructure.database.connection import get_connection
from app.infrastructure.database.migrations.runner import MigrationRunner
from app.infrastructure.database.seeds.dev_seed import (
    seed_all,
    seed_vai_tro,
    seed_xe,
    seed_khach_hang,
    seed_nha_cung_cap,
    seed_khuyen_mai,
    seed_phu_kien,
    seed_nhan_vien,
)


# =============================================================================
# Configuration
# =============================================================================

PERF_DB_NAME = "car_management_perf.db"
PERF_DB_DIR = Path(__file__).parent.parent.parent / "data"


def _get_perf_db_path() -> Path:
    return PERF_DB_DIR / PERF_DB_NAME


# =============================================================================
# Benchmark Thresholds
# =============================================================================

@dataclass
class PerfThreshold:
    """Performance threshold for a query category."""
    simple_select_ms: float = 50.0
    join_aggregation_ms: float = 200.0
    report_query_ms: float = 500.0


PERF_THRESHOLDS = PerfThreshold()


# =============================================================================
# Benchmark Utilities
# =============================================================================

@dataclass
class BenchmarkResult:
    """Result of a benchmark measurement."""
    query_name: str
    elapsed_ms: float
    threshold_ms: float
    passed: bool
    rows_returned: int = 0

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return (
            f"{status} | {self.query_name}: {self.elapsed_ms:.2f}ms "
            f"(threshold: {self.threshold_ms:.2f}ms)"
        )


@contextmanager
def benchmark(
    query_name: str,
    threshold_ms: float = 50.0,
):
    """Context manager to measure query execution time.

    Usage:
        with benchmark("my query", threshold_ms=100):
            cursor.execute("SELECT ...")
            results = cursor.fetchall()

    Args:
        query_name: Human-readable name for the query
        threshold_ms: Maximum acceptable time in milliseconds

    Yields:
        BenchmarkResult (via the context manager result attribute)
    """
    result = BenchmarkResult(
        query_name=query_name,
        elapsed_ms=0.0,
        threshold_ms=threshold_ms,
        passed=False,
        rows_returned=0,
    )
    start = time.perf_counter()
    try:
        yield result
    finally:
        elapsed = time.perf_counter() - start
        result.elapsed_ms = elapsed * 1000  # Convert to ms
        result.passed = result.elapsed_ms <= result.threshold_ms


def measure_query(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = (),
    query_name: str = "unnamed_query",
    threshold_ms: float = 50.0,
) -> BenchmarkResult:
    """Execute a query and measure its execution time.

    Args:
        conn: Database connection
        query: SQL query string
        params: Query parameters
        query_name: Name for reporting
        threshold_ms: Performance threshold in milliseconds

    Returns:
        BenchmarkResult with timing and pass/fail status
    """
    result = BenchmarkResult(
        query_name=query_name,
        elapsed_ms=0.0,
        threshold_ms=threshold_ms,
        passed=False,
        rows_returned=0,
    )
    start = time.perf_counter()
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    elapsed = time.perf_counter() - start
    result.elapsed_ms = elapsed * 1000
    result.rows_returned = len(rows)
    result.passed = result.elapsed_ms <= result.threshold_ms
    return result


# =============================================================================
# Large Seed Helper (Performance DB)
# =============================================================================

def seed_large_dataset(conn: sqlite3.Connection, scale: str = "full"):
    """Seed the performance DB with a large dataset.

    Args:
        conn: Database connection
        scale: 'mini' (100 KH, 500 HD) or 'full' (1000 KH, 5000 HD)
    """
    cursor = conn.cursor()

    vai_tro_count = cursor.execute("SELECT COUNT(*) FROM vai_tro").fetchone()[0]
    if vai_tro_count == 0:
        seed_vai_tro(cursor)

    nhan_vien_count = cursor.execute("SELECT COUNT(*) FROM nhan_vien").fetchone()[0]
    if nhan_vien_count == 0:
        seed_nhan_vien(cursor)

    xe_count = cursor.execute("SELECT COUNT(*) FROM xe").fetchone()[0]
    if xe_count == 0:
        seed_xe(cursor)

    kh_count = cursor.execute("SELECT COUNT(*) FROM khach_hang").fetchone()[0]
    if kh_count == 0:
        seed_khach_hang(cursor)

    ncc_count = cursor.execute("SELECT COUNT(*) FROM nha_cung_cap").fetchone()[0]
    if ncc_count == 0:
        seed_nha_cung_cap(cursor)

    km_count = cursor.execute("SELECT COUNT(*) FROM khuyen_mai").fetchone()[0]
    if km_count == 0:
        seed_khuyen_mai(cursor)

    pk_count = cursor.execute("SELECT COUNT(*) FROM phu_kien").fetchone()[0]
    if pk_count == 0:
        seed_phu_kien(cursor)

    conn.commit()

    # Determine target sizes based on scale
    if scale == "mini":
        target_kh = 100
        target_hd = 500
    else:
        target_kh = 1000
        target_hd = 5000

    # Bulk-insert additional KH to reach target
    current_kh = cursor.execute("SELECT COUNT(*) FROM khach_hang").fetchone()[0]
    if current_kh < target_kh:
        _bulk_insert_kh(cursor, target_kh - current_kh)

    # Bulk-insert additional HD to reach target
    current_hd = cursor.execute("SELECT COUNT(*) FROM hop_dong").fetchone()[0]
    if current_hd < target_hd:
        _bulk_insert_hop_dong(cursor, current_kh, target_hd - current_hd)

    conn.commit()


def _bulk_insert_kh(cursor, count: int):
    """Bulk insert khach_hang records."""
    import random
    from datetime import datetime, timedelta

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    phan_loai_options = ["Thuong", "VIP", "Vip"]
    first_names = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Nguyen", "Dao", "Dinh"]
    last_names = ["Van A", "Van B", "Thi C", "Thi D", "Van E", "Van F"]

    records = []
    for i in range(count):
        ho_ten = f"{random.choice(first_names)} {random.choice(last_names)} {i}"
        so_dien_thoai = f"0909{i:05d}"
        email = f"kh_perf_{i}_{random.randint(1000,9999)}@test.com"
        dia_chi = f"{i} Test Street, City"
        phan_loai = random.choice(phan_loai_options)
        tong_gia_tri = random.randint(0, 5_000_000_000)
        so_xe = random.randint(0, 5)
        records.append(
            (ho_ten, so_dien_thoai, email, dia_chi, None, phan_loai, tong_gia_tri, so_xe, now, now)
        )

    cursor.executemany(
        """INSERT INTO khach_hang
           (ho_ten, so_dien_thoai, email, dia_chi, ngay_sinh, phan_loai,
            tong_gia_tri_mua, so_xe_da_mua, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records
    )


def _bulk_insert_hop_dong(cursor, kh_count: int, count: int):
    """Bulk insert hop_dong records for performance testing."""
    import random
    from datetime import datetime, timedelta

    now = datetime.now()
    records = []

    # Get all KH and xe IDs
    kh_ids = [r[0] for r in cursor.execute("SELECT id FROM khach_hang").fetchall()]
    xe_ids = [r[0] for r in cursor.execute("SELECT id FROM xe").fetchall()]
    nv_ids = [r[0] for r in cursor.execute("SELECT id FROM nhan_vien").fetchall()]
    km_ids = [r[0] for r in cursor.execute("SELECT id FROM khuyen_mai").fetchall()] + [None]

    trang_thai_options = ["moi_tao", "da_thanh_toan", "da_giao_xe", "huy"]

    for i in range(count):
        kh_id = random.choice(kh_ids) if kh_ids else 1
        xe_id = random.choice(xe_ids) if xe_ids else 1
        nv_id = random.choice(nv_ids) if nv_ids else 1
        km_id = random.choice(km_ids)

        days_ago = random.randint(0, 365)
        ngay_tao = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        ngay_thanh_toan = (now - timedelta(days=days_ago - 1)).strftime("%Y-%m-%d %H:%M:%S") if random.random() > 0.3 else None
        ngay_giao_xe = (now - timedelta(days=days_ago - 2)).strftime("%Y-%m-%d %H:%M:%S") if random.random() > 0.4 else None

        gia_xe = random.randint(300_000_000, 2_000_000_000)
        tong_pk = random.randint(0, 30_000_000)
        tien_km = random.randint(0, 20_000_000)
        tong_tien = gia_xe + tong_pk - tien_km
        trang_thai = random.choice(trang_thai_options)

        ma_hd = f"HD perf {i:05d}"
        ly_do_huy = f"Huy reason {i}" if trang_thai == "huy" else None

        records.append(
            (
                ma_hd, kh_id, xe_id, nv_id, km_id,
                gia_xe, tong_pk, tien_km, tong_tien,
                trang_thai, ngay_tao, ngay_thanh_toan, ngay_giao_xe,
                ly_do_huy, "", now.strftime("%Y-%m-%d %H:%M:%S"), now.strftime("%Y-%m-%d %H:%M:%S")
            )
        )

    cursor.executemany(
        """INSERT INTO hop_dong
           (ma_hop_dong, khach_hang_id, xe_id, nhan_vien_id, khuyen_mai_id,
            gia_xe, tong_gia_phu_kien, tien_giam_km, tong_tien,
            trang_thai, ngay_tao, ngay_thanh_toan, ngay_giao_xe,
            ly_do_huy, ghi_chu, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        records
    )


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def perf_db_path():
    """Create/load the performance test database (session-scoped).

    Seeds the DB with 1000 KH and 5000 HĐ for realistic performance testing.
    """
    db_path = _get_perf_db_path()

    # Ensure data directory exists
    PERF_DB_DIR.mkdir(parents=True, exist_ok=True)

    # Check if we already have a populated perf DB
    if db_path.exists():
        # Verify it has enough records
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            kh_count = conn.execute("SELECT COUNT(*) FROM khach_hang").fetchone()[0]
            hd_count = conn.execute("SELECT COUNT(*) FROM hop_dong").fetchone()[0]
            if kh_count >= 100 and hd_count >= 500:
                conn.close()
                yield str(db_path)
                return
        except Exception:
            pass
        conn.close()
        db_path.unlink()

    # Create fresh perf DB
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    runner = MigrationRunner(str(db_path))
    runner.run_pending()

    # Seed with large dataset
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    seed_large_dataset(conn, scale="full")
    conn.close()

    yield str(db_path)

    # Cleanup after session (optional — comment out to inspect DB after test run)
    # if db_path.exists():
    #     db_path.unlink()


@pytest.fixture
def perf_conn(perf_db_path):
    """Provide a fresh connection to the perf DB for each test."""
    conn = sqlite3.connect(perf_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


@pytest.fixture
def thresholds():
    """Provide performance thresholds."""
    return PERF_THRESHOLDS
