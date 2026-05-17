"""Migration 032: Fix cuu_ho trang_thai CHECK constraint.

Add 'huy' and 'tu_choi' to valid trang_thai values for cuu_ho table.
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 032."""
    cursor = conn.cursor()

    # Recreate cuu_ho table with updated CHECK constraint
    # Step 1: Create new table with updated constraint
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuu_ho_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            khach_hang_id INTEGER NOT NULL,
            xe_id INTEGER NOT NULL,
            nhan_vien_id INTEGER,
            vi_tri TEXT NOT NULL,
            mo_ta TEXT,
            thoi_gian_yeu_cau TEXT DEFAULT CURRENT_TIMESTAMP,
            thoi_gian_xu_ly TEXT,
            trang_thai TEXT DEFAULT 'tiep_nhan'
                CHECK (trang_thai IN ('tiep_nhan', 'dang_xu_ly', 'hoan_thanh', 'huy', 'tu_choi')),
            chi_phi INTEGER DEFAULT 0 CHECK (chi_phi >= 0),
            ghi_chu TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            created_by INTEGER,
            FOREIGN KEY (khach_hang_id) REFERENCES khach_hang(id),
            FOREIGN KEY (xe_id) REFERENCES xe(id),
            FOREIGN KEY (nhan_vien_id) REFERENCES nhan_vien(id),
            FOREIGN KEY (created_by) REFERENCES nhan_vien(id)
        )
    """)

    # Step 2: Copy data from old table
    cursor.execute("""
        INSERT INTO cuu_ho_new (id, khach_hang_id, xe_id, nhan_vien_id, vi_tri, mo_ta,
            thoi_gian_yeu_cau, thoi_gian_xu_ly, trang_thai, chi_phi, ghi_chu,
            created_at, updated_at, created_by)
        SELECT id, khach_hang_id, xe_id, nhan_vien_id, vi_tri, mo_ta,
            thoi_gian_yeu_cau, thoi_gian_xu_ly, trang_thai, chi_phi, ghi_chu,
            created_at, updated_at, created_by
        FROM cuu_ho
    """)

    # Step 3: Drop old table
    cursor.execute("DROP TABLE cuu_ho")

    # Step 4: Rename new table
    cursor.execute("ALTER TABLE cuu_ho_new RENAME TO cuu_ho")

    # Step 5: Recreate indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cuu_ho_khach ON cuu_ho(khach_hang_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cuu_ho_xe ON cuu_ho(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cuu_ho_trang_thai ON cuu_ho(trang_thai)")

    logger.info("Migration 032: Updated cuu_ho trang_thai CHECK constraint")