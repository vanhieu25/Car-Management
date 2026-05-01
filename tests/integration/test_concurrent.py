"""SIT Integration Tests — T-G6.1.TEST.11: Concurrent Access.

Tests 50 concurrent users accessing DB simultaneously — no DB lock errors.

Run via:
    pytest tests/integration/test_concurrent.py -v
"""

import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.infrastructure.database.migrations.runner import MigrationRunner
from app.infrastructure.database.seeds.dev_seed import seed_vai_tro, seed_nhan_vien


# =============================================================================
# Test Configuration
# =============================================================================

SIT_DB_NAME = "car_management_sit_concurrent.db"
SIT_DB_DIR = Path(__file__).parent.parent.parent / "data"
THREAD_COUNT = 50


def _get_sit_db_path() -> Path:
    return SIT_DB_DIR / SIT_DB_NAME


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def sit_db_path():
    db_path = _get_sit_db_path()
    SIT_DB_DIR.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

    runner = MigrationRunner(str(db_path))
    runner.run_pending()

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    seed_vai_tro(cursor)
    seed_nhan_vien(cursor)

    conn.commit()
    conn.close()

    yield str(db_path)

    if db_path.exists():
        db_path.unlink()


# =============================================================================
# TEST-11: Concurrent DB Access
# =============================================================================

