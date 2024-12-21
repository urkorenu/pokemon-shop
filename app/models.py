from flask_login import UserMixin
from datetime import datetime
from app import db


class User(db.Model, UserMixin):
    """
    Represents a user in the application.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        password_hash (str): The hashed password of the user.
        role (str): The role of the user (default is "normal").
        location (str): The location of the user.
        contact_preference (str): The preferred contact method of the user.
        contact_details (str): The contact details of the user.
        rating (float): The rating of the user.
        feedback_count (int): The number of feedbacks received by the user.
        request_status (str): The request status of the user.
    """

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
    request_status = db.Column(db.String(20), default=None)

    def set_password(self, password):
        """
        Set the password for the user.

        Args:
            password (str): The password to be hashed and set.
        """
        from flask_bcrypt import generate_password_hash

        self.password_hash = generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """
        Check if the provided password matches the stored hashed password.

        Args:
            password (str): The password to check.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        from flask_bcrypt import check_password_hash

        return check_password_hash(self.password_hash, password)


class Card(db.Model):
    """
    Represents a card in the application.

    Attributes:
        id (int): The unique identifier for the card.
        name (str): The name of the card.
        price (float): The price of the card.
        condition (str): The condition of the card.
        amount (int): The amount of the card available.
        set_name (str): The name of the set the card belongs to.
        number (str): The number of the card in the set.
        image_url (str): The URL of the card's image.
        is_graded (bool): Whether the card is graded.
        grade (float): The grade of the card.
        grading_company (str): The company that graded the card.
        tcg_price (float): The TCG price of the card.
        card_type (str): The type of the card.
        uploaded_at (datetime): The date and time when the card was uploaded.
        uploader_id (int): The ID of the user who uploaded the card.
        uploader (User): The user who uploaded the card.
        follow_tcg (bool): Whether to follow TCG price updates.
    """

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
    follow_tcg = db.Column(db.Boolean, default=False)


# Define the association table for orders and cards
order_cards = db.Table(
    "order_cards",
    db.Column("order_id", db.Integer, db.ForeignKey("order.id"), primary_key=True),
    db.Column("card_id", db.Integer, db.ForeignKey("card.id"), primary_key=True),
    db.Column("quantity", db.Integer, nullable=False, default=1),
)


class Order(db.Model):
    """
    Represents an order in the application.

    Attributes:
        id (int): The unique identifier for the order.
        buyer_id (int): The ID of the user who placed the order.
        seller_id (int): The ID of the user who is selling the items.
        status (str): The status of the order (default is "Pending").
        feedback (str): The feedback for the order.
        rating (int): The rating for the order.
        created_at (datetime): The date and time when the order was created.
        buyer (User): The user who placed the order.
        seller (User): The user who is selling the items.
        cards (list of Card): The list of cards in the order.
    """

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
    """
    Represents a cart in the application.

    Attributes:
        id (int): The unique identifier for the cart.
        user_id (int): The ID of the user who owns the cart.
        card_id (int): The ID of the card in the cart.
        quantity (int): The quantity of the card in the cart.
        user (User): The user who owns the cart.
        card (Card): The card in the cart.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey("card.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", backref="cart_items")
    card = db.relationship("Card", backref="cart_entries")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
    is_read = db.Column(db.Boolean, default=False)
