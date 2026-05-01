"""TraGop scheduler - daily jobs for installment management.

TRG-07: Daily check for overdue payments.
- Runs at configured time each day (default: 00:01)
- Marks overdue installments (ngay_den_han + 5 days < today)
- Logs results to audit log
"""

import sqlite3
from datetime import datetime

from app.application.services.tra_gop_service import TraGopService


def run_daily_overdue_check(conn: sqlite3.Connection) -> dict:
    """Run the daily overdue check job.

    Args:
        conn: sqlite3.Connection instance.

    Returns:
        Dict with job results:
        - ran_at: timestamp
        - overdue_count: number of records updated
        - status: 'success' or 'error'
        - error: error message if failed
    """
    result = {
        "ran_at": datetime.now().isoformat(),
        "overdue_count": 0,
        "status": "success",
        "error": None,
    }

    try:
        service = TraGopService(conn)
        count = service.daily_overdue_check()
        result["overdue_count"] = count
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


# Standalone execution entry point
if __name__ == "__main__":
    import os
    import sys

    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))))

    db_path = os.environ.get(
        "CAR_DB_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        ))), "data", "car_management.db")
    )

    conn = sqlite3.connect(db_path)
    result = run_daily_overdue_check(conn)
    print(f"Daily overdue check completed: {result}")
    conn.close()
