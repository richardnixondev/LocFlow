class ParserError(Exception):
    """Base exception for parser errors."""
    pass


class UnsupportedFormatError(ParserError):
    """Raised when file format is not supported."""
    pass


class ParseError(ParserError):
    """Raised when file content cannot be parsed."""
    pass


class ExportError(ParserError):
    """Raised when entries cannot be exported to target format."""
    pass
