import re
from parsers.base import BaseParser, ParsedEntry
from parsers.exceptions import ParseError

# Regex patterns for .strings format
COMMENT_PATTERN = re.compile(r'/\*\s*(.*?)\s*\*/', re.DOTALL)
ENTRY_PATTERN = re.compile(
    r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;'
)


class StringsParser(BaseParser):
    def parse(self, content: str) -> list[ParsedEntry]:
        entries = []
        # Track comments for context
        last_comment = ""
        order = 0

        # Process line by line to associate comments with entries
        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Multi-line comment
            if line.startswith("/*"):
                comment_text = line
                while "*/" not in comment_text and i < len(lines) - 1:
                    i += 1
                    comment_text += "\n" + lines[i]
                match = COMMENT_PATTERN.search(comment_text)
                if match:
                    last_comment = match.group(1).strip()
                i += 1
                continue

            # Entry
            match = ENTRY_PATTERN.search(line if line else "")
            if match:
                key = self._unescape(match.group(1))
                value = self._unescape(match.group(2))
                entries.append(ParsedEntry(
                    key=key,
                    source_text=value,
                    context=last_comment,
                    order=order,
                ))
                order += 1
                last_comment = ""

            i += 1

        return entries

    def export(self, entries: list[ParsedEntry], translations: dict[str, str] | None = None) -> str:
        lines = []
        for entry in sorted(entries, key=lambda e: e.order):
            text = translations.get(entry.key, entry.source_text) if translations else entry.source_text
            if entry.context:
                lines.append(f"/* {entry.context} */")
            escaped_key = self._escape(entry.key)
            escaped_value = self._escape(text)
            lines.append(f'"{escaped_key}" = "{escaped_value}";')
            lines.append("")
        return "\n".join(lines)

    def _unescape(self, s: str) -> str:
        """Unescape Apple .strings format."""
        s = s.replace('\\"', '"')
        s = s.replace("\\n", "\n")
        s = s.replace("\\t", "\t")
        s = s.replace("\\\\", "\\")
        # Handle \Uxxxx unicode escapes
        s = re.sub(
            r'\\U([0-9a-fA-F]{4})',
            lambda m: chr(int(m.group(1), 16)),
            s
        )
        return s

    def _escape(self, s: str) -> str:
        """Escape for Apple .strings format."""
        s = s.replace("\\", "\\\\")
        s = s.replace('"', '\\"')
        s = s.replace("\n", "\\n")
        s = s.replace("\t", "\\t")
        return s
