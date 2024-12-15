from flask import Flask, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_caching import Cache
from flask_babel import Babel
from flask_session import Session
from redis import Redis
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object("config.Config")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
    app.config["LANGUAGES"] = ["en", "he"]
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = True
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "pokemon-shop:"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
    app.config["SESSION_REDIS"] = Redis(host="redis", port=6379)
    Session(app)

    # Initialize Babel for internationalization
    babel = Babel(app)
    babel.init_app(
        app,
        locale_selector=lambda: session.get("lang")
        or request.accept_languages.best_match(app.config["LANGUAGES"]),
    )

    # Initialize extensions with the app
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
            user_id (int): The ID of the user to load.

        Returns:
            User: The user instance if found, otherwise None.
        """
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.auth"
    login_manager.login_message = "Please log in to access this page."

    @app.context_processor
    def inject_counts():
        """
        Inject counts of cart items, pending orders, and orders without feedback into the template context.

        Returns:
            dict: A dictionary with counts of cart items, pending orders, and orders without feedback.
        """
        if current_user.is_authenticated:
            user_id = current_user.id
            cart_items_count = (
                cache.get(f"cart_count_{user_id}")
                or Cart.query.filter_by(user_id=user_id).count()
            )
            pending_orders = (
                cache.get(f"pending_orders_{user_id}")
                or Order.query.filter_by(seller_id=user_id, status="Pending").count()
            )
            orders_without_feedback = (
                cache.get(f"orders_without_feedback_{user_id}")
                or Order.query.filter_by(
                    buyer_id=user_id, status="Confirmed", feedback=None
                ).count()
            )
            users_want_uploader_role = 0
            if current_user.role == "admin":
                users_want_uploader_role = (
                    cache.get("users_want_uploader_role")
                    or User.query.filter_by(request_status="pending").count()
                )
                cache.set(
                    f"users_want_uploader_role",
                    users_want_uploader_role,
                    timeout=60,
                )
            cache.set(f"cart_count_{user_id}", cart_items_count, timeout=60)
            cache.set(f"pending_orders_{user_id}", pending_orders, timeout=60)
            cache.set(
                f"orders_without_feedback_{user_id}",
                orders_without_feedback,
                timeout=60,
            )

        else:
            cart_items_count = pending_orders = orders_without_feedback = users_want_uploader_role =0

        return {
            "cart_items_count": cart_items_count,
            "pending_orders": pending_orders,
            "orders_without_feedback": orders_without_feedback,
            "users_want_uploader_role": users_want_uploader_role,
        }



    # Register the dict_without filter
    @app.template_filter("dict_without")
    def dict_without(d, key):
        """
        Remove a key from a dictionary.

        Args:
            d (dict): The dictionary to remove the key from.
            key: The key to remove from the dictionary.

        Returns:
            dict: A new dictionary without the specified key.
        """
        return {k: v for k, v in d.items() if k != key}

    # Register blueprints for different routes
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.order_routes import order_bp
    from app.routes.seller_routes import seller_bp

    app.register_blueprint(user_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(seller_bp, url_prefix="/seller")

    return app
