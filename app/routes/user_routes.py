from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_login import login_required, current_user
from sqlalchemy.sql import func, case
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import or_
import boto3
from config import Config
from urllib.parse import urlparse
from ..models import Card, Cart, db, User, Order
from ..cities import CITIES_IN_ISRAEL
from ..mail_service import send_email
from app import cache
from app.utils import roles_required

# Create a Blueprint for user routes
user_bp = Blueprint("user", __name__)


class Pagination:
    """
    A class to handle pagination of items.

    Attributes:
        items (list): List of items to paginate.
        page (int): Current page number.
        per_page (int): Number of items per page.
        total (int): Total number of items.
    """

    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page

    def has_prev(self):
        """Check if there is a previous page."""
        return self.page > 1

    def has_next(self):
        """Check if there is a next page."""
        return self.page < self.pages

    def prev_num(self):
        """Get the previous page number."""
        return self.page - 1

    def next_num(self):
        """Get the next page number."""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """
        Iterate over the page numbers for pagination.

        Args:
            left_edge (int): Number of pages to show at the left edge.
            left_current (int): Number of pages to show to the left of the current page.
            right_current (int): Number of pages to show to the right of the current page.
            right_edge (int): Number of pages to show at the right edge.

        Yields:
            int: Page numbers to display.
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (num > self.page - left_current and num < self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


@user_bp.route("/")
def view_cards():
    """
    Route to view cards.

    Methods:
        GET: Renders the cards page with pagination.

    Returns:
        Rendered template for viewing cards.
    """
    page = request.args.get("page", 1, type=int)
    filtered_data = filter_cards(page=page)
    cards_list, unique_set_names, stats = (
        filtered_data["cards"],
        filtered_data["unique_set_names"],
        filtered_data["stats"],
    )
    pagination = Pagination(cards_list, page, 12, stats["total_cards"])
    return render_template(
        "cards.html",
        cards=cards_list,
        unique_set_names=unique_set_names,
        pagination=pagination,
        cities=CITIES_IN_ISRAEL,
        **stats,
        show_sold_checkbox=False,
    )


@user_bp.route("/set-language", methods=["POST"])
def set_language():
    """
    Route to set the language preference.

    Methods:
        POST: Sets the language in the session and redirects to the referrer.

    Returns:
        Redirect to the referrer or the cards view.
    """
    lang = request.form.get("lang")
    referrer = request.form.get("referrer", "/").replace("\\", "/")
    if lang in ["en", "he"]:
        session["lang"] = lang
    else:
        flash(_("Invalid language selection."), "danger")
    parsed_referrer = urlparse(referrer)
    return redirect(
        referrer
        if not parsed_referrer.netloc and not parsed_referrer.scheme
        else url_for("user.view_cards")
    )


@user_bp.route("/report_user/<int:user_id>", methods=["POST"])
@login_required
def report_user(user_id):
    """
    Route to report a user.

    Methods:
        POST: Sends an email to the admin with the report details.

    Args:
        user_id (int): ID of the user to report.

    Returns:
        Redirect to the reported user's profile.
    """
    user = User.query.get_or_404(user_id)
    reason, details = request.form.get("reason"), request.form.get("details")
    if not reason:
        flash("Please provide a reason for the report.", "danger")
        return redirect(url_for("user.profile", user_id=user_id))
    send_email(
        Config.ADMIN_MAIL,
        f"User Report - {user.username}",
        f"User '{current_user.username}' reported the user '{user.username}'.\nReason: {reason}\nDetails: {details if details else 'No additional details provided.'}",
    )
    flash("User has been reported successfully. Thank you!", "success")
    return redirect(url_for("user.profile", user_id=user_id))


@user_bp.route("/profile/<int:user_id>")
def profile(user_id):
    """
    Route to view a user's profile.

    Methods:
        GET: Renders the profile page with the user's cards and feedback.

    Args:
        user_id (int): ID of the user whose profile to view.

    Returns:
        Rendered template for the user's profile.
    """
    page, show_sold = (
        request.args.get("page", 1, type=int),
        request.args.get("show_sold") == "on",
    )
    user = User.query.get_or_404(user_id)
    filtered_data = filter_cards(user_id=user_id, show_sold=show_sold, page=page)
    cards_list, unique_set_names, stats = (
        filtered_data["cards"],
        filtered_data["unique_set_names"],
        filtered_data["stats"],
    )
    pagination = Pagination(cards_list, page, 12, stats["total_cards"])
    completed_orders = (
        db.session.query(User.username, Order.feedback, Order.rating)
        .join(Order, Order.buyer_id == User.id)
        .filter(Order.seller_id == user_id, Order.status == "Completed")
        .all()
    )
    return render_template(
        "profile.html",
        user=user,
        cards=cards_list,
        feedback=completed_orders,
        unique_set_names=unique_set_names,
        pagination=pagination,
        **stats,
        show_sold_checkbox=True,
    )


@user_bp.route("/my-cards")
@login_required
def my_cards():
    """
    Route to view the current user's cards with search and pagination.

    Methods:
        GET: Renders the page with the user's available and sold cards.

    Returns:
        Rendered template for the user's cards.
    """
    if current_user.role == "normal":
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("user.view_cards"))

    # Get search query and pagination details
    search_query = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 8  # Cards per page

    # Base query for available and sold cards
    available_query = Card.query.filter(Card.uploader_id == current_user.id, Card.amount > 0)
    sold_query = Card.query.filter_by(uploader_id=current_user.id, amount=0)

    # Apply search filter
    if search_query:
        available_query = available_query.filter(Card.name.ilike(f"%{search_query}%"))
        sold_query = sold_query.filter(Card.name.ilike(f"%{search_query}%"))

    # Paginate queries
    available_cards = available_query.paginate(page=page, per_page=per_page, error_out=False)
    sold_cards = sold_query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "my_cards.html",
        available_cards=available_cards,
        sold_cards=sold_cards,
        search_query=search_query,
    )


@user_bp.route("/edit-card/<int:card_id>", methods=["GET", "POST"])
@login_required
def edit_card(card_id):
    """
    Route to edit a card.

    Methods:
        GET: Renders the edit card page.
        POST: Updates the card details.

    Args:
        card_id (int): ID of the card to edit.

    Returns:
        Rendered template for editing the card or redirect to the user's cards.
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

        is_graded_value = request.form.get("is_graded", "").lower()
        grade = request.form.get("grade")
        grading_company = request.form.get("grading_company")

        card.is_graded = is_graded_value == "yes"
        card.grade = grade if grade not in (None, "", "None") else None
        card.grading_company = grading_company if grading_company not in (None, "", "None") else None
        db.session.commit()
        flash("Card updated successfully!", "success")
        return redirect(url_for("user.my_cards"))
    return render_template("edit_card.html", card=card)


