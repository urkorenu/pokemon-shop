from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # Create and configure the Flask app
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes.user_routes import user_bp
    from .routes.admin_routes import admin_bp

    app.register_blueprint(user_bp, url_prefix="/")  # User routes on root URL
    app.register_blueprint(admin_bp, url_prefix="/admin")  # Admin routes under /admin

    # Test route for debugging
    @app.route("/test")
    def test():
        return "This is a test route! Flask is running correctly."

    return app

