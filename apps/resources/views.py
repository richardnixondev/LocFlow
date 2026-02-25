from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAbove

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString
from apps.resources.serializers import (
    FileUploadSerializer,
    ResourceFileSerializer,
    TranslatableStringListSerializer,
    TranslatableStringSerializer,
)
from apps.resources.services import detect_format_from_filename, process_upload
from parsers.factory import ParserFactory


@api_view(["POST"])
@permission_classes([IsManagerOrAbove])
def upload_resource(request, slug):
    """Upload a resource file for parsing and string extraction."""
    project = get_object_or_404(Project, slug=slug)
    serializer = FileUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uploaded_file = serializer.validated_data["file"]
    file_format = serializer.validated_data.get("file_format")

    if not file_format:
        file_format = detect_format_from_filename(uploaded_file.name)
        if not file_format:
            return Response(
                {"error": "Could not detect file format. Please specify file_format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        return Response(
            {"error": "File must be UTF-8 encoded."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = process_upload(project, content, uploaded_file.name, file_format)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(result, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def list_resources(request, slug):
    """List resource files for a project."""
    project = get_object_or_404(Project, slug=slug)
    resources = ResourceFile.objects.filter(project=project)
    serializer = ResourceFileSerializer(resources, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def list_strings(request, slug):
    """List translatable strings for a project with optional filters."""
    project = get_object_or_404(Project, slug=slug)
    queryset = TranslatableString.objects.filter(project=project, is_active=True)

    # Filter by untranslated for a specific language
    language = request.query_params.get("language")
    untranslated = request.query_params.get("untranslated")

    if untranslated and language:
        queryset = queryset.exclude(
            translations__language_code=language,
        )
    elif language:
        queryset = queryset.filter(
            translations__language_code=language,
        )

    # Filter by translation status
    trans_status = request.query_params.get("status")
    if trans_status and language:
        queryset = queryset.filter(
            translations__language_code=language,
            translations__status=trans_status,
        )

    # Search by key or source text
    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(key__icontains=search) | queryset.filter(
            source_text__icontains=search
        )

    queryset = queryset.annotate(translation_count=Count("translations")).distinct()
    serializer = TranslatableStringListSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def string_detail(request, slug, string_id):
    """Get a translatable string with all its translations."""
    project = get_object_or_404(Project, slug=slug)
    string = get_object_or_404(
        TranslatableString.objects.prefetch_related("translations"),
        project=project,
        pk=string_id,
    )
    serializer = TranslatableStringSerializer(string)
    return Response(serializer.data)


@api_view(["GET"])
def export_translations(request, slug, language, file_format):
    """Export translations for a language in the specified format."""
    project = get_object_or_404(Project, slug=slug)

    try:
        parser = ParserFactory.get_parser(file_format)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    strings = TranslatableString.objects.filter(
        project=project, is_active=True
    ).prefetch_related("translations")

    from parsers.base import ParsedEntry

    entries = []
    translations_map = {}

    for s in strings:
        entry = ParsedEntry(
            key=s.key,
            source_text=s.source_text,
            context=s.context,
            has_plurals=s.has_plurals,
            plural_forms=s.plural_forms,
            order=s.order,
            max_length=s.max_length,
        )
        entries.append(entry)

        translation = s.translations.filter(language_code=language).first()
        if translation:
            translations_map[s.key] = translation.translated_text

    content = parser.export(entries, translations_map if translations_map else None)

    content_types = {
        "json": "application/json",
        "po": "text/x-gettext-translation",
        "strings": "text/plain",
        "xliff": "application/xml",
        "xlf": "application/xml",
    }
    content_type = content_types.get(file_format, "text/plain")

    return Response(
        content,
        content_type=f"{content_type}; charset=utf-8",
    )
