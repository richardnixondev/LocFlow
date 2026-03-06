import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString
from apps.translations.models import Translation


@pytest.fixture
def project(db):
    return Project.objects.create(name="Perm Project", slug="perm-project")


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
def translatable_string(project, resource_file):
    return TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="greeting",
        source_text="Hello",
        order=0,
    )


@pytest.mark.django_db
class TestUnauthenticatedAccess:
    """Unauthenticated requests should get 401 on all endpoints."""

    def test_list_projects_401(self, anon_client):
        url = reverse("project-list")
        response = anon_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_project_401(self, anon_client):
        url = reverse("project-list")
        response = anon_client.post(url, {"name": "X"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_strings_401(self, anon_client, project):
        url = reverse("string-list", kwargs={"slug": project.slug})
        response = anon_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_translation_401(self, anon_client, project, translatable_string):
        url = reverse(
            "translation-create",
            kwargs={"slug": project.slug, "string_id": translatable_string.pk},
        )
        response = anon_client.post(
            url, {"language_code": "pt", "translated_text": "Olá"}, format="json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_progress_401(self, anon_client, project):
        url = reverse("translation-progress", kwargs={"slug": project.slug})
        response = anon_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_export_401(self, anon_client, project):
        url = reverse(
            "export-translations",
            kwargs={"slug": project.slug, "language": "pt", "file_format": "json"},
        )
        response = anon_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestViewerPermissions:
    """Viewer can read but cannot write."""

    def test_viewer_list_projects(self, viewer_client, project):
        url = reverse("project-list")
        response = viewer_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_viewer_create_project_403(self, viewer_client):
        url = reverse("project-list")
        response = viewer_client.post(url, {"name": "New"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_create_translation_403(
        self, viewer_client, project, translatable_string
    ):
        url = reverse(
            "translation-create",
            kwargs={"slug": project.slug, "string_id": translatable_string.pk},
        )
        response = viewer_client.post(
            url, {"language_code": "pt", "translated_text": "Olá"}, format="json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_read_progress(self, viewer_client, project):
        url = reverse("translation-progress", kwargs={"slug": project.slug})
        response = viewer_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTranslatorPermissions:
    """Translator can read and create translations, but cannot manage projects."""

    def test_translator_list_projects(self, translator_client, project):
        url = reverse("project-list")
        response = translator_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_translator_create_project_403(self, translator_client):
        url = reverse("project-list")
        response = translator_client.post(url, {"name": "New"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_translator_create_translation(
        self, translator_client, project, translatable_string
    ):
        url = reverse(
            "translation-create",
            kwargs={"slug": project.slug, "string_id": translatable_string.pk},
        )
        response = translator_client.post(
            url, {"language_code": "pt", "translated_text": "Olá"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_translator_update_translation(
        self, translator_client, project, translatable_string
    ):
        translation = Translation.objects.create(
            string=translatable_string,
            language_code="pt",
            translated_text="Olá",
        )
        url = reverse(
            "translation-update",
            kwargs={
                "slug": project.slug,
                "string_id": translatable_string.pk,
                "language": "pt",
            },
        )
        response = translator_client.patch(
            url, {"translated_text": "Oi"}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestManagerPermissions:
    """Manager can create projects and upload resources."""

    def test_manager_create_project(self, api_client):
        url = reverse("project-list")
        response = api_client.post(
            url, {"name": "Manager Project"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_manager_delete_project(self, api_client, project):
        url = reverse("project-detail", kwargs={"slug": project.slug})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
