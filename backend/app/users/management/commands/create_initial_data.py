from typing import Any

from django.core.management.base import BaseCommand

from app.core.config import settings
from app.users.models import User


class Command(BaseCommand):
    help = "Create initial data in DB: the first superuser from FIRST_SUPERUSER"

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Creating initial data")
        if not User.objects.filter(email=settings.FIRST_SUPERUSER).exists():
            User.objects.create_superuser(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
            )
        self.stdout.write("Initial data created")
