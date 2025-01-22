from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    jsonify,
)
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
from itsdangerous import URLSafeTimedSerializer
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_babel import _



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
                if not user.is_active:
                    flash(
                        _("Your account is not activated. Please check your email."),
                        "error",
                    )
                    return redirect(url_for("auth.auth"))
                if user.role == "banned":
                    flash(_("Your account has been banned"), "error")
                    return redirect(url_for("auth.auth"))
                login_user(user, remember=bool(request.form.get("remember")))
                flash(_("Login successful!"), "success")
                return redirect(url_for("user.view_cards"))
            flash(_("Invalid email or password."), "error")
        elif form_type == "register":
            username, email, password = (
                request.form.get("username"),
                request.form.get("email"),
                request.form.get("password"),
            )
            location, contact_preference, contact_details = (
                request.form.get("location"),
                request.form.get("contact_preference"),
                request.form.get("contact_details"),
            )
            if not all([username, email, password, location]):
                flash(_("All fields are required."), "error")
                return redirect(url_for("auth.auth"))
            if contact_preference not in ["phone", "facebook"] or not contact_details:
                flash(_("Invalid contact preference or details."), "error")
                return redirect(url_for("auth.auth"))
            if User.query.filter_by(username=username).first():
                flash(_("Username already taken. Please choose a different one."), "error")
                return redirect(url_for("auth.auth"))
            if User.query.filter_by(email=email).first():
                flash(_("Email already registered. Please log in."), "error")
                return redirect(url_for("auth.auth"))
            if not is_password_strong(password):
                flash(
                    _("Password must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters."),
                    "error",
                )
                return redirect(url_for("auth.auth"))
            user = User(
                username=username,
                email=email,
                location=location,
                role="normal",
                contact_preference=contact_preference,
                contact_details=contact_details,
            )
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
                serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
                token = serializer.dumps(user.email)
                activation_link = url_for(
                    "auth.confirm_email", token=token, _external=True
                )
                send_email(
                    recipient=user.email,
                    subject="Activate Your Account",
                    body=f"Click the link to activate your account: {activation_link}",
                )
                flash(_("Registration successful! Please log in."), "success")
                return redirect(url_for("auth.auth"))
            except Exception as e:
                db.session.rollback()
                flash(
                    _("An error occurred during registration. Please try again."), "error"
                )
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
    flash(_("You have been logged out."), "success")
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
            current_user.contact_preference = request.form.get(
                "contact_preference", current_user.contact_preference
            )
            current_user.contact_details = request.form.get(
                "contact_details", current_user.contact_details
            )
            db.session.commit()
            flash(_("Profile updated successfully!"), "success")
        elif action == "change_password":
            old_password, new_password = request.form.get(
                "old_password"
            ), request.form.get("new_password")
            if not check_password_hash(current_user.password_hash, old_password):
                flash(_("Old password is incorrect."), "danger")
            else:
                current_user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash(_("Password updated successfully!"), "success")
        elif action == "delete_account":
            db.session.delete(current_user)
            db.session.commit()
            flash(_("Your account has been deleted."), "success")
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
        flash(_("You already have the uploader or admin role."), "info")
        return redirect(url_for("auth.account"))
    if current_user.request_status == "Pending":
        flash(_("Your request is already pending. Please wait for admin review."), "info")
        return redirect(url_for("auth.account"))
    if not request.form.get("rules_accepted"):
        flash(_("You must accept the rules before submitting your request."), "danger")
        return redirect(url_for("auth.account"))
    if not all(
        [current_user.email, current_user.location, current_user.contact_details]
    ):
        flash(
            _("Please ensure your profile details (email, location, and contact details) are updated."),
            "danger",
        )
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
        send_email(
            recipient=Config.ADMIN_MAIL,
            subject=f"Uploader Role Request from {current_user.username}",
            body=message_body,
        )
        current_user.request_status = "Pending"
        db.session.commit()
        flash(_(
            "Your request to become an uploader has been submitted successfully!"),
            "success",
        )
    except Exception as e:
        flash(_("Failed to send the request. Please try again later."), "danger")
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
    old_password, new_password = request.form.get("old_password"), request.form.get(
        "new_password"
    )
    if not check_password_hash(current_user.password_hash, old_password):
        flash(_("Old password is incorrect."), "error")
        return redirect(url_for("auth.account"))
    current_user.password_hash = generate_password_hash(new_password).decode("utf-8")
    db.session.commit()
    flash(_("Password updated successfully!"), "success")
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
    flash(_(message), "success" if success else "danger")
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


