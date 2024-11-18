from flask import Blueprint, render_template, request, redirect, url_for
from ..models import Card, Cart, db

user_bp = Blueprint("user", __name__)

@user_bp.route("/cards")
def view_cards():
    cards = Card.query.all()
    return render_template("cards.html", cards=cards)

@user_bp.route("/cart", methods=["POST"])
def add_to_cart():
    card_id = request.form.get("card_id")
    user_id = 1  # Replace with session user ID
    quantity = request.form.get("quantity", 1)
    cart_item = Cart(user_id=user_id, card_id=card_id, quantity=quantity)
    db.session.add(cart_item)
    db.session.commit()
    return redirect(url_for("user.view_cards"))

@user_bp.route("/cart")
def view_cart():
    user_id = 1  # Replace with session user ID
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    return render_template("cart.html", cart_items=cart_items)

