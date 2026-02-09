import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString


@pytest.fixture
def project():
    return Project.objects.create(name="Test Project", slug="test-project")


@pytest.fixture
def sample_json_file():
    content = json.dumps({
        "greeting": "Hello",
        "farewell": "Goodbye",
        "welcome": "Welcome to the app",
    })
    return SimpleUploadedFile("messages.json", content.encode("utf-8"))


@pytest.mark.django_db
class TestUploadAPI:
    def test_upload_json_file(self, api_client, project, sample_json_file):
        url = reverse("resource-upload", kwargs={"slug": "test-project"})
        response = api_client.post(url, {"file": sample_json_file}, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "processed"
        assert response.data["new"] == 3
        assert response.data["version"] == 1

    def test_upload_duplicate_file(self, api_client, project):
        content = json.dumps({"key": "value"})
        file1 = SimpleUploadedFile("test.json", content.encode("utf-8"))
        file2 = SimpleUploadedFile("test.json", content.encode("utf-8"))

        url = reverse("resource-upload", kwargs={"slug": "test-project"})
        api_client.post(url, {"file": file1}, format="multipart")
        response = api_client.post(url, {"file": file2}, format="multipart")
        assert response.data["status"] == "unchanged"

    def test_upload_detects_changes(self, api_client, project):
        content_v1 = json.dumps({"key1": "Hello", "key2": "World"})
        content_v2 = json.dumps({"key1": "Hello!", "key3": "New string"})

        url = reverse("resource-upload", kwargs={"slug": "test-project"})

        file1 = SimpleUploadedFile("msgs.json", content_v1.encode("utf-8"))
        api_client.post(url, {"file": file1}, format="multipart")

        file2 = SimpleUploadedFile("msgs.json", content_v2.encode("utf-8"))
        response = api_client.post(url, {"file": file2}, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["new"] == 1       # key3
        assert response.data["updated"] == 1   # key1
        assert response.data["removed"] == 1   # key2
        assert response.data["version"] == 2

    def test_upload_invalid_format(self, api_client, project):
        file = SimpleUploadedFile("test.xyz", b"some content")
        url = reverse("resource-upload", kwargs={"slug": "test-project"})
        response = api_client.post(url, {"file": file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestResourceListAPI:
    def test_list_resources(self, api_client, project):
        ResourceFile.objects.create(
            project=project,
            file_path="messages.json",
            file_format="json",
            version=1,
            checksum="abc123",
        )
        url = reverse("resource-list", kwargs={"slug": "test-project"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestStringListAPI:
    def test_list_strings(self, api_client, project):
        rf = ResourceFile.objects.create(
            project=project,
            file_path="test.json",
            file_format="json",
            version=1,
            checksum="abc",
        )
        TranslatableString.objects.create(
            project=project,
            resource_file=rf,
            key="hello",
            source_text="Hello",
            order=0,
        )
        url = reverse("string-list", kwargs={"slug": "test-project"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["key"] == "hello"

    def test_search_strings(self, api_client, project):
        rf = ResourceFile.objects.create(
            project=project,
            file_path="test.json",
            file_format="json",
            version=1,
            checksum="abc",
        )
        TranslatableString.objects.create(
            project=project, resource_file=rf, key="btn.save", source_text="Save", order=0
        )
        TranslatableString.objects.create(
            project=project, resource_file=rf, key="btn.cancel", source_text="Cancel", order=1
        )
        url = reverse("string-list", kwargs={"slug": "test-project"})
        response = api_client.get(url, {"search": "save"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
