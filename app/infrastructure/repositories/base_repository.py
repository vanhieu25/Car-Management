"""Base repository interface and implementations."""

from typing import Any, Generic, List, Optional, TypeVar

import sqlite3

from app.domain.entities import BaseEntity

T = TypeVar("T", bound=BaseEntity)


class BaseRepository(Generic[T]):
    """Base repository with standard CRUD operations."""

    def __init__(self, conn: sqlite3.Connection, entity_class: type):
        self.conn = conn
        self.entity_class = entity_class
        self.table_name = self._get_table_name()

    def _get_table_name(self) -> str:
        """Derive table name from entity class name."""
        name = self.entity_class.__name__
        # Convert CamelCase to snake_case
        import re
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def find_by_id(self, id: int) -> Optional[T]:
        """Find entity by ID."""
        cursor = self.conn.execute(
            f"SELECT * FROM {self.table_name} WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        if row:
            return self.entity_class.from_row(row)
        return None

    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all entities with pagination."""
        cursor = self.conn.execute(
            f"SELECT * FROM {self.table_name} ORDER BY id LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [self.entity_class.from_row(row) for row in cursor.fetchall()]

    def create(self, entity: T) -> T:
        """Create a new entity."""
        data = entity.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor = self.conn.execute(sql, values)
        entity.id = cursor.lastrowid
        return entity

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        if entity.id is None:
            raise ValueError("Entity must have an id to update")

        data = entity.to_dict()
        data.pop("id", None)
        data.pop("created_at", None)

        columns = list(data.keys())
        set_clause = ", ".join([f"{col} = ?" for col in columns])
        values = [data[col] for col in columns]
        values.append(entity.id)

        sql = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        self.conn.execute(sql, values)
        return entity

    def delete(self, id: int) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        cursor = self.conn.execute(
            f"DELETE FROM {self.table_name} WHERE id = ?", (id,)
        )
        return cursor.rowcount > 0

    def count(self) -> int:
        """Count total entities."""
        cursor = self.conn.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        return cursor.fetchone()[0]

    def exists(self, id: int) -> bool:
        """Check if entity exists."""
        cursor = self.conn.execute(
            f"SELECT 1 FROM {self.table_name} WHERE id = ?", (id,)
        )
        return cursor.fetchone() is not None