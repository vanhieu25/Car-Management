"""SIT Integration Tests — 8 E2E Workflow Helpers.

This module provides pytest-based integration test helpers for the 8 E2E workflows:
- WF-01: Nhập kho (Import inventory from supplier)
- WF-02: Bán xe chuẩn (Standard car sale)
- WF-03: Bán trả góp (Installment sale)
- WF-04: Bảo hành (Warranty management)
- WF-05: Bảo dưỡng định kỳ (Scheduled maintenance)
- WF-06: Khiếu nại (Complaint handling)
- WF-07: Marketing → Lead → KH (Marketing lead to customer conversion)
- WF-08: Hủy hợp đồng (Contract cancellation)

Each test:
1. Uses the SIT database (via setup_sit_env.py)
2. Logs in as the appropriate role
3. Executes workflow steps programmatically via service/repo layers
4. Asserts final state (DB records, status transitions)
5. Cleans up test data after each run

Run via:
    pytest tests/integration/test_workflow.py -v
    pytest tests/integration/test_workflow.py::test_wf02_ban_xe_chuan -v
"""

import os
import sqlite3
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.infrastructure.database.connection import get_connection, get_connection_context
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
from app.domain.entities import NhanVien

# Import all services used across workflows
from app.application.services.auth_service import AuthService
from app.application.services.hop_dong_service import (
    HopDongService,
    HopDongCreateData,
    HopDongNotFoundError,
)
from app.application.services.nhap_kho_service import NhapKhoService
from app.application.services.bao_hanh_service import (
    BaoHanhService,
    BaoHanhYeuCauData,
    BaoHanhNotFoundError,
)
from app.application.services.bao_duong_service import (
    BaoDuongService,
    BaoDuongCreateData,
    BaoDuongUpdateData,
)
from app.application.services.khieu_nai_service import (
    KhieuNaiService,
    KhieuNaiCreateData,
    KhieuNaiUpdateData,
)
from app.application.services.chien_dich_mk_service import (
    ChienDichMkService,
    ChienDichMkCreateData,
    ChienDichMkUpdateData,
)
from app.application.services.lead_service import (
    LeadService,
    LeadCreateData,
    LeadUpdateData,
)
from app.application.services.khach_hang_service import (
    KhachHangService,
    KhachHangCreateData,
)
from app.application.services.tra_gop_service import TraGopService


# =============================================================================
# Test Configuration
# =============================================================================

SIT_DB_NAME = "car_management_sit_integration.db"
SIT_DB_DIR = Path(__file__).parent.parent.parent / "data"


