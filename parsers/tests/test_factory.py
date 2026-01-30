import pytest
from parsers.factory import ParserFactory
from parsers.json_parser import JSONParser
from parsers.po_parser import POParser
from parsers.strings_parser import StringsParser
from parsers.xliff_parser import XLIFFParser
from parsers.exceptions import UnsupportedFormatError


class TestParserFactory:
    def test_get_json_parser(self):
        parser = ParserFactory.get_parser("json")
        assert isinstance(parser, JSONParser)

    def test_get_po_parser(self):
        parser = ParserFactory.get_parser("po")
        assert isinstance(parser, POParser)

    def test_get_pot_parser(self):
        parser = ParserFactory.get_parser("pot")
        assert isinstance(parser, POParser)

    def test_get_strings_parser(self):
        parser = ParserFactory.get_parser("strings")
        assert isinstance(parser, StringsParser)

    def test_get_xliff_parser(self):
        parser = ParserFactory.get_parser("xliff")
        assert isinstance(parser, XLIFFParser)

    def test_get_xlf_parser(self):
        parser = ParserFactory.get_parser("xlf")
        assert isinstance(parser, XLIFFParser)

    def test_unsupported_format(self):
        with pytest.raises(UnsupportedFormatError, match="Unsupported format"):
            ParserFactory.get_parser("docx")

    def test_format_case_insensitive(self):
        parser = ParserFactory.get_parser("JSON")
        assert isinstance(parser, JSONParser)

    def test_format_strips_dot(self):
        parser = ParserFactory.get_parser(".json")
        assert isinstance(parser, JSONParser)

    def test_supported_formats(self):
        formats = ParserFactory.supported_formats()
        assert "json" in formats
        assert "po" in formats
        assert "pot" in formats
        assert "strings" in formats
        assert "xliff" in formats
        assert "xlf" in formats

    def test_register_custom_parser(self):
        from parsers.base import BaseParser, ParsedEntry

        class CustomParser(BaseParser):
            def parse(self, content: str) -> list[ParsedEntry]:
                return []

            def export(self, entries: list[ParsedEntry], translations=None) -> str:
                return ""

        ParserFactory.register("custom", CustomParser)
        parser = ParserFactory.get_parser("custom")
        assert isinstance(parser, CustomParser)

        # Cleanup: remove the custom parser to avoid side effects
        del ParserFactory._parsers["custom"]
