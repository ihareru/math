from django.core.management.base import (
    BaseCommand,
)
from django.utils import timezone

from apps.cheats.models import UserCheat


class Command(BaseCommand):
    help = (
        "Отключает истёкшие активации чит-кодов."
    )

    def handle(self, *args, **options):
        updated_count = (
            UserCheat.objects
            .filter(
                is_active=True,
                expires_at__isnull=False,
                expires_at__lte=timezone.now(),
            )
            .update(
                is_active=False,
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Отключено истёкших активаций: "
                f"{updated_count}"
            )
        )