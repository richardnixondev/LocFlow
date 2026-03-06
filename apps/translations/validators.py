from parsers.validation import validate_length, validate_plural_forms, validate_variables


def validate_translation(source_text, translated_text, max_length=None,
                         has_plurals=False, plural_translations=None,
                         language_code=None):
    """Validate a translation against its source string.

    Returns a list of error messages (empty if valid).
    """
    errors = []

    # Validate format variables are preserved
    errors.extend(validate_variables(source_text, translated_text))

    # Validate max length
    if max_length:
        errors.extend(validate_length(translated_text, max_length))

    # Validate plural forms
    if has_plurals and plural_translations and language_code:
        errors.extend(validate_plural_forms(plural_translations, language_code))

    return errors
