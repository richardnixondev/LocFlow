import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project


@pytest.mark.django_db
class TestProjectAPI:
    def test_create_project(self, api_client):
        url = reverse("project-list")
        data = {"name": "My Project", "source_language": "en"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "My Project"
        assert response.data["slug"] == "my-project"
        assert response.data["source_language"] == "en"

    def test_list_projects(self, api_client):
        Project.objects.create(name="Project A", slug="project-a")
        Project.objects.create(name="Project B", slug="project-b")
        url = reverse("project-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_project_by_slug(self, api_client):
        Project.objects.create(name="Test Project", slug="test-project")
        url = reverse("project-detail", kwargs={"slug": "test-project"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Project"

    def test_update_project(self, api_client):
        Project.objects.create(name="Old Name", slug="old-name")
        url = reverse("project-detail", kwargs={"slug": "old-name"})
        response = api_client.patch(url, {"name": "New Name"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "New Name"

    def test_delete_project(self, api_client):
        Project.objects.create(name="To Delete", slug="to-delete")
        url = reverse("project-detail", kwargs={"slug": "to-delete"})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(slug="to-delete").exists()

    def test_create_project_auto_slug(self, api_client):
        url = reverse("project-list")
        data = {"name": "Hello World App"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["slug"] == "hello-world-app"

    def test_project_not_found(self, api_client):
        url = reverse("project-detail", kwargs={"slug": "nonexistent"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
