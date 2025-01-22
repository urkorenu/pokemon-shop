from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from ..models import Card, db, Order, order_cards, User
from flask_login import current_user, login_required
from flask_babel import _
import requests
from app.upload_to_s3 import upload_to_s3
from config import Config
from app import cache
import os

# Create a Blueprint for the seller routes
seller_bp = Blueprint("seller", __name__)
API_KEY = Config.API_KEY
BASE_URL = "https://api.pokemontcg.io/v2"


@seller_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_card():
    """
    Upload a new card.

    Returns:
        Rendered template for the upload page or a redirect to the upload page with a flash message.
    """

    @cache.cached(timeout=86400, key_prefix="pokemon_sets")
    def get_pokemon_sets():
        """
        Fetch Pokémon sets from the API and cache the result.

        Returns:
            list: List of Pokémon sets with their names and max card numbers.
        """
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
        """
        Fetch Japanese sets from the API and cache the result.

        Returns:
            list: List of Japanese sets.
        """
        try:
            response = requests.get("https://www.jpn-cards.com/v2/set", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching Japanese sets: {e}", flush=True)
            return []

    if current_user.role == "normal":
        return render_template("notyet_upload.html")

    sets = get_pokemon_sets() if request.method == "GET" else []

    if request.method == "POST":
        name, follow_tcg, price = (
            request.form.get("name"),
            request.form.get("follow_tcg") == "on",
            float(request.form.get("price") or 0.0),
        )
        condition, set_name, number = (
            request.form.get("condition"),
            request.form.get("set_name"),
            request.form.get("number"),
        )
        card_type, is_graded = (
            request.form.get("card_type"),
            request.form.get("is_graded") == "on",
        )
        grade, grading_company = request.form.get("grade") if is_graded else None, (
            request.form.get("grading_company") if is_graded else None
        )
        language, file, back_file = (
            request.form.get("language"),
            request.files.get("image"),
            request.files.get("back_image"),
        )

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
                        _("No card found. Please verify the set name and card number."),
                        "danger",
                    )
                    return render_template("upload.html", sets=sets)

                filtered_cards = [
                    card
                    for card in card_data
                    if card.get("set", {}).get("name", "").strip().lower()
                    == set_name.strip().lower()
                    and str(card.get("number", "")).strip().lower()
                    == str(number).strip().lower()
                ]

                if not filtered_cards:
                    return (
                        jsonify(
                            {"error": "No card matches the given set name and number."}
                        ),
                        404,
                    )

                card_details = filtered_cards[0]
                api_card_name = card_details["name"]

                if name.lower() not in api_card_name.lower():
                    flash(
                        (f"Card name does not match. Expected: {api_card_name}"), "danger"
                    )
                    return render_template("upload.html", sets=sets)

                tcg_price_data = card_details.get("tcgplayer", {}).get("prices", {})
                selected_price = tcg_price_data.get(card_type, {}).get("market", 0.0)
                if follow_tcg:
                    price = round(selected_price * 3.65 + 0.5, 0)
                    price = max(price, 1)
                    condition = "NM"

            except requests.RequestException as e:
                print(f"Error fetching card details: {e}", flush=True)
                flash(_("Failed to fetch card details. Please try again later."), "danger")
                return render_template("upload.html", sets=sets)

        elif language == "jp":
            try:
                japanese_sets = get_japanese_sets()
                set_id = next(
                    (s["id"] for s in japanese_sets if s["name"] == set_name), None
                )
                if not set_id:
                    flash(_("Set not found. Please verify the set name."), "danger")
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
                    flash(_("No card found. Please verify the card number."), "danger")
                    return render_template("upload.html", sets=sets)

                name = card_data["name"]
                card_type = f"{card_type} - jpn"

            except requests.RequestException as e:
                print(f"Error fetching Japanese card details: {e}", flush=True)
                flash(
                    _("Failed to fetch Japanese card details. Please try again later."),
                    "danger",
                )
                return render_template("upload.html", sets=sets)
        else:
            flash(_("Invalid language selection."), "danger")
            return render_template("upload.html", sets=sets)

        image_url = upload_to_s3(file, bucket_name=Config.S3_BUCKET) if file else None
        back_image_url = (
            upload_to_s3(back_file, bucket_name=Config.S3_BUCKET) if back_file else None
        )

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
            back_image_url=back_image_url,
        )
        db.session.add(card)
        db.session.commit()
        flash(_("Card uploaded successfully!"), "success")
        return redirect(url_for("seller.upload_card"))

    return render_template("upload.html", sets=sets)


