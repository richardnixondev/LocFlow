import pytest
from parsers.strings_parser import StringsParser


@pytest.fixture
def parser():
    return StringsParser()


SIMPLE_STRINGS = '''
"greeting" = "Hello";
"farewell" = "Goodbye";
'''

STRINGS_WITH_COMMENTS = '''
/* Welcome message shown on launch */
"greeting" = "Hello";

/* Shown when user leaves */
"farewell" = "Goodbye";
'''

STRINGS_WITH_ESCAPES = '''
"quote_key" = "She said \\"hello\\"";
"newline_key" = "Line 1\\nLine 2";
"unicode_key" = "\\U0041pple";
'''


class TestStringsParserParse:
    def test_parse_simple(self, parser):
        entries = parser.parse(SIMPLE_STRINGS)

        assert len(entries) == 2
        assert entries[0].key == "greeting"
        assert entries[0].source_text == "Hello"
        assert entries[1].key == "farewell"
        assert entries[1].source_text == "Goodbye"

    def test_parse_with_comments(self, parser):
        entries = parser.parse(STRINGS_WITH_COMMENTS)

        assert len(entries) == 2
        assert entries[0].context == "Welcome message shown on launch"
        assert entries[1].context == "Shown when user leaves"

    def test_parse_escapes(self, parser):
        entries = parser.parse(STRINGS_WITH_ESCAPES)

        assert len(entries) == 3
        assert entries[0].source_text == 'She said "hello"'
        assert entries[1].source_text == "Line 1\nLine 2"
        assert entries[2].source_text == "Apple"  # \U0041 = 'A'

    def test_parse_empty_content(self, parser):
        entries = parser.parse("")
        assert entries == []

    def test_parse_preserves_order(self, parser):
        entries = parser.parse(SIMPLE_STRINGS)
        assert entries[0].order == 0
        assert entries[1].order == 1


class TestStringsParserExport:
    def test_export(self, parser):
        entries = parser.parse(STRINGS_WITH_COMMENTS)
        exported = parser.export(entries)

        assert '"greeting" = "Hello";' in exported
        assert '"farewell" = "Goodbye";' in exported
        assert "/* Welcome message shown on launch */" in exported

    def test_export_with_translations(self, parser):
        entries = parser.parse(SIMPLE_STRINGS)
        translations = {"greeting": "Hola", "farewell": "Adios"}
        exported = parser.export(entries, translations)

        assert '"greeting" = "Hola";' in exported
        assert '"farewell" = "Adios";' in exported

    def test_export_escapes_special_chars(self, parser):
        entries = parser.parse(SIMPLE_STRINGS)
        translations = {"greeting": 'He said "hi"', "farewell": "Line1\nLine2"}
        exported = parser.export(entries, translations)

        assert 'He said \\"hi\\"' in exported
        assert "Line1\\nLine2" in exported

    def test_roundtrip(self, parser):
        entries = parser.parse(STRINGS_WITH_COMMENTS)
        exported = parser.export(entries)
        re_entries = parser.parse(exported)

        assert len(re_entries) == len(entries)
        for orig, reparsed in zip(entries, re_entries):
            assert orig.key == reparsed.key
            assert orig.source_text == reparsed.source_text
            assert orig.context == reparsed.context
