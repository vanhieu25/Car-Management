#!/usr/bin/env python3
"""
Backup SIT Database for rollback before SIT test runs.

Creates a timestamped backup of the SIT database before starting a new test run.
This ensures clean rollback capability if test data gets contaminated.

Usage:
    python scripts/backup_sit_db.py                    # Backup SIT DB
    python scripts/backup_sit_db.py --list              # List existing backups
    python scripts/backup_sit_db.py --restore PATH     # Restore from backup
    python scripts/backup_sit_db.py --cleanup 7        # Keep only 7 days of backups
    python scripts/backup_sit_db.py --db-path /path/to/db  # Custom SIT DB path
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.database.connection import get_connection


DEFAULT_SIT_DB = Path(__file__).parent.parent / "data" / "car_management_sit.db"
DEFAULT_BACKUP_DIR = Path(__file__).parent.parent / "data" / "backup"


def get_backup_filename(sit_db_path: Path = None, timestamp: datetime = None) -> str:
    """Generate backup filename with timestamp."""
    if timestamp is None:
        timestamp = datetime.now()
    
    if sit_db_path is None:
        sit_db_path = DEFAULT_SIT_DB
    
    base_name = sit_db_path.stem  # e.g., "car_management_sit"
    date_str = timestamp.strftime("%Y-%m-%d_%H%M%S")
    return f"{base_name}_{date_str}.db"


def get_backup_path(backup_dir: Path = None, sit_db_path: Path = None, timestamp: datetime = None) -> Path:
    """Get the full backup path."""
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR
    
    filename = get_backup_filename(sit_db_path, timestamp)
    return backup_dir / filename


def backup_sit_db(
    db_path: Path = None,
    backup_dir: Path = None,
    quiet: bool = False,
) -> Path:
    """
    Create a timestamped backup of the SIT database.
    
    Args:
        db_path: Path to SIT database (default: data/car_management_sit.db)
        backup_dir: Directory to store backup (default: data/backup/)
        quiet: Suppress output
    
    Returns:
        Path to the created backup file.
    """
    if db_path is None:
        db_path = DEFAULT_SIT_DB
    
    if not db_path.exists():
        raise FileNotFoundError(f"SIT database not found: {db_path}")
    
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR
    
    # Ensure backup directory exists
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Get backup path with timestamp
    backup_path = get_backup_path(backup_dir, db_path)
    
    if not quiet:
        print(f"  Backing up SIT database...")
        print(f"    Source:  {db_path}")
        print(f"    Dest:    {backup_path}")
    
    # Use SQLite backup API for reliable hot backup (handles WAL correctly)
    source_conn = sqlite3.connect(str(db_path))
    
    # Checkpoint WAL first for consistent backup
    source_conn.execute("PRAGMA wal_checkpoint(FULL)")
    
    try:
        dest_conn = sqlite3.connect(str(backup_path))
        source_conn.backup(dest_conn)
        dest_conn.close()
        
        # Get file size
        size = backup_path.stat().st_size
        size_str = f"{size:,} bytes"
        
        if not quiet:
            print(f"  ✅ Backup created: {backup_path.name}")
            print(f"     Size: {size_str}")
        
        return backup_path
        
    finally:
        source_conn.close()


def list_backups(backup_dir: Path = None, sit_db_path: Path = None) -> list[Path]:
    """List all SIT database backups, newest first."""
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR
    
    if not backup_dir.exists():
        return []
    
    if sit_db_path is None:
        sit_db_path = DEFAULT_SIT_DB
    
    stem = sit_db_path.stem  # e.g., "car_management_sit"
    
    # Find all backups for this SIT DB
    pattern = f"{stem}_*.db"
    backups = list(backup_dir.glob(pattern))
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return backups


def cleanup_old_backups(keep_days: int = 30, backup_dir: Path = None) -> int:
    """Delete backups older than keep_days. Returns count deleted."""
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR
    
    if not backup_dir.exists():
        return 0
    
    cutoff = datetime.now() - datetime.timedelta(days=keep_days)
    count = 0
    
    for backup in backup_dir.glob("car_management_sit_*.db"):
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        if mtime < cutoff:
            backup.unlink()
            count += 1
    
    return count


def restore_sit_db(backup_path: Path, db_path: Path = None, quiet: bool = False) -> None:
    """
    Restore SIT database from a backup.
    
    Args:
        backup_path: Path to backup file to restore from
        db_path: Path to restore to (default: data/car_management_sit.db)
        quiet: Suppress output
    """
    if db_path is None:
        db_path = DEFAULT_SIT_DB
    
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Create safety backup of current state
    if db_path.exists():
        safety_backup = get_backup_path(DEFAULT_BACKUP_DIR, db_path)
        safety_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_path, safety_backup)
        if not quiet:
            print(f"  Safety backup of current DB: {safety_backup.name}")
    
    # Restore
    shutil.copy2(backup_path, db_path)
    
    if not quiet:
        print(f"  ✅ SIT DB restored from: {backup_path.name}")


def print_backup_summary(backup_path: Path, quiet: bool = False):
    """Print details of a backup file."""
    size = backup_path.stat().st_size
    mtime = datetime.fromtimestamp(backup_path.stat().st_mtime)
    
    # Try to get record counts from backup
    try:
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()
        
        tables = ["vai_tro", "nhan_vien", "xe", "khach_hang", "hop_dong", "bao_hanh"]
        counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                counts[table] = "N/A"
        
        conn.close()
        
        print(f"\n  {backup_path.name}")
        print(f"    Date:   {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Size:   {size:,} bytes")
        print(f"    Records:")
        for table, count in counts.items():
            print(f"      {table}: {count}")
        
    except Exception as e:
        if not quiet:
            print(f"\n  {backup_path.name} — could not read details: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Backup / restore SIT database for rollback capability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Create timestamped backup
  %(prog)s --list                    # List all backups
  %(prog)s --restore backup.db       # Restore from specific backup
  %(prog)s --cleanup 7               # Keep only last 7 days
        """,
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_SIT_DB,
        help=f"SIT database path (default: {DEFAULT_SIT_DB})",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help=f"Backup directory (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available backups",
    )
    parser.add_argument(
        "--restore", "-r",
        type=Path,
        metavar="BACKUP_PATH",
        help="Restore SIT DB from a backup file",
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        metavar="DAYS",
        help="Delete backups older than N days (default: 30)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Car-Management — SIT Database Backup Tool")
    print("=" * 60)
    
    if args.list:
        print(f"\n  Available backups in {args.backup_dir}:")
        backups = list_backups(args.backup_dir, args.db_path)
        if backups:
            for bp in backups:
                print_backup_summary(bp, args.quiet)
        else:
            print("  No backups found.")
        return 0
    
    if args.restore:
        try:
            restore_sit_db(args.restore, args.db_path, args.quiet)
            return 0
        except Exception as e:
            print(f"  [ERROR] Restore failed: {e}")
            return 1
    
    if args.cleanup is not None:
        count = cleanup_old_backups(args.cleanup, args.backup_dir)
        print(f"  Deleted {count} old backup(s).")
        return 0
    
    # Default: create backup
    try:
        backup_path = backup_sit_db(args.db_path, args.backup_dir, args.quiet)
        print("\n  SIT Database backup ready for rollback if needed.")
        return 0
    except FileNotFoundError as e:
        print(f"  [ERROR] {e}")
        print("  Run setup_sit_env.py first to create the SIT database.")
        return 1
    except Exception as e:
        print(f"  [ERROR] Backup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())