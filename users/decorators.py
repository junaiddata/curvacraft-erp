# users/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def admin_required(function):
    """
    Decorator to ensure the user is an admin.
    If not, it raises a PermissionDenied exception.
    """
    def check_admin(user):
        if not user.is_authenticated or user.role != 'admin':
            raise PermissionDenied
        return True
    return user_passes_test(check_admin)(function)