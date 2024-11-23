from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


# Initialize extensions
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # User loader function for Flask-Login
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    # Register blueprints
    from .routes.user_routes import user_bp
    from .routes.admin_routes import admin_bp
    from .routes.auth_routes import auth_bp
    from .routes.cart_routes import cart_bp

    app.register_blueprint(user_bp, url_prefix="/")  
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(cart_bp, url_prefix="/cart")


    # Test route for debugging
    @app.route("/test")
    def test():
        return "This is a test route! Flask is running correctly."

    return app

