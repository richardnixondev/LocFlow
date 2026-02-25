import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def user_factory(db):
    """Factory to create users with specific roles."""
    def _create_user(role="viewer", **kwargs):
        defaults = {
            "username": f"test_{role}",
            "email": f"{role}@example.com",
            "password": "testpass123!",
            "role": role,
        }
        defaults.update(kwargs)
        password = defaults.pop("password")
        user = User(**defaults)
        user.set_password(password)
        user.save()
        return user
    return _create_user


def _make_authenticated_client(user):
    """Create an APIClient authenticated with JWT for the given user."""
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


@pytest.fixture
def api_client(user_factory):
    """Authenticated API client with manager role (backwards-compatible)."""
    user = user_factory(role="manager")
    return _make_authenticated_client(user)


@pytest.fixture
def admin_client(user_factory):
    """Authenticated API client with admin role."""
    user = user_factory(role="admin", username="test_admin")
    return _make_authenticated_client(user)


@pytest.fixture
def translator_client(user_factory):
    """Authenticated API client with translator role."""
    user = user_factory(role="translator", username="test_translator")
    return _make_authenticated_client(user)


@pytest.fixture
def viewer_client(user_factory):
    """Authenticated API client with viewer role."""
    user = user_factory(role="viewer", username="test_viewer")
    return _make_authenticated_client(user)


@pytest.fixture
def anon_client():
    """Unauthenticated API client."""
    return APIClient()
