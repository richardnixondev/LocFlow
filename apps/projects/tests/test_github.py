"""Tests for GitHub integration views and services (mocked HTTP)."""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.projects.models import GitHubRepo, Project


@pytest.fixture
def project():
    return Project.objects.create(name="GH Project", slug="gh-project")


@pytest.fixture
def github_repo(project):
    return GitHubRepo.objects.create(
        project=project, owner="testowner", repo="testrepo", branch="main"
    )


@pytest.mark.django_db
class TestGitHubRepoDetail:
    url_name = "github-repo"

    def _url(self, slug="gh-project"):
        return reverse(self.url_name, kwargs={"slug": slug})

    def test_get_no_repo_linked(self, api_client, project):
        response = api_client.get(self._url())
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_repo_linked(self, api_client, project, github_repo):
        response = api_client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["owner"] == "testowner"
        assert response.data["repo"] == "testrepo"
        assert response.data["full_name"] == "testowner/testrepo"

    def test_put_create_repo(self, api_client, project):
        response = api_client.put(
            self._url(),
            {"owner": "myorg", "repo": "myrepo"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["owner"] == "myorg"
        assert GitHubRepo.objects.filter(project=project).exists()

    def test_put_update_repo(self, api_client, project, github_repo):
        response = api_client.put(
            self._url(),
            {"branch": "develop"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        github_repo.refresh_from_db()
        assert github_repo.branch == "develop"

    def test_delete_repo(self, api_client, project, github_repo):
        response = api_client.delete(self._url())
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not GitHubRepo.objects.filter(project=project).exists()

    def test_nonexistent_project(self, api_client):
        url = reverse(self.url_name, kwargs={"slug": "nope"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestGitHubRepoFiles:
    def _url(self, slug="gh-project"):
        return reverse("github-files", kwargs={"slug": slug})

    def test_no_repo_linked(self, api_client, project):
        response = api_client.get(self._url())
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("apps.projects.views.list_repo_tree")
    def test_list_files_success(self, mock_tree, api_client, project, github_repo):
        mock_tree.return_value = [
            {"path": "locales/en.json", "sha": "abc", "size": 100, "extension": "json"},
        ]
        response = api_client.get(self._url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["files"][0]["path"] == "locales/en.json"

    @patch("apps.projects.views.list_repo_tree", side_effect=Exception("API error"))
    def test_list_files_error(self, mock_tree, api_client, project, github_repo):
        response = api_client.get(self._url())
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "API error" in response.data["detail"]


@pytest.mark.django_db
class TestGitHubRepoSync:
    def _url(self, slug="gh-project"):
        return reverse("github-sync", kwargs={"slug": slug})

    def test_no_repo_linked(self, api_client, project):
        response = api_client.post(self._url())
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("apps.projects.views.sync_repo")
    def test_sync_success(self, mock_sync, api_client, project, github_repo):
        mock_sync.return_value = {
            "files_found": 2,
            "files_synced": 2,
            "errors": [],
            "details": [],
        }
        response = api_client.post(self._url())
        assert response.status_code == status.HTTP_200_OK
        assert response.data["files_synced"] == 2


@pytest.mark.django_db
class TestGitHubServices:
    """Test GitHub services with mocked HTTP calls."""

    @patch("apps.projects.services.requests.get")
    def test_list_repo_tree(self, mock_get, project, github_repo):
        from apps.projects.services import list_repo_tree

        # First call = _resolve_branch, second call = list_repo_tree
        branch_resp = MagicMock()
        branch_resp.status_code = 200
        branch_resp.json.return_value = {
            "tree": [
                {"type": "blob", "path": "locales/en.json", "sha": "a1", "size": 50},
                {"type": "blob", "path": "README.md", "sha": "a2", "size": 200},
                {"type": "tree", "path": "locales", "sha": "a3"},
            ]
        }

        tree_resp = MagicMock()
        tree_resp.status_code = 200
        tree_resp.json.return_value = branch_resp.json.return_value

        mock_get.return_value = branch_resp

        files = list_repo_tree(github_repo)
        assert len(files) == 1
        assert files[0]["path"] == "locales/en.json"

    @patch("apps.projects.services.requests.get")
    def test_resolve_branch_fallback(self, mock_get, project, github_repo):
        from apps.projects.services import list_repo_tree

        github_repo.branch = "main"
        github_repo.save()

        # First call (main) returns 404, second call (master) returns 200
        resp_404 = MagicMock()
        resp_404.status_code = 404

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"tree": []}

        mock_get.side_effect = [resp_404, resp_200, resp_200]

        files = list_repo_tree(github_repo)
        assert files == []
        github_repo.refresh_from_db()
        assert github_repo.branch == "master"

    @patch("apps.projects.services._get")
    def test_fetch_file_content_base64(self, mock_get, project, github_repo):
        import base64

        from apps.projects.services import fetch_file_content

        encoded = base64.b64encode(b'{"key": "value"}').decode()
        mock_get.return_value = MagicMock(
            json=lambda: {"encoding": "base64", "content": encoded}
        )

        content = fetch_file_content(github_repo, "test.json")
        assert content == '{"key": "value"}'

    @patch("apps.projects.services._get")
    def test_fetch_file_content_raw(self, mock_get, project, github_repo):
        from apps.projects.services import fetch_file_content

        mock_get.return_value = MagicMock(
            json=lambda: {"content": '{"raw": true}'}
        )

        content = fetch_file_content(github_repo, "test.json")
        assert content == '{"raw": true}'

    @patch("apps.projects.services.list_repo_tree")
    @patch("apps.projects.services.fetch_file_content")
    def test_sync_repo_success(self, mock_fetch, mock_tree, project, github_repo):
        from apps.projects.services import sync_repo

        mock_tree.return_value = [
            {"path": "en.json", "sha": "a1", "size": 50, "extension": "json"},
        ]
        mock_fetch.return_value = '{"greeting": "Hello"}'

        result = sync_repo(github_repo)
        assert result["files_synced"] == 1
        assert result["errors"] == []
        github_repo.refresh_from_db()
        assert github_repo.last_sync_status == "success"

    @patch("apps.projects.services.list_repo_tree")
    def test_sync_repo_no_files(self, mock_tree, project, github_repo):
        from apps.projects.services import sync_repo

        mock_tree.return_value = []

        result = sync_repo(github_repo)
        assert result["files_synced"] == 0
        github_repo.refresh_from_db()
        assert github_repo.last_sync_status == "warning"

    @patch("apps.projects.services.list_repo_tree")
    @patch("apps.projects.services.fetch_file_content", side_effect=Exception("parse error"))
    def test_sync_repo_file_error(self, mock_fetch, mock_tree, project, github_repo):
        from apps.projects.services import sync_repo

        mock_tree.return_value = [
            {"path": "bad.json", "sha": "a1", "size": 50, "extension": "json"},
        ]

        result = sync_repo(github_repo)
        assert result["files_synced"] == 0
        assert len(result["errors"]) == 1

    @patch("apps.projects.services.list_repo_tree", side_effect=Exception("boom"))
    def test_sync_repo_unexpected_error(self, mock_tree, project, github_repo):
        from apps.projects.services import sync_repo

        result = sync_repo(github_repo)
        assert len(result["errors"]) == 1
        github_repo.refresh_from_db()
        assert github_repo.last_sync_status == "error"
