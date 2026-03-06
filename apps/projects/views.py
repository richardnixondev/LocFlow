from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAbove
from apps.projects.models import GitHubRepo, Project
from apps.projects.serializers import (
    GitHubRepoReadSerializer,
    GitHubRepoSerializer,
    ProjectSerializer,
)
from apps.projects.services import list_repo_tree, sync_repo


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.select_related("github_repo").all()
    serializer_class = ProjectSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsManagerOrAbove()]
        return [IsAuthenticated()]


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsManagerOrAbove])
def github_repo_detail(request, slug):
    """Get, update, or remove a GitHub repo link for a project."""
    project = get_object_or_404(Project, slug=slug)

    if request.method == "GET":
        try:
            gh = project.github_repo
        except GitHubRepo.DoesNotExist:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        return Response(GitHubRepoReadSerializer(gh).data)

    if request.method == "DELETE":
        GitHubRepo.objects.filter(project=project).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PUT — create or update
    try:
        gh = project.github_repo
        serializer = GitHubRepoSerializer(gh, data=request.data, partial=True)
    except GitHubRepo.DoesNotExist:
        serializer = GitHubRepoSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    serializer.save(project=project)

    gh = project.github_repo
    return Response(GitHubRepoReadSerializer(gh).data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsManagerOrAbove])
def github_repo_files(request, slug):
    """List resource files detected in the linked GitHub repo."""
    project = get_object_or_404(Project, slug=slug)
    try:
        gh = project.github_repo
    except GitHubRepo.DoesNotExist:
        return Response(
            {"detail": "No GitHub repository linked."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        files = list_repo_tree(gh)
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"count": len(files), "files": files})


@api_view(["POST"])
@permission_classes([IsManagerOrAbove])
def github_repo_sync(request, slug):
    """Trigger a sync: import all resource files from the linked GitHub repo."""
    project = get_object_or_404(Project, slug=slug)
    try:
        gh = project.github_repo
    except GitHubRepo.DoesNotExist:
        return Response(
            {"detail": "No GitHub repository linked."},
            status=status.HTTP_404_NOT_FOUND,
        )

    results = sync_repo(gh)
    return Response(results)
