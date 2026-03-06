import re
from parsers.plural_rules import get_plural_forms

# Common format variable patterns
FORMAT_PATTERNS = [
    re.compile(r'%(?:\d+\$)?[sdifFeEgGxXou%]'),           # printf-style: %s, %d, %1$s
    re.compile(r'\{(?:\w*)\}'),                              # Python/Java style: {}, {name}, {0}
    re.compile(r'\{\{(?:\w+)\}\}'),                          # Handlebars/Angular: {{name}}
    re.compile(r'%\{(\w+)\}'),                               # Ruby style: %{name}
    re.compile(r'\$\{(\w+)\}'),                              # JS template literal: ${name}
    re.compile(r'\$(?:t|s)\([\w.]+\)'),                      # i18next interpolation
]


def extract_variables(text: str) -> set[str]:
    """Extract all format variables/placeholders from text."""
    variables = set()
    for pattern in FORMAT_PATTERNS:
        variables.update(pattern.findall(text) if pattern.groups else [m.group() for m in pattern.finditer(text)])
    return variables


def validate_variables(source: str, translation: str) -> list[str]:
    """Check that all format variables in source are present in translation.

    Returns list of error messages (empty if valid).
    """
    source_vars = extract_variables(source)
    translation_vars = extract_variables(translation)

    errors = []
    missing = source_vars - translation_vars
    if missing:
        errors.append(f"Missing variables in translation: {', '.join(sorted(missing))}")

    extra = translation_vars - source_vars
    if extra:
        errors.append(f"Extra variables in translation: {', '.join(sorted(extra))}")

    return errors


def validate_length(translation: str, max_length: int | None) -> list[str]:
    """Check translation length against max_length constraint."""
    if max_length is not None and len(translation) > max_length:
        return [f"Translation exceeds max length: {len(translation)} > {max_length}"]
    return []


def validate_plural_forms(plural_translations: dict[str, str], language_code: str) -> list[str]:
    """Validate that all required plural forms for a language are provided."""
    required = get_plural_forms(language_code)
    provided = set(plural_translations.keys())

    errors = []
    missing = set(required) - provided
    if missing:
        errors.append(f"Missing plural forms for {language_code}: {', '.join(sorted(missing))}")

    return errors
