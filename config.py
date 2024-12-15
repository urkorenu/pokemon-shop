import os


class Config:
    """
    Configuration class for setting environment variables and application settings.
    """

    # Secret key for the application, used for session management and security.
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

    # Database URI for SQLAlchemy, constructed from environment variables.
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )

    # AWS region for S3 bucket.
    AWS_REGION = os.getenv("AWS_REGION")

    # S3 bucket name.
    S3_BUCKET = os.getenv("S3_BUCKET")

    # API key for external services.
    API_KEY = os.getenv("API_KEY")

    # Admin email address.
    ADMIN_MAIL = os.getenv("ADMIN_MAIL")

    # Cache type for Flask-Caching.
    CACHE_TYPE = "flask_caching.backends.SimpleCache"

    # Disable SQLAlchemy track modifications to save resources.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
