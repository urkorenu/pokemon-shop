from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from ..models import User, db

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
        user = User(username=username, email=email)
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

