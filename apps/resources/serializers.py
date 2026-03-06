from rest_framework import serializers

from apps.resources.models import ResourceFile, TranslatableString
from apps.translations.models import Translation


class ResourceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceFile
        fields = [
            "id",
            "project",
            "file_path",
            "file_format",
            "version",
            "checksum",
            "uploaded_at",
        ]
        read_only_fields = ["id", "version", "checksum", "uploaded_at"]


class TranslationInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = [
            "id",
            "language_code",
            "translated_text",
            "plural_forms",
            "status",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]


class TranslatableStringSerializer(serializers.ModelSerializer):
    translations = TranslationInlineSerializer(many=True, read_only=True)

    class Meta:
        model = TranslatableString
        fields = [
            "id",
            "key",
            "source_text",
            "context",
            "max_length",
            "has_plurals",
            "plural_forms",
            "order",
            "is_active",
            "translations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TranslatableStringListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views (without inline translations)."""
    translation_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = TranslatableString
        fields = [
            "id",
            "key",
            "source_text",
            "context",
            "has_plurals",
            "order",
            "is_active",
            "translation_count",
        ]


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    file_format = serializers.ChoiceField(
        choices=["json", "po", "strings", "xliff"],
        required=False,
    )
