from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import Cart, Order, db, User
from ..mail_service import send_email

# Create a Blueprint for the cart routes
cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/view")
@login_required
def view_cart():
    """
    View the current user's cart.

    Retrieves all items in the current user's cart, groups them by the uploader,
    calculates the total price, and renders the cart template.

    Returns:
        Rendered template for the cart view.
    """
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    grouped_cart = {}
    for item in cart_items:
        grouped_cart.setdefault(item.card.uploader_id, []).append(item)
    total_price = sum(item.card.price * item.quantity for item in cart_items)
    return render_template(
        "cart.html", grouped_cart=grouped_cart, total_price=total_price
    )


@cart_bp.route("/remove/<int:cart_id>", methods=["POST"])
@login_required
def remove_from_cart(cart_id):
    """
    Remove an item from the cart.

    Args:
        cart_id (int): The ID of the cart item to remove.

    Returns:
        Redirect to the cart view with a flash message indicating success or failure.
    """
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
    """
    Checkout the current user's cart.

    Creates orders for each seller based on the items in the cart, sends notification
    emails to the sellers, clears the cart, and redirects to the cart view with a flash message.

    Returns:
        Redirect to the cart view with a flash message indicating success or failure.
    """
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))

    grouped_cart = {}
    for item in cart_items:
        grouped_cart.setdefault(item.card.uploader_id, []).append(item)

    for seller_id, items in grouped_cart.items():
        order = Order(buyer_id=current_user.id, seller_id=seller_id, status="Pending")
        db.session.add(order)
        db.session.flush()

        for item in items:
            db.session.execute(
                db.text(
                    "INSERT INTO order_cards (order_id, card_id, quantity) VALUES (:order_id, :card_id, :quantity)"
                ),
                {
                    "order_id": order.id,
                    "card_id": item.card_id,
                    "quantity": item.quantity,
                },
            )

            seller = User.query.get(seller_id)
            send_email(
                recipient=seller.email,
                subject="New Order Received",
                body=f"You have received a new order containing the following cards:\n"
                + "\n".join(f"- {item.card.name} (x{item.quantity})" for item in items)
                + f"\n\nBuyer Details:\nName: {current_user.username}\n"
                f"Contact: {current_user.contact_details} ({current_user.contact_preference})\n"
                f"Please confirm the order in your dashboard.",
            )

    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Orders placed successfully! Sellers have been notified.", "success")
    return redirect(url_for("cart.view_cart"))
