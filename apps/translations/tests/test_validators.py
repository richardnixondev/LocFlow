"""Tests for translations.validators — covering all branches."""

import pytest

from apps.translations.validators import validate_translation


class TestValidateTranslation:
    def test_valid_no_issues(self):
        errors = validate_translation("Hello", "Hola")
        assert errors == []

    def test_variable_mismatch(self):
        errors = validate_translation("Hello {name}", "Hola")
        assert len(errors) > 0
        assert any("name" in e for e in errors)

    def test_max_length_respected(self):
        errors = validate_translation("OK", "OK", max_length=10)
        assert errors == []

    def test_max_length_exceeded(self):
        errors = validate_translation("OK", "This is too long", max_length=5)
        assert len(errors) > 0

    def test_max_length_none_skipped(self):
        errors = validate_translation("OK", "Any length is fine", max_length=None)
        assert errors == []

    def test_max_length_zero_skipped(self):
        errors = validate_translation("OK", "Any length", max_length=0)
        assert errors == []

    def test_plurals_validated(self):
        errors = validate_translation(
            source_text="item",
            translated_text="item",
            has_plurals=True,
            plural_translations={"one": "item", "other": "items"},
            language_code="en",
        )
        assert errors == []

    def test_plurals_missing_form(self):
        errors = validate_translation(
            source_text="item",
            translated_text="item",
            has_plurals=True,
            plural_translations={"one": "item"},
            language_code="en",
        )
        assert len(errors) > 0

    def test_plurals_not_checked_without_all_args(self):
        # has_plurals=True but no plural_translations — should skip
        errors = validate_translation(
            source_text="item",
            translated_text="item",
            has_plurals=True,
            plural_translations=None,
            language_code="en",
        )
        assert errors == []

    def test_plurals_not_checked_without_language(self):
        errors = validate_translation(
            source_text="item",
            translated_text="item",
            has_plurals=True,
            plural_translations={"one": "item"},
            language_code=None,
        )
        assert errors == []
