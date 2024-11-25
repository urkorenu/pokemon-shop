from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def roles_required(*roles):
    """
    Decorator to restrict access to specific roles.
    Example usage: @roles_required("admin", "uploader")
    """
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for("user.view_cards"))
            return func(*args, **kwargs)
        return decorated_view
    return wrapper

