# app/__init__.py
from flask import Flask, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_caching import Cache
from flask_babel import Babel
from werkzeug.middleware.shared_data import SharedDataMiddleware



# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    app.config.from_object("config.Config")
    app.config["LANGUAGES"] = ["en", "he"]
    babel = Babel(app)

    def get_locale():
        return session.get("lang") or request.accept_languages.best_match(
            app.config["LANGUAGES"]
        )

    babel.init_app(app, locale_selector=get_locale)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)

    # Import models after db is initialized to avoid circular imports
    from app.models import Cart, Order, User  # Import models here

    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.auth"
    login_manager.login_message = "Please log in to access this page."

    # Context processor for injecting counts
    @app.context_processor
    def inject_counts():
        if current_user.is_authenticated:
            user_id = current_user.id
            cart_items_count = cache.get(f"cart_count_{user_id}")
            pending_orders = cache.get(f"pending_orders_{user_id}")
            orders_without_feedback = cache.get(f"orders_without_feedback_{user_id}")

            if cart_items_count is None:
                cart_items_count = Cart.query.filter_by(user_id=user_id).count()
                cache.set(
                    f"cart_count_{user_id}", cart_items_count, timeout=60
                )  # Cache for 60 seconds

            if pending_orders is None and current_user.role in ["uploader", "admin"]:
                pending_orders = Order.query.filter_by(
                    seller_id=user_id, status="Pending"
                ).count()
                cache.set(f"pending_orders_{user_id}", pending_orders, timeout=60)

            if orders_without_feedback is None:
                orders_without_feedback = Order.query.filter_by(
                    buyer_id=user_id, status="Confirmed", feedback=None
                ).count()
                cache.set(
                    f"orders_without_feedback_{user_id}",
                    orders_without_feedback,
                    timeout=60,
                )
        else:
            cart_items_count = 0
            pending_orders = 0
            orders_without_feedback = 0

        return {
            "cart_items_count": cart_items_count,
            "pending_orders": pending_orders,
            "orders_without_feedback": orders_without_feedback,
        }

    # Register blueprints
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.order_routes import order_bp

    app.register_blueprint(user_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(order_bp, url_prefix="/order")

    return app
