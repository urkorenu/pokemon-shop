from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User, db, Order, Cart
from flask_bcrypt import generate_password_hash, check_password_hash
from ..cities import CITIES_IN_ISRAEL

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/sign-in", methods=["GET", "POST"])
def auth():
    form_type = request.form.get("form_type")

    if request.method == "POST":
        if form_type == "login":
            email = request.form.get("email")
            password = request.form.get("password")
            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for("user.view_cards"))

            flash("Invalid email or password.", "error")

        elif form_type == "register":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            location = request.form.get("location")
            contact_preference = request.form.get("contact_preference")
            contact_details = request.form.get("contact_details")

            if not username or not email or not password or not location:
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
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("auth.auth"))
            except Exception as e:
                db.session.rollback()
                flash(
                    "An error occurred during registration. Please try again.", "error"
                )
                print(f"Error during registration: {e}")

    return render_template("auth.html", cities=CITIES_IN_ISRAEL)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.auth"))


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        # Handle profile updates
        username = request.form.get("username")
        email = request.form.get("email")

        if username:
            current_user.username = username
        if email:
            current_user.email = email

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("auth.account"))

    # Get user's order history
    orders = Order.query.filter_by(buyer_id=current_user.id).all()

    return render_template("account.html", orders=orders)


@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")

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
    # Delete all cart items for the user
    Cart.query.filter_by(user_id=current_user.id).delete()

    # Now delete the user
    user = User.query.get_or_404(current_user.id)
    db.session.delete(user)
    db.session.commit()

    logout_user()
    flash("Your account and all associated data have been deleted.", "success")
    return redirect(url_for("auth.login"))
