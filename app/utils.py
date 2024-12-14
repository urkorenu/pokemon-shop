from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def roles_required(*roles):
    """
    Decorator to restrict access to specific roles.

    Args:
        *roles: Variable length argument list of roles that are allowed access.

    Returns:
        function: The decorated function that checks for the required roles.
    """
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            """
            Inner function that checks if the current user is authenticated and has the required role.

            Args:
                *args: Variable length argument list.
                **kwargs: Arbitrary keyword arguments.

            Returns:
                function: The original function if the user has the required role, otherwise redirects to a different page.
            """
            if not current_user.is_authenticated or current_user.role not in roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for("user.view_cards"))
            return func(*args, **kwargs)
        return decorated_view
    return wrapper