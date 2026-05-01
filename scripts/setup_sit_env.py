#!/usr/bin/env python3
"""
Setup SIT (System Integration Testing) Environment for Car-Management.

Creates an isolated test database separate from the development DB.
Seeds minimal test users (admin, nv, kh) for role-based permission testing.

Usage:
    python scripts/setup_sit_env.py                    # Create clean SIT DB
    python scripts/setup_sit_env.py --db-path /path/to/db  # Custom path
    python scripts/setup_sit_env.py --seed-users        # Seed test users after schema created
"""

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.database.connection import get_connection
from app.infrastructure.database.connection import get_connection_context


SIT_DB_NAME = "car_management_sit.db"
SIT_DB_DIR = Path(__file__).parent.parent / "data"
SIT_DB_PATH = SIT_DB_DIR / SIT_DB_NAME

# Default test users for SIT
SIT_USERS = [
    {
        "username": "sit_admin",
        "password": "Admin@123",
        "ho_ten": "SIT Admin",
        "email": "sit_admin@dailyxeco.vn",
        "so_dien_thoai": "0988001001",
        "vai_tro_id": 1,  # admin
        "trang_thai": "active",
        "must_change_password": 0,
    },
    {
        "username": "sit_nv",
        "password": "Admin@123",
        "ho_ten": "SIT Nhân viên",
        "email": "sit_nv@dailyxeco.vn",
        "so_dien_thoai": "0988001002",
        "vai_tro_id": 2,  # sales
        "trang_thai": "active",
        "must_change_password": 0,
    },
    {
        "username": "sit_kt",
        "password": "Admin@123",
        "ho_ten": "SIT Kỹ thuật BH",
        "email": "sit_kt@dailyxeco.vn",
        "so_dien_thoai": "0988001003",
        "vai_tro_id": 3,  # ky_thuat_bh
        "trang_thai": "active",
        "must_change_password": 0,
    },
]


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt with cost factor 12 (BR-SEC-01)."""
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def ensure_directories():
    """Ensure data/ and data/backup/ directories exist."""
    SIT_DB_DIR.mkdir(parents=True, exist_ok=True)
    backup_dir = SIT_DB_DIR / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Directories ensured: {SIT_DB_DIR}")


def run_migrations(conn: sqlite3.Connection):
    """Run all migrations on the SIT database."""
    migrations_dir = Path(__file__).parent.parent / "app" / "infrastructure" / "database" / "migrations"
    
    if not migrations_dir.exists():
        print(f"  [WARNING] Migrations directory not found: {migrations_dir}")
        print("  Attempting to run migrations via MigrationRunner...")
        try:
            from app.infrastructure.database.migrations.runner import MigrationRunner
            runner = MigrationRunner()
            runner.run_pending()
            print("  Migrations completed via MigrationRunner.")
        except Exception as e:
            print(f"  [ERROR] Could not run migrations: {e}")
            raise
        return

    # Get all SQL files sorted
    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        print(f"  [WARNING] No .sql files found in {migrations_dir}")
        return

    cursor = conn.cursor()
    migration_count = 0
    
    for sql_file in sql_files:
        try:
            sql = sql_file.read_text()
            cursor.executescript(sql)
            conn.commit()
            migration_count += 1
            print(f"  ✓ Applied migration: {sql_file.name}")
        except sqlite3.Error as e:
            # Ignore "table already exists" errors — they are expected
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate" in error_msg:
                print(f"  ~ Skipped (already exists): {sql_file.name}")
            else:
                print(f"  ✗ Error in {sql_file.name}: {e}")
                raise

    print(f"  Applied {migration_count} migration file(s)")


def seed_test_users(conn: sqlite3.Connection):
    """Seed minimal test users for SIT role-based permission testing.
    
    Creates 3 users: admin, nv (sales), kt (kỹ thuật) for testing
    role permissions across all 8 workflows and 15 modules.
    """
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for user in SIT_USERS:
        password_hash = get_password_hash(user["password"])
        
        try:
            cursor.execute(
                """INSERT OR REPLACE INTO nhan_vien
                   (username, mat_khau_hash, ho_ten, email, so_dien_thoai,
                    vai_tro_id, trang_thai, must_change_password, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user["username"],
                    password_hash,
                    user["ho_ten"],
                    user["email"],
                    user["so_dien_thoai"],
                    user["vai_tro_id"],
                    user["trang_thai"],
                    user["must_change_password"],
                    now,
                    now,
                ),
            )
            print(f"  ✓ Seeded user: {user['username']} (role_id={user['vai_tro_id']})")
        except sqlite3.IntegrityError as e:
            print(f"  ~ User already exists: {user['username']} — updating password")
            cursor.execute(
                """UPDATE nhan_vien SET mat_khau_hash = ?, updated_at = ?
                   WHERE username = ?""",
                (password_hash, now, user["username"]),
            )

    conn.commit()
    print(f"  Seeded {len(SIT_USERS)} SIT test users")


