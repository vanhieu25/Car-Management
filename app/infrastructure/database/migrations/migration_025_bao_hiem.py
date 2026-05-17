"""Migration 025: Add insurance fields to bao_hanh table.

Adds:
- loai_bh: Loại bảo hiểm (bao_hanh, tnds, tai_nan, chao_no, that_lac)
- dai_ly_ban_id: FK to nhan_vien - đại lý bán bảo hiểm (NULL = chính đại lý)
- so_policy: Số policy bảo hiểm
- phi_bh: Phí bảo hiểm
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 025."""
    cursor = conn.cursor()

    # Add new columns to bao_hanh table
    cursor.execute("""
        ALTER TABLE bao_hanh ADD COLUMN loai_bh TEXT DEFAULT 'bao_hanh'
            CHECK (loai_bh IN ('bao_hanh', 'tnds', 'tai_nan', 'chao_no', 'that_lac'))
    """)
    logger.info("Added loai_bh column to bao_hanh")

    cursor.execute("""
        ALTER TABLE bao_hanh ADD COLUMN dai_ly_ban_id INTEGER
            REFERENCES nhan_vien(id)
    """)
    logger.info("Added dai_ly_ban_id column to bao_hanh")

    cursor.execute("""
        ALTER TABLE bao_hanh ADD COLUMN so_policy TEXT
    """)
    logger.info("Added so_policy column to bao_hanh")

    cursor.execute("""
        ALTER TABLE bao_hanh ADD COLUMN phi_bh INTEGER DEFAULT 0
    """)
    logger.info("Added phi_bh column to bao_hanh")

    # Create index for dai_ly_ban_id
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bh_dai_ly_ban ON bao_hanh(dai_ly_ban_id)")

    logger.info("Migration 025: insurance fields added to bao_hanh")