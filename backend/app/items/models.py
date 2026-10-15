import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="items"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
