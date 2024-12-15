from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..models import Card, db
from flask_login import current_user
import requests
from app.upload_to_s3 import upload_to_s3
from config import Config
from app import cache
from app.utils import roles_required

# Create a Blueprint for the seller routes
seller_bp = Blueprint("seller", __name__)

API_KEY = Config.API_KEY
BASE_URL = "https://api.pokemontcg.io/v2"


@seller_bp.route("/upload", methods=["GET", "POST"])
@roles_required("admin", "uploader")
def upload_card():
    """Upload a new card."""

    @cache.cached(timeout=86400, key_prefix="pokemon_sets")
    def get_pokemon_sets():
        """Fetches Pokémon sets from the API and caches the result for 24 hours."""
        try:
            response = requests.get(
                f"{BASE_URL}/sets", headers={"X-Api-Key": API_KEY}, timeout=10
            )
            response.raise_for_status()
            return [
                {"name": s["name"], "max_card_number": s.get("printedTotal", 0)}
                for s in response.json().get("data", [])
                if s.get("printedTotal")
            ]
        except requests.RequestException as e:
            print(f"Error fetching sets: {e}", flush=True)
            return []

    @cache.cached(timeout=86400, key_prefix="japanese_sets")
    def get_japanese_sets():
        """Fetches Japanese sets."""
        try:
            response = requests.get("https://www.jpn-cards.com/v2/set", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching Japanese sets: {e}", flush=True)
            return []

    sets = get_pokemon_sets() if request.method == "GET" else []

    if request.method == "POST":
        # Collect form data
        name = request.form.get("name")
        follow_tcg = request.form.get("follow_tcg") == "on"
        price = float(request.form.get("price") or 0.0)
        condition = request.form.get("condition")
        set_name = request.form.get("set_name")
        number = request.form.get("number")
        card_type = request.form.get("card_type")
        is_graded = request.form.get("is_graded") == "on"
        grade = request.form.get("grade") if is_graded else None
        grading_company = request.form.get("grading_company") if is_graded else None
        language = request.form.get("language")
        file = request.files.get("image")

        if language == "en":
            try:
                query = f'set.name:"{set_name}" number:"{number}"'
                response = requests.get(
                    f"{BASE_URL}/cards",
                    params={"q": query},
                    headers={"X-Api-Key": API_KEY},
                )
                response.raise_for_status()
                card_data = response.json().get("data", [])

                if not card_data:
                    flash(
                        "No card found. Please verify the set name and card number.",
                        "danger",
                    )
                    return render_template("upload.html", sets=sets)

                filtered_cards = [
                    card
                    for card in card_data
                    if card.get("set", {}).get("name") == set_name
                    and card.get("number") == number
                ]
                card_details = filtered_cards[0]
                api_card_name = card_details["name"]

                if name.lower() not in api_card_name.lower():
                    flash(
                        f"Card name does not match. Expected: {api_card_name}", "danger"
                    )
                    return render_template("upload.html", sets=sets)

                tcg_price_data = card_details.get("tcgplayer", {}).get("prices", {})
                selected_price = tcg_price_data.get(card_type, {}).get("market", 0.0)
                if follow_tcg:
                    price = round(selected_price * 3.56 + 0.5, 0)
                    condition = "NM"

            except requests.RequestException as e:
                print(f"Error fetching card details: {e}", flush=True)
                flash("Failed to fetch card details. Please try again later.", "danger")
                return render_template("upload.html", sets=sets)

        elif language == "jp":
            try:
                japanese_sets = get_japanese_sets()
                set_id = next(
                    (s["id"] for s in japanese_sets if s["name"] == set_name), None
                )
                if not set_id:
                    flash("Set not found. Please verify the set name.", "danger")
                    return render_template("upload.html", sets=sets)

                response = requests.get(
                    f"https://www.jpn-cards.com/v2/card/set_id={set_id}", timeout=10
                )
                response.raise_for_status()
                cards = response.json().get("data", [])

                card_data = next(
                    (card for card in cards if str(card["sequenceNumber"]) == number),
                    None,
                )
                if not card_data:
                    flash("No card found. Please verify the card number.", "danger")
                    return render_template("upload.html", sets=sets)

                name = card_data["name"]
                card_type = f"{card_type} - jpn"

            except requests.RequestException as e:
                print(f"Error fetching Japanese card details: {e}", flush=True)
                flash(
                    "Failed to fetch Japanese card details. Please try again later.",
                    "danger",
                )
                return render_template("upload.html", sets=sets)
        else:
            flash("Invalid language selection.", "danger")
            return render_template("upload.html", sets=sets)

        image_url = upload_to_s3(file, bucket_name=Config.S3_BUCKET) if file else None
        card = Card(
            name=name,
            price=price,
            follow_tcg=follow_tcg,
            tcg_price=selected_price if language == "en" else 0,
            condition=condition,
            amount=1,
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
        return redirect(url_for("seller.upload_card"))

    return render_template("upload.html", sets=sets)


@seller_bp.route("/en-sets", methods=["GET"])
@cache.cached(timeout=86400, key_prefix="english_pokemon_sets")
def get_english_sets():
    """Fetch English Pokémon sets."""
    try:
        response = requests.get(
            f"{BASE_URL}/sets", headers={"X-Api-Key": API_KEY}, timeout=10
        )
        response.raise_for_status()
        sets = [{"name": s["name"]} for s in response.json().get("data", [])]
        return jsonify(sets)
    except requests.RequestException as e:
        print(f"Error fetching English sets: {e}", flush=True)
        return jsonify([]), 500


@seller_bp.route("/jp-sets", methods=["GET"])
@cache.cached(timeout=86400, key_prefix="japanese_pokemon_sets")
def get_japanese_sets():
    """Fetch Japanese Pokémon sets."""
    try:
        response = requests.get("https://www.jpn-cards.com/v2/set", timeout=10)
        response.raise_for_status()
        sets = [{"name": s["name"]} for s in response.json()]
        return jsonify(sets)
    except requests.RequestException as e:
        print(f"Error fetching Japanese sets: {e}", flush=True)
        return jsonify([]), 500


@seller_bp.route("/card-details", methods=["GET"])
@roles_required("admin", "uploader")
@cache.cached(timeout=86400, query_string=True)
def get_card_details():
    """Get details of a specific card."""
    language = request.args.get("language", "en")
    set_name = request.args.get("set_name")
    number = request.args.get("number")

    if not set_name or not number:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        if language == "en":
            query = f'set.name:"{set_name}" number:"{number}"'
            response = requests.get(
                f"{BASE_URL}/cards", params={"q": query}, headers={"X-Api-Key": API_KEY}
            )
            response.raise_for_status()
            card_data = response.json().get("data", [])

            if not card_data:
                return jsonify({"error": "No card found"}), 404

            filtered_cards = [
                card
                for card in card_data
                if card.get("set", {}).get("name") == set_name
                and card.get("number") == number
            ]
            if not filtered_cards:
                return jsonify({"error": "No exact match found"}), 404

            card = filtered_cards[0]
            card_name = card["name"]
            card_types = list(card.get("tcgplayer", {}).get("prices", {}).keys())

            return jsonify(
                {
                    "name": card_name,
                    "types": card_types,
                    "prices": card.get("tcgplayer", {}).get("prices", {}),
                }
            )

        elif language == "jp":

            def get_set_id_by_name(sets_data, set_name):
                """Extract the set ID by matching the set name."""
                for set_entry in sets_data:
                    if set_entry.get("name") == set_name:
                        return set_entry.get("id")
                return None

            response = requests.get("https://www.jpn-cards.com/v2/set", timeout=10)
            response.raise_for_status()
            sets_data = response.json()

            set_id = get_set_id_by_name(sets_data, set_name)
            if not set_id:
                return jsonify({"error": "Set name not found"}), 404

            set_response = requests.get(
                f"https://www.jpn-cards.com/v2/card/set_id={set_id}"
            )
            set_response.raise_for_status()
            cards_data = set_response.json().get("data", [])

            card_data = next(
                (card for card in cards_data if str(card["sequenceNumber"]) == number),
                None,
            )
            if not card_data:
                return jsonify({"error": "No card found"}), 404

            return jsonify(
                {
                    "name": card_data["name"],
                    "types": [
                        "Normal",
                        "Holofoil",
                        "Reverseholofoil",
                        "1steditionholofoil",
                        "1stedition",
                    ],
                    "prices": {},
                }
            )

        else:
            return jsonify({"error": "Invalid language parameter"}), 400

    except requests.RequestException as e:
        print(f"Error fetching card details: {e}", flush=True)
        return jsonify({"error": "Failed to fetch card details"}), 500
