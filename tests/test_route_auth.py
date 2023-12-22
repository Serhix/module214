from unittest.mock import MagicMock, patch

from src.database.models import User

from src.services.auth import auth_service


def test_create_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_verification_email", mock_send_email)
    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]


def test_repeat_create_user(client, user):
    response = client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"


def test_login_user_not_confirmed(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


def test_login_user(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": 'password'},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


def test_login_wrong_email(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": 'email', "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


def test_refresh_token(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    refresh_token = current_user.refresh_token
    response = client.get("/api/auth/refresh_token", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client, user, session):
    refresh_token = user.get("refresh_token")
    if refresh_token is None:
        refresh_token = "invalid_refresh_token"
    response = client.get("/api/auth/refresh_token", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 401
    assert "Could not validate credentials" in response.text


def test_confirmed_email_success(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    token = current_user.refresh_token
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200
    assert response.json() == {"message": "Email confirmed"}


def test_confirmed_email_already_confirmed(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    token = current_user.refresh_token
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == 200
    assert response.json() == {"message": "Your email is already confirmed"}


def test_confirmed_email_invalid_token(client, session):
    invalid_token = "invalid_token"
    response = client.get(f"/api/auth/confirmed_email/{invalid_token}")
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid token for email verification"}


def test_verify_by_email(client, user, email, monkeypatch, session):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_verification_email", mock_send_email)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = False
    response = client.post(
        "/api/auth/verify_by_email",
        json=email,
    )
    assert response.json() == {"message": "Check your email for confirmation."}


def test_verify_by_email_already_confirmed(client, user, email, monkeypatch, session ):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_verification_email", mock_send_email)
    response = client.post(
        "/api/auth/verify_by_email",
        json=email,
    )
    assert response.json() == {"message": "Your email is already confirmed"}


def test_forgot_password(client, user, email, monkeypatch, session):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_verification_email", mock_send_email)
    response = client.post(
        "/api/auth/forgot_password",
        json=email,
    )
    assert response.json() == {"message": "Check your email for reset password."}


def test_reset_password_template(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    token = current_user.refresh_token

    response = client.get(
        f"/api/auth/reset_password_template/{token}")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("Content-Type")


def test_reset_password_template_unexpected_error(client, monkeypatch):
    mock_auth_service = MagicMock()
    monkeypatch.setattr("src.routes.auth.auth_service", mock_auth_service)
    mock_auth_service.get_email_from_token.side_effect = Exception()
    token = "any_token"
    response = client.get(f"/api/auth/reset_password_template/{token}")

    assert response.status_code == 500
    assert "An unexpected error occurred. Report this message to support:" in response.json()["detail"]


def test_reset_password(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    token = current_user.refresh_token

    response = client.post(
        f"/api/auth/reset_password/{token}",
        data={"new_password": 'test_pass', "confirm_password": 'test_pass'},
    )
    assert response.json() == {"message": "Password reset successfully"}


def test_reset_invalid_password(client, user, session):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    token = current_user.refresh_token

    response = client.post(
        f"/api/auth/reset_password/{token}",
        data={"new_password": 'ererererer', "confirm_password": 'dfgdgdfgdfgdfg'},
    )

    assert response.status_code == 422
    assert 'Unprocessable Entity' in response.text


def test_reset_password_exception(client, user, session):
    token = 'invalid_token'
    response = client.post(
        f"/api/auth/reset_password/{token}",
        data={"new_password": 'test_pass', "confirm_password": 'test_pass'},
    )

    assert response.status_code == 500
    assert 'An unexpected error occurred.' in response.text