import io

from unittest.mock import MagicMock, patch

from src.services.auth import auth_service


def test_get_contact(client, token):
    with patch.object(auth_service, 'r') as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == "deadpool"
        assert "id" in data


def test_update_avatar_user(client, token, monkeypatch, user, session):
    with patch.object(auth_service, 'r') as r_mock:
        r_mock.get.return_value = None
        mock_cloudinary_config = MagicMock()
        monkeypatch.setattr("src.routes.users.cloudinary.config", mock_cloudinary_config)
        mock_cloudinary_uploader_upload = MagicMock()
        monkeypatch.setattr("src.routes.users.cloudinary.uploader.upload", mock_cloudinary_uploader_upload)
        mock_cloudinary_image = MagicMock()
        monkeypatch.setattr("src.routes.users.cloudinary.CloudinaryImage.build_url", mock_cloudinary_image)

        fake_user = {"email": "test@example.com", "username": "testuser"}
        fake_file = io.BytesIO(b"fake_content")

        mock_cloudinary_uploader_upload.return_value = {"version": "123"}
        mock_cloudinary_image.return_value = "fake_url"

        response = client.patch("/api/users/avatar",
                                files={"file": ("fake_avatar.png", fake_file)},
                                headers={"Authorization": f"Bearer {token}"}
                                )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["avatar"] == "fake_url"
        assert "id" in data
