import uuid

from django.db import models


class ResourceFile(models.Model):
    FORMAT_CHOICES = [
        ("json", "JSON"),
        ("po", "PO/Gettext"),
        ("strings", "Apple Strings"),
        ("xliff", "XLIFF"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="resource_files",
    )
    file_path = models.CharField(max_length=500)
    file_format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    version = models.PositiveIntegerField(default=1)
    checksum = models.CharField(max_length=64)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "file_path", "version"],
                name="unique_project_file_version",
            ),
        ]

    def __str__(self):
        return f"{self.file_path} v{self.version}"


class TranslatableString(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="strings",
    )
    resource_file = models.ForeignKey(
        ResourceFile,
        on_delete=models.CASCADE,
        related_name="strings",
    )
    key = models.CharField(max_length=1000)
    source_text = models.TextField()
    context = models.TextField(blank=True, default="")
    max_length = models.PositiveIntegerField(null=True, blank=True)
    has_plurals = models.BooleanField(default=False)
    plural_forms = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "key"],
                name="unique_project_key",
            ),
        ]
        indexes = [
            models.Index(
                fields=["project", "is_active"],
                name="idx_project_active",
            ),
        ]

    def __str__(self):
        return self.key
