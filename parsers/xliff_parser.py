import xml.etree.ElementTree as ET
from parsers.base import BaseParser, ParsedEntry
from parsers.exceptions import ParseError


class XLIFFParser(BaseParser):
    NAMESPACES = {
        "1.2": "urn:oasis:names:tc:xliff:document:1.2",
        "2.0": "urn:oasis:names:tc:xliff:document:2.0",
    }

    def parse(self, content: str) -> list[ParsedEntry]:
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            raise ParseError(f"Invalid XML: {e}")

        ns = self._detect_namespace(root)
        ns_prefix = f"{{{ns}}}" if ns else ""

        entries = []
        order = 0

        for file_elem in root.iter(f"{ns_prefix}file"):
            for trans_unit in file_elem.iter(f"{ns_prefix}trans-unit"):
                unit_id = trans_unit.get("id", "")
                source_elem = trans_unit.find(f"{ns_prefix}source")

                if source_elem is None:
                    continue

                source_text = self._get_text(source_elem)

                # Get note for context
                note_elem = trans_unit.find(f"{ns_prefix}note")
                context = note_elem.text.strip() if note_elem is not None and note_elem.text else ""

                # Check for max-width
                max_length = None
                size_restriction = trans_unit.get("maxwidth") or trans_unit.get("size-restriction")
                if size_restriction:
                    try:
                        max_length = int(size_restriction)
                    except ValueError:
                        pass

                entries.append(ParsedEntry(
                    key=unit_id,
                    source_text=source_text,
                    context=context,
                    order=order,
                    max_length=max_length,
                ))
                order += 1

        return entries

    def export(self, entries: list[ParsedEntry], translations: dict[str, str] | None = None) -> str:
        ns = self.NAMESPACES["1.2"]
        ET.register_namespace("", ns)

        xliff = ET.Element(f"{{{ns}}}xliff", version="1.2")
        file_elem = ET.SubElement(xliff, f"{{{ns}}}file", {
            "source-language": "en",
            "datatype": "plaintext",
            "original": "locflow",
        })
        body = ET.SubElement(file_elem, f"{{{ns}}}body")

        for entry in sorted(entries, key=lambda e: e.order):
            trans_unit = ET.SubElement(body, f"{{{ns}}}trans-unit", id=entry.key)

            source = ET.SubElement(trans_unit, f"{{{ns}}}source")
            source.text = entry.source_text

            if translations and entry.key in translations:
                target = ET.SubElement(trans_unit, f"{{{ns}}}target")
                target.text = translations[entry.key]

            if entry.context:
                note = ET.SubElement(trans_unit, f"{{{ns}}}note")
                note.text = entry.context

            if entry.max_length:
                trans_unit.set("maxwidth", str(entry.max_length))

        return ET.tostring(xliff, encoding="unicode", xml_declaration=True)

    def _detect_namespace(self, root: ET.Element) -> str:
        tag = root.tag
        if "{" in tag:
            return tag.split("}")[0][1:]
        return ""

    def _get_text(self, element: ET.Element) -> str:
        """Get all text from element, including text in inline elements."""
        parts = []
        if element.text:
            parts.append(element.text)
        for child in element:
            parts.append(ET.tostring(child, encoding="unicode"))
        if element.tail:
            parts.append(element.tail)
        return "".join(parts).strip()
