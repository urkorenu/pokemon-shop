# order_routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models import db, Order, Card, User, order_cards, Cart
from ..mail_service import send_email

order_bp = Blueprint("order", __name__)


@order_bp.route("/place-order/<int:card_id>", methods=["POST"])
@login_required
def place_order(card_id):
    card = Card.query.get_or_404(card_id)
    if card.uploader_id == current_user.id:
        flash("You cannot order your own card.", "error")
        return redirect(url_for("user.view_cards"))

    # Ensure seller_id is fetched from the card uploader
    seller_id = card.uploader_id
    if not seller_id:
        flash("Seller information is missing for this card.", "error")
        return redirect(url_for("user.view_cards"))

    # Create the order with the seller_id
    order = Order(buyer_id=current_user.id, seller_id=seller_id, status="Pending")
    db.session.add(order)
    db.session.commit()

    # Notify seller by email
    seller = User.query.get(seller_id)
    buyer = current_user
    send_email(
        recipient=seller.email,
        subject="New Order Received",
        body=f"You have received a new order for your card '{card.name}'.\n"
        f"Buyer Details:\n"
        f"Name: {buyer.username}\n"
        f"Contact: {buyer.contact_details} ({buyer.contact_preference})\n"
        f"Please confirm the order in your dashboard.",
    )

    flash("Order placed successfully! The seller will contact you soon.", "success")
    return redirect(url_for("user.view_cards"))


@order_bp.route("/confirm-order/<int:order_id>", methods=["POST"])
@login_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.seller_id != current_user.id:
        flash("You are not authorized to confirm this order.", "danger")
        return redirect(url_for("order.pending_orders"))

    # Mark cards as unavailable (set amount to 0) and remove them from carts
    for card in order.cards:
        if card.amount > 0:  
            card.amount = 0
            db.session.query(Cart).filter_by(card_id=card.id).delete()  

    # Update order status to Confirmed
    order.status = "Confirmed"
    db.session.commit()

    # Notify buyer by email
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
    order = Order.query.get_or_404(order_id)
    if order.seller_id != current_user.id:
        flash("You are not authorized to reject this order.", "danger")
        return redirect(url_for("order.pending_orders"))

    order.status = "Rejected"
    db.session.commit()

    # Notify buyer
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
    order = Order.query.get_or_404(order_id)

    # Ensure the user is the buyer and the order is confirmed
    if order.buyer_id != current_user.id or order.status != "Confirmed":
        flash("You are not authorized to provide feedback for this order.", "danger")
        return redirect(url_for("order.my_orders"))

    # Get feedback and rating from the form
    feedback = request.form.get("feedback")
    rating = int(request.form.get("rating"))

    # Update the order with feedback and mark it as completed
    order.feedback = feedback
    order.rating = rating
    order.status = "Completed"

    # Update the seller's rating
    seller = order.seller
    if seller.rating is None:
        seller.rating = rating
    else:
        seller.rating = ((seller.rating * seller.feedback_count) + rating) / (
            seller.feedback_count + 1
        )
    seller.feedback_count += 1

    db.session.commit()
    flash("Thank you for your feedback!", "success")
    return redirect(url_for("order.my_orders"))


@order_bp.route("/my-orders")
@login_required
def my_orders():
    orders = Order.query.filter_by(buyer_id=current_user.id).all()

    orders_with_details = []
    for order in orders:
        # Fetch cards in the order using ORM relationships
        cards = (
            db.session.query(Card)
            .join(order_cards, Card.id == order_cards.c.card_id)
            .filter(order_cards.c.order_id == order.id)
            .all()
        )

        # Calculate total price
        total_price = sum(card.price for card in cards)

        # Add seller and other details
        seller = User.query.get(order.seller_id)

        orders_with_details.append(
            {
                "id": order.id,
                "seller": seller,
                "seller_id": seller.id,
                "created_at": order.created_at,
                "cards": cards,  # ORM objects with attributes
                "total_price": total_price,
                "status": order.status,
                "feedback": order.feedback,
                "rating": order.rating,
            }
        )

    return render_template("my_orders.html", orders=orders_with_details)


@order_bp.route("/pending-orders")
@login_required
def pending_orders():
    if current_user.role not in ["uploader", "admin"]:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for("user.view_cards"))

    # Fetch pending orders for the current seller
    pending_orders = Order.query.filter_by(
        seller_id=current_user.id, status="Pending"
    ).all()

    orders_with_details = []
    for order in pending_orders:
        # Fetch cards in the order using ORM relationships
        cards = (
            db.session.query(Card)
            .join(order_cards, Card.id == order_cards.c.card_id)
            .filter(order_cards.c.order_id == order.id)
            .all()
        )

        # Calculate total price
        total_price = sum(card.price for card in cards)

        orders_with_details.append(
            {
                "id": order.id,
                "buyer": order.buyer,
                "created_at": order.created_at,
                "cards": cards,  # ORM objects with attributes
                "total_price": total_price,
            }
        )

    return render_template("pending_orders.html", orders=orders_with_details)