class TestConcurrentDB:
    """Test concurrent DB access — no lock errors."""

    def test_50_concurrent_inserts_no_lock_errors(self, sit_db_path):
        """Test 50 concurrent connections can insert records without DB lock.

        Each thread:
        1. Opens its own DB connection (with timeout=30 to handle lock waits)
        2. Inserts a test record (khach_hang)
        3. Commits
        4. Closes connection

        Verify: no sqlite3.OperationalError: database is locked
        """
        errors = []
        insert_count = 0
        lock = threading.Lock()

        def worker(thread_id):
            nonlocal insert_count
            try:
                conn = sqlite3.connect(sit_db_path, timeout=30)
                conn.execute("PRAGMA foreign_keys = ON")

                conn.execute(
                    "INSERT INTO khach_hang (ho_ten, so_dien_thoai, email, dia_chi, phan_loai) VALUES (?, ?, ?, ?, ?)",
                    (f"Concurrent User {thread_id}", f"098800{thread_id:04d}", f"concurrent{thread_id}@test.com", "Test Address", "VIP")
                )
                conn.commit()
                conn.close()

                with lock:
                    insert_count += 1
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower():
                    errors.append(f"Thread {thread_id}: database is locked")
                else:
                    errors.append(f"Thread {thread_id}: {e}")
            except sqlite3.IntegrityError as e:
                errors.append(f"Thread {thread_id}: IntegrityError: {e}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {type(e).__name__}: {e}")

        # Run 50 threads
        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures = [executor.submit(worker, i) for i in range(THREAD_COUNT)]
            for future in as_completed(futures):
                pass  # Just wait for completion

        # Verify no lock errors (allow IntegrityError for constraint violations)
        lock_errors = [e for e in errors if "database is locked" in e.lower()]
        if lock_errors:
            pytest.fail(f"Got {len(lock_errors)} DB lock errors:\n" + "\n".join(lock_errors[:10]))

        assert insert_count == THREAD_COUNT, f"Expected {THREAD_COUNT} inserts, got {insert_count}"

        # Cleanup
        conn = sqlite3.connect(sit_db_path)
        conn.execute("DELETE FROM khach_hang WHERE so_dien_thoai LIKE '098800%' AND email LIKE 'concurrent%'")
        conn.commit()
        conn.close()

    def test_50_concurrent_selects_no_lock_errors(self, sit_db_path):
        """Test 50 concurrent SELECT queries without DB lock."""
        errors = []

        def worker(thread_id):
            try:
                conn = sqlite3.connect(sit_db_path, timeout=30)
                cursor = conn.execute("SELECT COUNT(*) FROM nhan_vien")
                cursor.fetchone()
                conn.close()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower():
                    errors.append(f"Thread {thread_id}: database is locked")
                else:
                    errors.append(f"Thread {thread_id}: {e}")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {type(e).__name__}: {e}")

        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures = [executor.submit(worker, i) for i in range(THREAD_COUNT)]
            for future in as_completed(futures):
                pass

        if errors:
            pytest.fail(f"Got {len(errors)} errors during concurrent selects:\n" + "\n".join(errors[:10]))

    def test_concurrent_reads_and_writes(self, sit_db_path):
        """Test mixed concurrent reads and writes — no lock errors."""
        errors = []
        write_count = 0
        read_count = 0
        lock = threading.Lock()

        def writer(thread_id):
            nonlocal write_count
            try:
                conn = sqlite3.connect(sit_db_path, timeout=30)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute(
                    "INSERT INTO khach_hang (ho_ten, so_dien_thoai, email, dia_chi, phan_loai) VALUES (?, ?, ?, ?, ?)",
                    (f"Writer {thread_id}", f"098810{thread_id:04d}", f"writer{thread_id}@test.com", "Write Address", "VIP")
                )
                conn.commit()
                conn.close()
                with lock:
                    write_count += 1
            except sqlite3.OperationalError as e:
                errors.append(f"Writer {thread_id}: {e}")
            except Exception as e:
                errors.append(f"Writer {thread_id}: {type(e).__name__}: {e}")

        def reader(thread_id):
            nonlocal read_count
            try:
                conn = sqlite3.connect(sit_db_path, timeout=30)
                cursor = conn.execute("SELECT COUNT(*) FROM khach_hang")
                cursor.fetchone()
                conn.close()
                with lock:
                    read_count += 1
            except sqlite3.OperationalError as e:
                errors.append(f"Reader {thread_id}: {e}")
            except Exception as e:
                errors.append(f"Reader {thread_id}: {type(e).__name__}: {e}")

        # 25 readers + 25 writers
        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures = []
            for i in range(25):
                futures.append(executor.submit(writer, i))
                futures.append(executor.submit(reader, i))
            for future in as_completed(futures):
                pass

        lock_errors = [e for e in errors if "database is locked" in str(e).lower()]
        if lock_errors:
            pytest.fail(f"Got {len(lock_errors)} DB lock errors:\n" + "\n".join(lock_errors[:10]))

        assert write_count == 25, f"Expected 25 writes, got {write_count}"
        assert read_count == 25, f"Expected 25 reads, got {read_count}"

        # Cleanup
        conn = sqlite3.connect(sit_db_path)
        conn.execute("DELETE FROM khach_hang WHERE so_dien_thoai LIKE '098810%' AND email LIKE 'writer%'")
        conn.commit()
        conn.close()

    def test_sequential_stress_no_cumulative_locks(self, sit_db_path):
        """Test rapid sequential inserts don't accumulate lock states.

        This catches cases where SQLite's busy_timeout isn't properly reset,
        or where connections aren't properly closed.
        """
        conn = sqlite3.connect(sit_db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM khach_hang")
        initial_count = cursor.fetchone()[0]
        conn.close()

        # 100 rapid sequential inserts
        for i in range(100):
            conn = sqlite3.connect(sit_db_path, timeout=30)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                "INSERT INTO khach_hang (ho_ten, so_dien_thoai, email, dia_chi, phan_loai) VALUES (?, ?, ?, ?, ?)",
                (f"Stress User {i}", f"098820{1000 + i:04d}", f"stress{i}@test.com", "Stress Address", "VIP")
            )
            conn.commit()
            conn.close()

        # Cleanup
        conn = sqlite3.connect(sit_db_path)
        conn.execute("DELETE FROM khach_hang WHERE so_dien_thoai LIKE '098820%' AND email LIKE 'stress%'")
        conn.commit()
        cursor = conn.execute("SELECT COUNT(*) FROM khach_hang")
        final_count = cursor.fetchone()[0]
        conn.close()

        assert final_count == initial_count, f"Expected {initial_count}, got {final_count} (cleanup failed)"