@seller_bp.route("/en-sets", methods=["GET"])
@cache.cached(timeout=86400, key_prefix="english_pokemon_sets")
def get_english_sets():
    """
    Fetch English Pokémon sets.

    Returns:
        JSON response with the list of English Pokémon sets.
    """
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
    """
    Fetch Japanese Pokémon sets.

    Returns:
        JSON response with the list of Japanese Pokémon sets.
    """
    try:
        response = requests.get("https://www.jpn-cards.com/v2/set", timeout=10)
        response.raise_for_status()
        sets = [{"name": s["name"]} for s in response.json()]
        return jsonify(sets)
    except requests.RequestException as e:
        print(f"Error fetching Japanese sets: {e}", flush=True)
        return jsonify([]), 500


@seller_bp.route("/card-details", methods=["GET"])
@cache.cached(timeout=86400, query_string=True)
def get_card_details():
    """
    Get details of a specific card.

    Returns:
        JSON response with the card details or an error message.
    """
    if not current_user.is_authenticated or current_user.role == "normal":
        # Check for a special token to allow programmatic access
        bypass_token = request.headers.get("X-Bypass-Token")
        if bypass_token != os.getenv(
            "BYPASS_TOKEN"
        ):  # Store token in environment variables
            return jsonify({"error": "Unauthorized access"}), 401
        else:
            print("Bypass token accepted", flush=True)

    print(f"Parameters: {request.args}", flush=True)

    language, set_name, number = (
        request.args.get("language", "en"),
        request.args.get("set_name"),
        request.args.get("number"),
    )

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
                if card.get("set", {}).get("name").strip().lower()
                == set_name.strip().lower()
                and str(card.get("number", "")).strip().lower()
                == str(number).strip().lower()
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
                """
                Get the set ID by set name.

                Args:
                    sets_data (list): List of sets data.
                    set_name (str): Name of the set.

                Returns:
                    int: Set ID.
                """
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


@seller_bp.route("/seller-dashboard")
@login_required
def seller_dashboard():
    """
    Seller Dashboard with pending orders, search, and summary statistics.

    Returns:
        Rendered template for the seller dashboard with orders and statistics.
    """
    if current_user.role not in ["uploader", "admin"]:
        flash(_("You do not have permission to access this page."), "danger")
        return redirect(url_for("user.view_cards"))

    search_query = request.args.get("search", "").strip()
    query = Order.query.filter_by(seller_id=current_user.id, status="Pending")

    if search_query:
        query = query.join(Order.buyer).filter(
            User.username.ilike(f"%{search_query}%")
            | Order.cards.any(Card.name.ilike(f"%{search_query}%"))
        )

    pending_orders = query.all()
    orders_with_details = []
    for order in pending_orders:
        cards = (
            db.session.query(Card)
            .join(order_cards, Card.id == order_cards.c.card_id)
            .filter(order_cards.c.order_id == order.id)
            .all()
        )
        total_price = sum(card.price for card in cards)
        orders_with_details.append(
            {
                "id": order.id,
                "buyer": order.buyer,
                "created_at": order.created_at,
                "cards": cards,
                "total_price": total_price,
            }
        )

    completed_orders_query = Order.query.filter_by(
        seller_id=current_user.id, status="Confirmed"
    )
    completed_orders = []
    for order in completed_orders_query:
        cards = (
            db.session.query(Card)
            .join(order_cards)
            .filter(order_cards.c.order_id == order.id)
            .all()
        )
        total_price = sum(card.price for card in cards)
        completed_orders.append(
            {
                "id": order.id,
                "buyer": order.buyer,
                "created_at": order.created_at,
                "cards": cards,
                "total_price": total_price,
            }
        )

    stats = {
        "pending_orders": len(pending_orders),
        "total_cards": Card.query.filter_by(uploader_id=current_user.id).count(),
        "sold_cards": Card.query.filter(
            Card.uploader_id == current_user.id, Card.amount == 0
        ).count(),
        "total_revenue": sum(order["total_price"] for order in completed_orders),
    }

    return render_template(
        "seller_dashboard.html",
        orders=orders_with_details,
        completed_orders=completed_orders,
        stats=stats,
    )
