from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Card, db
from flask_login import login_required
import requests
from app.upload_to_s3 import upload_to_s3

admin_bp = Blueprint("admin", __name__)

API_KEY = "d12c4b42-2505-47cd-b85a-48b96e76859f"
BASE_URL = "https://api.pokemontcg.io/v2"

@admin_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_card():
    try:
        # Fetch all sets
        response = requests.get(f"{BASE_URL}/sets", headers={"X-Api-Key": API_KEY})
        response.raise_for_status()
        sets = [{"name": s["name"], "max_card_number": s.get("printedTotal", 0)} for s in response.json().get("data", []) if s.get("printedTotal")]
    except requests.RequestException as e:
        sets = []
        print(f"Error fetching sets: {e}", flush=True)
        flash("Failed to fetch Pokémon TCG sets. Please try again later.", "danger")

    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        price = request.form.get("price")
        condition = request.form.get("condition")
        amount = request.form.get("amount")
        set_name = request.form.get("set_name")
        number = request.form.get("number")
        image_url = request.form.get("image_url")
        card_type = request.form.get("card_type")  
        is_graded = request.form.get("is_graded") == "on"
        grade = request.form.get("grade") if is_graded else None
        grading_company = request.form.get("grading_company") if is_graded else None

        try:
            query = f'set.name:"{set_name}" number:"{number}"'
            response = requests.get(f"{BASE_URL}/cards", params={"q": query}, headers={"X-Api-Key": API_KEY})
            response.raise_for_status()
            card_data = response.json().get("data", [])

            if not card_data:
                flash("No card found. Please verify the set name and card number.", "danger")
                return render_template("upload.html", sets=sets)

            card_details = card_data[0]
            api_card_name = card_details["name"]

            # Verify card name matches
            if name.lower() not in api_card_name.lower():
                flash(f"Card name does not match. Expected: {api_card_name}", "danger")
                return render_template("upload.html", sets=sets)

            # Extract TCG prices
            tcg_price_data = card_details.get("tcgplayer", {}).get("prices", {})
            selected_price = tcg_price_data.get(card_type, {}).get("market", 0.0)

        except requests.RequestException as e:
            print(f"Error fetching card details: {e}", flush=True)
            flash("Failed to fetch card details. Please try again later.", "danger")
            return render_template("upload.html", sets=sets)

        file = request.files.get("image")
        if file:
            image_url = upload_to_s3(file, bucket_name="your-s3-bucket", object_name=file.filename)
        
        # Save card to database
        card = Card(
            name=name,
            price=price,
            condition=condition,
            amount=amount,
            set_name=set_name,
            number=number,
            image_url=image_url,
            is_graded=is_graded,
            grade=grade,
            grading_company=grading_company,
            tcg_price=selected_price, 
            card_type=card_type
        )
        db.session.add(card)
        db.session.commit()
        flash("Card uploaded successfully!", "success")
        return redirect(url_for("admin.upload_card"))

    return render_template("upload.html", sets=sets)

@admin_bp.route('/reset_cards', methods=['POST'])
@login_required
def reset_cards():
    try:
        Card.query.delete()  # Deletes all records in the Card table
        db.session.commit()
        return {"message": "All cards have been reset."}, 200
    except Exception as e:
        print(f"Error resetting cards: {e}")
        return {"message": "Failed to reset cards."}, 500

