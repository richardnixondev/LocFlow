"""Tests for translation model string representation."""

import pytest

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString
from apps.translations.models import Translation


@pytest.mark.django_db
class TestTranslationModel:
    def test_str(self):
        p = Project.objects.create(name="P", slug="p")
        rf = ResourceFile.objects.create(
            project=p, file_path="en.json", file_format="json", version=1, checksum="x"
        )
        s = TranslatableString.objects.create(
            project=p, resource_file=rf, key="greeting", source_text="Hello", order=0
        )
        t = Translation.objects.create(
            string=s, language_code="pt-BR", translated_text="Ola"
        )
        assert str(t) == "greeting [pt-BR]"
