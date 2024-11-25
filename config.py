import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )

    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET = os.getenv("S3_BUCKET")
    API_KEY = os.getenv("API_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
