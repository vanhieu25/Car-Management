"""Migration runner - executes pending migrations in order."""

from app.shared.logger import logger
from app.infrastructure.database.connection import get_connection_context
from app.infrastructure.database.migrations import MIGRATIONS


class MigrationRunner:
    """Manages and runs database migrations."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._ensure_schema_version_table()

    def _ensure_schema_version_table(self) -> None:
        """Create schema_version table if it doesn't exist."""
        with get_connection_context(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _get_applied_versions(self):
        """Get list of applied migration versions."""
        with get_connection_context(self.db_path) as conn:
            cursor = conn.execute("SELECT version FROM schema_version ORDER BY version")
            return [row[0] for row in cursor.fetchall()]

    def _mark_applied(self, version: int, name: str) -> None:
        """Mark a migration as applied."""
        with get_connection_context(self.db_path) as conn:
            conn.execute(
                "INSERT INTO schema_version (version, name) VALUES (?, ?)",
                (version, name)
            )
            logger.info(f"Migration {version:03d} ({name}) marked as applied")

    def run_pending(self) -> int:
        """
        Run all pending migrations.

        Returns:
            Number of migrations applied.
        """
        applied = set(self._get_applied_versions())
        count = 0

        for version, name, run_func in MIGRATIONS:
            if version in applied:
                logger.debug(f"Migration {version:03d} already applied, skipping")
                continue

            logger.info(f"Running migration {version:03d}: {name}")
            try:
                with get_connection_context(self.db_path) as conn:
                    run_func(conn)

                self._mark_applied(version, name)
                logger.info(f"Migration {version:03d} ({name}) completed successfully")
                count += 1

            except Exception as e:
                logger.error(f"Migration {version:03d} ({name}) failed: {e}")
                raise

        logger.info(f"Migration runner finished. {count} migrations applied.")
        return count

    def get_current_version(self) -> int:
        """Get the current schema version."""
        applied = self._get_applied_versions()
        return max(applied) if applied else 0

    def get_status(self) -> dict:
        """Get detailed migration status."""
        applied = set(self._get_applied_versions())
        return {
            "current_version": self.get_current_version(),
            "total_migrations": len(MIGRATIONS),
            "applied": len(applied),
            "pending": len(MIGRATIONS) - len(applied),
            "migrations": [
                {
                    "version": v,
                    "name": n,
                    "applied": v in applied
                }
                for v, n, _ in MIGRATIONS
            ]
        }