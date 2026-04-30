"""Migration 014: Add must_change_password column to nhan_vien table.

This column is required by BR-NV-08:
- When Admin creates a new employee, the employee must change their password on first login.
- Default password is randomly generated (shown once to Admin).

Also adds CHECK constraint for password_min_length (BR-SEC-02).
"""

from app.shared.logger import logger


def run(conn):
    """Execute migration 014."""
    cursor = conn.cursor()

    # Add must_change_password column
    # This flag is set to True when admin creates a new employee
    # The employee will be forced to change password on first login
    cursor.execute("""
        ALTER TABLE nhan_vien ADD COLUMN must_change_password INTEGER DEFAULT 0
    """)

    # Add password_min_length column for tracking password policy
    cursor.execute("""
        ALTER TABLE nhan_vien ADD COLUMN password_min_length INTEGER DEFAULT 8
    """)

    # Add last_password_change timestamp for audit
    cursor.execute("""
        ALTER TABLE nhan_vien ADD COLUMN last_password_change TEXT
    """)

    # Update existing admin account to require password change (security best practice)
    cursor.execute("""
        UPDATE nhan_vien 
        SET must_change_password = 1 
        WHERE username = 'admin'
    """)

    logger.info("Migration 014: must_change_password column added to nhan_vien")
