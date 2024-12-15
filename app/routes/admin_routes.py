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
    search_query = request.args.get("search", "")
    if search_query:
        users = User.query.filter(
            User.username.ilike(f"%{search_query}%") |
            User.email.ilike(f"%{search_query}%") |
            User.location.ilike(f"%{search_query}%")
        ).all()
    else:
        users = User.query.all()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        user = User.query.get(user_id)
        if user:
            user.username = request.form.get(f"username_{user_id}")
            user.email = request.form.get(f"email_{user_id}")
            user.location = request.form.get(f"location_{user_id}")
            user.contact_preference = request.form.get(f"contact_preference_{user_id}")
            user.contact_details = request.form.get(f"contact_details_{user_id}")
            user.rating = request.form.get(f"rating_{user_id}")
            user.feedback_count = request.form.get(f"feedback_count_{user_id}")
            user.request_status = request.form.get(f"request_status_{user_id}")
            new_role = request.form.get(f"role_{user_id}")
            ban_reason = request.form.get(f"ban_reason_{user_id}")

            if new_role and new_role in ["normal", "uploader", "banned", "admin"]:
                old_role = user.role
                user.role = new_role
                if old_role != new_role:
                    if new_role == "uploader":
                        send_email(user.email, "Uploader Role Granted", f"Congratulations {user.username}, you have been granted the uploader role!")
                    elif new_role == "banned":
                        Card.query.filter_by(uploader_id=user.id).delete()
                        db.session.commit()
                        send_email(user.email, "Account Banned", f"Dear {user.username}, your account has been banned.\nReason: {ban_reason}")
                        flash(f"User {user.username} has been banned.", "warning")
                    elif old_role == "banned":
                        send_email(user.email, "Account Unbanned", f"Dear {user.username}, your account has been unbanned. You can access your account now.")
                db.session.commit()
                flash(f"User {user.username}'s role updated to {new_role}.", "success")
            else:
                flash("Invalid role data.", "error")

    return render_template("manage_users.html", users=users)
