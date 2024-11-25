import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def test_app():
    # Setup
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test_secret"

    print(f"Database URI during tests: {app.config['SQLALCHEMY_DATABASE_URI']}")

    with app.app_context():
        db.create_all()
        # Add a test user
        user = User(username="testuser", email="test@test.ctest")
        user.set_password("test")  # Set a hashed password
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login(client):
    # Attempt to login with the test user
    response = client.post(
        "/auth/login", data={"email": "test@test.ctest", "password": "test"}
    )
    assert response.status_code == 200
    assert b"Welcome, testuser!" in response.data
