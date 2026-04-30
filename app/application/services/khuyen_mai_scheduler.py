"""KhuyenMai scheduler - daily job functions for promotions.

TRG-06: Daily expiry check for promotions.
This module contains the daily job function that should be called
by a scheduler (e.g., APScheduler or cron).
"""

from typing import Dict, Any

import sqlite3


def daily_expiry_check(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Daily job to check and expire promotions.

    This function finds all promotions where:
    - den_ngay < today (current date)
    - trang_thai = 'dang_chay'

    And updates them to trang_thai = 'ket_thuc'.

    This function is designed to be called by a scheduler daily.
    Example integration with APScheduler:
        scheduler.add_job(
            daily_khuyen_mai_expiry,
            'cron',
            hour=0, minute=5,  # Run at 00:05 daily
            args=[db_conn]
        )

    Args:
        conn: sqlite3.Connection instance.

    Returns:
        Dict with:
        - expired_count: Number of promotions expired
        - today: Current date string
    """
    from datetime import datetime

    km_service = None

    try:
        # Import here to avoid circular imports
        from app.application.services.khuyen_mai_service import KhuyenMaiService

        km_service = KhuyenMaiService(conn)
        result = km_service.daily_expiry_check()

        return {
            "success": True,
            "expired_count": result["expired_count"],
            "today": result["today"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "today": datetime.now().strftime("%Y-%m-%d"),
        }


def get_scheduled_tasks() -> list:
    """Return list of scheduled tasks for promotions.

    This is a reference for integration with APScheduler or cron.
    Each task is a dict with name, function, and schedule info.

    Returns:
        List of task definitions.
    """
    return [
        {
            "name": "daily_khuyen_mai_expiry",
            "description": "Check and expire promotions past their end date",
            "module": "app.application.services.khuyen_mai_scheduler",
            "function": "daily_expiry_check",
            "schedule_type": "cron",
            "schedule": {
                "hour": 0,
                "minute": 5,
            },
            "note": "Run at 00:05 daily to process promotions ended the day before",
        },
    ]


# Example APScheduler integration (commented out for reference)
"""
from apscheduler.schedulers.background import BackgroundScheduler

def setup_km_scheduler(conn: sqlite3.Connection):
    '''Setup scheduler for promotion daily jobs.

    Args:
        conn: sqlite3.Connection instance.
    '''
    scheduler = BackgroundScheduler()

    # Daily expiry check at 00:05
    scheduler.add_job(
        daily_expiry_check,
        'cron',
        hour=0,
        minute=5,
        args=[conn],
        id='km_daily_expiry',
        name='Promotion Daily Expiry Check',
        replace_existing=True,
    )

    scheduler.start()
    return scheduler
"""


# Example cron integration (for reference)
"""
# Add to crontab (crontab -e):
# Run daily at 00:05
5 0 * * * cd /path/to/project && python -c "
import sqlite3
from app.application.services.khuyen_mai_scheduler import daily_expiry_check
conn = sqlite3.connect('car_management.db')
result = daily_expiry_check(conn)
conn.close()
print(f'KM Expiry: {result}')
"
"""