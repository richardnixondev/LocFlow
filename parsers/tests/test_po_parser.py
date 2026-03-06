import pytest
from parsers.po_parser import POParser
from parsers.exceptions import ParseError


@pytest.fixture
def parser():
    return POParser()


SIMPLE_PO = '''
msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\\n"

msgid "Hello"
msgstr "Hola"

msgid "Goodbye"
msgstr "Adios"
'''

PLURAL_PO = '''
msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

msgid "%d item"
msgid_plural "%d items"
msgstr[0] "%d elemento"
msgstr[1] "%d elementos"
'''

CONTEXT_PO = '''
msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\\n"

msgctxt "menu"
msgid "File"
msgstr "Archivo"

msgctxt "action"
msgid "File"
msgstr "Archivar"
'''


class TestPOParserParse:
    def test_parse_simple(self, parser):
        entries = parser.parse(SIMPLE_PO)

        assert len(entries) == 2
        assert entries[0].source_text == "Hello"
        assert entries[0].key == "Hello"
        assert entries[1].source_text == "Goodbye"

    def test_parse_plurals(self, parser):
        entries = parser.parse(PLURAL_PO)

        assert len(entries) == 1
        entry = entries[0]
        assert entry.has_plurals is True
        assert entry.source_text == "%d item"
        assert entry.plural_forms["one"] == "%d item"
        assert entry.plural_forms["other"] == "%d items"

    def test_parse_context(self, parser):
        entries = parser.parse(CONTEXT_PO)

        assert len(entries) == 2
        # Keys should include context separator
        keys = [e.key for e in entries]
        assert "menu\x04File" in keys
        assert "action\x04File" in keys

        # Context should be preserved
        for entry in entries:
            assert entry.context != ""

    def test_parse_flags(self, parser):
        po_content = '''
msgid ""
msgstr ""
"Content-Type: text/plain; charset=utf-8\\n"

#, fuzzy
msgid "Draft"
msgstr "Borrador"
'''
        entries = parser.parse(po_content)
        assert len(entries) == 1
        assert "fuzzy" in entries[0].flags


class TestPOParserExport:
    def test_export_simple(self, parser):
        entries = parser.parse(SIMPLE_PO)
        exported = parser.export(entries, translations={"Hello": "Hola", "Goodbye": "Adios"})

        assert "msgid" in exported
        assert "msgstr" in exported
        assert "Hello" in exported
        assert "Hola" in exported

    def test_export_preserves_structure(self, parser):
        entries = parser.parse(SIMPLE_PO)
        exported = parser.export(entries)

        # Should be valid PO that can be re-parsed
        re_entries = parser.parse(exported)
        assert len(re_entries) == len(entries)
        for orig, reparsed in zip(entries, re_entries):
            assert orig.source_text == reparsed.source_text
