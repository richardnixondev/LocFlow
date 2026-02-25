from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allows access only to users with admin role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_role
        )


class IsManagerOrAbove(BasePermission):
    """Allows access to users with manager or admin role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_manager_or_above
        )


class IsTranslatorOrAbove(BasePermission):
    """Allows access to users with translator, manager, or admin role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_translator_or_above
        )
