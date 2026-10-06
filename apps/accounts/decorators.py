from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has a specific role,
    raising PermissionDenied if they don't.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
                
            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied("You do not have permission to view this page.")
        return _wrapped_view
    return decorator

# Specific role decorators
admin_required = role_required(['admin'])
hr_required = role_required(['admin', 'hr'])
manager_required = role_required(['admin', 'hr', 'manager'])
