from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserGameStatistics


@receiver(
    post_save,
    sender=settings.AUTH_USER_MODEL,
)
def create_user_game_statistics(
    sender,
    instance,
    created,
    **kwargs,
):
    if created:
        UserGameStatistics.objects.get_or_create(
            user=instance,
        )