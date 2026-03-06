from parsers.base import BaseParser
from parsers.json_parser import JSONParser
from parsers.po_parser import POParser
from parsers.strings_parser import StringsParser
from parsers.xliff_parser import XLIFFParser
from parsers.exceptions import UnsupportedFormatError


class ParserFactory:
    _parsers: dict[str, type[BaseParser]] = {
        "json": JSONParser,
        "po": POParser,
        "pot": POParser,
        "strings": StringsParser,
        "xliff": XLIFFParser,
        "xlf": XLIFFParser,
    }

    @classmethod
    def get_parser(cls, file_format: str) -> BaseParser:
        """Get a parser instance for the given file format.

        Args:
            file_format: File extension or format name (e.g., 'json', 'po', 'strings', 'xliff')

        Returns:
            An instance of the appropriate parser.

        Raises:
            UnsupportedFormatError: If the format is not supported.
        """
        file_format = file_format.lower().lstrip(".")
        parser_class = cls._parsers.get(file_format)
        if parser_class is None:
            supported = ", ".join(sorted(cls._parsers.keys()))
            raise UnsupportedFormatError(
                f"Unsupported format: '{file_format}'. Supported formats: {supported}"
            )
        return parser_class()

    @classmethod
    def register(cls, format_name: str, parser_class: type[BaseParser]) -> None:
        """Register a new parser for a file format."""
        cls._parsers[format_name.lower()] = parser_class

    @classmethod
    def supported_formats(cls) -> list[str]:
        """Return list of supported format names."""
        return sorted(cls._parsers.keys())
