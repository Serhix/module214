import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

from main import app
from src.database.models import Base
from src.database.db import get_db
from src.database.models import User


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def session():
    # Create the database

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(session):
    # Dependency override

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture(scope="module")
def user():
    return {"username": "deadpool", "email": "deadpool@example.com", "password": "123456789"}


@pytest.fixture(scope="function")
def email():
    return {"email": "deadpool@example.com"}


@pytest.fixture(scope="module")
def contact():
    return {
        f"first_name": "test_first_name",
        "last_name": "test_last_name",
        "email": "test@gmail.com",
        "phone": "+380980000000",
        "birthday": "2023-12-25T12:29:33.106Z",
        "description": "string",
        "favorites": "false",
        "created_at": "2023-12-20T12:29:33.106Z",
        "updated_at": "2023-12-20T12:29:33.106Z"
    }


@pytest.fixture(scope="module")
def contact_for_update():
    return {
        f"first_name": "test_first_name_2",
        "last_name": "test_last_name",
        "email": "test@gmail.com",
        "phone": "+380980000000",
        "birthday": "2023-12-22T12:29:33.106Z",
        "description": "string",
        "favorites": "false",
        "created_at": "2023-12-20T12:29:33.106Z",
        "updated_at": "2023-12-20T12:29:33.106Z"
    }


@pytest.fixture(scope="function")
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_verification_email", mock_send_email)
    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    data = response.json()
    return data["access_token"]