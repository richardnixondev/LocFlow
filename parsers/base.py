from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedEntry:
    key: str
    source_text: str
    context: str = ""
    has_plurals: bool = False
    plural_forms: dict = field(default_factory=dict)
    order: int = 0
    max_length: int | None = None
    flags: list[str] = field(default_factory=list)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: str) -> list[ParsedEntry]:
        """Parse file content and return a list of ParsedEntry objects."""
        ...

    @abstractmethod
    def export(self, entries: list[ParsedEntry], translations: dict[str, str] | None = None) -> str:
        """Export entries back to the original file format.

        Args:
            entries: List of ParsedEntry objects to export.
            translations: Optional dict mapping key to translated text.
        """
        ...
