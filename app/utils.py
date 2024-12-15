from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from app.models import User, Cart, Card, Order, db
from flask_login import logout_user


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





def delete_user_account(user_id, is_admin=False):
    """
    Deletes a user account and cleans up associated data.

    Args:
        user_id (int): ID of the user to be deleted.
        is_admin (bool): Whether this is triggered by an admin.

    Returns:
        bool: True if deletion was successful, False otherwise.
        str: Feedback message.
    """
    user = User.query.get(user_id)
    if not user:
        return False, "User not found."

    try:
        # Step 1: Remove user's cards from carts
        Cart.query.filter(Cart.card_id.in_(
            Card.query.with_entities(Card.id).filter_by(uploader_id=user.id)
        )).delete(synchronize_session=False)

        # Step 2: Delete all cards uploaded by the user
        Card.query.filter_by(uploader_id=user.id).delete(synchronize_session=False)

        # Step 3: Delete orders associated with the user
        Order.query.filter_by(buyer_id=user.id).delete(synchronize_session=False)
        Order.query.filter_by(seller_id=user.id).delete(synchronize_session=False)

        # Step 4: Delete the user
        db.session.delete(user)
        db.session.commit()

        # Step 5: Logout the user if it's self-deletion
        if not is_admin:
            logout_user()

        return True, f"User '{user.username}' and all associated data have been deleted."

    except Exception as e:
        db.session.rollback()
        return False, f"An error occurred while deleting the account: {str(e)}"

