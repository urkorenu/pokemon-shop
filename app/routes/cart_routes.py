from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Cart, Card, Order, db, User
from ..mail_service import send_email

cart_bp = Blueprint("cart", __name__)

@cart_bp.route("/view")
@login_required
def view_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    grouped_cart = {}
    for item in cart_items:
        seller_id = item.card.uploader_id
        if seller_id not in grouped_cart:
            grouped_cart[seller_id] = []
        grouped_cart[seller_id].append(item)

    total_price = sum(item.card.price * item.quantity for item in cart_items)
    return render_template("cart.html", grouped_cart=grouped_cart, total_price=total_price)


@cart_bp.route("/remove/<int:cart_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id != current_user.id:
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for("cart.view_cart"))

    db.session.delete(cart_item)
    db.session.commit()
    flash("Item removed from cart.", "success")
    return redirect(url_for("cart.view_cart"))

@cart_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))

    grouped_cart = {}
    for item in cart_items:
        seller_id = item.card.uploader_id
        if seller_id not in grouped_cart:
            grouped_cart[seller_id] = []
        grouped_cart[seller_id].append(item)

    for seller_id, items in grouped_cart.items():
        order = Order(buyer_id=current_user.id, seller_id=seller_id, status="Pending")
        db.session.add(order)
        db.session.flush()  # Get the order ID

        # Insert into the order_cards table using raw SQLAlchemy
        for item in items:
            insert_stmt = db.text(
                """
                INSERT INTO order_cards (order_id, card_id, quantity)
                VALUES (:order_id, :card_id, :quantity)
                """
            )
            db.session.execute(
                insert_stmt,
                {"order_id": order.id, "card_id": item.card_id, "quantity": item.quantity},
            )

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
    return redirect(url_for("cart.view_cart"))


