from dataclasses import dataclass

from django.db.models import Q
from django.utils import timezone

from apps.cheats.models import (
    RewardType,
    UserCheat,
)


DEFAULT_STREAK_TO_STAR = 10
DEFAULT_STAR_MULTIPLIER = 1


@dataclass(frozen=True)
class ActiveGameRewards:
    streak_to_star: int
    star_multiplier: int
    freeze_streak: bool
    show_correct_answer: bool


def get_active_user_cheats(*, user):
    """
    Возвращает действующие активации пользователя.
    """
    now = timezone.now()

    return (
        UserCheat.objects
        .filter(
            user=user,
            is_active=True,
        )
        .filter(
            Q(expires_at__isnull=True)
            | Q(expires_at__gt=now)
        )
        .select_related("cheat")
        .prefetch_related(
            "cheat__rewards"
        )
        .filter(
            cheat__is_active=True,
        )
    )


def get_active_game_rewards(
    *,
    user,
) -> ActiveGameRewards:
    """
    Собирает итоговую игровую конфигурацию
    из всех активных кодов пользователя.
    """
    streak_to_star = DEFAULT_STREAK_TO_STAR
    star_multiplier = DEFAULT_STAR_MULTIPLIER
    freeze_streak = False
    show_correct_answer = False

    activations = get_active_user_cheats(
        user=user,
    )

    for activation in activations:
        for reward in activation.cheat.rewards.all():
            data = reward.reward_data

            if (
                reward.reward_type
                == RewardType.STREAK_TO_STAR
            ):
                answers = data.get("answers")

                if (
                    isinstance(answers, int)
                    and not isinstance(answers, bool)
                    and answers >= 2
                ):
                    # При нескольких бонусах выбираем
                    # наиболее выгодный порог.
                    streak_to_star = min(
                        streak_to_star,
                        answers,
                    )

            elif (
                reward.reward_type
                == RewardType.DOUBLE_STARS
            ):
                multiplier = data.get(
                    "multiplier"
                )

                if (
                    isinstance(multiplier, int)
                    and not isinstance(
                        multiplier,
                        bool,
                    )
                    and multiplier >= 2
                ):
                    star_multiplier = max(
                        star_multiplier,
                        multiplier,
                    )

            elif (
                reward.reward_type
                == RewardType.FREEZE_STREAK
            ):
                if data.get("enabled") is True:
                    freeze_streak = True

            elif (
                reward.reward_type
                == RewardType.SHOW_CORRECT_ANSWER
            ):
                if data.get("enabled") is True:
                    show_correct_answer = True

    return ActiveGameRewards(
        streak_to_star=streak_to_star,
        star_multiplier=star_multiplier,
        freeze_streak=freeze_streak,
        show_correct_answer=show_correct_answer,
    )