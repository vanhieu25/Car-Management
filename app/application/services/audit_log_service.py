"""Audit log service - log all system actions.

Implements BR-SEC-09: Audit trail for all system actions.
Implements TRG-08: Integration with authentication service.

Actions logged:
- LOGIN: User login success
- LOGOUT: User logout
- CREATE_<TABLE>: New record created
- UPDATE_<TABLE>: Record updated
- DELETE_<TABLE>: Record deleted
- CHANGE_PASSWORD: User changed password
- CANCEL_HD: Contract cancelled

Noi dung format:
{
    "before": {...},  // null for CREATE
    "after": {...},   // null for DELETE
    "changes": {...}   // for UPDATE - only changed fields
}
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict

import sqlite3


# Action constants
class AuditAction:
    """Audit action constants."""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    
    # Contract
    CANCEL_HD = "CANCEL_HD"
    
    # Generic CRUD (use with table name prefix)
    CREATE = "CREATE_"
    UPDATE = "UPDATE_"
    DELETE = "DELETE_"


@dataclass
class AuditLogEntry:
    """Represents an audit log entry."""
    nhan_vien_id: int
    hanh_dong: str
    bang_anh_huong: str = None
    ban_ghi_id: int = None
    noi_dung: Dict[str, Any] = field(default_factory=dict)
    thoi_gian: str = None
    
    def __post_init__(self):
        if self.thoi_gian is None:
            self.thoi_gian = datetime.now().isoformat()


class AuditLogService:
    """Service for creating and querying audit log entries.
    
    Automatically captures user from current session.
    """
    
    def __init__(self, conn: sqlite3.Connection):
        """Initialize with database connection.
        
        Args:
            conn: sqlite3.Connection instance.
        """
        self.conn = conn
    
    def log(
        self,
        action: str,
        nhan_vien_id: int = None,
        bang_anh_huong: str = None,
        ban_ghi_id: int = None,
        before: Dict[str, Any] = None,
        after: Dict[str, Any] = None,
        changes: Dict[str, Any] = None,
    ) -> int:
        """Create an audit log entry.
        
        Args:
            action: Action code (LOGIN, UPDATE_XE, etc.)
            nhan_vien_id: User ID performing the action.
            bang_anh_huong: Table name affected.
            ban_ghi_id: Record ID affected.
            before: State before the action.
            after: State after the action.
            changes: For UPDATE - only changed fields.
            
        Returns:
            ID of created audit log entry.
        """
        # Build noi_dung JSON
        noi_dung = {}
        if before is not None:
            noi_dung["before"] = before
        if after is not None:
            noi_dung["after"] = after
        if changes is not None:
            noi_dung["changes"] = changes
        
        noi_dung_json = json.dumps(noi_dung, ensure_ascii=False) if noi_dung else None
        
        cursor = self.conn.execute(
            """INSERT INTO audit_log 
               (nhan_vien_id, hanh_dong, bang_anh_huong, ban_ghi_id, noi_dung, thoi_gian)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                nhan_vien_id,
                action,
                bang_anh_huong,
                ban_ghi_id,
                noi_dung_json,
                datetime.now().isoformat(),
            )
        )
        self.conn.commit()
        
        return cursor.lastrowid
    
    def log_login(self, nhan_vien_id: int, username: str) -> int:
        """Log a login event.
        
        Args:
            nhan_vien_id: User ID.
            username: Username for logging.
            
        Returns:
            Audit log entry ID.
        """
        return self.log(
            action=AuditAction.LOGIN,
            nhan_vien_id=nhan_vien_id,
            bang_anh_huong="nhan_vien",
            ban_ghi_id=nhan_vien_id,
            after={"username": username, "event": "login_success"},
        )
    
    def log_logout(self, nhan_vien_id: int) -> int:
        """Log a logout event.
        
        Args:
            nhan_vien_id: User ID.
            
        Returns:
            Audit log entry ID.
        """
        return self.log(
            action=AuditAction.LOGOUT,
            nhan_vien_id=nhan_vien_id,
            bang_anh_huong="nhan_vien",
            ban_ghi_id=nhan_vien_id,
        )
    
    def log_create(
        self,
        action: str,
        nhan_vien_id: int,
        table: str,
        record_id: int,
        record_data: Dict[str, Any],
    ) -> int:
        """Log a create event.
        
        Args:
            action: Action code (e.g., "CREATE_XE").
            nhan_vien_id: User ID performing the action.
            table: Table name.
            record_id: ID of created record.
            record_data: Full record data.
            
        Returns:
            Audit log entry ID.
        """
        return self.log(
            action=action,
            nhan_vien_id=nhan_vien_id,
            bang_anh_huong=table,
            ban_ghi_id=record_id,
            after=record_data,
        )
    
    def log_update(
        self,
        action: str,
        nhan_vien_id: int,
        table: str,
        record_id: int,
        before: Dict[str, Any],
        after: Dict[str, Any],
        changes: Dict[str, Any] = None,
    ) -> int:
        """Log an update event.
        
        Args:
            action: Action code (e.g., "UPDATE_XE").
            nhan_vien_id: User ID.
            table: Table name.
            record_id: Record ID.
            before: State before update.
            after: State after update.
            changes: Only changed fields (optional).
            
        Returns:
            Audit log entry ID.
        """
        return self.log(
            action=action,
            nhan_vien_id=nhan_vien_id,
            bang_anh_huong=table,
            ban_ghi_id=record_id,
            before=before,
            after=after,
            changes=changes or self._compute_changes(before, after),
        )
    
    def log_delete(
        self,
        action: str,
        nhan_vien_id: int,
        table: str,
        record_id: int,
        before: Dict[str, Any],
    ) -> int:
        """Log a delete event.
        
        Args:
            action: Action code (e.g., "DELETE_XE").
            nhan_vien_id: User ID.
            table: Table name.
            record_id: Record ID.
            before: Record state before deletion.
            
        Returns:
            Audit log entry ID.
        """
        return self.log(
            action=action,
            nhan_vien_id=nhan_vien_id,
            bang_anh_huong=table,
            ban_ghi_id=record_id,
            before=before,
        )
    
    def log_contract_cancel(
        self,
        nhan_vien_id: int,
        hop_dong_id: int,
        ly_do: str = None,
    ) -> int:
        """Log a contract cancellation.
        
        Args:
            nhan_vien_id: User ID performing cancellation.
            hop_dong_id: Contract ID.
            ly_do: Cancellation reason.
            
        Returns:
            Audit log entry ID.
        """
        return self.log(
            action=AuditAction.CANCEL_HD,
            nhan_vien_id=nhan_vien_id,
            bang_anh_huong="hop_dong",
            ban_ghi_id=hop_dong_id,
            after={"ly_do_huy": ly_do} if ly_do else None,
        )
    
    def log_password_change(self, nhan_vien_id: int) -> int:
        """Log a password change event.
        
        Args:
            nhan_vien_id: User ID.
            
        Returns:
            Audit log entry ID.
        """
        return self.log(
            action=AuditAction.CHANGE_PASSWORD,
            nhan_vien_id=nhan_vien_id,
            bang_anh_huong="nhan_vien",
            ban_ghi_id=nhan_vien_id,
            after={"event": "password_changed"},
        )
    
    def _compute_changes(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute only the changed fields between before and after.
        
        Args:
            before: State before.
            after: State after.
            
        Returns:
            Dict of only changed fields.
        """
        changes = {}
        for key in after:
            if key in before:
                if before[key] != after[key]:
                    changes[key] = {"from": before[key], "to": after[key]}
            else:
                changes[key] = {"to": after[key]}
        return changes
    
    def query(
        self,
        nhan_vien_id: int = None,
        action: str = None,
        table: str = None,
        from_time: datetime = None,
        to_time: datetime = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Dict[str, Any]]:
        """Query audit logs with filters.
        
        Args:
            nhan_vien_id: Filter by user ID.
            action: Filter by action (partial match).
            table: Filter by table name.
            from_time: Start time filter.
            to_time: End time filter.
            limit: Max results.
            offset: Offset for pagination.
            
        Returns:
            List of audit log entries.
        """
        conditions = []
        params = []
        
        if nhan_vien_id is not None:
            conditions.append("nhan_vien_id = ?")
            params.append(nhan_vien_id)
        
        if action is not None:
            conditions.append("hanh_dong LIKE ?")
            params.append(f"{action}%")
        
        if table is not None:
            conditions.append("bang_anh_huong = ?")
            params.append(table)
        
        if from_time is not None:
            conditions.append("thoi_gian >= ?")
            params.append(from_time.isoformat())
        
        if to_time is not None:
            conditions.append("thoi_gian <= ?")
            params.append(to_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT al.*, nv.username, nv.ho_ten
            FROM audit_log al
            LEFT JOIN nhan_vien nv ON al.nhan_vien_id = nv.id
            WHERE {where_clause}
            ORDER BY al.thoi_gian DESC
            LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        
        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            entry = {
                "id": row[0],
                "nhan_vien_id": row[1],
                "hanh_dong": row[2],
                "bang_anh_huong": row[3],
                "ban_ghi_id": row[4],
                "noi_dung": json.loads(row[5]) if row[5] else {},
                "thoi_gian": row[6],
                "username": row[7] if len(row) > 7 else None,
                "ho_ten": row[8] if len(row) > 8 else None,
            }
            results.append(entry)
        
        return results
    
    def count(
        self,
        nhan_vien_id: int = None,
        action: str = None,
        table: str = None,
        from_time: datetime = None,
        to_time: datetime = None,
    ) -> int:
        """Count audit logs with filters.
        
        Returns:
            Count of matching entries.
        """
        conditions = []
        params = []
        
        if nhan_vien_id is not None:
            conditions.append("nhan_vien_id = ?")
            params.append(nhan_vien_id)
        
        if action is not None:
            conditions.append("hanh_dong LIKE ?")
            params.append(f"{action}%")
        
        if table is not None:
            conditions.append("bang_anh_huong = ?")
            params.append(table)
        
        if from_time is not None:
            conditions.append("thoi_gian >= ?")
            params.append(from_time.isoformat())
        
        if to_time is not None:
            conditions.append("thoi_gian <= ?")
            params.append(to_time.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM audit_log WHERE {where_clause}",
            params
        )
        return cursor.fetchone()[0]


# Singleton instance for easy access
_audit_service: Optional[AuditLogService] = None


def get_audit_service(conn: sqlite3.Connection) -> AuditLogService:
    """Get audit log service instance.
    
    Args:
        conn: Database connection.
        
    Returns:
        AuditLogService instance.
    """
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditLogService(conn)
    return _audit_service


def reset_audit_service():
    """Reset the audit service singleton (for testing)."""
    global _audit_service
    _audit_service = None