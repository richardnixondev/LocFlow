# Simplified CLDR plural categories per language
# Each language maps to a list of required plural form names
PLURAL_RULES: dict[str, list[str]] = {
    # One/Other languages (most European)
    "en": ["one", "other"],
    "de": ["one", "other"],
    "es": ["one", "many", "other"],
    "fr": ["one", "many", "other"],
    "it": ["one", "many", "other"],
    "pt": ["one", "many", "other"],
    "pt-BR": ["one", "many", "other"],
    "nl": ["one", "other"],
    "sv": ["one", "other"],
    "da": ["one", "other"],
    "no": ["one", "other"],
    "fi": ["one", "other"],
    # Zero/One/Other
    "lv": ["zero", "one", "other"],
    # One/Few/Many/Other (Slavic)
    "pl": ["one", "few", "many", "other"],
    "ru": ["one", "few", "many", "other"],
    "uk": ["one", "few", "many", "other"],
    "cs": ["one", "few", "many", "other"],
    "sk": ["one", "few", "many", "other"],
    "hr": ["one", "few", "other"],
    # Arabic
    "ar": ["zero", "one", "two", "few", "many", "other"],
    # East Asian (no plural forms, just "other")
    "zh": ["other"],
    "ja": ["other"],
    "ko": ["other"],
    "vi": ["other"],
    "th": ["other"],
    "id": ["other"],
    "ms": ["other"],
    # Turkish
    "tr": ["one", "other"],
    # Hebrew
    "he": ["one", "two", "other"],
}

DEFAULT_PLURAL_FORMS = ["one", "other"]


def get_plural_forms(language_code: str) -> list[str]:
    """Get required plural forms for a given language code.

    Tries exact match first, then base language (e.g., pt-BR -> pt).
    Falls back to DEFAULT_PLURAL_FORMS if not found.
    """
    if language_code in PLURAL_RULES:
        return PLURAL_RULES[language_code]
    base = language_code.split("-")[0].split("_")[0]
    if base in PLURAL_RULES:
        return PLURAL_RULES[base]
    return DEFAULT_PLURAL_FORMS
