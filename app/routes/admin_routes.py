from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..models import Card, db, User
from flask_login import current_user
import requests
from app.upload_to_s3 import upload_to_s3
import boto3
from config import Config
from app import cache
from app.utils import roles_required

admin_bp = Blueprint("admin", __name__)

API_KEY = Config.API_KEY
BASE_URL = "https://api.pokemontcg.io/v2"


@admin_bp.route("/upload", methods=["GET", "POST"])
@roles_required("admin", "uploader")
def upload_card():
    @cache.cached(timeout=3600, key_prefix="pokemon_sets")
    def get_pokemon_sets():
        """Fetch Pokémon TCG sets from the API."""
        response = requests.get(f"{BASE_URL}/sets", headers={"X-Api-Key": API_KEY})
        response.raise_for_status()
        return [
            {"name": s["name"], "max_card_number": s.get("printedTotal", 0)}
            for s in response.json().get("data", [])
            if s.get("printedTotal")
        ]

    try:
        sets = get_pokemon_sets()
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
        card_type = request.form.get("card_type")
        is_graded = request.form.get("is_graded") == "on"
        grade = request.form.get("grade") if is_graded else None
        grading_company = request.form.get("grading_company") if is_graded else None

        try:
            query = f'set.name:"{set_name}" number:"{number}"'
            response = requests.get(
                f"{BASE_URL}/cards", params={"q": query}, headers={"X-Api-Key": API_KEY}
            )
            response.raise_for_status()
            card_data = response.json().get("data", [])

            if not card_data:
                flash(
                    "No card found. Please verify the set name and card number.",
                    "danger",
                )
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

        # Image upload to S3
        file = request.files.get("image")
        image_url = None
        if file:
            image_url = upload_to_s3(
                file,
                bucket_name=Config.S3_BUCKET,
            )

        # Save card to database
        card = Card(
            name=name,
            price=price,
            tcg_price=selected_price,
            condition=condition,
            amount=amount,
            set_name=set_name,
            number=number,
            image_url=image_url,
            is_graded=is_graded,
            grade=grade,
            grading_company=grading_company,
            card_type=card_type,
            uploader_id=current_user.id,
        )
        db.session.add(card)
        db.session.commit()
        flash("Card uploaded successfully!", "success")
        return redirect(url_for("admin.upload_card"))

    return render_template("upload.html", sets=sets)


@admin_bp.route("/card-details", methods=["GET"])
@cache.cached(timeout=600, query_string=True)
def get_card_details():
    """Fetch card details for the selected set and number."""
    set_name = request.args.get("set_name")
    number = request.args.get("number")

    if not set_name or not number:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        query = f'set.name:"{set_name}" number:"{number}"'
        response = requests.get(
            f"{BASE_URL}/cards", params={"q": query}, headers={"X-Api-Key": API_KEY}
        )
        response.raise_for_status()
        card_data = response.json().get("data", [])

        if not card_data:
            return jsonify({"error": "No card found"}), 404

        card = card_data[0]
        card_name = card["name"]
        card_types = list(card.get("tcgplayer", {}).get("prices", {}).keys())

        return jsonify({"name": card_name, "types": card_types})

    except requests.RequestException as e:
        print(f"Error fetching card details: {e}", flush=True)
        return jsonify({"error": "Failed to fetch card details"}), 500


@admin_bp.route("/reset_cards", methods=["POST"])
@roles_required("admin")
def reset_cards():
    try:
        # Fetch all image URLs from the Card table
        cards = Card.query.all()
        image_urls = [card.image_url for card in cards if card.image_url]

        # Initialize S3 client
        s3 = boto3.client("s3", region_name=Config.AWS_REGION)
        bucket_name = Config.S3_BUCKET

        # Delete images from S3
        for url in image_urls:
            try:
                # Extract the object key from the URL
                object_key = url.split(f"{bucket_name}/")[-1]
                s3.delete_object(Bucket=bucket_name, Key=object_key)
                print(f"Deleted {object_key} from S3.", flush=True)
            except Exception as e:
                print(f"Failed to delete {url} from S3: {e}", flush=True)

        # Delete all records in the Card table
        Card.query.delete()
        db.session.commit()
        return {"message": "All cards and associated images have been deleted."}, 200

    except Exception as e:
        print(f"Error resetting cards: {e}", flush=True)
        return {"message": "Failed to reset cards."}, 500


@admin_bp.route("/users", methods=["GET", "POST"])
@roles_required("admin")
def manage_users():
    users = User.query.filter(User.role != "admin").all()  # Exclude admins

    if request.method == "POST":
        user_id = request.form.get("user_id")  # Ensure user_id is correctly submitted
        new_role = request.form.get(
            f"role_{user_id}"
        )  # Fetch the role for the specific user

        if not user_id or not new_role:
            flash("Invalid user or role data.", "error")
            return redirect(url_for("admin.manage_users"))

        if new_role not in ["normal", "uploader"]:
            flash("Invalid role.", "error")
            return redirect(url_for("admin.manage_users"))

        user = User.query.get(user_id)
        if user:
            user.role = new_role
            db.session.commit()
            flash(f"User {user.username} promoted to {new_role}.", "success")
        else:
            flash("User not found.", "error")

    return render_template("manage_users.html", users=users)
