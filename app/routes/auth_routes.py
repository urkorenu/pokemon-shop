from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User, db
from flask_bcrypt import generate_password_hash, check_password_hash
from ..cities import CITIES_IN_ISRAEL
from ..mail_service import send_email
from config import Config
from app.utils import delete_user_account
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create a Blueprint for authentication routes
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/sign-in", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def auth():
    """
    Handle user authentication (login and registration).

    GET: Render the authentication page.
    POST: Process login or registration form submission.

    Returns:
        Rendered template for the authentication page or redirect to another route.
    """
    form_type = request.form.get("form_type")
    if request.method == "POST":
        if form_type == "login":
            email, password = request.form.get("email"), request.form.get("password")
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if user.role == "banned":
                    flash("Your account has been banned", "error")
                    return redirect(url_for("auth.auth"))
                login_user(user, remember=bool(request.form.get("remember")))
                flash("Login successful!", "success")
                return redirect(url_for("user.view_cards"))
            flash("Invalid email or password.", "error")
        elif form_type == "register":
            username, email, password = request.form.get("username"), request.form.get("email"), request.form.get("password")
            location, contact_preference, contact_details = request.form.get("location"), request.form.get("contact_preference"), request.form.get("contact_details")
            if not all([username, email, password, location]):
                flash("All fields are required.", "error")
                return redirect(url_for("auth.auth"))
            if contact_preference not in ["phone", "facebook"] or not contact_details:
                flash("Invalid contact preference or details.", "error")
                return redirect(url_for("auth.auth"))
            if User.query.filter_by(username=username).first():
                flash("Username already taken. Please choose a different one.", "error")
                return redirect(url_for("auth.auth"))
            if User.query.filter_by(email=email).first():
                flash("Email already registered. Please log in.", "error")
                return redirect(url_for("auth.auth"))
            if not is_password_strong(password):
                flash("Password must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters.", "error")
                return redirect(url_for("auth.auth"))
            user = User(username=username, email=email, location=location, role="normal", contact_preference=contact_preference, contact_details=contact_details)
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("auth.auth"))
            except Exception as e:
                db.session.rollback()
                flash("An error occurred during registration. Please try again.", "error")
                print(f"Error during registration: {e}")
    return render_template("auth.html", cities=CITIES_IN_ISRAEL)

@auth_bp.route("/logout")
@login_required
def logout():
    """
    Log out the current user.

    Returns:
        Redirect to the authentication page.
    """
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.auth"))

@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    """
    Handle user account management (profile update, password change, account deletion).

    GET: Render the account management page.
    POST: Process profile update, password change, or account deletion form submission.

    Returns:
        Rendered template for the account management page or redirect to another route.
    """
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_profile":
            current_user.username = request.form.get("username", current_user.username)
            current_user.email = request.form.get("email", current_user.email)
            current_user.location = request.form.get("location", current_user.location)
            current_user.contact_preference = request.form.get("contact_preference", current_user.contact_preference)
            current_user.contact_details = request.form.get("contact_details", current_user.contact_details)
            db.session.commit()
            flash("Profile updated successfully!", "success")
        elif action == "change_password":
            old_password, new_password = request.form.get("old_password"), request.form.get("new_password")
            if not check_password_hash(current_user.password_hash, old_password):
                flash("Old password is incorrect.", "danger")
            else:
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash("Password updated successfully!", "success")
        elif action == "delete_account":
            db.session.delete(current_user)
            db.session.commit()
            flash("Your account has been deleted.", "success")
            return redirect(url_for("auth.login"))
        return redirect(url_for("auth.account"))
    return render_template("account.html", cities=CITIES_IN_ISRAEL)

@auth_bp.route("/request_uploader", methods=["POST"])
@login_required
def request_uploader():
    """
    Handle uploader role request submission.

    POST: Process uploader role request form submission.

    Returns:
        Redirect to the account management page.
    """
    if current_user.role in ["uploader", "admin"]:
        flash("You already have the uploader or admin role.", "info")
        return redirect(url_for("auth.account"))
    if current_user.request_status == "Pending":
        flash("Your request is already pending. Please wait for admin review.", "info")
        return redirect(url_for("auth.account"))
    if not request.form.get("rules_accepted"):
        flash("You must accept the rules before submitting your request.", "danger")
        return redirect(url_for("auth.account"))
    if not all([current_user.email, current_user.location, current_user.contact_details]):
        flash("Please ensure your profile details (email, location, and contact details) are updated.", "danger")
        return redirect(url_for("auth.account"))
    message_body = f"""
    User {current_user.username} has requested to become an uploader.

    User Details:
    - Email: {current_user.email}
    - Location: {current_user.location}
    - Contact Preference: {current_user.contact_preference}
    - Contact Details: {current_user.contact_details}

    Please review the request.
    """
    try:
        send_email(recipient=Config.ADMIN_MAIL, subject=f"Uploader Role Request from {current_user.username}", body=message_body)
        current_user.request_status = "Pending"
        db.session.commit()
        flash("Your request to become an uploader has been submitted successfully!", "success")
    except Exception as e:
        flash("Failed to send the request. Please try again later.", "danger")
        print(str(e))
    return redirect(url_for("auth.account"))

@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    """
    Handle password change request.

    POST: Process password change form submission.

    Returns:
        Redirect to the account management page.
    """
    old_password, new_password = request.form.get("old_password"), request.form.get("new_password")
    if not check_password_hash(current_user.password_hash, old_password):
        flash("Old password is incorrect.", "error")
        return redirect(url_for("auth.account"))
    current_user.password_hash = generate_password_hash(new_password).decode("utf-8")
    db.session.commit()
    flash("Password updated successfully!", "success")
    return redirect(url_for("auth.account"))

@auth_bp.route("/auth/delete_account", methods=["POST"])
@login_required
def delete_account():
    """
    Handle account deletion request.

    POST: Process account deletion form submission.

    Returns:
        Redirect to the authentication page.
    """
    success, message = delete_user_account(current_user.id)
    flash(message, "success" if success else "danger")
    return redirect(url_for("auth.auth"))

def is_password_strong(password):
    """
    Check if the password is strong.

    Args:
        password (str): The password to check.

    Returns:
        bool: True if the password is strong, False otherwise.
    """
    return bool(re.match(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)[A-Za-z\d]{8,}$", password))