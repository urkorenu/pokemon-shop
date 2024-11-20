from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Cart, Card, db

cart_bp = Blueprint("cart", __name__)

@cart_bp.route("/cart")
def view_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.card.price * item.quantity for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@cart_bp.route("/cart/add", methods=["POST"])
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
            flash(f"You cannot add more {card.name} cards. Only {card.amount} available.", "danger")
    else:
        if card.amount > 0:
            cart_item = Cart(user_id=current_user.id, card_id=card.id, quantity=1)
            db.session.add(cart_item)
            db.session.commit()
            flash(f"{card.name} has been added to your cart.", "success")
        else:
            flash(f"{card.name} is out of stock.", "danger")

    #return redirect(request.referrer)  # Redirects back to the current page
    #return redirect(url_for("user.view_cards"))
    return redirect(request.referrer)



@cart_bp.route("/cart/remove/<int:cart_id>", methods=["POST"])
def remove_from_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id != current_user.id:
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for("cart.view_cart"))

    db.session.delete(cart_item)
    db.session.commit()
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart.view_cart"))

@cart_bp.route("/cart/update", methods=["POST"])
def update_cart():
    cart_id = request.form.get("cart_id")
    quantity = int(request.form.get("quantity", 1))
    cart_item = Cart.query.get_or_404(cart_id)

    if cart_item.user_id != current_user.id:
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for("cart.view_cart"))

    cart_item.quantity = max(1, quantity)
    db.session.commit()
    flash("Cart updated successfully.", "success")
    return redirect(url_for("cart.view_cart"))

