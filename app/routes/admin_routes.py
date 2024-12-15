from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Card, User, db
from app.utils import roles_required, delete_user_account
from ..mail_service import send_email

# Create a Blueprint for admin routes
admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/users", methods=["GET", "POST"])
@roles_required("admin")
def manage_users():
    """
    Route to manage users. Allows searching, updating, and deleting users.
    Only accessible by admin users.

    Methods:
        GET: Renders the user management page with a list of users.
        POST: Handles user updates and deletions.

    Returns:
        Rendered template for user management.
    """
    # Get the search query from the request
    search_query = request.args.get("search", "")

    # Filter users based on the search query or get all users
    users = User.query.filter(
        User.username.ilike(f"%{search_query}%") |
        User.email.ilike(f"%{search_query}%") |
        User.location.ilike(f"%{search_query}%")
    ).all() if search_query else User.query.all()

    if request.method == "POST":
        # Handle user deletion
        delete_user_id = request.form.get("delete_user_id")
        if delete_user_id:
            success, message = delete_user_account(delete_user_id, is_admin=True)
            flash(message, "success" if success else "danger")
            return redirect(url_for("admin.manage_users"))

        # Handle user updates
        user_id = request.form.get("user_id")
        user = User.query.get(user_id)
        if user:
            user.username = request.form.get(f"username_{user_id}")
            user.email = request.form.get(f"email_{user_id}")
            user.location = request.form.get(f"location_{user_id}")
            user.contact_preference = request.form.get(f"contact_preference_{user_id}")
            user.contact_details = request.form.get(f"contact_details_{user_id}")
            user.rating = float(request.form.get(f"rating_{user_id}", 0))
            user.feedback_count = int(request.form.get(f"feedback_count_{user_id}", 0))
            user.request_status = request.form.get(f"request_status_{user_id}", "").strip()

            new_role = request.form.get(f"role_{user_id}")
            ban_reason = request.form.get(f"ban_reason_{user_id}")

            if new_role in ["normal", "uploader", "banned", "admin"]:
                old_role = user.role
                user.role = new_role
                if old_role != new_role:
                    if new_role == "uploader":
                        user.request_status = "None"
                        send_email(user.email, "Uploader Role Granted", f"Congratulations {user.username}, you have been granted the uploader role!")
                    elif new_role == "banned":
                        Card.query.filter_by(uploader_id=user.id).delete()
                        send_email(user.email, "Account Banned", f"Dear {user.username}, your account has been banned.\nReason: {ban_reason}")
                        flash(f"User {user.username} has been banned.", "warning")
                    elif old_role == "banned":
                        send_email(user.email, "Account Unbanned", f"Dear {user.username}, your account has been unbanned. You can access your account now.")
                db.session.commit()
                flash(f"User {user.username}'s role updated to {new_role}.", "success")
            else:
                flash("Invalid role data.", "error")

    return render_template("manage_users.html", users=users)