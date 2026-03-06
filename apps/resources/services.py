import hashlib

from django.db import transaction

from apps.projects.models import Project
from apps.resources.models import ResourceFile, TranslatableString
from parsers.factory import ParserFactory


def compute_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def detect_format_from_filename(filename: str) -> str | None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else None
    format_map = {
        "json": "json",
        "po": "po",
        "pot": "po",
        "strings": "strings",
        "xliff": "xliff",
        "xlf": "xliff",
    }
    return format_map.get(ext)


@transaction.atomic
def process_upload(project: Project, file_content: str, file_path: str, file_format: str) -> dict:
    """Process an uploaded resource file.

    Parses the file, detects changes from previous version, and saves strings.

    Returns a summary dict with counts of new, updated, and removed strings.
    """
    checksum = compute_checksum(file_content)

    # Check if this exact file was already uploaded
    existing = ResourceFile.objects.filter(
        project=project,
        file_path=file_path,
        checksum=checksum,
    ).first()
    if existing:
        return {
            "resource_file_id": str(existing.id),
            "version": existing.version,
            "status": "unchanged",
            "new": 0,
            "updated": 0,
            "removed": 0,
        }

    # Determine next version
    last_version = (
        ResourceFile.objects.filter(project=project, file_path=file_path)
        .order_by("-version")
        .values_list("version", flat=True)
        .first()
    ) or 0

    resource_file = ResourceFile.objects.create(
        project=project,
        file_path=file_path,
        file_format=file_format,
        version=last_version + 1,
        checksum=checksum,
    )

    # Parse the file
    parser = ParserFactory.get_parser(file_format)
    entries = parser.parse(file_content)

    # Get existing active strings for this project
    existing_strings = {
        s.key: s
        for s in TranslatableString.objects.filter(project=project, is_active=True)
    }

    new_count = 0
    updated_count = 0
    seen_keys = set()

    for entry in entries:
        seen_keys.add(entry.key)
        existing_string = existing_strings.get(entry.key)

        if existing_string is None:
            # New string
            TranslatableString.objects.create(
                project=project,
                resource_file=resource_file,
                key=entry.key,
                source_text=entry.source_text,
                context=entry.context,
                max_length=entry.max_length,
                has_plurals=entry.has_plurals,
                plural_forms=entry.plural_forms,
                order=entry.order,
            )
            new_count += 1
        else:
            # Check if source text changed
            changed = (
                existing_string.source_text != entry.source_text
                or existing_string.context != entry.context
                or existing_string.has_plurals != entry.has_plurals
                or existing_string.plural_forms != entry.plural_forms
            )
            if changed:
                existing_string.source_text = entry.source_text
                existing_string.context = entry.context
                existing_string.max_length = entry.max_length
                existing_string.has_plurals = entry.has_plurals
                existing_string.plural_forms = entry.plural_forms
                existing_string.order = entry.order
                existing_string.resource_file = resource_file
                existing_string.save()
                updated_count += 1

    # Mark removed strings as inactive
    removed_keys = set(existing_strings.keys()) - seen_keys
    removed_count = 0
    if removed_keys:
        removed_count = TranslatableString.objects.filter(
            project=project,
            key__in=removed_keys,
            is_active=True,
        ).update(is_active=False)

    return {
        "resource_file_id": str(resource_file.id),
        "version": resource_file.version,
        "status": "processed",
        "new": new_count,
        "updated": updated_count,
        "removed": removed_count,
    }
