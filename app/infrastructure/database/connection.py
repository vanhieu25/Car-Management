"""Database connection factory and management."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

import sqlite3


class DatabaseConfig:
    """Configuration for database connection."""

    def __init__(self, db_path: str = "data/car_management.db"):
        self.db_path = db_path
        self.journal_mode = "WAL"
        self.foreign_keys = True

    @property
    def connection_string(self) -> str:
        return self.db_path


# Global config
_config = DatabaseConfig()


def get_config() -> DatabaseConfig:
    """Get current database configuration."""
    return _config


def set_config(config: DatabaseConfig) -> None:
    """Set database configuration."""
    global _config
    _config = config


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Create and configure a database connection.

    Args:
        db_path: Optional path override. Uses config default if not provided.

    Returns:
        Configured SQLite connection.
    """
    if db_path is None:
        db_path = _config.db_path

    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row

    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON")

    # Enable synchronous NORMAL for balance of safety and speed
    conn.execute("PRAGMA synchronous=NORMAL")

    # Set busy timeout to 30 seconds
    conn.execute("PRAGMA busy_timeout=30000")

    # Enable unique constraint validation
    conn.execute("PRAGMA unique_checks=ON")

    return conn


@contextmanager
def get_connection_context(db_path: Optional[str] = None):
    """
    Context manager for database connections.
    Automatically commits on success and rolls back on error.

    Args:
        db_path: Optional path override.

    Yields:
        sqlite3.Connection
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection):
    """
    Context manager for explicit transactions.
    Use when you need multiple operations in one transaction.

    Args:
        conn: Active database connection.

    Yields:
        sqlite3.Connection (same instance)
    """
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def get_db_path() -> str:
    """Get the current database file path."""
    return _config.db_path


def init_database() -> None:
    """
    Initialize database with migrations.
    Runs all pending migrations in order.
    """
    from app.infrastructure.database.migrations.runner import MigrationRunner

    runner = MigrationRunner()
    runner.run_pending()


def close_connection(conn: sqlite3.Connection) -> None:
    """Close a database connection safely."""
    if conn:
        conn.close()