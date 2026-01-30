import pytest
from parsers.xliff_parser import XLIFFParser
from parsers.exceptions import ParseError


@pytest.fixture
def parser():
    return XLIFFParser()


BASIC_XLIFF = '''<?xml version="1.0" encoding="UTF-8"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
  <file source-language="en" target-language="es" datatype="plaintext" original="test">
    <body>
      <trans-unit id="greeting">
        <source>Hello</source>
        <target>Hola</target>
      </trans-unit>
      <trans-unit id="farewell">
        <source>Goodbye</source>
        <target>Adios</target>
      </trans-unit>
    </body>
  </file>
</xliff>'''

XLIFF_WITH_NOTES = '''<?xml version="1.0" encoding="UTF-8"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
  <file source-language="en" target-language="de" datatype="plaintext" original="test">
    <body>
      <trans-unit id="welcome">
        <source>Welcome</source>
        <note>Shown on the home page</note>
      </trans-unit>
      <trans-unit id="error_msg" maxwidth="50">
        <source>An error occurred</source>
        <note>Generic error message</note>
      </trans-unit>
    </body>
  </file>
</xliff>'''

INVALID_XML = '<xliff><broken'


class TestXLIFFParserParse:
    def test_parse_basic(self, parser):
        entries = parser.parse(BASIC_XLIFF)

        assert len(entries) == 2
        assert entries[0].key == "greeting"
        assert entries[0].source_text == "Hello"
        assert entries[1].key == "farewell"
        assert entries[1].source_text == "Goodbye"

    def test_parse_with_notes(self, parser):
        entries = parser.parse(XLIFF_WITH_NOTES)

        assert len(entries) == 2
        assert entries[0].context == "Shown on the home page"
        assert entries[1].context == "Generic error message"

    def test_parse_max_length(self, parser):
        entries = parser.parse(XLIFF_WITH_NOTES)

        error_entry = [e for e in entries if e.key == "error_msg"][0]
        assert error_entry.max_length == 50

    def test_parse_preserves_order(self, parser):
        entries = parser.parse(BASIC_XLIFF)
        assert entries[0].order == 0
        assert entries[1].order == 1

    def test_parse_invalid_xml(self, parser):
        with pytest.raises(ParseError, match="Invalid XML"):
            parser.parse(INVALID_XML)


class TestXLIFFParserExport:
    def test_export_with_translations(self, parser):
        entries = parser.parse(BASIC_XLIFF)
        translations = {"greeting": "Bonjour", "farewell": "Au revoir"}
        exported = parser.export(entries, translations)

        assert "Bonjour" in exported
        assert "Au revoir" in exported
        assert "Hello" in exported  # source should still be there
        assert "Goodbye" in exported

    def test_export_without_translations(self, parser):
        entries = parser.parse(BASIC_XLIFF)
        exported = parser.export(entries)

        assert "Hello" in exported
        assert "Goodbye" in exported
        # Without translations, there should be no target elements
        assert "Bonjour" not in exported

    def test_export_preserves_context(self, parser):
        entries = parser.parse(XLIFF_WITH_NOTES)
        exported = parser.export(entries)

        assert "Shown on the home page" in exported
        assert "Generic error message" in exported

    def test_export_produces_valid_xml(self, parser):
        entries = parser.parse(BASIC_XLIFF)
        exported = parser.export(entries, {"greeting": "Hola"})

        # Should be re-parseable
        re_entries = parser.parse(exported)
        assert len(re_entries) == len(entries)
