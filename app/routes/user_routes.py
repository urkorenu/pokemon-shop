from sqlalchemy.sql import func, case
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..models import Card, Cart, db, User, Order
from flask_login import login_required, current_user
from flask_babel import _
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import or_
import boto3
from config import Config
from urllib.parse import urlparse
from ..cities import CITIES_IN_ISRAEL
from ..mail_service import send_email
from app import cache

# Create a Blueprint for user routes
user_bp = Blueprint("user", __name__)


@user_bp.route("/")
def view_cards():
    """
    View all cards with pagination.

    Returns:
        Rendered template for the cards page with paginated card data.
    """
    page = request.args.get("page", 1, type=int)
    paginated_cards, unique_set_names, stats = filter_cards(page=page)
    return render_template(
        "cards.html",
        cards=paginated_cards.items,
        unique_set_names=unique_set_names,
        pagination=paginated_cards,
        cities=CITIES_IN_ISRAEL,
        total_cards=stats["total_cards"],
        total_sets=stats["total_sets"],
        total_graded=stats["total_graded"],
        show_sold_checkbox=False,
    )


@user_bp.route("/set-language", methods=["POST"])
def set_language():
    """
    Set the language for the session.

    Returns:
        Redirects to the referrer or the cards view.
    """
    lang = request.form.get("lang")
    referrer = request.form.get("referrer", "/")
    if lang in ["en", "he"]:
        session["lang"] = lang
    else:
        flash(_("Invalid language selection."), "danger")
    referrer = referrer.replace("\\", "/")
    parsed_referrer = urlparse(referrer)
    if not parsed_referrer.netloc and not parsed_referrer.scheme:
        return redirect(referrer)
    return redirect(url_for("user.view_cards"))


@user_bp.route("/report_user/<int:user_id>", methods=["POST"])
@login_required
def report_user(user_id):
    """
    Report a user for inappropriate behavior.

    Args:
        user_id (int): The ID of the user to report.

    Returns:
        Redirects to the reported user's profile with a flash message.
    """
    user = User.query.get_or_404(user_id)
    reason = request.form.get("reason")
    details = request.form.get("details")
    if not reason:
        flash("Please provide a reason for the report.", "danger")
        return redirect(url_for("user.profile", user_id=user_id))
    send_email(
        recipient=Config.ADMIN_MAIL,
        subject=f"User Report - {user.username}",
        body=f"User '{current_user.username}' reported the user '{user.username}'.\nReason: {reason}\nDetails: {details if details else 'No additional details provided.'}",
    )
    flash("User has been reported successfully. Thank you!", "success")
    return redirect(url_for("user.profile", user_id=user_id))


@user_bp.route("/profile/<int:user_id>")
def profile(user_id):
    """
    View a user's profile and their cards.

    Args:
        user_id (int): The ID of the user whose profile to view.

    Returns:
        Rendered template for the user's profile page with their cards and feedback.
    """
    user = User.query.get_or_404(user_id)
    show_sold = request.args.get("show_sold") == "on"
    page = request.args.get("page", 1, type=int)
    paginated_cards, unique_set_names, stats = filter_cards(
        user_id=user_id, show_sold=show_sold, page=page
    )
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
        total_cards=stats["total_cards"],
        total_sets=stats["total_sets"],
        total_graded=stats["total_graded"],
        show_sold_checkbox=True,
    )


@user_bp.route("/my-cards")
@login_required
def my_cards():
    """
    View the current user's uploaded cards.

    Returns:
        Rendered template for the user's cards page.
    """
    if current_user.role == "normal":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("user.view_cards"))
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
    """
    Edit a card's details.

    Args:
        card_id (int): The ID of the card to edit.

    Returns:
        Rendered template for the edit card page or redirects to the user's cards page with a flash message.
    """
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
    """
    Delete a card.

    Args:
        card_id (int): The ID of the card to delete.

    Returns:
        Redirects to the user's cards page with a flash message.
    """
    card = Card.query.get_or_404(card_id)
    if current_user.role != "admin" and card.uploader_id != current_user.id:
        flash("You do not have permission to delete this card.", "danger")
        return redirect(url_for("user.my_cards"))
    s3 = boto3.client("s3", region_name=Config.AWS_REGION)
    bucket_name = Config.S3_BUCKET
    if card.image_url:
        try:
            parsed_url = urlparse(card.image_url)
            object_key = parsed_url.path.lstrip("/")
            s3.delete_object(Bucket=bucket_name, Key=object_key)
        except Exception as e:
            print(f"Failed to delete {card.image_url} from S3: {e}", flush=True)
            flash("Failed to delete the image from S3.", "danger")
    if current_user.role == "admin" and card.uploader_id != current_user.id:
        uploader = User.query.get(card.uploader_id)
        if uploader and uploader.email:
            send_email(
                recipient=uploader.email,
                subject="Your Card Has Been Deleted",
                body=f"Hello {uploader.username},\n\nYour card '{card.name}' (Card Number: {card.number}, Set: {card.set_name}) has been deleted by an administrator.\n\nIf you have any questions, please contact support.\n\nBest regards,\nThe Pika-Card Team",
            )
    Cart.query.filter_by(card_id=card.id).delete()
    db.session.delete(card)
    db.session.commit()
    flash("Card deleted successfully!", "success")
    return redirect(url_for("user.my_cards"))


