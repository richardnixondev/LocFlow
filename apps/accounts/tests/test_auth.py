import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


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

    def test_me_includes_name_fields(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "first_name" in response.data
        assert "last_name" in response.data


@pytest.mark.django_db
class TestUpdateProfile:
    url = reverse("auth-me")

    def test_update_name(self, api_client):
        response = api_client.patch(
            self.url,
            {"first_name": "John", "last_name": "Doe"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "John"
        assert response.data["last_name"] == "Doe"

    def test_update_email(self, api_client):
        response = api_client.patch(
            self.url,
            {"email": "newemail@example.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "newemail@example.com"

    def test_duplicate_email_rejected(self, api_client, user_factory):
        user_factory(role="viewer", username="other", email="taken@example.com")
        response = api_client.patch(
            self.url,
            {"email": "taken@example.com"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_cannot_change_role(self, api_client):
        response = api_client.patch(
            self.url, {"role": "admin"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "manager"  # unchanged

    def test_cannot_change_username(self, api_client):
        response = api_client.patch(
            self.url, {"username": "hacked"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "test_manager"  # unchanged

    def test_unauthenticated(self, anon_client):
        response = anon_client.patch(
            self.url, {"first_name": "Anon"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestChangePassword:
    url = reverse("auth-change-password")

    def test_change_password_success(self, api_client, user_factory):
        # api_client uses test_manager with password testpass123!
        response = api_client.post(
            self.url,
            {
                "old_password": "testpass123!",
                "new_password": "NewStr0ng!Pass",
                "new_password_confirm": "NewStr0ng!Pass",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user = User.objects.get(username="test_manager")
        assert user.check_password("NewStr0ng!Pass")

    def test_wrong_old_password(self, api_client):
        response = api_client.post(
            self.url,
            {
                "old_password": "wrongpassword",
                "new_password": "NewStr0ng!Pass",
                "new_password_confirm": "NewStr0ng!Pass",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "old_password" in response.data

    def test_password_mismatch(self, api_client):
        response = api_client.post(
            self.url,
            {
                "old_password": "testpass123!",
                "new_password": "NewStr0ng!Pass",
                "new_password_confirm": "DifferentPass1!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password(self, api_client):
        response = api_client.post(
            self.url,
            {
                "old_password": "testpass123!",
                "new_password": "123",
                "new_password_confirm": "123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated(self, anon_client):
        response = anon_client.post(
            self.url,
            {
                "old_password": "testpass123!",
                "new_password": "NewStr0ng!Pass",
                "new_password_confirm": "NewStr0ng!Pass",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
