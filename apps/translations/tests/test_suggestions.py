import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString
from apps.translations.models import Translation
from apps.translations.services import get_suggestions


@pytest.fixture
def project():
    return Project.objects.create(name="Test Project", slug="test-project")


@pytest.fixture
def project2():
    return Project.objects.create(name="Other Project", slug="other-project")


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
def resource_file2(project2):
    return ResourceFile.objects.create(
        project=project2,
        file_path="messages.json",
        file_format="json",
        version=1,
        checksum="def456",
    )


@pytest.fixture
def string_hello(project, resource_file):
    return TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="greeting",
        source_text="Hello, welcome to the application",
        order=0,
    )


@pytest.fixture
def string_similar(project, resource_file):
    return TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="greeting_v2",
        source_text="Hello, welcome to our application",
        order=1,
    )


@pytest.fixture
def string_different(project, resource_file):
    return TranslatableString.objects.create(
        project=project,
        resource_file=resource_file,
        key="error_msg",
        source_text="Something went completely wrong",
        order=2,
    )


@pytest.fixture
def string_cross_project(project2, resource_file2):
    return TranslatableString.objects.create(
        project=project2,
        resource_file=resource_file2,
        key="welcome",
        source_text="Hello, welcome to this application",
        order=0,
    )


@pytest.fixture
def approved_translation(string_similar):
    return Translation.objects.create(
        string=string_similar,
        language_code="pt-BR",
        translated_text="Olá, bem-vindo ao nosso aplicativo",
        status="approved",
    )


@pytest.fixture
def draft_translation(string_similar):
    return Translation.objects.create(
        string=string_similar,
        language_code="es",
        translated_text="Hola, bienvenido a nuestra aplicación",
        status="draft",
    )


@pytest.fixture
def cross_project_translation(string_cross_project):
    return Translation.objects.create(
        string=string_cross_project,
        language_code="pt-BR",
        translated_text="Olá, bem-vindo a este aplicativo",
        status="approved",
    )


@pytest.fixture
def different_translation(string_different):
    return Translation.objects.create(
        string=string_different,
        language_code="pt-BR",
        translated_text="Algo deu completamente errado",
        status="approved",
    )


# ==================== Service Tests ====================


@pytest.mark.django_db
class TestSuggestionsService:
    def test_returns_similar_approved_translations(
        self, string_hello, approved_translation
    ):
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="pt-BR",
            exclude_string_id=string_hello.pk,
        )
        assert len(results) == 1
        assert results[0]["source_text"] == "Hello, welcome to our application"
        assert results[0]["translated_text"] == "Olá, bem-vindo ao nosso aplicativo"
        assert results[0]["similarity"] >= 0.7

    def test_excludes_draft_translations(
        self, string_hello, draft_translation
    ):
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="es",
            exclude_string_id=string_hello.pk,
        )
        assert len(results) == 0

    def test_excludes_own_string(self, string_similar, approved_translation):
        results = get_suggestions(
            source_text=string_similar.source_text,
            language_code="pt-BR",
            exclude_string_id=string_similar.pk,
        )
        assert all(r["string_key"] != "greeting_v2" for r in results)

    def test_filters_by_language(
        self, string_hello, approved_translation
    ):
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="fr",
            exclude_string_id=string_hello.pk,
        )
        assert len(results) == 0

    def test_respects_min_similarity(
        self, string_hello, approved_translation
    ):
        # Very high threshold should return nothing
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="pt-BR",
            min_similarity=0.99,
            exclude_string_id=string_hello.pk,
        )
        assert len(results) == 0

    def test_respects_max_results(
        self, string_hello, approved_translation, cross_project_translation
    ):
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="pt-BR",
            max_results=1,
            exclude_string_id=string_hello.pk,
        )
        assert len(results) <= 1

    def test_cross_project_by_default(
        self, string_hello, approved_translation, cross_project_translation
    ):
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="pt-BR",
            exclude_string_id=string_hello.pk,
        )
        slugs = {r["project_slug"] for r in results}
        assert "other-project" in slugs or "test-project" in slugs

    def test_scope_project_limits_results(
        self, string_hello, approved_translation, cross_project_translation
    ):
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="pt-BR",
            exclude_string_id=string_hello.pk,
            project_slug="test-project",
        )
        assert all(r["project_slug"] == "test-project" for r in results)

    def test_excludes_inactive_strings(
        self, string_hello, string_similar, approved_translation
    ):
        string_similar.is_active = False
        string_similar.save()
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="pt-BR",
            exclude_string_id=string_hello.pk,
        )
        assert len(results) == 0

    def test_dissimilar_strings_filtered_out(
        self, string_hello, different_translation
    ):
        results = get_suggestions(
            source_text=string_hello.source_text,
            language_code="pt-BR",
            exclude_string_id=string_hello.pk,
        )
        assert all(r["string_key"] != "error_msg" for r in results)


# ==================== API Tests ====================


@pytest.mark.django_db
class TestSuggestionsAPI:
    def _url(self, slug, string_id):
        return reverse(
            "translation-suggestions",
            kwargs={"slug": slug, "string_id": string_id},
        )

    def test_returns_suggestions(
        self, api_client, string_hello, approved_translation
    ):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(url, {"language": "pt-BR"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["source_text"] == string_hello.source_text
        assert response.data["language"] == "pt-BR"
        assert response.data["count"] == 1
        assert len(response.data["suggestions"]) == 1

    def test_language_required(self, api_client, string_hello):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "language" in response.data["detail"].lower()

    def test_invalid_min_similarity(self, api_client, string_hello):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(url, {"language": "pt-BR", "min_similarity": "abc"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_min_similarity_out_of_range(self, api_client, string_hello):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(url, {"language": "pt-BR", "min_similarity": "1.5"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_max_results(self, api_client, string_hello):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(url, {"language": "pt-BR", "max_results": "0"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_max_results_out_of_range(self, api_client, string_hello):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(url, {"language": "pt-BR", "max_results": "101"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_scope_project(
        self, api_client, string_hello, approved_translation, cross_project_translation
    ):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(
            url, {"language": "pt-BR", "scope": "project"}
        )
        assert response.status_code == status.HTTP_200_OK
        for s in response.data["suggestions"]:
            assert s["project_slug"] == "test-project"

    def test_nonexistent_project(self, api_client, string_hello):
        url = self._url("nonexistent", string_hello.pk)
        response = api_client.get(url, {"language": "pt-BR"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_string(self, api_client, project):
        import uuid
        url = self._url("test-project", uuid.uuid4())
        response = api_client.get(url, {"language": "pt-BR"})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_empty_results(self, api_client, string_hello):
        url = self._url("test-project", string_hello.pk)
        response = api_client.get(url, {"language": "pt-BR"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["suggestions"] == []
