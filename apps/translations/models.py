import uuid

from django.db import models


class Translation(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("review", "In Review"),
        ("approved", "Approved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    string = models.ForeignKey(
        "resources.TranslatableString",
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language_code = models.CharField(max_length=20)
    translated_text = models.TextField()
    plural_forms = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["string", "language_code"],
                name="unique_string_language",
            ),
        ]
        indexes = [
            models.Index(
                fields=["language_code", "status"],
                name="idx_language_status",
            ),
        ]

    def __str__(self):
        return f"{self.string.key} [{self.language_code}]"
