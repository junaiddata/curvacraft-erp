# users/decorators.py
from django.core.exceptions import PermissionDenied

def role_required(*roles):
    """
    A decorator that checks if a user has one of the specified roles.
    Usage: @role_required('admin', 'staff')
    """
    def decorator(function):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in roles:
                return function(request, *args, **kwargs)
            else:
                # Redirect to home or show a permission denied error
                raise PermissionDenied
        return wrapper
    return decorator

# We can keep a simple one for just admins if we want
admin_required = role_required('admin')