@user_bp.route("/delete-card/<int:card_id>", methods=["POST"])
@login_required
def delete_card(card_id):
    """
    Route to delete a card.

    Methods:
        POST: Deletes the card and its image from S3.

    Args:
        card_id (int): ID of the card to delete.

    Returns:
        Redirect to the user's cards.
    """
    card = Card.query.get_or_404(card_id)
    if current_user.role != "admin" and card.uploader_id != current_user.id:
        flash("You do not have permission to delete this card.", "danger")
        return redirect(url_for("user.my_cards"))
    s3 = boto3.client("s3", region_name=Config.AWS_REGION)
    if card.image_url:
        try:
            s3.delete_object(
                Bucket=Config.S3_BUCKET, Key=urlparse(card.image_url).path.lstrip("/")
            )
        except Exception as e:
            print(f"Failed to delete {card.image_url} from S3: {e}", flush=True)
            flash("Failed to delete the image from S3.", "danger")
    if current_user.role == "admin" and card.uploader_id != current_user.id:
        uploader = User.query.get(card.uploader_id)
        if uploader and uploader.email:
            send_email(
                uploader.email,
                "Your Card Has Been Deleted",
                f"Hello {uploader.username},\n\nYour card '{card.name}' (Card Number: {card.number}, Set: {card.set_name}) has been deleted by an administrator.\n\nIf you have any questions, please contact support.\n\nBest regards,\nThe Pika-Card Team",
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
    Route to report a card.

    Methods:
        POST: Sends an email to the admin with the report details.

    Args:
        card_id (int): ID of the card to report.

    Returns:
        Redirect to the cards view.
    """
    card = Card.query.get_or_404(card_id)
    reason, details = request.form.get("reason"), request.form.get("details", "")
    send_email(
        Config.ADMIN_MAIL,
        f"Report: Card #{card.id} - {reason}",
        f"Card Name: {card.name}\nReason: {reason}\nDetails: {details}\nUser: {current_user.username}",
    )
    flash("Report submitted successfully. Admin will review it.", "success")
    return redirect(url_for("user.view_cards"))


@user_bp.route("/cart", methods=["POST"])
@login_required
def add_to_cart():
    """
    Route to add a card to the cart.

    Methods:
        POST: Adds the card to the user's cart.

    Returns:
        Redirect to the cards view.
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
            db.session.add(Cart(user_id=current_user.id, card_id=card.id, quantity=1))
            db.session.commit()
            flash(f"{card.name} has been added to your cart.", "success")
        else:
            flash(f"{card.name} is out of stock.", "danger")
    return redirect(url_for("user.view_cards"))


@user_bp.route("/cart")
@login_required
def view_cart():
    """
    Route to view the user's cart.

    Methods:
        GET: Renders the cart page with the items in the user's cart.

    Returns:
        Rendered template for the cart.
    """
    user_id = current_user.id
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    grouped_cart = {}
    for item in cart_items:
        grouped_cart.setdefault(item.card.uploader_id, []).append(item)
    total_price = sum(item.card.price * item.quantity for item in cart_items)
    return render_template(
        "cart.html", grouped_cart=grouped_cart, total_price=total_price
    )


@user_bp.route("/contact", methods=["GET", "POST"])
def contact_us():
    """
    Route for the contact us page.

    Methods:
        GET: Renders the contact us page.
        POST: Sends the contact message to the admin.

    Returns:
        Rendered template for the contact us page or redirect to the contact us page.
    """
    if request.method == "POST":
        name, email, message_content = (
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("message"),
        )
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
            send_email(Config.ADMIN_MAIL, f"New Contact Us Message from {name}", msg)
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            flash("Failed to send message. Please try again later.", "danger")
            print(str(e), flush=True)
        return redirect(url_for("user.contact_us"))
    return render_template("contact.html")


@user_bp.route("/about", methods=["GET"])
def about_us():
    """
    Route for the about us page.

    Methods:
        GET: Renders the about us page.

    Returns:
        Rendered template for the about us page.
    """
    return render_template("about.html")


@user_bp.route("/templates/css/styles.css.jinja")
def styles():
    """
    Route for the CSS styles.

    Methods:
        GET: Renders the CSS styles template.

    Returns:
        Rendered template for the CSS styles.
    """
    return render_template("css/styles.css.jinja")


@cache.cached(timeout=60, query_string=True)
def filter_cards(base_query=None, user_id=None, show_sold=False, page=1, per_page=12):
    """
    Filter cards based on various criteria.

    Args:
        base_query (Query): Base query to filter cards.
        user_id (int): ID of the user to filter cards by.
        show_sold (bool): Whether to show sold cards.
        page (int): Page number for pagination.
        per_page (int): Number of items per page.

    Returns:
        dict: Filtered cards, unique set names, and statistics.
    """
    uploader_alias = aliased(User)
    base_query = base_query or Card.query.options(joinedload(Card.uploader)).join(
        uploader_alias
    )
    name_query, set_name_query, location_query = (
        request.args.get("name", "").strip(),
        request.args.get("set_name", ""),
        request.args.get("location", "").strip(),
    )
    is_graded, sort_option, show_sold = (
        request.args.get("is_graded", ""),
        request.args.get("sort", ""),
        request.args.get("show_sold", "off") == "on" or show_sold,
    )

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

    paginated_cards = query.paginate(page=page, per_page=per_page, error_out=False)
    cards_list = [
        {
            "id": card.id,
            "name": card.name,
            "set_name": card.set_name,
            "price": float(card.price),
            "amount": card.amount,
            "is_graded": card.is_graded,
            "image_url": card.image_url,
            "card_type": card.card_type,
            "condition": card.condition,
            "uploaded_at": card.uploaded_at,
            "tcg_price": card.tcg_price,
            "grading_company": card.grading_company,
            "grade": card.grade,
            "uploader": (
                {
                    "id": card.uploader.id,
                    "username": card.uploader.username,
                    "location": card.uploader.location,
                }
                if card.uploader
                else None
            ),
        }
        for card in paginated_cards.items
    ]
    unique_set_names = sorted({card["set_name"] for card in cards_list})

    return {
        "cards": cards_list,
        "unique_set_names": unique_set_names,
        "stats": {
            "total_cards": int(stats.total_cards),
            "total_sets": int(stats.total_sets),
            "total_graded": int(stats.total_graded),
        },
    }
