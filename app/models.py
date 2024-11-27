from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Table, Column, Integer, ForeignKey
from app import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="normal")
    location = db.Column(db.String(120), nullable=True)
    contact_preference = db.Column(db.String(20), nullable=False)
    contact_details = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    feedback_count = db.Column(db.Integer, default=0)

    def set_password(self, password):
        from flask_bcrypt import generate_password_hash

        self.password_hash = generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        from flask_bcrypt import check_password_hash

        return check_password_hash(self.password_hash, password)


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    set_name = db.Column(db.String(120), nullable=False)
    number = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(250), nullable=True)
    is_graded = db.Column(db.Boolean, default=False)
    grade = db.Column(db.Float, nullable=True)
    grading_company = db.Column(db.String(50), nullable=True)
    tcg_price = db.Column(db.Float, nullable=True)
    card_type = db.Column(db.String(50), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    uploader = db.relationship("User", backref="uploaded_cards")


# Define the association table for orders and cards
order_cards = db.Table(
    "order_cards",
    db.Column("order_id", db.Integer, db.ForeignKey("order.id"), primary_key=True),
    db.Column("card_id", db.Integer, db.ForeignKey("card.id"), primary_key=True),
    db.Column("quantity", db.Integer, nullable=False, default=1),
)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    feedback = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    buyer = db.relationship("User", foreign_keys=[buyer_id], backref="orders")
    seller = db.relationship("User", foreign_keys=[seller_id], backref="sales")
    cards = db.relationship("Card", secondary=order_cards, backref="orders")


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey("card.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", backref="cart_items")
    card = db.relationship("Card", backref="cart_entries")

