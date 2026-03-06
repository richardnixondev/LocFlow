import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        TRANSLATOR = "translator", "Translator"
        VIEWER = "viewer", "Viewer"

    ROLE_HIERARCHY = {
        Role.ADMIN: 4,
        Role.MANAGER: 3,
        Role.TRANSLATOR: 2,
        Role.VIEWER: 1,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.VIEWER
    )

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_manager_or_above(self):
        return self.ROLE_HIERARCHY.get(self.role, 0) >= self.ROLE_HIERARCHY[self.Role.MANAGER]

    @property
    def is_translator_or_above(self):
        return self.ROLE_HIERARCHY.get(self.role, 0) >= self.ROLE_HIERARCHY[self.Role.TRANSLATOR]

    def __str__(self):
        return f"{self.username} ({self.role})"
