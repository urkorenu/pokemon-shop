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
@login_required  # Ensures only authenticated users can access this route
def add_to_cart():
    if not current_user.is_authenticated:
        flash("You need to log in to add items to your cart.", "danger")
        return redirect(url_for("auth.login"))

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

@cart_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))

    # Group cart items by seller
    grouped_items = {}
    for item in cart_items:
        seller_id = item.card.uploader_id
        if seller_id not in grouped_items:
            grouped_items[seller_id] = []
        grouped_items[seller_id].append(item)

    # Create an order for each seller
    for seller_id, items in grouped_items.items():
        order = Order(buyer_id=current_user.id, seller_id=seller_id, status="Pending")
        db.session.add(order)
        db.session.flush()  # Get the order ID for the bridge table

        for item in items:
            order_card = OrderCard(order_id=order.id, card_id=item.card_id, quantity=item.quantity)
            db.session.add(order_card)

            # Notify the seller
            seller = User.query.get(seller_id)
            send_email(
                recipient=seller.email,
                subject="New Order Received",
                body=f"You have received a new order containing the following cards:\n" +
                     "\n".join(f"- {item.card.name} (x{item.quantity})" for item in items) +
                     f"\n\nBuyer Details:\nName: {current_user.username}\n"
                     f"Contact: {current_user.contact_details} ({current_user.contact_preference})\n"
                     f"Please confirm the order in your dashboard."
            )

    # Clear the cart
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash("Orders placed successfully! Sellers have been notified.", "success")
    return redirect(url_for("user.view_cards"))