@user_bp.route("/report_card/<int:card_id>", methods=["POST"])
@login_required
def report_card(card_id):
    """
    Report a card for inappropriate content.

    Args:
        card_id (int): The ID of the card to report.

    Returns:
        Redirects to the cards view with a flash message.
    """
    card = Card.query.get_or_404(card_id)
    reason = request.form.get("reason")
    details = request.form.get("details", "")
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
    """
    Add a card to the user's cart.

    Returns:
        Redirects to the cards view with a flash message.
    """
    card_id = request.form.get("card_id")
    card = Card.query.get_or_404(card_id)
    cart_item = Cart.query.filter_by(user_id=current_user.id, card_id=card.id).first()
    if cart_item:
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
    """
    View the current user's cart.

    Returns:
        Rendered template for the cart page with grouped cart items and total price.
    """
    user_id = current_user.id
    cart_items = Cart.query.filter_by(user_id=user_id).all()
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
    """
    Contact the support team.

    GET: Displays the contact form.
    POST: Sends the contact message to the support team.

    Returns:
        Rendered template for the contact page with a flash message indicating success or failure.
    """
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message_content = request.form.get("message")
        if not (name and email and message_content):
            flash("All fields are required!", "danger")
            return redirect(url_for("user.contact_us"))
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
    """
    View the about us page.

    Returns:
        Rendered template for the about us page.
    """
    return render_template("about.html")


@cache.cached(timeout=60, query_string=True)
def filter_cards(base_query=None, user_id=None, show_sold=False, page=1, per_page=12):
    """
    Filter and paginate cards based on various criteria.

    Args:
        base_query (Query): The base query to filter cards.
        user_id (int): The ID of the user whose cards to filter.
        show_sold (bool): Whether to show sold cards.
        page (int): The page number for pagination.
        per_page (int): The number of cards per page.

    Returns:
        tuple: Paginated cards, unique set names, and card statistics.
    """
    uploader_alias = aliased(User)
    if base_query is None:
        base_query = Card.query.options(joinedload(Card.uploader)).join(uploader_alias)
    name_query = request.args.get("name", "").strip()
    set_name_query = request.args.get("set_name", "")
    location_query = request.args.get("location", "").strip()
    is_graded = request.args.get("is_graded", "")
    sort_option = request.args.get("sort", "")
    show_sold = request.args.get("show_sold", "off") == "on" or show_sold
    query = base_query.filter(
        or_(uploader_alias.role == "uploader", uploader_alias.role == "admin")
    )
    if user_id:
        query = query.filter(Card.uploader_id == user_id)
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
    if sort_option == "price_asc":
        query = query.order_by(Card.price.asc())
    elif sort_option == "price_desc":
        query = query.order_by(Card.price.desc())
    elif sort_option == "card_number":
        query = query.order_by(Card.number.asc())
    stats = (
        query.with_entities(
            func.count(Card.id).label("total_cards"),
            func.count(func.distinct(Card.set_name)).label("total_sets"),
            func.count(case((Card.is_graded == True, 1))).label("total_graded"),
        )
        .order_by(None)
        .first()
    )
    stats_dict = {
        "total_cards": stats.total_cards,
        "total_sets": stats.total_sets,
        "total_graded": stats.total_graded,
    }
    paginated_cards = query.paginate(page=page, per_page=per_page, error_out=False)
    unique_set_names = {card.set_name for card in query}
    return paginated_cards, sorted(unique_set_names), stats_dict


@user_bp.route("/templates/css/styles.css.jinja")
def styles():
    """
    Serve the CSS styles.

    Returns:
        Rendered template for the CSS styles.
    """
    return render_template("css/styles.css.jinja")
