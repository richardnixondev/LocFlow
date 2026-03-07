"""Tests for resource model string representations."""

import pytest

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString


@pytest.mark.django_db
class TestResourceModels:
    def test_resource_file_str(self):
        p = Project.objects.create(name="P", slug="p")
        rf = ResourceFile.objects.create(
            project=p, file_path="en.json", file_format="json", version=3, checksum="x"
        )
        assert str(rf) == "en.json v3"

    def test_translatable_string_str(self):
        p = Project.objects.create(name="P", slug="p2")
        rf = ResourceFile.objects.create(
            project=p, file_path="en.json", file_format="json", version=1, checksum="x"
        )
        s = TranslatableString.objects.create(
            project=p, resource_file=rf, key="nav.home", source_text="Home", order=0
        )
        assert str(s) == "nav.home"
