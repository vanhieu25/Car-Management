"""Migration 029: Extend bao_hiem table with insurance company and vehicle info.

Adds:
- cong_ty_bh_id: FK to cong_ty_bh (insurance company)
- ngay_hieu_luc: Effective date of insurance
- xe_id: FK to xe (for dealership vehicles)
- hop_dong_id: FK to hop_dong (for dealership vehicles)
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 029."""
    cursor = conn.cursor()

    # Add columns to bao_hiem table
    cursor.execute("""
        ALTER TABLE bao_hiem ADD COLUMN cong_ty_bh_id INTEGER
            REFERENCES cong_ty_bh(id)
    """)
    logger.info("Added cong_ty_bh_id column to bao_hiem")

    cursor.execute("""
        ALTER TABLE bao_hiem ADD COLUMN ngay_hieu_luc TEXT
    """)
    logger.info("Added ngay_hieu_luc column to bao_hiem")

    cursor.execute("""
        ALTER TABLE bao_hiem ADD COLUMN xe_id INTEGER
            REFERENCES xe(id)
    """)
    logger.info("Added xe_id column to bao_hiem")

    cursor.execute("""
        ALTER TABLE bao_hiem ADD COLUMN hop_dong_id INTEGER
            REFERENCES hop_dong(id)
    """)
    logger.info("Added hop_dong_id column to bao_hiem")

    # Create indexes for new fields
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhiem_cong_ty ON bao_hiem(cong_ty_bh_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhiem_xe ON bao_hiem(xe_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bhiem_hop_dong ON bao_hiem(hop_dong_id)")

    logger.info("Migration 029: bao_hiem extended with new fields")