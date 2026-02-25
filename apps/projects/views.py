from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsManagerOrAbove
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsManagerOrAbove()]
        return [IsAuthenticated()]
