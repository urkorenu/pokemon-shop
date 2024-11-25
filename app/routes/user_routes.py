from flask import Blueprint, render_template, request, redirect, url_for
from ..models import Card, Cart, db
from flask_login import login_required

user_bp = Blueprint("user", __name__)


@user_bp.route("/")
def view_cards():
    # Get search and filter parameters from the request
    name_query = request.args.get("name", "").strip()
    set_name_query = request.args.get("set_name", "")
    sort_option = request.args.get("sort", "")
    is_graded = request.args.get("is_graded", "")
    grading_company = request.args.get("grading_company", "")

    # Query the database
    query = Card.query

    if name_query:
        query = query.filter(Card.name.ilike(f"%{name_query}%"))
    if set_name_query:
        query = query.filter(Card.set_name == set_name_query)
    if is_graded == "yes":
        query = query.filter(Card.is_graded == True)
    elif is_graded == "no":
        query = query.filter(Card.is_graded == False)
    if grading_company:
        query = query.filter(Card.grading_company.ilike(f"%{grading_company}%"))

    # Apply sorting
    if sort_option == "price_asc":
        query = query.order_by(Card.price.asc())
    elif sort_option == "price_desc":
        query = query.order_by(Card.price.desc())
    elif sort_option == "card_number":
        query = query.order_by(Card.number.asc())

    # Execute the query
    cards = query.all()

    # Get unique set names for the filter dropdown
    unique_set_names = [
        card.set_name for card in Card.query.distinct(Card.set_name).all()
    ]

    return render_template("cards.html", cards=cards, unique_set_names=unique_set_names)


@user_bp.route("/cart", methods=["POST"])
@login_required
def add_to_cart():
    card_id = request.form.get("card_id")
    user_id = 1  # Replace with session user ID
    quantity = request.form.get("quantity", 1)
    cart_item = Cart(user_id=user_id, card_id=card_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()
    return redirect(url_for("user.view_cards"))


@user_bp.route("/cart")
@login_required
def view_cart():
    user_id = 1  # Replace with session user ID
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    return render_template("cart.html", cart_items=cart_items)
