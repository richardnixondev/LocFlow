from django.contrib import admin

from apps.translations.models import Translation


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ["string", "language_code", "status", "updated_at"]
    list_filter = ["status", "language_code"]
    search_fields = ["string__key", "translated_text"]
    readonly_fields = ["id", "created_at", "updated_at"]
