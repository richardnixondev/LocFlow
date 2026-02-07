from django.contrib import admin

from apps.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "source_language", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
