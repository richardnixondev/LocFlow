"""URL configuration for locflow project."""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView

from locflow.views import swagger_ui

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.accounts.urls')),
    path('api/v1/', include('apps.projects.urls')),
    path('api/v1/', include('apps.resources.urls')),
    path('api/v1/', include('apps.translations.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', swagger_ui, name='swagger-ui'),
]
