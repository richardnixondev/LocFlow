"""Tests for project and GitHub repo model behavior."""

import pytest

from apps.projects.models import GitHubRepo, Project


@pytest.mark.django_db
class TestProjectModel:
    def test_str(self):
        p = Project.objects.create(name="My App", slug="my-app")
        assert str(p) == "My App"

    def test_auto_slug_dedup(self):
        Project.objects.create(name="Demo", slug="demo")
        p2 = Project(name="Demo")
        p2.save()
        assert p2.slug == "demo-1"

    def test_auto_slug_dedup_multiple(self):
        Project.objects.create(name="Test", slug="test")
        Project.objects.create(name="Test", slug="test-1")
        p3 = Project(name="Test")
        p3.save()
        assert p3.slug == "test-2"


@pytest.mark.django_db
class TestGitHubRepoModel:
    def test_str(self):
        p = Project.objects.create(name="GH", slug="gh")
        gh = GitHubRepo.objects.create(
            project=p, owner="acme", repo="locales", branch="main"
        )
        assert str(gh) == "acme/locales:main"

    def test_full_name(self):
        p = Project.objects.create(name="GH2", slug="gh2")
        gh = GitHubRepo.objects.create(
            project=p, owner="acme", repo="app", branch="main"
        )
        assert gh.full_name == "acme/app"
