import json
from parsers.base import BaseParser, ParsedEntry
from parsers.exceptions import ParseError

I18NEXT_SUFFIXES = ("_zero", "_one", "_two", "_few", "_many", "_other", "_plural")


class JSONParser(BaseParser):
    def parse(self, content: str) -> list[ParsedEntry]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ParseError("JSON root must be an object")

        flat = self._flatten(data)
        return self._group_entries(flat)

    def export(self, entries: list[ParsedEntry], translations: dict[str, str] | None = None) -> str:
        result = {}
        for entry in sorted(entries, key=lambda e: e.order):
            text = translations.get(entry.key, entry.source_text) if translations else entry.source_text
            if entry.has_plurals:
                # Export plural forms
                forms = entry.plural_forms or {}
                if translations:
                    # Check if we have translated plural forms
                    for form_name, form_text in forms.items():
                        result_key = f"{entry.key}_{form_name}"
                        self._set_nested(result, result_key, translations.get(result_key, form_text))
                else:
                    for form_name, form_text in forms.items():
                        result_key = f"{entry.key}_{form_name}"
                        self._set_nested(result, result_key, form_text)
            else:
                self._set_nested(result, entry.key, text)
        return json.dumps(result, ensure_ascii=False, indent=2) + "\n"

    def _flatten(self, data: dict, prefix: str = "") -> list[tuple[str, str]]:
        items = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                items.extend(self._flatten(value, full_key))
            else:
                items.append((full_key, str(value) if not isinstance(value, str) else value))
        return items

    def _group_entries(self, flat_items: list[tuple[str, str]]) -> list[ParsedEntry]:
        # Detect i18next plural patterns
        plural_groups: dict[str, dict[str, str]] = {}
        regular: list[tuple[int, str, str]] = []

        for order, (key, value) in enumerate(flat_items):
            plural_suffix = None
            base_key = key
            for suffix in I18NEXT_SUFFIXES:
                if key.endswith(suffix):
                    plural_suffix = suffix[1:]  # remove leading _
                    base_key = key[:-len(suffix)]
                    break

            if plural_suffix:
                if base_key not in plural_groups:
                    plural_groups[base_key] = {}
                plural_groups[base_key][plural_suffix] = value
            else:
                regular.append((order, key, value))

        entries = []
        order_counter = 0

        # Add regular entries
        for _, key, value in regular:
            # Skip if this key is actually the base of a plural group
            if key not in plural_groups:
                entries.append(ParsedEntry(
                    key=key,
                    source_text=value,
                    order=order_counter,
                ))
                order_counter += 1

        # Add plural groups
        for base_key, forms in plural_groups.items():
            source = forms.get("one", forms.get("other", next(iter(forms.values()))))
            entries.append(ParsedEntry(
                key=base_key,
                source_text=source,
                has_plurals=True,
                plural_forms=forms,
                order=order_counter,
            ))
            order_counter += 1

        return entries

    def _set_nested(self, data: dict, key: str, value: str) -> None:
        parts = key.split(".")
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
