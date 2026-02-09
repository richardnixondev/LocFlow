import pytest
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
def translatable_string(project, resource_file):
    return TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="greeting",
        source_text="Hello",
        order=0,
    )


@pytest.mark.django_db
class TestTranslationAPI:
    def test_create_translation(self, api_client, translatable_string):
        url = reverse(
            "translation-create",
            kwargs={"slug": "test-project", "string_id": translatable_string.pk},
        )
        data = {
            "language_code": "pt-BR",
            "translated_text": "Ola",
            "status": "draft",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["language_code"] == "pt-BR"
        assert response.data["translated_text"] == "Ola"

    def test_update_translation(self, api_client, translatable_string):
        Translation.objects.create(
            string=translatable_string,
            language_code="es",
            translated_text="Hola",
            status="draft",
        )
        url = reverse(
            "translation-update",
            kwargs={
                "slug": "test-project",
                "string_id": translatable_string.pk,
                "language": "es",
            },
        )
        response = api_client.put(
            url,
            {
                "string": str(translatable_string.pk),
                "language_code": "es",
                "translated_text": "Hola!",
                "status": "review",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["translated_text"] == "Hola!"
        assert response.data["status"] == "review"


@pytest.mark.django_db
class TestProgressAPI:
    def test_progress_empty(self, api_client, project):
        url = reverse("translation-progress", kwargs={"slug": "test-project"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_strings"] == 0
        assert response.data["languages"] == []

    def test_progress_with_translations(
        self, api_client, project, resource_file, translatable_string
    ):
        s2 = TranslatableString.objects.create(
            project=project,
            resource_file=resource_file,
            key="farewell",
            source_text="Goodbye",
            order=1,
        )
        Translation.objects.create(
            string=translatable_string,
            language_code="pt-BR",
            translated_text="Ola",
            status="approved",
        )
        Translation.objects.create(
            string=s2,
            language_code="pt-BR",
            translated_text="Adeus",
            status="draft",
        )
        Translation.objects.create(
            string=translatable_string,
            language_code="es",
            translated_text="Hola",
            status="draft",
        )

        url = reverse("translation-progress", kwargs={"slug": "test-project"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_strings"] == 2

        languages = {l["code"]: l for l in response.data["languages"]}
        assert languages["pt-BR"]["translated"] == 2
        assert languages["pt-BR"]["approved"] == 1
        assert languages["pt-BR"]["progress_percent"] == 100.0
        assert languages["es"]["translated"] == 1
        assert languages["es"]["progress_percent"] == 50.0
