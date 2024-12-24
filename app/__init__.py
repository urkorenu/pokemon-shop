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
from config import Config
import os

# Initialize extensions (without specific configurations)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
socketio = SocketIO(  # Initialize without message_queue for now
    cors_allowed_origins="https://www.pika-card.store",
    logger=True,
    engineio_logger=True,
    manage_session=True,
    message_queue=f"redis://{os.getenv('ELASTIC_CACHE')}:6379/0",
)

def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask application.
    """
    config = Config()  # Create the Config object
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Update app configuration
    app.config.update(
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        LANGUAGES=["en", "he"],
        SESSION_TYPE="redis",
        SESSION_PERMANENT=True,
        SESSION_USE_SIGNER=True,
        SESSION_KEY_PREFIX="pokemon-shop:",
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        SESSION_REDIS=Redis(
            host=config.ELASTIC_CACHE,
            port=6379,
            decode_responses=False,
        ),
        SESSION_SERIALIZER="json",
    )

    # Initialize Flask extensions
    Session(app)
    CORS(app, origins=["https://www.pika-card.store"], supports_credentials=True)

    # Initialize socketio with the resolved Redis message queue
    socketio.init_app(app, manage_session=True)

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
            "CACHE_REDIS_URL": f"redis://{config.ELASTIC_CACHE}:6379/0",
            "CACHE_DEFAULT_TIMEOUT": 300,
        },
    )

    # Blueprints and other app-level configurations
    from app.models import Cart, Order, User
    from app.routes.chat_routes import get_chat_room

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.auth"
    login_manager.login_message = "Please log in to access this page."

    @app.context_processor
    def inject_counts():
        try:
            if current_user.is_authenticated:
                user_id = current_user.id
                cart_items_count = (
                    db.session.query(func.count())
                    .select_from(Cart)
                    .filter(Cart.user_id == user_id)
                    .scalar()
                )
                pending_orders = cache.get(f"pending_orders_{user_id}") or 0
                orders_without_feedback = cache.get(f"orders_without_feedback_{user_id}") or 0
                users_want_uploader_role = cache.get("users_want_uploader_role") or 0
                unread_message_count = 0

                # Example: Safe Redis Access
                for user in User.query.filter(User.id != current_user.id).all():
                    room = get_chat_room(current_user.id, user.id)
                    redis_key = f"{room}:unread"
                    redis_value = app.config["SESSION_REDIS"].get(redis_key)
                    unread_count = int(redis_value or 0)
                    unread_message_count += unread_count
            else:
                cart_items_count = pending_orders = orders_without_feedback = (
                    users_want_uploader_role
                ) = unread_message_count = 0
        except Exception as e:
            print(f"Error in inject_counts: {e}")
            cart_items_count = pending_orders = orders_without_feedback = (
                users_want_uploader_role
            ) = unread_message_count = 0

        return {
            "cart_items_count": cart_items_count,
            "pending_orders": pending_orders,
            "orders_without_feedback": orders_without_feedback,
            "users_want_uploader_role": users_want_uploader_role,
            "unread_message_count": unread_message_count,
        }

    @app.template_filter("dict_without")
    def dict_without(d, key):
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

