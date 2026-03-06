from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.projects.views import (
    ProjectViewSet,
    github_repo_detail,
    github_repo_files,
    github_repo_sync,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("projects/<slug:slug>/github/", github_repo_detail, name="github-repo"),
    path("projects/<slug:slug>/github/files/", github_repo_files, name="github-files"),
    path("projects/<slug:slug>/github/sync/", github_repo_sync, name="github-sync"),
]
