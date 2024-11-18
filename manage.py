from flask import Flask
from app import create_app, db
from flask_migrate import Migrate

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

