from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.projects.models import Project
from apps.resources.models import TranslatableString
from apps.translations.models import Translation
from apps.translations.serializers import TranslationSerializer


@api_view(["POST"])
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