# Email Confirmation Route
@auth_bp.route("/confirm_email/<token>")
def confirm_email(token):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_active = True
            db.session.commit()
            flash(_("Your email has been confirmed. Please log in."), "success")
            return redirect(url_for("auth.auth"))
        else:
            flash(_("Invalid or expired token."), "danger")
    except Exception as e:
        flash(_("Invalid or expired token."), "danger")
    return redirect(url_for("auth.auth"))


# Forgot Password Request
@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email)
            reset_link = url_for("auth.reset_password", token=token, _external=True)
            send_email(
                recipient=email,
                subject="Password Reset Request",
                body=f"Click the link to reset your password: {reset_link}",
            )
            flash(_("Password reset instructions sent to your email."), "info")
        else:
            flash(_("Email not found."), "danger")
    return render_template("forgot_password.html")


# Reset Password Route
@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, max_age=3600)
    except Exception as e:
        flash(_("Invalid or expired token."), "danger")
        return redirect(url_for("auth.auth"))

    if request.method == "POST":
        password = request.form.get("password")
        if not is_password_strong(password):
            flash(_("Password does not meet strength requirements."), "danger")
            return redirect(url_for("auth.reset_password", token=token))
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash(_("Your password has been reset. Please log in."), "success")
            return redirect(url_for("auth.auth"))
        else:
            flash(_("User not found."), "danger")
    return render_template("reset_password.html", token=token)


@auth_bp.route("/google-signin", methods=["POST"])
def google_signin():
    register = False
    token = request.json.get("token")
    try:
        # Verify the token with Google's servers
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            "169202792825-l01b3l32pb9pdug96d98po37upjn4dgp.apps.googleusercontent.com",
        )
        user_id = idinfo["sub"]
        email = idinfo["email"]
        name = idinfo.get("name", "Google User")

        # Check if user already exists in the database
        user = User.query.filter_by(email=email).first()

        if not user:
            # Create a new user if one doesn't exist
            user = User(
                username=name,
                email=email,
                google_id=user_id,
                contact_preference="google",
                contact_details="N/A",
                is_active=True,
                role="normal",
            )
            db.session.add(user)
            db.session.commit()
            register = True

        # Log the user in
        login_user(user)

        # Redirect to the details page
        if register:
            return jsonify({"success": True, "redirect_url": url_for("auth.details")})
        return jsonify({"success": True, "redirect_url": url_for("user.home_page")})
    except ValueError as e:
        return jsonify({"success": False, "error": "Invalid token"})
    except Exception as e:
        return jsonify({"success": False, "error": "An unexpected error occurred"})


@auth_bp.route("/details", methods=["GET", "POST"])
@login_required
def details():
    if request.method == "POST":
        location = request.form.get("location")
        contact_preference = request.form.get("contact_preference")
        contact_details = request.form.get("contact_details")

        if not location or not contact_preference or not contact_details:
            flash(_("All fields are required."), "danger")
            return redirect(url_for("auth.details"))

        current_user.location = location
        current_user.contact_preference = contact_preference
        current_user.contact_details = contact_details
        db.session.commit()
        flash(_("Details updated successfully."), "success")
        return redirect(url_for("user.home_page"))

    cities = CITIES_IN_ISRAEL
    return render_template("details.html", cities=cities)
