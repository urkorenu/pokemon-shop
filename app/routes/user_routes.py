from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import Card, Cart, db, User, Order
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
import boto3
from config import Config
from ..cities import CITIES_IN_ISRAEL
from ..mail_service import send_email


user_bp = Blueprint("user", __name__)


@user_bp.route("/")
def view_cards():
    # Get search and filter parameters from the request
    name_query = request.args.get("name", "").strip()
    set_name_query = request.args.get("set_name", "")
    sort_option = request.args.get("sort", "")
    location_query = request.args.get("location", "").strip()
    is_graded = request.args.get("is_graded", "")

    # Query the database with eager loading for uploader relationship
    query = Card.query.options(joinedload(Card.uploader))

    if name_query:
        query = query.filter(Card.name.ilike(f"%{name_query}%"))
    if set_name_query:
        query = query.filter(Card.set_name == set_name_query)
    if location_query:
        query = query.join(Card.uploader).filter(
            User.location.ilike(f"%{location_query}%")
        )
    if is_graded == "yes":
        query = query.filter(Card.is_graded.is_(True))
    elif is_graded == "no":
        query = query.filter(Card.is_graded.is_(False))

    # Apply sorting
    if sort_option == "price_asc":
        query = query.order_by(Card.price.asc())
    elif sort_option == "price_desc":
        query = query.order_by(Card.price.desc())
    elif sort_option == "card_number":
        query = query.order_by(Card.number.asc())

    # Execute the query
    cards = Card.query.join(User).filter(User.role == "uploader").all()


    # Get unique set names for the filter dropdown
    unique_set_names = [
        card.set_name for card in Card.query.distinct(Card.set_name).all()
    ]

    return render_template(
        "cards.html",
        cards=cards,
        unique_set_names=unique_set_names,
        cities=CITIES_IN_ISRAEL,
    )


@user_bp.route("/profile/<int:user_id>")
def profile(user_id):
    user = User.query.get_or_404(user_id)

    # Get search and filter parameters
    name_query = request.args.get("name", "").strip()
    set_name_query = request.args.get("set_name", "")
    is_graded = request.args.get("is_graded", "")
    sort_option = request.args.get("sort", "")

    # Filter user's uploaded cards
    query = Card.query.filter_by(uploader_id=user_id)

    if name_query:
        query = query.filter(Card.name.ilike(f"%{name_query}%"))
    if set_name_query:
        query = query.filter(Card.set_name == set_name_query)
    if is_graded == "yes":
        query = query.filter(Card.is_graded.is_(True))
    elif is_graded == "no":
        query = query.filter(Card.is_graded.is_(False))

    # Apply sorting
    if sort_option == "price_asc":
        query = query.order_by(Card.price.asc())
    elif sort_option == "price_desc":
        query = query.order_by(Card.price.desc())
    elif sort_option == "card_number":
        query = query.order_by(Card.number.asc())

    cards = query.all()

    # Fetch feedback and ratings for the user's completed sales
    completed_orders = (
        db.session.query(User.username, Order.feedback, Order.rating)
        .join(Order, Order.buyer_id == User.id)
        .filter(Order.seller_id == user_id, Order.status == "Completed")
        .all()
    )

    return render_template(
        "profile.html",
        user=user,
        cards=cards,
        feedback=completed_orders,
        unique_set_names=Card.query.distinct(Card.set_name).all(),
        include_location=False,  # Exclude location filter
    )


@user_bp.route("/my-cards")
@login_required
def my_cards():
    if current_user.role == "normal":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("user.view_cards"))

    # Fetch the cards uploaded by the current user
    my_cards = Card.query.filter_by(uploader_id=current_user.id).all()

    return render_template("my_cards.html", cards=my_cards)


@user_bp.route("/edit-card/<int:card_id>", methods=["GET", "POST"])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)

    if card.uploader_id != current_user.id:
        flash("You do not have permission to edit this card.", "danger")
        return redirect(url_for("user.my_cards"))

    if request.method == "POST":
        card.name = request.form.get("name", card.name)
        card.price = request.form.get("price", card.price)
        card.condition = request.form.get("condition", card.condition)
        card.amount = request.form.get("amount", card.amount)
        card.set_name = request.form.get("set_name", card.set_name)
        card.number = request.form.get("number", card.number)
        card.card_type = request.form.get("card_type", card.card_type)
        card.is_graded = request.form.get("is_graded") == "yes"
        card.grading_company = request.form.get("grading_company", card.grading_company)
        card.grade = request.form.get("grade", card.grade)

        db.session.commit()
        flash("Card updated successfully!", "success")
        return redirect(url_for("user.my_cards"))

    return render_template("edit_card.html", card=card)


