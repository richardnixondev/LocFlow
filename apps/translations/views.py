from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsTranslatorOrAbove

from apps.projects.models import Project
from apps.resources.models import TranslatableString
from apps.translations.models import Translation
from apps.translations.serializers import (
    TranslationSerializer,
    TranslationSuggestionSerializer,
)
from apps.translations.services import get_suggestions


@api_view(["POST"])
@permission_classes([IsTranslatorOrAbove])
def create_translation(request, slug, string_id):
    """Submit a translation for a string."""
    project = get_object_or_404(Project, slug=slug)
    string = get_object_or_404(
        TranslatableString, project=project, pk=string_id, is_active=True
    )

    data = request.data.copy()
    data["string"] = string.pk

    serializer = TranslationSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PUT", "PATCH"])
@permission_classes([IsTranslatorOrAbove])
def update_translation(request, slug, string_id, language):
    """Update a translation for a string in a specific language."""
    project = get_object_or_404(Project, slug=slug)
    string = get_object_or_404(
        TranslatableString, project=project, pk=string_id, is_active=True
    )
    translation = get_object_or_404(
        Translation, string=string, language_code=language
    )

    partial = request.method == "PATCH"
    serializer = TranslationSerializer(
        translation, data=request.data, partial=partial
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


@api_view(["GET"])
def translation_progress(request, slug):
    """Get translation progress per language for a project."""
    project = get_object_or_404(Project, slug=slug)

    total_strings = TranslatableString.objects.filter(
        project=project, is_active=True
    ).count()

    if total_strings == 0:
        return Response({"total_strings": 0, "languages": []})

    # Get all unique languages with translations for this project
    language_stats = (
        Translation.objects.filter(
            string__project=project, string__is_active=True
        )
        .values("language_code")
        .annotate(
            translated=Count("id"),
            approved=Count("id", filter=Q(status="approved")),
        )
        .order_by("language_code")
    )

    languages = []
    for stat in language_stats:
        languages.append({
            "code": stat["language_code"],
            "translated": stat["translated"],
            "approved": stat["approved"],
            "progress_percent": round(
                (stat["translated"] / total_strings) * 100, 1
            ),
        })

    return Response({
        "total_strings": total_strings,
        "languages": languages,
    })


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="language", type=str, required=True,
            description="Target language code (e.g. pt-BR)",
        ),
        OpenApiParameter(
            name="min_similarity", type=float, required=False,
            description="Minimum similarity threshold (0.0-1.0, default 0.7)",
        ),
        OpenApiParameter(
            name="max_results", type=int, required=False,
            description="Maximum number of results (1-100, default 10)",
        ),
        OpenApiParameter(
            name="scope", type=str, required=False,
            description="'project' to limit to current project, default cross-project",
        ),
    ],
    responses={200: TranslationSuggestionSerializer(many=True)},
    summary="Get translation memory suggestions",
    description="Find similar approved translations for a given source string.",
)
@api_view(["GET"])
def translation_suggestions(request, slug, string_id):
    """Get translation memory suggestions for a string."""
    project = get_object_or_404(Project, slug=slug)
    string = get_object_or_404(
        TranslatableString, project=project, pk=string_id, is_active=True
    )

    language = request.query_params.get("language")
    if not language:
        return Response(
            {"detail": "Query parameter 'language' is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Parse optional params
    min_similarity = request.query_params.get("min_similarity")
    if min_similarity is not None:
        try:
            min_similarity = float(min_similarity)
            if not 0.0 <= min_similarity <= 1.0:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "min_similarity must be a float between 0.0 and 1.0."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    max_results = request.query_params.get("max_results")
    if max_results is not None:
        try:
            max_results = int(max_results)
            if not 1 <= max_results <= 100:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "max_results must be an integer between 1 and 100."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    scope = request.query_params.get("scope")
    project_slug = slug if scope == "project" else None

    suggestions = get_suggestions(
        source_text=string.source_text,
        language_code=language,
        min_similarity=min_similarity,
        max_results=max_results,
        exclude_string_id=string.pk,
        project_slug=project_slug,
    )

    return Response({
        "source_text": string.source_text,
        "language": language,
        "min_similarity": min_similarity if min_similarity is not None else 0.7,
        "count": len(suggestions),
        "suggestions": suggestions,
    })