def seed_minimal_data(conn: sqlite3.Connection):
    """Seed minimal data required for SIT testing.
    
    Seeds only the essential data needed for workflow testing:
    - 3 vai_tro (admin/sales/ky_thuat)
    - 3 test users (above)
    - 10 xe sample
    - 10 khach_hang sample
    - 5 nha_cung_cap sample
    - 5 khuyen_mai sample
    - 5 phu_kien sample
    """
    from app.infrastructure.database.seeds.dev_seed import (
        seed_vai_tro, seed_xe, seed_khach_hang, seed_phu_kien,
        seed_nha_cung_cap, seed_khuyen_mai,
    )
    
    cursor = conn.cursor()
    
    print("  Seeding vai_tro...")
    seed_vai_tro(cursor)
    
    print("  Seeding xe (10 sample)...")
    seed_xe(cursor)
    
    print("  Seeding khach_hang (10 sample)...")
    seed_khach_hang(cursor)
    
    print("  Seeding phu_kien (5 sample)...")
    seed_phu_kien(cursor)
    
    print("  Seeding nha_cung_cap (5 sample)...")
    seed_nha_cung_cap(cursor)
    
    print("  Seeding khuyen_mai (5 sample)...")
    seed_khuyen_mai(cursor)
    
    conn.commit()
    print("  Minimal data seeding complete.")


def create_sit_db(db_path: Path, seed_users: bool = True, seed_data: bool = False):
    """
    Create a fresh SIT database with schema + optional test data.
    
    Args:
        db_path: Path for the SIT database file
        seed_users: If True, seed the 3 test users (admin, nv, kt)
        seed_data: If True, seed minimal data (xe, KH, NCC, KM, PK)
    """
    print(f"\n=== Setting up SIT Environment ===")
    print(f"  Database: {db_path}")
    
    # Ensure parent directory
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing SIT DB to ensure clean slate
    if db_path.exists():
        backup_path = db_path.parent / f"{db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(db_path, backup_path)
        print(f"  Existing SIT DB backed up to: {backup_path.name}")
        db_path.unlink()
    
    # Create new database and run migrations
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    
    print("\n  [1/3] Running migrations...")
    run_migrations(conn)
    
    if seed_users:
        print("\n  [2/3] Seeding test users (admin/nv/kt)...")
        seed_test_users(conn)
    
    if seed_data:
        print("\n  [3/3] Seeding minimal test data...")
        seed_minimal_data(conn)
    
    conn.close()
    
    print(f"\n  ✅ SIT environment created at: {db_path}")
    
    # Print summary
    print("\n  SIT Database Summary:")
    conn2 = sqlite3.connect(str(db_path))
    cursor = conn2.cursor()
    
    tables_to_check = [
        "vai_tro", "nhan_vien", "xe", "khach_hang", 
        "hop_dong", "phu_kien", "nha_cung_cap", "khuyen_mai"
    ]
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    {table}: {count} records")
        except sqlite3.OperationalError:
            print(f"    {table}: table not found")
    
    conn2.close()


def main():
    parser = argparse.ArgumentParser(
        description="Setup SIT (System Integration Testing) environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Create clean SIT DB with test users
  %(prog)s --no-users                # Create SIT DB without seeding test users
  %(prog)s --seed-data               # Create SIT DB + seed minimal test data
  %(prog)s --db-path /tmp/test.db    # Custom DB path
        """,
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=SIT_DB_PATH,
        help=f"Path for SIT database (default: {SIT_DB_PATH})",
    )
    parser.add_argument(
        "--no-users",
        action="store_true",
        help="Skip seeding test users (admin, nv, kt)",
    )
    parser.add_argument(
        "--seed-data",
        action="store_true",
        help="Seed minimal test data (xe, KH, NCC, KM, PK)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress verbose output",
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("=" * 60)
        print("  Car-Management — SIT Environment Setup")
        print("=" * 60)
    
    try:
        create_sit_db(
            db_path=args.db_path,
            seed_users=not args.no_users,
            seed_data=args.seed_data,
        )
        
        if not args.quiet:
            print("\n" + "=" * 60)
            print("  SIT Environment Ready!")
            print("  Test Users:")
            print("    admin  / Admin@123  (Admin role)")
            print("    nv     / Admin@123  (Sales role)")
            print("    kt     / Admin@123  (Kỹ thuật BH role)")
            print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n  [ERROR] Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())