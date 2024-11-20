from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Card, db
from flask_login import login_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_card():
    if request.method == "POST":
        # Extract data from the form
        name = request.form.get("name")
        price = request.form.get("price")
        condition = request.form.get("condition")
        amount = request.form.get("amount")
        set_name = request.form.get("set_name")
        number = request.form.get("number")
        image_url = request.form.get("image_url")

        # Validate input
        if not name or not price or not condition or not amount or not set_name or not number:
            flash("All fields except image URL are required.", "error")
            return redirect(url_for("admin.upload_card"))

        try:
            # Create a new card and add it to the database
            card = Card(
                name=name,
                price=float(price),
                condition=condition,
                amount=int(amount),
                set_name=set_name,
                number=number,
                image_url=image_url,
            )
            db.session.add(card)
            db.session.commit()
            flash("Card successfully uploaded!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")

        # Redirect to the upload page after successful submission
        return redirect(url_for("admin.upload_card"))

    # Render the upload form
    return render_template("upload.html")

