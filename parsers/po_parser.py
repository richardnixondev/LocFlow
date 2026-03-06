import polib
from parsers.base import BaseParser, ParsedEntry
from parsers.exceptions import ParseError


class POParser(BaseParser):
    def parse(self, content: str) -> list[ParsedEntry]:
        try:
            po = polib.pofile(content)
        except Exception as e:
            raise ParseError(f"Invalid PO file: {e}")

        entries = []
        for order, entry in enumerate(po):
            if entry.obsolete:
                continue

            flags = list(entry.flags)
            context_parts = []
            if entry.msgctxt:
                context_parts.append(entry.msgctxt)
            if entry.comment:
                context_parts.append(entry.comment)

            key = entry.msgctxt + "\x04" + entry.msgid if entry.msgctxt else entry.msgid

            if entry.msgid_plural:
                plural_forms = {}
                plural_forms["one"] = entry.msgid
                plural_forms["other"] = entry.msgid_plural
                # Include translated plural forms if available
                for idx, text in sorted(entry.msgstr_plural.items()):
                    if text:
                        plural_forms[f"form{idx}"] = text

                entries.append(ParsedEntry(
                    key=key,
                    source_text=entry.msgid,
                    context="\n".join(context_parts),
                    has_plurals=True,
                    plural_forms=plural_forms,
                    order=order,
                    flags=flags,
                ))
            else:
                entries.append(ParsedEntry(
                    key=key,
                    source_text=entry.msgid,
                    context="\n".join(context_parts),
                    order=order,
                    flags=flags,
                ))

        return entries

    def export(self, entries: list[ParsedEntry], translations: dict[str, str] | None = None) -> str:
        po = polib.POFile()
        po.metadata = {
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Transfer-Encoding": "8bit",
        }

        for entry in sorted(entries, key=lambda e: e.order):
            # Parse key to extract msgctxt
            if "\x04" in entry.key:
                msgctxt, msgid = entry.key.split("\x04", 1)
            else:
                msgctxt = None
                msgid = entry.key if not entry.source_text else entry.source_text

            translated = translations.get(entry.key, "") if translations else ""

            po_entry = polib.POEntry(
                msgid=entry.source_text,
                msgstr=translated if not entry.has_plurals else "",
                msgctxt=msgctxt,
            )

            if entry.has_plurals:
                po_entry.msgid_plural = entry.plural_forms.get("other", "")
                if translations:
                    # Expect translations to contain plural forms
                    po_entry.msgstr_plural = {
                        0: translations.get(entry.key, ""),
                    }
                else:
                    po_entry.msgstr_plural = {0: "", 1: ""}

            if entry.context:
                po_entry.comment = entry.context.split("\n")[-1] if "\n" in entry.context else (entry.context if not msgctxt else "")

            if entry.flags:
                po_entry.flags = entry.flags

            po.append(po_entry)

        return str(po)
