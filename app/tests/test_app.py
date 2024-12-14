import pytest
from app import create_app, db


@pytest.fixture
def test_app():
    """
    Sets up a Flask test app for basic app verification.
    Does not delete or modify existing data in the database.
    """
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test_secret"
    app.config["CACHE_TYPE"] = "flask_caching.backends.NullCache"

    with app.app_context():
        db.create_all()  # Creates tables for the test
        yield app  # Test runs here
        db.session.remove()


@pytest.fixture
def client(test_app):
    """
    Provides a test client to simulate HTTP requests to the app.
    """
    return test_app.test_client()


def test_home_page(client):
    """
    Test to check if the home page is accessible and working.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Available" in response.data  # Check if "Welcome" text is in the page


def test_login_page(client):
    """
    Test to verify the login page renders correctly.
    """
    response = client.get("/auth/sign-in")
    assert response.status_code == 200
    assert b"Login" in response.data  # Check if "Login" text is in the page