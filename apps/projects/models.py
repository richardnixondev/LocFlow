import uuid

from django.db import models
from django.utils.text import slugify


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField(blank=True, default="")
    source_language = models.CharField(max_length=10, default="en")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Project.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)


class GitHubRepo(models.Model):
    """Links a project to a GitHub repository for auto-importing resource files."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="github_repo",
    )
    owner = models.CharField(max_length=255, help_text="GitHub user or org")
    repo = models.CharField(max_length=255, help_text="Repository name")
    branch = models.CharField(max_length=255, default="main")
    base_path = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Subdirectory to scan, e.g. 'src/locales'. Leave empty for repo root.",
    )
    file_patterns = models.JSONField(
        default=list,
        blank=True,
        help_text="File extensions to import, e.g. ['json','po']. Empty = auto-detect.",
    )
    access_token = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Personal access token for private repos (optional).",
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=50, blank=True, default="")
    last_sync_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "GitHub repository"
        verbose_name_plural = "GitHub repositories"

    def __str__(self):
        return f"{self.owner}/{self.repo}:{self.branch}"

    @property
    def full_name(self):
        return f"{self.owner}/{self.repo}"
