import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestUserManagement:
    list_url = reverse("user-list")

    def detail_url(self, pk):
        return reverse("user-detail", args=[pk])

    def test_admin_list_users(self, admin_client, user_factory):
        user_factory(role="translator", username="t1")
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        usernames = [u["username"] for u in response.data["results"]]
        assert "test_admin" in usernames
        assert "t1" in usernames

    def test_admin_get_user(self, admin_client, user_factory):
        user = user_factory(role="viewer", username="detail_user")
        response = admin_client.get(self.detail_url(user.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "detail_user"

    def test_admin_create_user(self, admin_client):
        response = admin_client.post(
            self.list_url,
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "Str0ng!Pass",
                "role": "translator",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "newuser"
        assert response.data["role"] == "translator"
        assert "password" not in response.data
        assert User.objects.filter(username="newuser").exists()

    def test_admin_create_user_default_role(self, admin_client):
        response = admin_client.post(
            self.list_url,
            {
                "username": "defaultrole",
                "email": "default@example.com",
                "password": "Str0ng!Pass",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(username="defaultrole")
        assert user.role == "viewer"

    def test_admin_create_user_weak_password(self, admin_client):
        response = admin_client.post(
            self.list_url,
            {
                "username": "weakpw",
                "email": "weak@example.com",
                "password": "123",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_create_user_duplicate_username(self, admin_client, user_factory):
        user_factory(role="viewer", username="existing")
        response = admin_client.post(
            self.list_url,
            {
                "username": "existing",
                "email": "other@example.com",
                "password": "Str0ng!Pass",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_update_role(self, admin_client, user_factory):
        user = user_factory(role="viewer", username="promote_me")
        response = admin_client.patch(
            self.detail_url(user.pk), {"role": "translator"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"] == "translator"

    def test_admin_deactivate_user(self, admin_client, user_factory):
        user = user_factory(role="viewer", username="deactivate_me")
        response = admin_client.patch(
            self.detail_url(user.pk), {"is_active": False}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_admin_cannot_deactivate_self(self, admin_client):
        admin = User.objects.get(username="test_admin")
        response = admin_client.patch(
            self.detail_url(admin.pk), {"is_active": False}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_cannot_change_own_role(self, admin_client):
        admin = User.objects.get(username="test_admin")
        response = admin_client.patch(
            self.detail_url(admin.pk), {"role": "viewer"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_manager_forbidden(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_translator_forbidden(self, translator_client):
        response = translator_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_forbidden(self, viewer_client):
        response = viewer_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_not_allowed(self, admin_client, user_factory):
        user = user_factory(role="viewer", username="nodelete")
        response = admin_client.delete(self.detail_url(user.pk))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