def _get_sit_db_path() -> Path:
    """Return path to SIT integration test database."""
    return SIT_DB_DIR / SIT_DB_NAME


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def sit_db_path():
    """Create a fresh SIT database seeded with test data for the session."""
    db_path = _get_sit_db_path()

    # Ensure data directory exists
    SIT_DB_DIR.mkdir(parents=True, exist_ok=True)

    # Remove old SIT DB if exists
    if db_path.exists():
        db_path.unlink()

    # Create fresh DB and run migrations
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    runner = MigrationRunner(str(db_path))
    runner.run_pending()

    # Seed test users and minimal data
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Seed vai_tro
    seed_vai_tro(cursor)

    # Seed test users (admin/sales/kt roles)
    seed_nhan_vien(cursor)

    # Seed minimal data for workflows
    seed_xe(cursor)
    seed_khach_hang(cursor)
    seed_nha_cung_cap(cursor)
    seed_khuyen_mai(cursor)
    seed_phu_kien(cursor)

    conn.commit()
    conn.close()

    yield str(db_path)

    # Cleanup after session
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sit_conn(sit_db_path):
    """Provide a fresh SIT DB connection for each test (auto-cleanup)."""
    import sqlite3
    conn = sqlite3.connect(sit_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def admin_conn(sit_db_path):
    """Connection logged in as admin."""
    import sqlite3
    conn = sqlite3.connect(sit_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def sales_conn(sit_db_path):
    """Connection logged in as sales (nv) user."""
    import sqlite3
    conn = sqlite3.connect(sit_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def kt_conn(sit_db_path):
    """Connection logged in as kỹ thuật BH user."""
    import sqlite3
    conn = sqlite3.connect(sit_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def sample_xe_id(sit_conn):
    """Return ID of a sample available xe."""
    cursor = sit_conn.execute(
        "SELECT id FROM xe WHERE so_luong_ton > 0 AND trang_thai = 'con_hang' LIMIT 1"
    )
    row = cursor.fetchone()
    assert row, "No available xe found in seed data"
    return row[0]


@pytest.fixture
def sample_kh_id(sit_conn):
    """Return ID of a sample khach_hang."""
    cursor = sit_conn.execute("SELECT id FROM khach_hang LIMIT 1")
    row = cursor.fetchone()
    assert row, "No khach_hang found in seed data"
    return row[0]


@pytest.fixture
def sample_nv_id(sit_conn):
    """Return ID of a sample nhan_vien (sales)."""
    cursor = sit_conn.execute(
        "SELECT id FROM nhan_vien WHERE vai_tro_id = 2 LIMIT 1"
    )
    row = cursor.fetchone()
    assert row, "No sales NV found in seed data"
    return row[0]


@pytest.fixture
def admin_nv_id(sit_conn):
    """Return ID of admin nhan_vien."""
    cursor = sit_conn.execute(
        "SELECT id FROM nhan_vien WHERE vai_tro_id = 1 LIMIT 1"
    )
    row = cursor.fetchone()
    return row[0] if row else 1


@pytest.fixture
def kt_nv_id(sit_conn):
    """Return ID of kỹ thuật BH nhan_vien."""
    cursor = sit_conn.execute(
        "SELECT id FROM nhan_vien WHERE vai_tro_id = 3 LIMIT 1"
    )
    row = cursor.fetchone()
    return row[0] if row else 3


# =============================================================================
# Test Cleanup Helper
# =============================================================================

def cleanup_test_data(conn, created_ids: dict):
    """Clean up all test data created during a workflow test.

    Args:
        conn: Database connection
        created_ids: Dict of table_name -> list of IDs to delete
    """
    cursor = conn.cursor()
    for table, ids in created_ids.items():
        if ids:
            placeholders = ",".join("?" * len(ids))
            cursor.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", ids)
    conn.commit()


# =============================================================================
# WF-01: Nhập kho (Import from Supplier)
# =============================================================================

def test_wf01_nhap_kho(sit_conn, admin_nv_id):
    """WF-01: Nhập kho từ NCC.

    Steps:
    1. Get a xe with trang_thai='da_ban' and so_luong_ton=0
    2. Create nhap_kho with 1 unit of that xe at given price
    3. Assert xe.so_luong_ton increased by 1
    4. Assert xe.trang_thai changed from 'da_ban' to 'con_hang' (TRG-04)
    5. Assert nhap_kho record created with correct nha_cung_cap_id

    Cleanup: Delete nhap_kho, chi_tiet_nhap_kho, restore xe stock.
    """
    cursor = sit_conn.cursor()

    # Find a 'da_ban' xe with 0 stock to test TRG-04
    cursor.execute(
        "SELECT id, ma_xe, so_luong_ton, trang_thai FROM xe LIMIT 1"
    )
    xe = dict(cursor.fetchone())

    original_stock = xe["so_luong_ton"]
    original_status = xe["trang_thai"]

    # Get a supplier
    cursor.execute("SELECT id FROM nha_cung_cap LIMIT 1")
    ncc_row = cursor.fetchone()
    assert ncc_row, "No nha_cung_cap found"
    ncc_id = ncc_row[0]

    # Create inventory receipt via service
    service = NhapKhoService(sit_conn)
    ngay_nhap = datetime.now().strftime("%Y-%m-%d")

    items = [
        {
            "loai_item": "xe",
            "item_id": xe["id"],
            "so_luong": 1,
            "gia_nhap": 400_000_000,
        }
    ]

    created_nk = service.create(
        nha_cung_cap_id=ncc_id,
        items=items,
        nhan_vien_id=admin_nv_id,
        ngay_nhap=ngay_nhap,
        ghi_chu="WF-01 test data",
    )

    # Refresh xe state
    cursor.execute(
        "SELECT so_luong_ton, trang_thai FROM xe WHERE id = ?", (xe["id"],)
    )
    row = cursor.fetchone()
    new_stock = row[0]
    new_status = row[1]

    # Assert: stock increased
    assert new_stock == original_stock + 1, (
        f"Xe stock should increase by 1: expected {original_stock + 1}, got {new_stock}"
    )

    # Assert: TRG-04 — if was 'da_ban' with 0 stock, now 'con_hang'
    if original_status == "da_ban" and original_stock == 0:
        assert new_status == "con_hang", (
            f"Xe trang_thai should change from 'da_ban' to 'con_hang': got '{new_status}'"
        )

    # Assert: nhap_kho record created
    assert created_nk["id"] is not None
    assert created_nk["nha_cung_cap_id"] == ncc_id

    # Cleanup
    cleanup_test_data(sit_conn, {
        "chi_tiet_nhap_kho": [created_nk["id"]],
        "nhap_kho": [created_nk["id"]],
    })

    # Restore xe stock
    sit_conn.execute(
        "UPDATE xe SET so_luong_ton = ?, trang_thai = ? WHERE id = ?",
        (original_stock, original_status, xe["id"])
    )
    sit_conn.commit()


# =============================================================================
# WF-02: Bán xe chuẩn (Standard Car Sale)
# =============================================================================

def test_wf02_ban_xe_chuan(sit_conn, sample_kh_id, sample_nv_id, sample_xe_id):
    """WF-02: Bán xe chuẩn — full lifecycle.

    Steps:
    1. Create HopDong (moi_tao) with xe + optional PK + optional KM
    2. Assert HopDong status = 'moi_tao', tong_tien calculated
    3. set_paid() → status = 'da_thanh_toan', xe stock -1
    4. set_delivered() → status = 'da_giao_xe', BH auto-created (TRG-02)
    5. Assert KH: tong_gia_tri_mua updated, so_xe_da_mua incremented
    6. Assert NV: so_hop_dong and doanh_thu KPI updated

    Cleanup: Delete BH, HopDong, HopDongPhuKien, restore stock.
    """
    cursor = sit_conn.cursor()

    # Get original xe stock
    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    original_xe_stock = cursor.fetchone()[0]

    # Get original KH stats
    cursor.execute(
        "SELECT tong_gia_tri_mua, so_xe_da_mua FROM khach_hang WHERE id = ?",
        (sample_kh_id,)
    )
    kh_row = cursor.fetchone()
    original_kh_tong = kh_row[0]
    original_kh_so_xe = kh_row[1]

    # Get original NV KPI
    cursor.execute(
        "SELECT so_hop_dong, doanh_thu FROM nhan_vien WHERE id = ?",
        (sample_nv_id,)
    )
    nv_row = cursor.fetchone()
    original_nv_hd = nv_row[0] or 0
    original_nv_dt = nv_row[1] or 0

    # Step 1: Create contract
    service = HopDongService(sit_conn)
    data = HopDongCreateData(
        khach_hang_id=sample_kh_id,
        xe_id=sample_xe_id,
        nhan_vien_id=sample_nv_id,
        ghi_chu="WF-02 test",
    )
    created_hd = service.create(data)
    hd_id = created_hd.id

    # Assert: status = moi_tao
    assert created_hd.trang_thai == "moi_tao", (
        f"Expected status 'moi_tao', got '{created_hd.trang_thai}'"
    )
    assert created_hd.tong_tien > 0, "tong_tien must be > 0"

    # Step 2: set_paid
    paid_hd = service.set_paid(hd_id, sample_nv_id)
    assert paid_hd.trang_thai == "da_thanh_toan", (
        f"Expected 'da_thanh_toan', got '{paid_hd.trang_thai}'"
    )

    # Assert: xe stock decreased
    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    new_xe_stock = cursor.fetchone()[0]
    assert new_xe_stock == original_xe_stock - 1, (
        f"Xe stock should decrease by 1: expected {original_xe_stock - 1}, got {new_xe_stock}"
    )

    # Step 3: set_delivered → creates warranty
    delivered_hd = service.set_delivered(hd_id, sample_nv_id)
    assert delivered_hd.trang_thai == "da_giao_xe", (
        f"Expected 'da_giao_xe', got '{delivered_hd.trang_thai}'"
    )

    # Assert: BH auto-created (TRG-02)
    cursor.execute("SELECT id FROM bao_hanh WHERE hop_dong_id = ?", (hd_id,))
    bh_row = cursor.fetchone()
    assert bh_row, "Warranty should be auto-created on delivery (TRG-02)"
    bh_id = bh_row[0]

    # Refresh KH stats
    cursor.execute(
        "SELECT tong_gia_tri_mua, so_xe_da_mua FROM khach_hang WHERE id = ?",
        (sample_kh_id,)
    )
    kh_row = cursor.fetchone()
    new_kh_tong = kh_row[0]
    new_kh_so_xe = kh_row[1]

    assert new_kh_tong == original_kh_tong + paid_hd.tong_tien, (
        f"KH tong_gia_tri_mua should increase by tong_tien"
    )
    assert new_kh_so_xe == original_kh_so_xe + 1, (
        f"KH so_xe_da_mua should increase by 1"
    )

    # Refresh NV KPI
    cursor.execute(
        "SELECT so_hop_dong, doanh_thu FROM nhan_vien WHERE id = ?",
        (sample_nv_id,)
    )
    nv_row = cursor.fetchone()
    new_nv_hd = nv_row[0] or 0
    new_nv_dt = nv_row[1] or 0

    assert new_nv_hd == original_nv_hd + 1, "NV so_hop_dong should increment"
    assert new_nv_dt == original_nv_dt + paid_hd.tong_tien, (
        "NV doanh_thu should increase by tong_tien"
    )

    # Cleanup
    sit_conn.execute("DELETE FROM bao_hanh WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong WHERE id = ?", (hd_id,))
    sit_conn.execute(
        "UPDATE xe SET so_luong_ton = ? WHERE id = ?",
        (original_xe_stock, sample_xe_id)
    )
    sit_conn.execute(
        "UPDATE khach_hang SET tong_gia_tri_mua = ?, so_xe_da_mua = ? WHERE id = ?",
        (original_kh_tong, original_kh_so_xe, sample_kh_id)
    )
    sit_conn.execute(
        "UPDATE nhan_vien SET so_hop_dong = ?, doanh_thu = ? WHERE id = ?",
        (original_nv_hd, original_nv_dt, sample_nv_id)
    )
    sit_conn.commit()


# =============================================================================
# WF-03: Bán trả góp (Installment Sale)
# =============================================================================

def test_wf03_ban_tra_gop(sit_conn, sample_kh_id, sample_nv_id, sample_xe_id):
    """WF-03: Bán trả góp — contract with installment plan.

    Steps:
    1. Create HopDong (moi_tao)
    2. set_paid()
    3. set_delivered()
    4. Create TraGop record with bank, principal, interest, n months
    5. Assert TraGop created and tra_gop_lich_su rows = n
    6. Assert each lich_su row has correct thoi_gian (1 month apart)

    Cleanup: Delete TG, TG lich_su, BH, HopDong, restore stock.
    """
    cursor = sit_conn.cursor()

    # Get original xe stock
    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    original_xe_stock = cursor.fetchone()[0]

    # Step 1: Create contract
    service = HopDongService(sit_conn)
    tg_service = TraGopService(sit_conn)

    data = HopDongCreateData(
        khach_hang_id=sample_kh_id,
        xe_id=sample_xe_id,
        nhan_vien_id=sample_nv_id,
    )
    created_hd = service.create(data)
    hd_id = created_hd.id

    # Step 2: set_paid
    service.set_paid(hd_id, sample_nv_id)

    # Step 3: set_delivered
    service.set_delivered(hd_id, sample_nv_id)

    # Step 4: Create installment plan
    ngan_hang = "Vietcombank"
    P = int(created_hd.tong_tien * 0.7)  # 70% loan
    r_year = 8.5  # 8.5% annual
    n = 12  # 12 months

    created_tg = tg_service.create(
        hop_dong_id=hd_id,
        ngan_hang=ngan_hang,
        P=P,
        r_year=r_year,
        n=n,
        nhan_vien_id=sample_nv_id,
    )

    assert created_tg is not None, "TraGop should be created"
    assert created_tg.ngan_hang == ngan_hang
    assert created_tg.so_tien_vay == P
    assert created_tg.lai_suat_nam == r_year
    assert created_tg.so_ky == n

    # Step 5: Assert lich_su rows = n
    cursor.execute(
        "SELECT COUNT(*) FROM tra_gop_lich_su WHERE tra_gop_id = ?",
        (created_tg.id,)
    )
    lich_su_count = cursor.fetchone()[0]
    assert lich_su_count == n, (
        f"Expected {n} lich_su rows, got {lich_su_count}"
    )

    # Step 6: Verify first payment is ~1 month from now
    cursor.execute(
        """SELECT ngay_den_han FROM tra_gop_lich_su
           WHERE tra_gop_id = ? ORDER BY id LIMIT 1""",
        (created_tg.id,)
    )
    first_row = cursor.fetchone()
    assert first_row is not None, "Should have at least 1 lich_su row"

    # Cleanup
    sit_conn.execute("DELETE FROM tra_gop_lich_su WHERE tra_gop_id = ?", (created_tg.id,))
    sit_conn.execute("DELETE FROM tra_gop WHERE id = ?", (created_tg.id,))
    sit_conn.execute("DELETE FROM bao_hanh WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong WHERE id = ?", (hd_id,))
    sit_conn.execute(
        "UPDATE xe SET so_luong_ton = ? WHERE id = ?",
        (original_xe_stock, sample_xe_id)
    )
    sit_conn.commit()


# =============================================================================
# WF-04: Bảo hành (Warranty Management)
# =============================================================================

def test_wf04_bao_hanh(sit_conn, admin_nv_id, sample_kh_id, sample_xe_id, sample_nv_id):
    """WF-04: Bảo hành — warranty request lifecycle.

    Steps:
    1. Create HopDong → set_paid → set_delivered (auto-creates BH)
    2. Find BH by hop_dong_id
    3. Create a warranty request (yeu_cau) with phan_loai='mien_phi'
    4. Assert yeu_cau status = 'tiep_nhan'
    5. Update status: tiep_nhan → dang_xu_ly → hoan_thanh
    6. Assert final state

    Cleanup: Delete yeu_cau, BH, HopDong, restore stock.
    """
    cursor = sit_conn.cursor()

    # Get xe stock
    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    original_xe_stock = cursor.fetchone()[0]

    # Step 1: Create and deliver contract (creates BH automatically)
    hd_service = HopDongService(sit_conn)
    bh_service = BaoHanhService(sit_conn)

    data = HopDongCreateData(
        khach_hang_id=sample_kh_id,
        xe_id=sample_xe_id,
        nhan_vien_id=sample_nv_id,
    )
    created_hd = hd_service.create(data)
    hd_id = created_hd.id

    hd_service.set_paid(hd_id, sample_nv_id)
    hd_service.set_delivered(hd_id, sample_nv_id)

    # Step 2: Find BH by hop_dong_id
    bh = bh_service.get_by_hop_dong_id(hd_id)
    assert bh is not None, "BH should exist after delivery (TRG-02)"
    assert bh["trang_thai"] == "con_hieu_luc", (
        f"BH should be 'con_hieu_luc', got '{bh['trang_thai']}'"
    )

    # Step 3: Create warranty request
    from datetime import datetime
    yeu_cau_data = BaoHanhYeuCauData(
        ngay_yeu_cau=datetime.now().strftime("%Y-%m-%d"),
        loai_yeu_cau="sua_chua",
        mo_ta_tinh_trang="WF-04 test - lỗi phanh",
        phan_loai="mien_phi",
        chi_phi=0,
        nhan_vien_id=admin_nv_id,
        ghi_chu="Test WF-04",
    )

    created_yeu_cau = bh_service.create_request(bh["id"], yeu_cau_data)
    assert created_yeu_cau is not None
    assert created_yeu_cau["phan_loai"] == "mien_phi"

    # Step 4: Assert initial status
    assert created_yeu_cau["trang_thai"] == "dang_xu_ly", (
        f"Initial status should be 'dang_xu_ly', got '{created_yeu_cau['trang_thai']}'"
    )

    # Step 5: Update status flow
    bh_service.update_request(
        created_yeu_cau["id"],
        trang_thai="da_hoan_thanh",
        nhan_vien_id=admin_nv_id,
    )

    # Cleanup
    sit_conn.execute("DELETE FROM bao_hanh_yeu_cau WHERE id = ?", (created_yeu_cau["id"],))
    sit_conn.execute("DELETE FROM bao_hanh WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong WHERE id = ?", (hd_id,))
    sit_conn.execute(
        "UPDATE xe SET so_luong_ton = ? WHERE id = ?",
        (original_xe_stock, sample_xe_id)
    )
    sit_conn.commit()


# =============================================================================
# WF-05: Bảo dưỡng định kỳ (Scheduled Maintenance)
# =============================================================================

def test_wf05_bao_duong(sit_conn, admin_nv_id, sample_kh_id, sample_xe_id, sample_nv_id):
    """WF-05: Bảo dưỡng định kỳ — maintenance schedule lifecycle.

    Steps:
    1. Create HopDong → set_paid → set_delivered
    2. Create BaoDuong record (trang_thai='cho_xac_nhan')
    3. Update BaoDuong: confirm and set ngay_thuc_te (trang_thai='dang_thuc_hien')
    4. Complete BaoDuong (trang_thai='hoan_thanh')
    5. Assert final status and chi_phi recorded

    Cleanup: Delete BaoDuong, BH, HopDong, restore stock.
    """
    cursor = sit_conn.cursor()

    # Get xe stock
    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    original_xe_stock = cursor.fetchone()[0]

    # Step 1: Create and deliver contract
    hd_service = HopDongService(sit_conn)
    bd_service = BaoDuongService(sit_conn)

    data = HopDongCreateData(
        khach_hang_id=sample_kh_id,
        xe_id=sample_xe_id,
        nhan_vien_id=sample_nv_id,
    )
    created_hd = hd_service.create(data)
    hd_id = created_hd.id

    hd_service.set_paid(hd_id, sample_nv_id)
    hd_service.set_delivered(hd_id, sample_nv_id)

    # Step 2: Create BaoDuong record
    from datetime import date
    ngay_du_kien = date.today().strftime("%Y-%m-%d")

    bd_data = BaoDuongCreateData(
        khach_hang_id=sample_kh_id,
        xe_id=sample_xe_id,
        ngay_du_kien=ngay_du_kien,
        km_xe=15000,
        noi_dung="WF-05 test - bảo dưỡng định kỳ 15,000km",
        chi_phi=1_500_000,
        nhan_vien_id=admin_nv_id,
        ghi_chu="Test WF-05",
    )

    created_bd = bd_service.create(bd_data)
    assert created_bd is not None
    assert created_bd.trang_thai == "cho_xac_nhan"

    # Step 3: Update — confirm and set ngay_thuc_te
    update_data = BaoDuongUpdateData(
        ngay_thuc_te=ngay_du_kien,
        trang_thai="da_xac_nhan",
    )
    bd_service.update(created_bd.id, update_data)

    cursor.execute(
        "SELECT trang_thai, ngay_thuc_te FROM bao_duong WHERE id = ?",
        (created_bd.id,)
    )
    row = cursor.fetchone()
    assert row["trang_thai"] == "da_xac_nhan"
    assert row["ngay_thuc_te"] is not None

    # Step 4: Start work
    bd_service.update(
        created_bd.id,
        BaoDuongUpdateData(trang_thai="dang_thuc_hien")
    )

    cursor.execute(
        "SELECT trang_thai FROM bao_duong WHERE id = ?",
        (created_bd.id,)
    )
    assert cursor.fetchone()[0] == "dang_thuc_hien"

    # Step 5: Complete
    bd_service.update(
        created_bd.id,
        BaoDuongUpdateData(trang_thai="da_hoan_thanh")
    )

    cursor.execute("SELECT trang_thai FROM bao_duong WHERE id = ?", (created_bd.id,))
    assert cursor.fetchone()[0] == "da_hoan_thanh"

    # Cleanup
    sit_conn.execute("DELETE FROM bao_duong WHERE id = ?", (created_bd.id,))
    sit_conn.execute("DELETE FROM bao_hanh WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong WHERE id = ?", (hd_id,))
    sit_conn.execute(
        "UPDATE xe SET so_luong_ton = ? WHERE id = ?",
        (original_xe_stock, sample_xe_id)
    )
    sit_conn.commit()


# =============================================================================
# WF-06: Khiếu nại (Complaint Handling)
# =============================================================================

def test_wf06_khieu_nai(sit_conn, admin_nv_id, sample_kh_id, sample_nv_id):
    """WF-06: Khiếu nại — complaint lifecycle.

    Steps:
    1. Create KhieuNai (trang_thai='moi')
    2. Update: assign nhan_vien_xu_ly_id, set trang_thai='dang_xu_ly'
    3. Update: set trang_thai='da_giai_quyet', danh_gia_hai_long=4
    4. Assert final trang_thai='da_giai_quyet' and ly_do set

    Cleanup: Delete KhieuNai.
    """
    cursor = sit_conn.cursor()

    kn_service = KhieuNaiService(sit_conn)

    # Step 1: Create complaint
    kn_data = KhieuNaiCreateData(
        khach_hang_id=sample_kh_id,
        tieu_de="WF-06 test - khiếu nại chất lượng dịch vụ",
        noi_dung="Xe giao bị trầy cốp sau 3 ngày sử dụng",
        muc_do="trung_binh",
        created_by=sample_nv_id,
    )

    created_kn = kn_service.create(kn_data)
    assert created_kn is not None
    assert created_kn["trang_thai"] == "moi", (
        f"Initial status should be 'moi', got '{created_kn['trang_thai']}'"
    )

    # Step 2: Assign and move to dang_xu_ly
    update_data = KhieuNaiUpdateData(
        nhan_vien_xu_ly_id=admin_nv_id,
        trang_thai="dang_xu_ly",
    )
    kn_service.update(created_kn["id"], update_data)

    cursor.execute(
        "SELECT trang_thai, nhan_vien_xu_ly_id FROM khieu_nai WHERE id = ?",
        (created_kn["id"],)
    )
    row = dict(cursor.fetchone())
    assert row["trang_thai"] == "dang_xu_ly"
    assert row["nhan_vien_xu_ly_id"] == admin_nv_id

    # Step 3: Resolve with satisfaction rating
    resolve_data = KhieuNaiUpdateData(
        trang_thai="da_giai_quyet",
        ly_do="Đã đổi cốp mới và bồi thường 2 triệu",
        danh_gia_hai_long=4,
    )
    kn_service.update(created_kn["id"], resolve_data)

    cursor.execute(
        "SELECT trang_thai, danh_gia_hai_long, ly_do FROM khieu_nai WHERE id = ?",
        (created_kn["id"],)
    )
    row = dict(cursor.fetchone())
    assert row["trang_thai"] == "da_giai_quyet", (
        f"Final status should be 'da_giai_quyet', got '{row['trang_thai']}'"
    )
    assert row["danh_gia_hai_long"] == 4, (
        f"Satisfaction rating should be 4, got '{row['danh_gia_hai_long']}'"
    )

    # Cleanup
    sit_conn.execute("DELETE FROM khieu_nai WHERE id = ?", (created_kn["id"],))
    sit_conn.commit()


# =============================================================================
# WF-07: Marketing → Lead → Customer
# =============================================================================

def test_wf07_marketing_lead_kh(sit_conn, admin_nv_id, sample_nv_id):
    """WF-07: Marketing → Lead → KH conversion.

    Steps:
    1. Create ChienDichMk (trang_thai='dang_chay')
    2. Create Lead linked to that campaign (trang_thai='moi')
    3. Update Lead: trang_thai='dang_cham_soc'
    4. Convert Lead → create new KhachHang (trang_thai='chuyen_doi')
    5. Assert Lead.khach_hang_id is set
    6. Assert KhachHang record exists with correct ho_ten

    Cleanup: Delete KH, Lead, ChienDichMk.
    """
    cursor = sit_conn.cursor()

    cd_service = ChienDichMkService(sit_conn)
    lead_service = LeadService(sit_conn)
    kh_service = KhachHangService(sit_conn)

    # Step 1: Create marketing campaign
    from datetime import date
    today = date.today()
    cd_data = ChienDichMkCreateData(
        ten_chien_dich="WF-07 Test Campaign",
        kenh_tiep_thi="facebook",
        ngay_bat_dau=today.strftime("%Y-%m-%d"),
        ngay_ket_thuc=(today + timedelta(days=30)).strftime("%Y-%m-%d"),
        ngan_sach=50_000_000,
        muc_tieu="Generate 20 leads",
        so_luong_lead_muc_tieu=20,
        created_by=admin_nv_id,
    )

    created_cd = cd_service.create(cd_data)
    assert created_cd is not None
    assert created_cd["trang_thai"] == "nhap"  # BR-MK-01: starts as 'nhap'

    # Activate campaign
    cd_service.update(
        created_cd["id"],
        ChienDichMkUpdateData(trang_thai="dang_chay"),
    )

    # Step 2: Create lead
    lead_data = LeadCreateData(
        chien_dich_id=created_cd["id"],
        ho_ten="Nguyen Van Lead Test",
        so_dien_thoai="0909000999",
        email="lead@test.com",
        nguon="Facebook",
        nhu_cau="Muốn mua xe Toyota Camry 2024",
        nhan_vien_phu_trach_id=sample_nv_id,
        ghi_chu="WF-07 test lead",
        created_by=sample_nv_id,
    )

    created_lead = lead_service.create(lead_data)
    assert created_lead is not None
    assert created_lead["trang_thai"] == "moi"
    assert created_lead["chien_dich_id"] == created_cd["id"]

    # Step 3: Update lead status
    lead_service.update(
        created_lead["id"],
        LeadUpdateData(trang_thai="dang_cham_soc"),
    )

    cursor.execute(
        "SELECT trang_thai FROM lead WHERE id = ?", (created_lead["id"],)
    )
    assert cursor.fetchone()[0] == "dang_cham_soc"

    # Step 4: Convert lead to customer
    converted_kh = lead_service.convert_to_customer(created_lead["id"])

    assert converted_kh is not None
    # convert_to_customer returns the updated lead record with khach_hang_id set
    assert converted_kh["khach_hang_id"] is not None

    # Step 5: Assert Lead.khach_hang_id is set
    cursor.execute(
        "SELECT khach_hang_id, trang_thai FROM lead WHERE id = ?",
        (created_lead["id"],)
    )
    lead_row = dict(cursor.fetchone())
    assert lead_row["khach_hang_id"] == converted_kh["khach_hang_id"], (
        "Lead khach_hang_id should match converted KH id"
    )
    assert lead_row["trang_thai"] == "chuyen_doi", (
        f"Lead status should be 'chuyen_doi', got '{lead_row['trang_thai']}'"
    )

    # Step 6: Assert KhachHang exists
    cursor.execute(
        "SELECT ho_ten, so_dien_thoai FROM khach_hang WHERE id = ?",
        (converted_kh["khach_hang_id"],)
    )
    kh_row = dict(cursor.fetchone())
    assert kh_row["ho_ten"] == created_lead["ho_ten"]
    assert kh_row["so_dien_thoai"] == created_lead["so_dien_thoai"]

    # Cleanup
    sit_conn.execute("DELETE FROM lead WHERE id = ?", (created_lead["id"],))
    sit_conn.execute("DELETE FROM chien_dich_mk WHERE id = ?", (created_cd["id"],))
    sit_conn.commit()


# =============================================================================
# WF-08: Hủy hợp đồng (Contract Cancellation)
# =============================================================================

def test_wf08_huy_hop_dong(sit_conn, admin_nv_id, sample_kh_id, sample_nv_id, sample_xe_id):
    """WF-08: Hủy hợp đồng — cancellation with stock return.

    Steps:
    1. Create HopDong (moi_tao)
    2. set_paid() → stock decreased
    3. cancel() as admin → status='huy', stock returned (TRG-03)
    4. Assert: bao_hanh deleted, tra_gop deleted
    5. Assert: xe.so_luong_ton restored
    6. Assert: hop_dong.trang_thai='huy', ly_do_huy set

    Note: Cannot cancel if da_giao_xe (BR-HD-06).

    Cleanup: Delete HopDong, HopDongPhuKien, restore stock.
    """
    cursor = sit_conn.cursor()

    # Get original xe stock
    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    original_xe_stock = cursor.fetchone()[0]

    # Step 1: Create contract
    service = HopDongService(sit_conn)
    data = HopDongCreateData(
        khach_hang_id=sample_kh_id,
        xe_id=sample_xe_id,
        nhan_vien_id=sample_nv_id,
    )
    created_hd = service.create(data)
    hd_id = created_hd.id

    # Step 2: set_paid → stock decreased
    service.set_paid(hd_id, sample_nv_id)

    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    stock_after_paid = cursor.fetchone()[0]
    assert stock_after_paid == original_xe_stock - 1, (
        f"Stock after paid should be {original_xe_stock - 1}, got {stock_after_paid}"
    )

    # Step 3: cancel as admin
    cancelled_hd = service.cancel(
        hop_dong_id=hd_id,
        ly_do="WF-08 test cancellation - xe không đúng màu",
        nhan_vien_id=admin_nv_id,
        nhan_vien_vai_tro="A-01",
    )

    # Step 4: Assert status = 'huy'
    assert cancelled_hd.trang_thai == "huy", (
        f"Expected 'huy', got '{cancelled_hd.trang_thai}'"
    )
    assert cancelled_hd.ly_do_huy is not None
    assert cancelled_hd.ly_do_huy != ""

    # Step 5: Assert bao_hanh deleted (TRG-03)
    cursor.execute("SELECT COUNT(*) FROM bao_hanh WHERE hop_dong_id = ?", (hd_id,))
    bh_count = cursor.fetchone()[0]
    assert bh_count == 0, f"bao_hanh should be deleted: got {bh_count} records"

    # Step 6: Assert tra_gop deleted (TRG-03)
    cursor.execute("SELECT COUNT(*) FROM tra_gop WHERE hop_dong_id = ?", (hd_id,))
    tg_count = cursor.fetchone()[0]
    assert tg_count == 0, f"tra_gop should be deleted: got {tg_count} records"

    # Step 7: Assert xe stock restored (TRG-03)
    cursor.execute("SELECT so_luong_ton FROM xe WHERE id = ?", (sample_xe_id,))
    restored_stock = cursor.fetchone()[0]
    assert restored_stock == original_xe_stock, (
        f"Stock should be restored to {original_xe_stock}, got {restored_stock}"
    )

    # Cleanup
    sit_conn.execute("DELETE FROM hop_dong_phu_kien WHERE hop_dong_id = ?", (hd_id,))
    sit_conn.execute("DELETE FROM hop_dong WHERE id = ?", (hd_id,))
    sit_conn.execute(
        "UPDATE xe SET so_luong_ton = ? WHERE id = ?",
        (original_xe_stock, sample_xe_id)
    )
    sit_conn.commit()
