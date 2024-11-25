import pytest
from app import create_app, db


@pytest.fixture
def test_app():
    # Setup
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test_secret"

    with app.app_context():
        db.create_all()
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
    response = client.post(
        "/auth/login", data={"email": "test@test.ctest", "password": "test"}
    )
    assert response.status_code == 200
