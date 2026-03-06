from difflib import SequenceMatcher

from django.conf import settings
from django.db import connection

from apps.translations.models import Translation


def get_tm_defaults():
    """Get Translation Memory defaults from settings."""
    defaults = getattr(settings, "TRANSLATION_MEMORY", {})
    return {
        "min_similarity": defaults.get("MIN_SIMILARITY", 0.7),
        "max_results": defaults.get("MAX_RESULTS", 10),
    }


def get_suggestions(
    source_text,
    language_code,
    min_similarity=None,
    max_results=None,
    exclude_string_id=None,
    project_slug=None,
):
    """
    Find translation suggestions based on source text similarity.

    Uses pg_trgm TrigramSimilarity on PostgreSQL,
    falls back to difflib.SequenceMatcher on SQLite.
    """
    defaults = get_tm_defaults()
    min_similarity = min_similarity if min_similarity is not None else defaults["min_similarity"]
    max_results = max_results if max_results is not None else defaults["max_results"]

    if connection.vendor == "postgresql":
        return _pg_trgm_suggestions(
            source_text, language_code, min_similarity, max_results,
            exclude_string_id, project_slug,
        )
    return _difflib_suggestions(
        source_text, language_code, min_similarity, max_results,
        exclude_string_id, project_slug,
    )


def _base_queryset(language_code, exclude_string_id, project_slug):
    """Build the base queryset for approved translations."""
    qs = (
        Translation.objects.filter(
            language_code=language_code,
            status="approved",
            string__is_active=True,
        )
        .select_related("string", "string__project")
    )

    if exclude_string_id:
        qs = qs.exclude(string_id=exclude_string_id)

    if project_slug:
        qs = qs.filter(string__project__slug=project_slug)

    return qs


def _pg_trgm_suggestions(
    source_text, language_code, min_similarity, max_results,
    exclude_string_id, project_slug,
):
    """PostgreSQL-based similarity search using pg_trgm."""
    from django.contrib.postgres.search import TrigramSimilarity

    qs = _base_queryset(language_code, exclude_string_id, project_slug)

    results = (
        qs.annotate(similarity=TrigramSimilarity("string__source_text", source_text))
        .filter(similarity__gte=min_similarity)
        .order_by("-similarity")[:max_results]
    )

    return [
        {
            "source_text": t.string.source_text,
            "translated_text": t.translated_text,
            "similarity": round(float(t.similarity), 2),
            "project_name": t.string.project.name,
            "project_slug": t.string.project.slug,
            "string_key": t.string.key,
            "language_code": t.language_code,
        }
        for t in results
    ]


def _difflib_suggestions(
    source_text, language_code, min_similarity, max_results,
    exclude_string_id, project_slug,
):
    """SQLite fallback using difflib.SequenceMatcher."""
    qs = _base_queryset(language_code, exclude_string_id, project_slug)

    scored = []
    for t in qs.iterator():
        similarity = SequenceMatcher(
            None, source_text.lower(), t.string.source_text.lower()
        ).ratio()
        if similarity >= min_similarity:
            scored.append({
                "source_text": t.string.source_text,
                "translated_text": t.translated_text,
                "similarity": round(similarity, 2),
                "project_name": t.string.project.name,
                "project_slug": t.string.project.slug,
                "string_key": t.string.key,
                "language_code": t.language_code,
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:max_results]
