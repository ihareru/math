from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserGameStatistics
from .services.generation_settings import (
    create_default_generation_settings,
)


@receiver(
    post_save,
    sender=settings.AUTH_USER_MODEL,
)
def create_user_game_data(
    sender,
    instance,
    created,
    **kwargs,
):
    if not created:
        return

    UserGameStatistics.objects.get_or_create(
        user=instance,
    )

    create_default_generation_settings(
        user=instance,
    )