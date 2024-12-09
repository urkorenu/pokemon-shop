from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..models import Card, Cart, db, User, Order
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import or_
from flask_sqlalchemy import Pagination
import boto3
from config import Config
from urllib.parse import urlparse
from ..cities import CITIES_IN_ISRAEL
from ..mail_service import send_email


user_bp = Blueprint("user", __name__)


@user_bp.route("/")
def view_cards():
    # Get the page number from request args (default to page 1)
    page = request.args.get("page", 1, type=int)

    # Call filter_cards with pagination
    paginated_cards, unique_set_names = filter_cards(page=page)

    return render_template(
        "cards.html",
        cards=paginated_cards.items,
        unique_set_names=unique_set_names,
        pagination=paginated_cards,
        cities=CITIES_IN_ISRAEL,
        show_sold_checkbox=False,
    )


@user_bp.route("/set-language", methods=["POST"])
def set_language():
    lang = request.form.get("lang")
    if lang in ["en", "he"]:
        session["lang"] = lang
    else:
        flash("Invalid language selection.", "danger")

    referrer = request.referrer
    if referrer:
        referrer = referrer.replace('\\', '')
        parsed_referrer = urlparse(referrer)
        if not parsed_referrer.netloc and not parsed_referrer.scheme:
            return redirect(referrer)
    return redirect(url_for("user.view_cards"))


@user_bp.route("/report_user/<int:user_id>", methods=["POST"])
@login_required
def report_user(user_id):
    user = User.query.get_or_404(user_id)

    reason = request.form.get("reason")
    details = request.form.get("details")

    if not reason:
        flash("Please provide a reason for the report.", "danger")
        return redirect(url_for("user.profile", user_id=user_id))

    # Example of storing or sending the report (adjust as needed)
    send_email(
        recipient=Config.ADMIN_MAIL,
        subject=f"User Report - {user.username}",
        body=(
            f"User '{current_user.username}' reported the user '{user.username}'.\n"
            f"Reason: {reason}\nDetails: {details if details else 'No additional details provided.'}"
        ),
    )

    flash("User has been reported successfully. Thank you!", "success")
    return redirect(url_for("user.profile", user_id=user_id))


@user_bp.route("/profile/<int:user_id>")
def profile(user_id):
    user = User.query.get_or_404(user_id)

    # Filter cards
    show_sold = request.args.get("show_sold") == "on"
    page = request.args.get("page", 1, type=int)

    paginated_cards, unique_set_names = filter_cards(
        user_id=user_id, show_sold=show_sold, page=page
    )

    # Fetch feedback for the user's completed sales
    completed_orders = (
        db.session.query(User.username, Order.feedback, Order.rating)
        .join(Order, Order.buyer_id == User.id)
        .filter(Order.seller_id == user_id, Order.status == "Completed")
        .all()
    )

    return render_template(
        "profile.html",
        user=user,
        cards=paginated_cards.items,
        feedback=completed_orders,
        unique_set_names=unique_set_names,
        pagination=paginated_cards,
        show_sold_checkbox=True,
    )


@user_bp.route("/my-cards")
@login_required
def my_cards():
    if current_user.role == "normal":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("user.view_cards"))

    # Fetch available and sold cards separately
    available_cards = (
        Card.query.filter_by(uploader_id=current_user.id).filter(Card.amount > 0).all()
    )
    sold_cards = (
        Card.query.filter_by(uploader_id=current_user.id).filter(Card.amount == 0).all()
    )

    return render_template(
        "my_cards.html", available_cards=available_cards, sold_cards=sold_cards
    )


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

    # Ensure only admins can delete other users' cards, not their own
    if current_user.role != "admin":
        if card.uploader_id != current_user.id:
            flash("You do not have permission to delete this card.", "danger")
            return redirect(url_for("user.my_cards"))

    # Initialize S3 client
    s3 = boto3.client("s3", region_name=Config.AWS_REGION)
    bucket_name = Config.S3_BUCKET

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

    # Notify the seller via email if deleted by an admin and uploader is not the current user
    if current_user.role == "admin" and card.uploader_id != current_user.id:
        uploader = User.query.get(card.uploader_id)
        if uploader and uploader.email:  # Ensure the uploader exists and has an email
            email_subject = "Your Card Has Been Deleted"
            email_body = (
                f"Hello {uploader.username},\n\n"
                f"Your card '{card.name}' (Card Number: {card.number}, Set: {card.set_name}) "
                f"has been deleted by an administrator.\n\n"
                "If you have any questions, please contact support.\n\n"
                "Best regards,\nThe Pika-Card Team"
            )
            try:
                send_email(
                    recipient=uploader.email,
                    subject=email_subject,
                    body=email_body,
                )
            except Exception as e:
                print(f"Failed to send email notification: {e}", flush=True)

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


@user_bp.route("/about", methods=["GET"])
def about_us():
    return render_template("about.html")


from sqlalchemy.orm import aliased


def filter_cards(base_query=None, user_id=None, show_sold=False, page=1, per_page=12):
    """
    Reusable function to filter cards based on search and filter parameters.

    :param base_query: Optional base query to filter on (defaults to all cards).
    :param user_id: Optional user_id to filter cards by uploader.
    :param show_sold: Boolean indicating whether to include sold cards (amount == 0).
    :return: Filtered query and unique set names.
    """
    # Use an alias for User table to avoid duplicate joins
    uploader_alias = aliased(User)

    if base_query is None:
        base_query = Card.query.options(joinedload(Card.uploader)).join(uploader_alias)

    # Filters
    name_query = request.args.get("name", "").strip()
    set_name_query = request.args.get("set_name", "")
    location_query = request.args.get("location", "").strip()
    is_graded = request.args.get("is_graded", "")
    sort_option = request.args.get("sort", "")
    show_sold = request.args.get("show_sold", "off") == "on" or show_sold

    # Base filters
    query = base_query.filter(
        or_(uploader_alias.role == "uploader", uploader_alias.role == "admin")
    )

    if user_id:
        query = query.filter(Card.uploader_id == user_id)

    # Only exclude sold cards if 'show_sold' is False
    if not show_sold:
        query = query.filter(Card.amount > 0)

    if name_query:
        query = query.filter(Card.name.ilike(f"%{name_query}%"))
    if set_name_query:
        query = query.filter(Card.set_name == set_name_query)
    if location_query:
        query = query.filter(uploader_alias.location.ilike(f"%{location_query}%"))
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

    # Paginate the query
    paginated_cards = query.paginate(page=page, per_page=per_page, error_out=False)

    # Extract unique set names for the current page
    unique_set_names = {card.set_name for card in paginated_cards.items}

    return paginated_cards, sorted(unique_set_names)
