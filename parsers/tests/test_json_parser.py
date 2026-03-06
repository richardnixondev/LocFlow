import json
import pytest
from parsers.json_parser import JSONParser
from parsers.exceptions import ParseError


@pytest.fixture
def parser():
    return JSONParser()


class TestJSONParserParse:
    def test_parse_flat_json(self, parser):
        content = json.dumps({
            "greeting": "Hello",
            "farewell": "Goodbye",
            "thanks": "Thank you",
        })
        entries = parser.parse(content)

        assert len(entries) == 3
        assert entries[0].key == "greeting"
        assert entries[0].source_text == "Hello"
        assert entries[1].key == "farewell"
        assert entries[1].source_text == "Goodbye"
        assert entries[2].key == "thanks"
        assert entries[2].source_text == "Thank you"

    def test_parse_nested_json(self, parser):
        content = json.dumps({
            "common": {
                "ok": "OK",
                "cancel": "Cancel",
            },
            "auth": {
                "login": "Log in",
                "logout": "Log out",
            },
        })
        entries = parser.parse(content)

        keys = {e.key for e in entries}
        assert "common.ok" in keys
        assert "common.cancel" in keys
        assert "auth.login" in keys
        assert "auth.logout" in keys
        assert len(entries) == 4

    def test_parse_i18next_plurals(self, parser):
        content = json.dumps({
            "item_one": "{{count}} item",
            "item_other": "{{count}} items",
            "message": "Hello world",
        })
        entries = parser.parse(content)

        # Should have 2 entries: one plural group + one regular
        assert len(entries) == 2

        regular = [e for e in entries if not e.has_plurals]
        plural = [e for e in entries if e.has_plurals]

        assert len(regular) == 1
        assert regular[0].key == "message"

        assert len(plural) == 1
        assert plural[0].key == "item"
        assert plural[0].has_plurals is True
        assert plural[0].plural_forms["one"] == "{{count}} item"
        assert plural[0].plural_forms["other"] == "{{count}} items"

    def test_parse_invalid_json(self, parser):
        with pytest.raises(ParseError, match="Invalid JSON"):
            parser.parse("{invalid json content")

    def test_parse_non_object_root(self, parser):
        with pytest.raises(ParseError, match="JSON root must be an object"):
            parser.parse('["array", "not", "object"]')

    def test_parse_empty_object(self, parser):
        entries = parser.parse("{}")
        assert entries == []

    def test_parse_preserves_order(self, parser):
        content = json.dumps({
            "z_key": "last",
            "a_key": "first",
            "m_key": "middle",
        })
        entries = parser.parse(content)
        assert entries[0].order == 0
        assert entries[1].order == 1
        assert entries[2].order == 2


class TestJSONParserExport:
    def test_export_flat(self, parser):
        content = json.dumps({"greeting": "Hello", "farewell": "Goodbye"})
        entries = parser.parse(content)
        exported = parser.export(entries)
        result = json.loads(exported)

        assert result["greeting"] == "Hello"
        assert result["farewell"] == "Goodbye"

    def test_export_nested(self, parser):
        content = json.dumps({
            "common": {
                "ok": "OK",
                "cancel": "Cancel",
            }
        })
        entries = parser.parse(content)
        exported = parser.export(entries)
        result = json.loads(exported)

        assert result["common"]["ok"] == "OK"
        assert result["common"]["cancel"] == "Cancel"

    def test_export_with_translations(self, parser):
        content = json.dumps({"greeting": "Hello"})
        entries = parser.parse(content)
        translations = {"greeting": "Hola"}
        exported = parser.export(entries, translations)
        result = json.loads(exported)

        assert result["greeting"] == "Hola"

    def test_roundtrip(self, parser):
        original = {
            "title": "My App",
            "menu": {
                "home": "Home",
                "settings": "Settings",
            },
        }
        content = json.dumps(original)
        entries = parser.parse(content)
        exported = parser.export(entries)
        result = json.loads(exported)

        assert result == original

    def test_export_plurals(self, parser):
        content = json.dumps({
            "item_one": "{{count}} item",
            "item_other": "{{count}} items",
        })
        entries = parser.parse(content)
        exported = parser.export(entries)
        result = json.loads(exported)

        assert result["item_one"] == "{{count}} item"
        assert result["item_other"] == "{{count}} items"
