# order_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import db, Order, Card, User
from .mail_service import send_email

order_bp = Blueprint("order", __name__)

@order_bp.route("/place-order/<int:card_id>", methods=["POST"])
@login_required
def place_order(card_id):
    card = Card.query.get_or_404(card_id)
    if card.seller_id == current_user.id:
        flash("You cannot order your own card.", "error")
        return redirect(url_for("user.view_cards"))
    
    order = Order(buyer_id=current_user.id, card_id=card_id)
    db.session.add(order)
    db.session.commit()

    # Notify seller by email
    seller = User.query.get(card.seller_id)
    buyer = current_user
    send_email(
        recipient=seller.email,
        subject="New Order Received",
        body=f"You have received a new order for your card '{card.name}'.\n"
             f"Buyer Details:\n"
             f"Name: {buyer.username}\n"
             f"Contact: {buyer.contact_details} ({buyer.contact_preference})\n"
             f"Please confirm the order in your dashboard."
    )

    flash("Order placed successfully! The seller will contact you soon.", "success")
    return redirect(url_for("user.view_cards"))

@order_bp.route("/confirm-order/<int:order_id>", methods=["POST"])
@login_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.card.seller_id != current_user.id:
        flash("You are not authorized to confirm this order.", "error")
        return redirect(url_for("user.my_cards"))

    order.status = "Confirmed"
    db.session.commit()

    # Notify buyer by email
    buyer = User.query.get(order.buyer_id)
    send_email(
        recipient=buyer.email,
        subject="Order Confirmed",
        body=f"Your order for '{order.card.name}' has been confirmed by the seller.\n"
             f"The seller will contact you soon."
    )

    flash("Order confirmed and buyer notified.", "success")
    return redirect(url_for("user.my_orders"))


@order_bp.route("/submit-feedback/<int:order_id>", methods=["POST"])
@login_required
def submit_feedback(order_id):
    order = Order.query.get_or_404(order_id)
    if order.buyer_id != current_user.id or order.status != "Confirmed":
        flash("You are not authorized to provide feedback for this order.", "error")
        return redirect(url_for("user.my_orders"))

    feedback = request.form.get("feedback")
    rating = int(request.form.get("rating"))

    order.feedback = feedback
    order.rating = rating
    order.status = "Completed"

    # Update seller's rating
    seller = order.card.seller
    seller.rating = ((seller.rating * seller.feedback_count) + rating) / (seller.feedback_count + 1)
    seller.feedback_count += 1

    db.session.commit()
    flash("Thank you for your feedback!", "success")
    return redirect(url_for("user.my_orders"))

