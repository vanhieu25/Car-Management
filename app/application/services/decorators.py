"""Decorators for service layer permission checking.

Provides @require_permission decorator for service methods.
"""

import functools
from typing import Callable, Union

from app.application.services.permission_service import PermissionService, PermissionDeniedError
from app.application.services.session import session_manager


def require_permission(
    module: str,
    action: str,
    use_session: bool = True,
) -> Callable:
    """Decorator to enforce permission on service methods.
    
    Checks if the current user (from session) has permission
    to perform the specified action on the given module.
    
    Args:
        module: Module identifier (e.g., 'xe', 'khach_hang').
        action: Action identifier (e.g., 'view', 'create', 'update', 'delete').
        use_session: If True, get role from current session.
                     If False, role must be passed as keyword argument 'vai_tro_id'.
    
    Raises:
        PermissionDeniedError: If user lacks required permission.
        
    Example:
        @require_permission('xe', 'create')
        def create_xe(self, data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get vai_tro_id from session or kwargs
            if use_session:
                try:
                    session = session_manager.require_session()
                    vai_tro_id = session.vai_tro_id
                except PermissionError:
                    raise PermissionDeniedError(
                        module, action,
                        "Yêu cầu đăng nhập để thực hiện chức năng này"
                    )
            else:
                vai_tro_id = kwargs.pop("vai_tro_id", None)
                if vai_tro_id is None:
                    raise PermissionDeniedError(
                        module, action,
                        "Không xác định được vai trò người dùng"
                    )
            
            # Check permission
            permission_service = PermissionService()
            if not permission_service.has_permission(vai_tro_id, module, action):
                raise PermissionDeniedError(module, action)
            
            # Update session activity (touch)
            if use_session:
                session_manager.touch()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_login(func: Callable) -> Callable:
    """Decorator to require authenticated session.
    
    Example:
        @require_login
        def sensitive_operation(self):
            session = session_manager.require_session()
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = session_manager.require_session()
        # Update activity
        session_manager.touch()
        return func(*args, **kwargs)
    return wrapper
