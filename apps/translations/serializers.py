from rest_framework import serializers

from apps.translations.models import Translation
from apps.translations.validators import validate_translation


class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = [
            "id",
            "string",
            "language_code",
            "translated_text",
            "plural_forms",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        string_obj = data.get("string") or self.instance.string
        translated_text = data.get(
            "translated_text",
            self.instance.translated_text if self.instance else "",
        )
        language_code = data.get(
            "language_code",
            self.instance.language_code if self.instance else "",
        )

        errors = validate_translation(
            source_text=string_obj.source_text,
            translated_text=translated_text,
            max_length=string_obj.max_length,
            has_plurals=string_obj.has_plurals,
            plural_translations=data.get("plural_forms", {}),
            language_code=language_code,
        )

        if errors:
            raise serializers.ValidationError({"translation_errors": errors})

        return data


class TranslationSuggestionSerializer(serializers.Serializer):
    source_text = serializers.CharField()
    translated_text = serializers.CharField()
    similarity = serializers.FloatField()
    project_name = serializers.CharField()
    project_slug = serializers.SlugField()
    string_key = serializers.CharField()
    language_code = serializers.CharField()


class ProgressSerializer(serializers.Serializer):
    total_strings = serializers.IntegerField()
    languages = serializers.ListField()
