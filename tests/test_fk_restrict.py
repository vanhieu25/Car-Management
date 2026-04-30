"""Test FK ON DELETE RESTRICT: deleting parent with children should fail."""

import pytest
import sqlite3
import tempfile
import os
import sys


@pytest.fixture
def seeded_db():
    """Create a database with seed data applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from app.infrastructure.database.migrations.runner import MigrationRunner

    runner = MigrationRunner(db_path)
    runner.run_pending()

    from app.infrastructure.database.seeds.dev_seed import seed_all
    seed_all(db_path)

    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


def test_delete_xe_with_hop_dong_fails(seeded_db):
    """Test that deleting a xe which has associated hop_dong fails with RESTRICT."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a xe that has at least one hop_dong
    cursor = conn.execute("""
        SELECT xe_id, COUNT(*) as cnt FROM hop_dong 
        GROUP BY xe_id HAVING cnt > 0 LIMIT 1
    """)
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one xe with hop_dong"

    xe_id = row[0]

    # Verify the xe exists
    cursor = conn.execute("SELECT ma_xe FROM xe WHERE id = ?", (xe_id,))
    assert cursor.fetchone() is not None

    # Attempt to delete the xe should fail due to RESTRICT
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM xe WHERE id = ?", (xe_id,))
        conn.commit()

    conn.close()


def test_delete_khach_hang_with_hop_dong_fails(seeded_db):
    """Test that deleting a khach_hang with associated hop_dong fails."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a khach_hang that has at least one hop_dong
    cursor = conn.execute("""
        SELECT khach_hang_id, COUNT(*) as cnt FROM hop_dong 
        GROUP BY khach_hang_id HAVING cnt > 0 LIMIT 1
    """)
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one khach_hang with hop_dong"

    kh_id = row[0]

    # Attempt to delete should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM khach_hang WHERE id = ?", (kh_id,))
        conn.commit()

    conn.close()


def test_delete_nhan_vien_with_hop_dong_fails(seeded_db):
    """Test that deleting a nhan_vien with associated hop_dong fails."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a nhan_vien that has at least one hop_dong
    cursor = conn.execute("""
        SELECT nhan_vien_id, COUNT(*) as cnt FROM hop_dong 
        GROUP BY nhan_vien_id HAVING cnt > 0 LIMIT 1
    """)
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one nhan_vien with hop_dong"

    nv_id = row[0]

    # Attempt to delete should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM nhan_vien WHERE id = ?", (nv_id,))
        conn.commit()

    conn.close()


def test_delete_khuyen_mai_with_hop_dong_fails(seeded_db):
    """Test that deleting a khuyen_mai referenced by hop_dong fails."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a khuyen_mai that is used in at least one hop_dong
    cursor = conn.execute("""
        SELECT khuyen_mai_id, COUNT(*) as cnt FROM hop_dong 
        WHERE khuyen_mai_id IS NOT NULL
        GROUP BY khuyen_mai_id HAVING cnt > 0 LIMIT 1
    """)
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one khuyen_mai used in hop_dong"

    km_id = row[0]

    # Attempt to delete should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM khuyen_mai WHERE id = ?", (km_id,))
        conn.commit()

    conn.close()


def test_delete_vai_tro_with_nhan_vien_fails(seeded_db):
    """Test that deleting a vai_tro with associated nhan_vien fails."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a vai_tro that has at least one nhan_vien
    cursor = conn.execute("""
        SELECT vai_tro_id, COUNT(*) as cnt FROM nhan_vien 
        GROUP BY vai_tro_id HAVING cnt > 0 LIMIT 1
    """)
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one vai_tro with nhan_vien"

    vt_id = row[0]

    # Attempt to delete should fail
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("DELETE FROM vai_tro WHERE id = ?", (vt_id,))
        conn.commit()

    conn.close()


def test_delete_xe_without_hop_dong_succeeds(seeded_db):
    """Test that deleting a xe without any hop_dong succeeds."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a xe that has NO hop_dong
    cursor = conn.execute("""
        SELECT id FROM xe 
        WHERE id NOT IN (SELECT DISTINCT xe_id FROM hop_dong)
        LIMIT 1
    """)
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one xe without hop_dong"

    xe_id = row[0]

    # Deletion should succeed
    conn.execute("DELETE FROM xe WHERE id = ?", (xe_id,))
    conn.commit()

    # Verify it's gone
    cursor = conn.execute("SELECT COUNT(*) FROM xe WHERE id = ?", (xe_id,))
    assert cursor.fetchone()[0] == 0

    conn.close()


def test_delete_khach_hang_without_hop_dong_succeeds(seeded_db):
    """Test that deleting a khach_hang without hop_dong succeeds."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a khach_hang that has NO hop_dong
    cursor = conn.execute("""
        SELECT id FROM khach_hang 
        WHERE id NOT IN (SELECT DISTINCT khach_hang_id FROM hop_dong)
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row is None:
        pytest.skip("Test requires at least one khach_hang without hop_dong")

    kh_id = row[0]

    # Deletion should succeed
    conn.execute("DELETE FROM khach_hang WHERE id = ?", (kh_id,))
    conn.commit()

    conn.close()


def test_cascade_delete_hop_dong_does_not_delete_xe(seeded_db):
    """Test that deleting hop_dong does NOT delete the associated xe (only RESTRICT, no CASCADE from xe)."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a hop_dong and its xe
    cursor = conn.execute("""
        SELECT hd.id, hd.xe_id, x.ma_xe FROM hop_dong hd
        JOIN xe x ON x.id = hd.xe_id
        LIMIT 1
    """)
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one hop_dong"

    hd_id, xe_id, ma_xe = row

    # Count hop_dong for this xe
    cursor = conn.execute("SELECT COUNT(*) FROM hop_dong WHERE xe_id = ?", (xe_id,))
    hd_count = cursor.fetchone()[0]

    # Delete the hop_dong
    conn.execute("DELETE FROM hop_dong WHERE id = ?", (hd_id,))
    conn.commit()

    # Verify xe still exists
    cursor = conn.execute("SELECT COUNT(*) FROM xe WHERE id = ?", (xe_id,))
    assert cursor.fetchone()[0] == 1, "xe should still exist after deleting hop_dong"

    # If there were multiple hop_dong, they should still exist
    if hd_count > 1:
        cursor = conn.execute("SELECT COUNT(*) FROM hop_dong WHERE xe_id = ?", (xe_id,))
        assert cursor.fetchone()[0] == hd_count - 1

    conn.close()


def test_delete_hop_dong_succeeds_when_no_child_records(seeded_db):
    """Test that deleting hop_dong itself always works."""
    conn = sqlite3.connect(seeded_db)
    conn.execute("PRAGMA foreign_keys = ON")

    # Find a hop_dong (hop_dong is the parent for bao_hanh, tra_gop)
    cursor = conn.execute("SELECT id, ma_hop_dong FROM hop_dong LIMIT 1")
    row = cursor.fetchone()
    assert row is not None, "Test requires at least one hop_dong"

    hd_id = row[0]

    # Deletion should succeed
    conn.execute("DELETE FROM hop_dong WHERE id = ?", (hd_id,))
    conn.commit()

    # Verify it's gone
    cursor = conn.execute("SELECT COUNT(*) FROM hop_dong WHERE id = ?", (hd_id,))
    assert cursor.fetchone()[0] == 0

    conn.close()
