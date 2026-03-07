from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import UserViewSet, change_password, me

router = DefaultRouter()
router.register("users", UserViewSet)

urlpatterns = [
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", me, name="auth-me"),
    path("auth/change-password/", change_password, name="auth-change-password"),
    path("", include(router.urls)),
]
