from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Card, User, db
from config import Config
from app.utils import roles_required
from ..mail_service import send_email

# Create a Blueprint for admin routes
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET", "POST"])
@roles_required("admin")
def manage_users():
    """
    Manage users by allowing an admin to view all users and update their roles.
    Handles both GET and POST requests.

    GET: Renders the manage_users.html template with a list of all users.
    POST: Updates the role of a user based on the form data submitted.

    Returns:
        A rendered template for GET requests.
        A redirect to the manage_users route for POST requests.
    """
    # Query all users from the database
    users = User.query.all()

    if request.method == "POST":
        # Get user ID, new role, and ban reason from the form
        user_id = request.form.get("user_id")
        new_role = request.form.get(f"role_{user_id}")
        ban_reason = request.form.get(f"ban_reason_{user_id}")

        # Validate the form data
        if (
            not user_id
            or not new_role
            or new_role not in ["normal", "uploader", "banned", "admin"]
        ):
            flash("Invalid user or role data.", "error")
            return redirect(url_for("admin.manage_users"))

        # Query the user by ID
        user = User.query.get(user_id)
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("admin.manage_users"))

        # Store the old role and update the user's role
        old_role = user.role
        user.role = new_role

        # Handle role changes and send appropriate emails
        if old_role != new_role:
            if new_role == "uploader":
                send_email(
                    user.email,
                    "Uploader Role Granted",
                    f"Congratulations {user.username}, you have been granted the uploader role!",
                )
            elif new_role == "banned":
                # Delete all cards uploaded by the user and commit the changes
                Card.query.filter_by(uploader_id=user.id).delete()
                db.session.commit()
                send_email(
                    user.email,
                    "Account Banned",
                    f"Dear {user.username}, your account has been banned.\nReason: {ban_reason}",
                )
                flash(f"User {user.username} has been banned.", "warning")
            elif old_role == "banned":
                send_email(
                    user.email,
                    "Account Unbanned",
                    f"Dear {user.username}, your account has been unbanned. You can access your account now.",
                )

        # Commit the changes to the database
        db.session.commit()
        flash(f"User {user.username}'s role updated to {new_role}.", "success")

    # Render the manage_users.html template with the list of users
    return render_template("manage_users.html", users=users)
