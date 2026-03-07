"""Additional tests for resources views — string filters, detail, export."""

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString
from apps.translations.models import Translation


@pytest.fixture
def project():
    return Project.objects.create(name="Test Project", slug="test-project")


@pytest.fixture
def resource_file(project):
    return ResourceFile.objects.create(
        project=project,
        file_path="messages.json",
        file_format="json",
        version=1,
        checksum="abc123",
    )


@pytest.fixture
def strings(project, resource_file):
    s1 = TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="greeting",
        source_text="Hello",
        order=0,
    )
    s2 = TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="farewell",
        source_text="Goodbye",
        order=1,
    )
    s3 = TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="welcome",
        source_text="Welcome",
        order=2,
    )
    return s1, s2, s3


@pytest.mark.django_db
class TestStringDetail:
    def test_get_string_detail(self, api_client, project, resource_file):
        s = TranslatableString.objects.create(
            project=project,
            resource_file=resource_file,
            key="hello",
            source_text="Hello",
            order=0,
        )
        url = reverse("string-detail", kwargs={"slug": "test-project", "string_id": s.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["key"] == "hello"
        assert response.data["source_text"] == "Hello"

    def test_string_detail_not_found(self, api_client, project):
        import uuid

        url = reverse(
            "string-detail",
            kwargs={"slug": "test-project", "string_id": uuid.uuid4()},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_string_detail_with_translations(self, api_client, project, resource_file):
        s = TranslatableString.objects.create(
            project=project,
            resource_file=resource_file,
            key="btn.save",
            source_text="Save",
            order=0,
        )
        Translation.objects.create(
            string=s,
            language_code="pt-BR",
            translated_text="Salvar",
            status="approved",
        )
        url = reverse("string-detail", kwargs={"slug": "test-project", "string_id": s.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["translations"]) == 1


@pytest.mark.django_db
class TestStringFilters:
    def test_filter_by_language(self, api_client, project, strings):
        s1, s2, _ = strings
        Translation.objects.create(
            string=s1, language_code="pt-BR", translated_text="Ola", status="draft"
        )
        url = reverse("string-list", kwargs={"slug": "test-project"})
        response = api_client.get(url, {"language": "pt-BR"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["key"] == "greeting"

    def test_filter_untranslated(self, api_client, project, strings):
        s1, _, _ = strings
        Translation.objects.create(
            string=s1, language_code="pt-BR", translated_text="Ola", status="draft"
        )
        url = reverse("string-list", kwargs={"slug": "test-project"})
        response = api_client.get(url, {"language": "pt-BR", "untranslated": "true"})
        assert response.status_code == status.HTTP_200_OK
        keys = [s["key"] for s in response.data]
        assert "greeting" not in keys
        assert "farewell" in keys
        assert "welcome" in keys

    def test_filter_by_status(self, api_client, project, strings):
        s1, s2, _ = strings
        Translation.objects.create(
            string=s1, language_code="es", translated_text="Hola", status="approved"
        )
        Translation.objects.create(
            string=s2, language_code="es", translated_text="Adios", status="draft"
        )
        url = reverse("string-list", kwargs={"slug": "test-project"})
        response = api_client.get(url, {"language": "es", "status": "approved"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["key"] == "greeting"

    def test_inactive_strings_excluded(self, api_client, project, resource_file):
        TranslatableString.objects.create(
            project=project,
            resource_file=resource_file,
            key="active",
            source_text="Active",
            order=0,
            is_active=True,
        )
        TranslatableString.objects.create(
            project=project,
            resource_file=resource_file,
            key="removed",
            source_text="Removed",
            order=1,
            is_active=False,
        )
        url = reverse("string-list", kwargs={"slug": "test-project"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        keys = [s["key"] for s in response.data]
        assert "active" in keys
        assert "removed" not in keys


@pytest.mark.django_db
class TestExportTranslations:
    def test_export_json(self, api_client, project, resource_file):
        s = TranslatableString.objects.create(
            project=project,
            resource_file=resource_file,
            key="greeting",
            source_text="Hello",
            order=0,
        )
        Translation.objects.create(
            string=s, language_code="pt-BR", translated_text="Ola", status="approved"
        )
        url = reverse(
            "export-translations",
            kwargs={"slug": "test-project", "language": "pt-BR", "file_format": "json"},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "greeting" in str(response.content)

    def test_export_without_translations(self, api_client, project, resource_file):
        TranslatableString.objects.create(
            project=project,
            resource_file=resource_file,
            key="hello",
            source_text="Hello",
            order=0,
        )
        url = reverse(
            "export-translations",
            kwargs={"slug": "test-project", "language": "fr", "file_format": "json"},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_export_unsupported_format(self, api_client, project):
        url = reverse(
            "export-translations",
            kwargs={"slug": "test-project", "language": "en", "file_format": "csv"},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_export_nonexistent_project(self, api_client):
        url = reverse(
            "export-translations",
            kwargs={"slug": "nonexistent", "language": "en", "file_format": "json"},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUploadEdgeCases:
    def test_upload_utf8_error(self, api_client, project):
        # Create a file with invalid UTF-8 bytes
        bad_bytes = b"\xff\xfe invalid utf-8"
        file = SimpleUploadedFile("test.json", bad_bytes)
        url = reverse("resource-upload", kwargs={"slug": "test-project"})
        response = api_client.post(url, {"file": file}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "UTF-8" in response.data["error"]

    def test_upload_with_explicit_format(self, api_client, project):
        content = json.dumps({"key": "value"})
        file = SimpleUploadedFile("data.txt", content.encode("utf-8"))
        url = reverse("resource-upload", kwargs={"slug": "test-project"})
        response = api_client.post(
            url, {"file": file, "file_format": "json"}, format="multipart"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_nonexistent_project(self, api_client):
        content = json.dumps({"key": "value"})
        file = SimpleUploadedFile("test.json", content.encode("utf-8"))
        url = reverse("resource-upload", kwargs={"slug": "nonexistent"})
        response = api_client.post(url, {"file": file}, format="multipart")
        assert response.status_code == status.HTTP_404_NOT_FOUND
