from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models import db, Order, Card, User, order_cards, Cart
from ..mail_service import send_email

# Create a Blueprint for the order routes
order_bp = Blueprint("order", __name__)


@order_bp.route("/place-order/<int:card_id>", methods=["POST"])
@login_required
def place_order(card_id):
    """
    Place an order for a card.

    Args:
        card_id (int): The ID of the card to order.

    Returns:
        Redirect to the user's card view with a flash message indicating success or failure.
    """
    card = Card.query.get_or_404(card_id)
    if card.uploader_id == current_user.id:
        flash("You cannot order your own card.", "error")
        return redirect(url_for("user.view_cards"))

    seller_id = card.uploader_id
    if not seller_id:
        flash("Seller information is missing for this card.", "error")
        return redirect(url_for("user.view_cards"))

    order = Order(buyer_id=current_user.id, seller_id=seller_id, status="Pending")
    db.session.add(order)
    db.session.commit()

    seller = User.query.get(seller_id)
    send_email(
        recipient=seller.email,
        subject="New Order Received",
        body=f"You have received a new order for your card '{card.name}'.\n"
        f"Buyer Details:\n"
        f"Name: {current_user.username}\n"
        f"Contact: {current_user.contact_details} ({current_user.contact_preference})\n"
        f"Please confirm the order in your dashboard.",
    )

    flash("Order placed successfully! The seller will contact you soon.", "success")
    return redirect(url_for("user.view_cards"))


@order_bp.route("/confirm-order/<int:order_id>", methods=["POST"])
@login_required
def confirm_order(order_id):
    """
    Confirm an order.

    Args:
        order_id (int): The ID of the order to confirm.

    Returns:
        Redirect to the pending orders view with a flash message indicating success or failure.
    """
    order = Order.query.get_or_404(order_id)
    if order.seller_id != current_user.id:
        flash("You are not authorized to confirm this order.", "danger")
        return redirect(url_for("order.pending_orders"))

    for card in order.cards:
        if card.amount > 0:
            card.amount = 0
            db.session.query(Cart).filter_by(card_id=card.id).delete()

    order.status = "Confirmed"
    db.session.commit()

    buyer = User.query.get(order.buyer_id)
    send_email(
        recipient=buyer.email,
        subject="Order Confirmed",
        body=f"Your order for cards has been confirmed by the seller.\n"
        f"The seller will contact you soon.\n\nOrder ID: {order.id}",
    )

    flash("Order confirmed, cards marked as sold, and buyer notified.", "success")
    return redirect(url_for("order.pending_orders"))


@order_bp.route("/reject-order/<int:order_id>", methods=["POST"])
@login_required
def reject_order(order_id):
    """
    Reject an order.

    Args:
        order_id (int): The ID of the order to reject.

    Returns:
        Redirect to the pending orders view with a flash message indicating success or failure.
    """
    order = Order.query.get_or_404(order_id)
    if order.seller_id != current_user.id:
        flash("You are not authorized to reject this order.", "danger")
        return redirect(url_for("order.pending_orders"))

    order.status = "Rejected"
    db.session.commit()

    send_email(
        recipient=order.buyer.email,
        subject="Order Rejected",
        body=f"Your order with ID {order.id} has been rejected by the seller.",
    )
    flash("Order rejected successfully.", "success")
    return redirect(url_for("order.pending_orders"))


@order_bp.route("/submit-feedback/<int:order_id>", methods=["POST"])
@login_required
def submit_feedback(order_id):
    """
    Submit feedback for an order.

    Args:
        order_id (int): The ID of the order to provide feedback for.

    Returns:
        Redirect to the user's orders view with a flash message indicating success or failure.
    """
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id or order.status != "Confirmed":
        flash("You are not authorized to provide feedback for this order.", "danger")
        return redirect(url_for("order.my_orders"))

    feedback = request.form.get("feedback")
    rating = int(request.form.get("rating"))

    order.feedback = feedback
    order.rating = rating
    order.status = "Completed"

    seller = order.seller
    seller.rating = (
        ((seller.rating * seller.feedback_count) + rating) / (seller.feedback_count + 1)
        if seller.rating
        else rating
    )
    seller.feedback_count += 1

    db.session.commit()
    flash("Thank you for your feedback!", "success")
    return redirect(url_for("order.my_orders"))


@order_bp.route("/my-orders")
@login_required
def my_orders():
    """
    View the current user's orders.

    Retrieves all orders placed by the current user, including details about the cards and sellers.

    Returns:
        Rendered template for the user's orders view.
    """
    orders = Order.query.filter_by(buyer_id=current_user.id).all()
    orders_with_details = []

    for order in orders:
        cards = (
            db.session.query(Card)
            .join(order_cards, Card.id == order_cards.c.card_id)
            .filter(order_cards.c.order_id == order.id)
            .all()
        )
        total_price = sum(card.price for card in cards)
        seller = User.query.get(order.seller_id)

        orders_with_details.append(
            {
                "id": order.id,
                "seller": seller,
                "seller_id": seller.id,
                "created_at": order.created_at,
                "cards": cards,
                "total_price": total_price,
                "status": order.status,
                "feedback": order.feedback,
                "rating": order.rating,
            }
        )

    return render_template("my_orders.html", orders=orders_with_details)
