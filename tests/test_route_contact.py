from unittest.mock import MagicMock, patch

from src.services.auth import auth_service


def test_create_contact(client, token, contact):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.post(
            "/api/contacts", json=contact, headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["first_name"] == "test_first_name"
        assert "id" in data


def test_get_contact(client, token):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["first_name"] == "test_first_name"
        assert "id" in data


def test_get_contact_not_found(client, token):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/contacts/2", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Not Found"


def test_get_contacts(client, token):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/contacts", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["first_name"] == "test_first_name"
        assert "id" in data[0]


def test_update_contact(client, token, contact_for_update):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.put(
            "/api/contacts/1",
            json=contact_for_update,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["first_name"] == "test_first_name_2"
        assert data["email"] == "test@gmail.com"
        assert data["id"] == 1


def test_update_contact_not_found(client, token, contact_for_update):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.put(
            "/api/contacts/2",
            json=contact_for_update,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Not Found"


def test_get_contact_by_upcoming_birthdays(client, token):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.get(
            "/api/contacts/upcoming_birthdays",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["first_name"] == "test_first_name_2"
        assert "id" in data[0]


def test_delete_contact(client, token):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.delete(
            "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 204, response.text


def test_repeat_delete_contact(client, token):
    with patch.object(auth_service, "r") as r_mock:
        r_mock.get.return_value = None
        response = client.delete(
            "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == "Not Found"
