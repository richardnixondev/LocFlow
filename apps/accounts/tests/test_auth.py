import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestRegister:
    url = reverse("auth-register")

    def test_register_success(self, anon_client):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Str0ng!Pass",
            "password_confirm": "Str0ng!Pass",
        }
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "newuser"
        assert "password" not in response.data
        assert User.objects.filter(username="newuser").exists()

    def test_register_password_mismatch(self, anon_client):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Str0ng!Pass",
            "password_confirm": "DifferentPass1!",
        }
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in str(response.data)

    def test_register_weak_password(self, anon_client):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "123",
            "password_confirm": "123",
        }
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username(self, anon_client, user_factory):
        user_factory(role="viewer", username="existing")
        data = {
            "username": "existing",
            "email": "other@example.com",
            "password": "Str0ng!Pass",
            "password_confirm": "Str0ng!Pass",
        }
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_ignores_role_field(self, anon_client):
        data = {
            "username": "sneaky",
            "email": "sneaky@example.com",
            "password": "Str0ng!Pass",
            "password_confirm": "Str0ng!Pass",
            "role": "admin",
        }
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(username="sneaky")
        assert user.role == "viewer"

    def test_register_default_role_is_viewer(self, anon_client):
        data = {
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "Str0ng!Pass",
            "password_confirm": "Str0ng!Pass",
        }
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["role"] == "viewer"


@pytest.mark.django_db
class TestLogin:
    url = reverse("auth-login")

    def test_login_success(self, anon_client, user_factory):
        user_factory(role="manager", username="loginuser")
        data = {"username": "loginuser", "password": "testpass123!"}
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_credentials(self, anon_client, user_factory):
        user_factory(role="viewer", username="loginuser2")
        data = {"username": "loginuser2", "password": "wrongpass"}
        response = anon_client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_token(self, anon_client, user_factory):
        user = user_factory(role="viewer", username="refreshuser")
        # Login first
        login_url = reverse("auth-login")
        response = anon_client.post(
            login_url,
            {"username": "refreshuser", "password": "testpass123!"},
            format="json",
        )
        refresh_token = response.data["refresh"]

        # Refresh
        url = reverse("auth-refresh")
        response = anon_client.post(url, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data


@pytest.mark.django_db
class TestMe:
    url = reverse("auth-me")

    def test_me_authenticated(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "test_manager"
        assert response.data["role"] == "manager"

    def test_me_unauthenticated(self, anon_client):
        response = anon_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
