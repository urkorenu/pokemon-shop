from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..models import Card, db, User
from config import Config
from app.utils import roles_required
from ..mail_service import send_email

admin_bp = Blueprint("admin", __name__)

API_KEY = Config.API_KEY
BASE_URL = "https://api.pokemontcg.io/v2"

@admin_bp.route("/users", methods=["GET", "POST"])
@roles_required("admin")
def manage_users():
    users = User.query.all()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        new_role = request.form.get(f"role_{user_id}")
        ban_reason = request.form.get(f"ban_reason_{user_id}", None)

        if not user_id or not new_role:
            flash("Invalid user or role data.", "error")
            return redirect(url_for("admin.manage_users"))

        if new_role not in ["normal", "uploader", "banned", "admin"]:
            flash("Invalid role.", "error")
            return redirect(url_for("admin.manage_users"))

        user = User.query.get(user_id)

        if user:
            old_role = user.role
            user.role = new_role

            # Handle role-specific logic
            if old_role != new_role:
                if new_role == "uploader":
                    send_email(
                        recipient=user.email,
                        subject="Uploader Role Granted",
                        body=f"Congratulations {user.username}, you have been granted the uploader role!",
                    )

                elif new_role == "banned":
                    cards_to_remove = Card.query.filter_by(uploader_id=user.id).all()
                    for card in cards_to_remove:
                        db.session.execute(
                            "DELETE FROM cart WHERE card_id = :card_id",
                            {"card_id": card.id},
                        )
                    db.session.commit()
                    send_email(
                        recipient=user.email,
                        subject="Account Banned",
                        body=f"Dear {user.username}, your account has been banned.\nReason: {ban_reason}",
                    )
                    flash(f"User {user.username} has been banned.", "warning")

                elif old_role == "banned" and new_role != "banned":
                    send_email(
                        recipient=user.email,
                        subject="Account Unbanned",
                        body=f"Dear {user.username}, your account has been unbanned. You can access your account now.",
                    )

            db.session.commit()
            flash(f"User {user.username}'s role updated to {new_role}.", "success")
        else:
            flash("User not found.", "error")

    return render_template("manage_users.html", users=users)
