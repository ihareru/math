from django.db import transaction

from apps.game.models import UserGameStatistics
from apps.game.services.generation_settings import (
    create_default_generation_settings,
)


@transaction.atomic
def ensure_user_game_data(*, user):
    """
    Гарантирует наличие служебных игровых данных
    пользователя.

    Используется как защита от ручного удаления
    связанных записей или старых аккаунтов.
    """
    statistics, _ = (
        UserGameStatistics.objects.get_or_create(
            user=user,
        )
    )

    generation_settings = (
        create_default_generation_settings(
            user=user,
        )
    )

    return statistics, generation_settings