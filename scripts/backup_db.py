#!/usr/bin/env python3
"""
Backup database script for Car Management.
Backs up the SQLite database to data/backup/YYYY-MM-DD.db
Can be run manually or scheduled via cron.
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.database.connection import get_db_path
from app.shared.logger import logger


DEFAULT_BACKUP_DIR = Path(__file__).parent.parent / "data" / "backup"


def get_backup_path(backup_dir: Path = None, backup_date: date = None) -> Path:
    """Get the backup file path for a given date."""
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR
    if backup_date is None:
        backup_date = date.today()
    return backup_dir / f"{backup_date.isoformat()}.db"


def backup_db(
    db_path: str = None,
    backup_path: Path = None,
    compress: bool = False,
) -> Path:
    """
    Create a backup of the database.

    Args:
        db_path: Path to source database. Uses default if not provided.
        backup_path: Path to backup file. Auto-generates if not provided.
        compress: If True, creates a compressed (.gz) backup.

    Returns:
        Path to the created backup file.
    """
    if db_path is None:
        db_path = get_db_path()

    source = Path(db_path)
    if not source.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    if backup_path is None:
        backup_path = get_backup_path()

    # Ensure backup directory exists
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    # For SQLite WAL databases, use backup API for consistency
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA wal_checkpoint(FULL)")

    try:
        if compress:
            import gzip

            with open(source, "rb") as src, gzip.open(
                str(backup_path) + ".gz", "wb"
            ) as dst:
                shutil.copyfileobj(src, dst)
            backup_path = Path(str(backup_path) + ".gz")
            logger.info(f"Compressed backup created: {backup_path}")
        else:
            # Use SQLite backup API for reliable hot backup
            dest_conn = sqlite3.connect(str(backup_path))
            conn.backup(dest_conn)
            dest_conn.close()
            logger.info(f"Backup created: {backup_path}")

        return backup_path

    finally:
        conn.close()


def list_backups(backup_dir: Path = None) -> list[Path]:
    """List all available backups, newest first."""
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR

    if not backup_dir.exists():
        return []

    backups = list(backup_dir.glob("*.db")) + list(backup_dir.glob("*.db.gz"))
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return backups


def cleanup_old_backups(keep_days: int = 30, backup_dir: Path = None) -> int:
    """
    Remove backups older than keep_days.

    Args:
        keep_days: Number of days to keep backups for.
        backup_dir: Directory to clean up. Uses default if not provided.

    Returns:
        Number of files deleted.
    """
    from datetime import timedelta

    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR

    if not backup_dir.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=keep_days)
    count = 0

    for backup in backup_dir.glob("*.db"):
        if datetime.fromtimestamp(backup.stat().st_mtime) < cutoff:
            backup.unlink()
            count += 1
            logger.info(f"Deleted old backup: {backup}")

    for backup in backup_dir.glob("*.db.gz"):
        if datetime.fromtimestamp(backup.stat().st_mtime) < cutoff:
            backup.unlink()
            count += 1
            logger.info(f"Deleted old backup: {backup}")

    return count


def restore_db(backup_path: Path, db_path: str = None) -> None:
    """
    Restore database from a backup.

    Args:
        backup_path: Path to the backup file to restore from.
        db_path: Path to restore to. Uses default if not provided.
    """
    import gzip

    if db_path is None:
        db_path = get_db_path()

    source = Path(backup_path)
    if not source.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    dest = Path(db_path)

    # Create a backup of current database before restoring
    if dest.exists():
        current_backup = get_backup_path(
            backup_dir=DEFAULT_BACKUP_DIR,
            backup_date=date.today(),
        )
        current_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, current_backup)
        logger.warning(f"Current database backed up to: {current_backup}")

    if source.suffix == ".gz":
        with gzip.open(source, "rb") as src, open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)
    else:
        shutil.copy2(source, dest)

    logger.info(f"Database restored from: {backup_path}")


def run_daily_backup() -> Path:
    """Run the daily backup task. Called by scheduler or cron."""
    today = date.today()
    backup_path = get_backup_path(backup_date=today)

    # Skip if backup already exists for today
    if backup_path.exists():
        logger.info(f"Backup for {today} already exists at {backup_path}")
        return backup_path

    return backup_db()


def main():
    parser = argparse.ArgumentParser(
        description="Backup the Car Management database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Backup to data/backup/YYYY-MM-DD.db
  %(prog)s --list             # List all backups
  %(prog)s --restore data/backup/2026-04-30.db  # Restore from backup
  %(prog)s --cleanup 7        # Keep only last 7 days of backups
  %(prog)s --compress         # Create compressed backup
        """,
    )

    parser.add_argument(
        "--db",
        "-d",
        dest="db_path",
        help="Path to database file (default: from config)",
    )
    parser.add_argument(
        "--backup-dir",
        "-b",
        dest="backup_dir",
        type=Path,
        help="Backup directory (default: data/backup)",
    )
    parser.add_argument(
        "--compress",
        "-c",
        action="store_true",
        help="Create compressed (.gz) backup",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available backups",
    )
    parser.add_argument(
        "--restore",
        "-r",
        dest="restore_path",
        type=Path,
        help="Restore database from backup file",
    )
    parser.add_argument(
        "--cleanup",
        dest="cleanup_days",
        type=int,
        metavar="N",
        help="Delete backups older than N days",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress verbose output",
    )

    args = parser.parse_args()

    # Set up logging
    import logging

    if args.quiet:
        logging.getLogger("car_management").setLevel(logging.WARNING)

    if args.list:
        backups = list_backups(args.backup_dir)
        if backups:
            print("Available backups:")
            for b in backups:
                size = b.stat().st_size
                mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                print(f"  {b.name}  ({size:,} bytes)  {mtime}")
        else:
            print("No backups found.")
        return

    if args.restore_path:
        restore_db(args.restore_path, args.db_path)
        return

    if args.cleanup_days is not None:
        count = cleanup_old_backups(args.cleanup_days, args.backup_dir)
        print(f"Deleted {count} old backup(s).")
        return

    # Default: create backup
    backup_path = backup_db(
        db_path=args.db_path,
        backup_path=get_backup_path(args.backup_dir) if args.backup_dir else None,
        compress=args.compress,
    )
    print(f"Backup saved to: {backup_path}")


if __name__ == "__main__":
    main()
