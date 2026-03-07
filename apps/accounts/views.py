from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django.contrib.auth import get_user_model

from apps.accounts.permissions import IsAdminRole
from apps.accounts.serializers import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    CreateUserSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)

User = get_user_model()


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    """Get or update the current authenticated user's profile."""
    if request.method == "PATCH":
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the current user's password."""
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save()
    return Response({"detail": "Password changed successfully."})


class UserViewSet(ModelViewSet):
    """Admin-only user management (list, retrieve, create, partial update)."""

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsAdminRole]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return AdminUserSerializer
