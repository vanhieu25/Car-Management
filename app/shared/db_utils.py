"""Database utilities for converting between DB rows and entities."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

import sqlite3


def row_to_entity(row: sqlite3.Row, entity_class: type) -> Optional[Any]:
    """Convert a database row to an entity instance."""
    if row is None:
        return None
    return entity_class(**dict(row))


def entity_to_dict(entity: Any, exclude: list = None) -> Dict[str, Any]:
    """
    Convert an entity to a dictionary.

    Args:
        entity: Entity instance.
        exclude: List of field names to exclude.

    Returns:
        Dictionary representation.
    """
    if exclude is None:
        exclude = ["id", "created_at", "updated_at"]

    result = {}
    for key, value in entity.__dict__.items():
        if key not in exclude and value is not None:
            result[key] = value
    return result


def dict_to_json(data: Dict[str, Any]) -> str:
    """Convert dictionary to JSON string."""
    return json.dumps(data, ensure_ascii=False, default=str)


def json_to_dict(json_str: str) -> Dict[str, Any]:
    """Convert JSON string to dictionary."""
    if not json_str:
        return {}
    return json.loads(json_str)


def format_currency(amount: int) -> str:
    """Format amount as Vietnamese currency."""
    return f"{amount:,}đ"


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string to datetime."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace(" ", "T"))
    except ValueError:
        return None


def to_iso_date(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO date string."""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d")


def to_iso_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO datetime string."""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_iso() -> str:
    """Get current date in ISO format."""
    return datetime.now().strftime("%Y-%m-%d")