@user_bp.route("/delete-card/<int:card_id>", methods=["POST"])
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)

    if card.uploader_id != current_user.id and current_user.role != "admin":
        flash("You do not have permission to delete this card.", "danger")
        return redirect(url_for("user.my_cards"))

    # Initialize S3 client
    s3 = boto3.client("s3", region_name=Config.AWS_REGION)
    bucket_name = Config.S3_BUCKET

    # Debugging: Print Config values
    print(f"AWS_REGION: {Config.AWS_REGION}, S3_BUCKET: {Config.S3_BUCKET}", flush=True)

    # Delete the image from S3 if it exists
    if card.image_url:
        try:
            # Extract the object key from the URL
            from urllib.parse import urlparse

            parsed_url = urlparse(card.image_url)
            object_key = parsed_url.path.lstrip("/")  # Remove leading slash

            # Debugging: Print extracted object_key
            print(f"Deleting S3 object key: {object_key}", flush=True)

            # Perform the S3 delete operation
            response = s3.delete_object(Bucket=bucket_name, Key=object_key)
            print(f"Delete response: {response}", flush=True)
        except Exception as e:
            print(f"Failed to delete {card.image_url} from S3: {e}", flush=True)
            flash("Failed to delete the image from S3.", "danger")

    # Delete the card from the database
    Cart.query.filter_by(card_id=card.id).delete()
    db.session.delete(card)
    db.session.commit()
    flash("Card deleted successfully!", "success")
    return redirect(url_for("user.my_cards"))


@user_bp.route("/report_card/<int:card_id>", methods=["POST"])
@login_required
def report_card(card_id):
    card = Card.query.get_or_404(card_id)
    reason = request.form.get("reason")
    details = request.form.get("details", "")

    # Send an email to the admin (replace with your mail logic)
    send_email(
        recipient=Config.ADMIN_MAIL,
        subject=f"Report: Card #{card.id} - {reason}",
        body=f"Card Name: {card.name}\nReason: {reason}\nDetails: {details}\nUser: {current_user.username}",
    )

    flash("Report submitted successfully. Admin will review it.", "success")
    return redirect(url_for("user.view_cards"))


@user_bp.route("/cart", methods=["POST"])
@login_required
def add_to_cart():
    card_id = request.form.get("card_id")
    card = Card.query.get_or_404(card_id)

    # Check if the card is already in the cart
    cart_item = Cart.query.filter_by(user_id=current_user.id, card_id=card.id).first()

    if cart_item:
        # Check if adding more exceeds the available amount
        if cart_item.quantity < card.amount:
            cart_item.quantity += 1
            db.session.commit()
            flash(f"{card.name} has been added to your cart.", "success")
        else:
            flash(
                f"You cannot add more {card.name} cards. Only {card.amount} available.",
                "danger",
            )
    else:
        if card.amount > 0:
            cart_item = Cart(user_id=current_user.id, card_id=card.id, quantity=1)
            db.session.add(cart_item)
            db.session.commit()
            flash(f"{card.name} has been added to your cart.", "success")
        else:
            flash(f"{card.name} is out of stock.", "danger")

    return redirect(url_for("user.view_cards"))


@user_bp.route("/cart")
@login_required
def view_cart():
    user_id = current_user.id
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    # Group items by seller
    grouped_cart = {}
    for item in cart_items:
        seller_id = item.card.uploader_id
        if seller_id not in grouped_cart:
            grouped_cart[seller_id] = []
        grouped_cart[seller_id].append(item)

    total_price = sum(item.card.price * item.quantity for item in cart_items)
    return render_template(
        "cart.html", grouped_cart=grouped_cart, total_price=total_price
    )


@user_bp.route("/contact", methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message_content = request.form.get("message")

        if not (name and email and message_content):
            flash("All fields are required!", "danger")
            return redirect(url_for("user.contact_us"))

        # Send email to the admin
        msg = f"""
        You have received a new message via Contact Us Form:

        Name: {name}
        Email: {email}

        Message:
        {message_content}
        """

        try:
            send_email(
                recipient=Config.ADMIN_MAIL,
                subject=f"New Contact Us Message from {name}",
                body=msg,
            )
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            flash("Failed to send message. Please try again later.", "danger")
            print(str(e), flush=True)

        return redirect(url_for("user.contact_us"))

    return render_template("contact.html")

@user_bp.route('/about', methods=["GET"])
def about_us():
    return render_template("about.html")
