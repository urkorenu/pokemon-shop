from flask import Flask, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_caching import Cache
from flask_babel import Babel
from flask_session import Session
from redis import Redis
from flask_socketio import SocketIO
from sqlalchemy import cast, String, func
from flask_cors import CORS
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
socketio = SocketIO(
    cors_allowed_origins="https://www.pika-card.store",
    logger=True,
    engineio_logger=True,
    manage_session=True,
    message_queue="redis://redis:6379/0"
)


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask application.
    """
    app = Flask(__name__)
    app.config.from_object("config.Config")
    app.config.update(
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        LANGUAGES=["en", "he"],
        SESSION_TYPE="redis",
        SESSION_PERMANENT=True,
        SESSION_USE_SIGNER=True,
        SESSION_KEY_PREFIX="pokemon-shop:",
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        SESSION_REDIS=Redis(host="redis", port=6379),
    )

    # Initialize Flask extensions
    Session(app)  # Manage sessions using Flask-Session
    CORS(app, origins=["https://www.pika-card.store"], supports_credentials=True)
    socketio.init_app(app, manage_session=True)
    # Initialize Babel for internationalization
    babel = Babel(app)
    babel.init_app(
        app,
        locale_selector=lambda: session.get("lang")
        or request.accept_languages.best_match(app.config["LANGUAGES"]),
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "RedisCache",
            "CACHE_REDIS_URL": "redis://redis:6379/0",
            "CACHE_DEFAULT_TIMEOUT": 300,
        },
    )

    from app.models import Cart, Order, User

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user by their user ID.

        Args:
            user_id (int): The user ID.

        Returns:
            User: The user object.
        """
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.auth"
    login_manager.login_message = "Please log in to access this page."

    @app.context_processor
    def inject_counts():
        """
        Inject counts of cart items, pending orders, orders without feedback, and users who requested uploader role into the template context.

        Returns:
            dict: A dictionary with counts of various user-related items.
        """
        if current_user.is_authenticated:
            user_id = current_user.id
            cart_items_count = (
                db.session.query(func.count())
                .select_from(Cart)
                .filter(Cart.user_id == user_id)
                .scalar()
            )
            pending_orders = (
                cache.get(f"pending_orders_{user_id}")
                or Order.query.filter_by(seller_id=user_id, status="Pending").count()
            )
            cache.set(f"pending_orders_{user_id}", pending_orders, timeout=60)
            orders_without_feedback = (
                cache.get(f"orders_without_feedback_{user_id}")
                or Order.query.filter_by(
                    buyer_id=user_id, status="Confirmed", feedback=None
                ).count()
            )
            cache.set(
                f"orders_without_feedback_{user_id}",
                orders_without_feedback,
                timeout=60,
            )
            users_want_uploader_role = cache.get("users_want_uploader_role") or (
                current_user.role == "admin"
                and User.query.filter(
                    (User.request_status == "Pending")
                    | (cast(User.request_status, String) == "0")
                ).count()
            )
            cache.set("users_want_uploader_role", users_want_uploader_role, timeout=60)
        else:
            cart_items_count = pending_orders = orders_without_feedback = (
                users_want_uploader_role
            ) = 0

        return {
            "cart_items_count": cart_items_count,
            "pending_orders": pending_orders,
            "orders_without_feedback": orders_without_feedback,
            "users_want_uploader_role": users_want_uploader_role,
        }

    @app.template_filter("dict_without")
    def dict_without(d, key):
        """
        Remove a key from a dictionary.

        Args:
            d (dict): The dictionary.
            key: The key to remove.

        Returns:
            dict: The dictionary without the specified key.
        """
        return {k: v for k, v in d.items() if k != key}

    # Register blueprints for different routes
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.order_routes import order_bp
    from app.routes.seller_routes import seller_bp
    from app.routes.chat_routes import chat_bp

    app.register_blueprint(user_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(seller_bp, url_prefix="/seller")
    app.register_blueprint(chat_bp, url_prefix="/chat")

    return app

