import pytest
from parsers.validation import (
    extract_variables,
    validate_variables,
    validate_length,
    validate_plural_forms,
)


class TestExtractVariables:
    def test_extract_printf_variables(self):
        text = "Hello %s, you have %d messages"
        variables = extract_variables(text)
        assert "%s" in variables
        assert "%d" in variables

    def test_extract_python_variables(self):
        text = "Hello {name}, you have {count} messages"
        variables = extract_variables(text)
        assert "{name}" in variables
        assert "{count}" in variables

    def test_extract_positional_printf(self):
        text = "Hello %1$s, meet %2$s"
        variables = extract_variables(text)
        assert "%1$s" in variables
        assert "%2$s" in variables

    def test_extract_empty_braces(self):
        text = "Hello {}, you have {} messages"
        variables = extract_variables(text)
        assert "{}" in variables

    def test_extract_no_variables(self):
        text = "Hello world"
        variables = extract_variables(text)
        assert len(variables) == 0

    def test_extract_handlebars_variables(self):
        text = "Hello {{name}}"
        variables = extract_variables(text)
        assert "{{name}}" in variables or "name" in variables

    def test_extract_ruby_variables(self):
        text = "Hello %{name}"
        variables = extract_variables(text)
        assert "name" in variables


class TestValidateVariables:
    def test_validate_variables_ok(self):
        source = "Hello %s, you have %d messages"
        translation = "Hola %s, tienes %d mensajes"
        errors = validate_variables(source, translation)
        assert errors == []

    def test_validate_variables_missing(self):
        source = "Hello %s, you have %d messages"
        translation = "Hola, tienes mensajes"
        errors = validate_variables(source, translation)
        assert len(errors) > 0
        assert "Missing variables" in errors[0]

    def test_validate_variables_extra(self):
        source = "Hello %s"
        translation = "Hola %s, %d extras"
        errors = validate_variables(source, translation)
        assert any("Extra variables" in e for e in errors)

    def test_validate_python_format_ok(self):
        source = "Hello {name}"
        translation = "Hola {name}"
        errors = validate_variables(source, translation)
        assert errors == []


class TestValidateLength:
    def test_validate_length_ok(self):
        errors = validate_length("Short", 100)
        assert errors == []

    def test_validate_length_exceeded(self):
        errors = validate_length("This is a very long translation", 10)
        assert len(errors) == 1
        assert "exceeds max length" in errors[0]

    def test_validate_length_none(self):
        errors = validate_length("Any length is fine", None)
        assert errors == []

    def test_validate_length_exact(self):
        errors = validate_length("12345", 5)
        assert errors == []


class TestValidatePluralForms:
    def test_validate_plural_forms(self):
        translations = {"one": "item", "other": "items"}
        errors = validate_plural_forms(translations, "en")
        assert errors == []

    def test_validate_plural_forms_missing(self):
        translations = {"one": "item"}
        errors = validate_plural_forms(translations, "en")
        assert len(errors) == 1
        assert "Missing plural forms" in errors[0]

    def test_validate_plural_forms_slavic(self):
        # Polish requires one, few, many, other
        translations = {
            "one": "element",
            "few": "elementy",
            "many": "elementow",
            "other": "elementow",
        }
        errors = validate_plural_forms(translations, "pl")
        assert errors == []

    def test_validate_plural_forms_slavic_missing(self):
        translations = {"one": "element", "other": "elementow"}
        errors = validate_plural_forms(translations, "pl")
        assert len(errors) == 1
        assert "few" in errors[0] or "many" in errors[0]

    def test_validate_plural_forms_east_asian(self):
        # Japanese only needs "other"
        translations = {"other": "items"}
        errors = validate_plural_forms(translations, "ja")
        assert errors == []
