from rest_framework import serializers

from apps.projects.models import GitHubRepo, Project


class GitHubRepoSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = GitHubRepo
        fields = [
            "id",
            "owner",
            "repo",
            "branch",
            "base_path",
            "file_patterns",
            "access_token",
            "last_synced_at",
            "last_sync_status",
            "last_sync_message",
            "full_name",
            "created_at",
        ]
        read_only_fields = ["id", "last_synced_at", "last_sync_status", "last_sync_message", "created_at"]
        extra_kwargs = {
            "access_token": {"write_only": True},
        }


class GitHubRepoReadSerializer(serializers.ModelSerializer):
    """Read-only serializer (never exposes the token)."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = GitHubRepo
        fields = [
            "id",
            "owner",
            "repo",
            "branch",
            "base_path",
            "file_patterns",
            "has_token",
            "last_synced_at",
            "last_sync_status",
            "last_sync_message",
            "full_name",
            "created_at",
        ]

    has_token = serializers.SerializerMethodField()

    def get_has_token(self, obj):
        return bool(obj.access_token)


class ProjectSerializer(serializers.ModelSerializer):
    github_repo = GitHubRepoReadSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "source_language",
            "github_repo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]
