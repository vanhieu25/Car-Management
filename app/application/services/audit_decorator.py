"""Audit decorator for service methods.

Provides @audit decorator to automatically log service method calls.
Implements BR-SEC-09: Audit trail for all system actions.

Usage:
    @audit("CREATE_XE")
    def create_xe(self, data):
        # ... create xe ...
        return xe
    
    @audit("UPDATE_HD")
    def update_hop_dong(self, hop_dong_id, data):
        # ... update ...
        return result
"""

import functools
import json
from typing import Callable, Any, Dict, Optional

from app.application.services.audit_log_service import AuditLogService, AuditAction


def audit(
    action: str,
    table: str = None,
    id_param: int = None,
    get_before: Callable = None,
    get_after: Callable = None,
):
    """Decorator to automatically audit service method calls.
    
    Args:
        action: Action code (e.g., "CREATE_XE", "UPDATE_HD").
        table: Table name (optional, derived from action if not provided).
        id_param: Index of parameter that contains record ID (optional).
        get_before: Function to extract record state before change.
                    Takes same args as the decorated method.
        get_after: Function to extract record state after change.
                   Takes same args as the decorated method.
    
    Usage:
        @audit("CREATE_XE", table="xe")
        def create_xe(self, data):
            pass
        
        @audit("UPDATE_XE", id_param=0, get_before=lambda xe_id: self.get_xe(xe_id))
        def update_xe(self, xe_id, data):
            pass
    
    Note: The decorator relies on the service having access to:
    - self.conn: Database connection
    - self._session: Current session (with user_id)
    - self._audit_service: AuditLogService instance (optional, will create if not exists)
    """
    
    def decorator(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # Get database connection
            conn = getattr(self, 'conn', None)
            if conn is None:
                raise RuntimeError(
                    f"Service {self.__class__.__name__} needs 'conn' attribute for @audit"
                )
            
            # Get audit service
            audit_service = getattr(self, '_audit_service', None)
            if audit_service is None:
                audit_service = AuditLogService(conn)
                self._audit_service = audit_service
            
            # Get current user from session
            session = getattr(self, '_session', None)
            nhan_vien_id = None
            if session:
                nhan_vien_id = session.user_id
            
            # Determine table name
            table_name = table
            if table_name is None:
                # Derive from action (e.g., "CREATE_XE" -> "xe")
                if action.startswith("CREATE_"):
                    table_name = action.replace("CREATE_", "").lower()
                elif action.startswith("UPDATE_"):
                    table_name = action.replace("UPDATE_", "").lower()
                elif action.startswith("DELETE_"):
                    table_name = action.replace("DELETE_", "").lower()
            
            # Get record ID if id_param specified
            record_id = None
            if id_param is not None:
                if id_param < len(args):
                    record_id = args[id_param]
            
            # Get before state if function provided
            before = None
            if get_before is not None:
                try:
                    before = get_before(*args, **kwargs)
                except Exception:
                    pass  # Ignore errors getting before state
            
            # Execute the method
            result = method(self, *args, **kwargs)
            
            # Get after state if function provided
            after = None
            if get_after is not None:
                try:
                    after = get_after(*args, **kwargs)
                except Exception:
                    pass
            
            # Extract record_id from result if not set
            if record_id is None and result is not None:
                if isinstance(result, dict) and 'id' in result:
                    record_id = result['id']
                elif hasattr(result, 'id'):
                    record_id = result.id
            
            # Log the action
            try:
                if action == AuditAction.LOGIN:
                    audit_service.log_login(nhan_vien_id, kwargs.get('username', ''))
                elif action == AuditAction.LOGOUT:
                    audit_service.log_logout(nhan_vien_id)
                elif action == AuditAction.CHANGE_PASSWORD:
                    audit_service.log_password_change(nhan_vien_id)
                elif action.startswith("CREATE_"):
                    audit_service.log_create(
                        action=action,
                        nhan_vien_id=nhan_vien_id,
                        table=table_name,
                        record_id=record_id,
                        record_data=after or {},
                    )
                elif action.startswith("UPDATE_"):
                    audit_service.log_update(
                        action=action,
                        nhan_vien_id=nhan_vien_id,
                        table=table_name,
                        record_id=record_id,
                        before=before,
                        after=after,
                    )
                elif action.startswith("DELETE_"):
                    audit_service.log_delete(
                        action=action,
                        nhan_vien_id=nhan_vien_id,
                        table=table_name,
                        record_id=record_id,
                        before=before,
                    )
                else:
                    # Generic log for other actions
                    audit_service.log(
                        action=action,
                        nhan_vien_id=nhan_vien_id,
                        bang_anh_huong=table_name,
                        ban_ghi_id=record_id,
                        before=before,
                        after=after,
                    )
            except Exception as e:
                # Don't let audit failure break the main operation
                import logging
                logging.error(f"Audit logging failed: {e}")
            
            return result
        
        return wrapper
    
    return decorator


def audit_login(method: Callable) -> Callable:
    """Decorator specifically for login method."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        
        # Log successful login
        if hasattr(self, '_session') and self._session:
            audit_service = getattr(self, '_audit_service', None)
            if audit_service is None:
                conn = getattr(self, 'conn', None)
                if conn:
                    audit_service = AuditLogService(conn)
                    self._audit_service = audit_service
            
            if audit_service and result and hasattr(result, 'user'):
                try:
                    audit_service.log_login(result.user.id, result.user.username)
                except Exception:
                    pass
        
        return result
    
    return wrapper


def audit_logout(method: Callable) -> Callable:
    """Decorator specifically for logout method."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # Get user before logout
        nhan_vien_id = None
        if hasattr(self, '_session') and self._session:
            nhan_vien_id = self._session.user_id
        
        result = method(self, *args, **kwargs)
        
        # Log logout
        if nhan_vien_id:
            audit_service = getattr(self, '_audit_service', None)
            if audit_service is None:
                conn = getattr(self, 'conn', None)
                if conn:
                    audit_service = AuditLogService(conn)
                    self._audit_service = audit_service
            
            if audit_service:
                try:
                    audit_service.log_logout(nhan_vien_id)
                except Exception:
                    pass
        
        return result