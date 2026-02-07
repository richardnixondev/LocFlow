from django.contrib import admin

from apps.resources.models import ResourceFile, TranslatableString


@admin.register(ResourceFile)
class ResourceFileAdmin(admin.ModelAdmin):
    list_display = ["file_path", "project", "file_format", "version", "uploaded_at"]
    list_filter = ["file_format", "project"]
    search_fields = ["file_path"]
    readonly_fields = ["id", "checksum", "uploaded_at"]


@admin.register(TranslatableString)
class TranslatableStringAdmin(admin.ModelAdmin):
    list_display = ["key", "project", "source_text", "is_active", "has_plurals"]
    list_filter = ["is_active", "has_plurals", "project"]
    search_fields = ["key", "source_text"]
    readonly_fields = ["id", "created_at", "updated_at"]
