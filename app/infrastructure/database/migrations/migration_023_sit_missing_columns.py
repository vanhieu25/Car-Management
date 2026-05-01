"""Migration 023: Add missing columns for SIT test compatibility.

- bao_hanh_yeu_cau.phan_loai: distinguishes mien_phi vs tinh_phi warranty requests
- tra_gop.trang_thai: tracks overall installment plan status
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 023."""
    cursor = conn.cursor()

    # Add phan_loai to bao_hanh_yeu_cau
    # BR-BH-04: 'mien_phi' (NSX fault) or 'tinh_phi' (customer fault)
    cursor.execute("""
        ALTER TABLE bao_hanh_yeu_cau
        ADD COLUMN phan_loai TEXT DEFAULT 'mien_phi'
        CHECK (phan_loai IN ('mien_phi', 'tinh_phi'))
    """)

    # Add trang_thai to tra_gop
    # Tracks overall installment status: dang_tra (active), hoan_thanh (all paid)
    cursor.execute("""
        ALTER TABLE tra_gop
        ADD COLUMN trang_thai TEXT DEFAULT 'dang_tra'
        CHECK (trang_thai IN ('dang_tra', 'hoan_thanh'))
    """)

    logger.info("Migration 023: phan_loai added to bao_hanh_yeu_cau, trang_thai added to tra_gop")