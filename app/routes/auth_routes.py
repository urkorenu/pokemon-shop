from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User, db, Order, Cart
from flask_bcrypt import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate form inputs
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("auth.register"))

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("auth.login"))

        # Create the new user
        user = User(username=username, email=email, role="normal")
        user.set_password(password)  # Hash and set the password
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        # Check user existence and password
        if user and user.check_password(password):
            login_user(user)  # Log in the user
            flash("Login successful!", "success")
            return redirect(url_for("user.view_cards"))

        flash("Invalid email or password.", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


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
    orders = Order.query.filter_by(user_id=current_user.id).all()

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


