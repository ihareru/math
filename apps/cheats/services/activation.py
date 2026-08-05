from dataclasses import dataclass

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.cheats.models import (
    CheatCode,
    RewardType,
    UserCheat,
)

from .exceptions import (
    CheatCodeExpiredError,
    CheatCodeInactiveError,
    CheatCodeNotFoundError,
    CheatCodeNotStartedError,
    CheatGlobalLimitReachedError,
    CheatHasNoRewardsError,
    CheatUserLimitReachedError,
)


@dataclass(frozen=True)
class CheatActivationResult:
    activation: UserCheat
    cheat: CheatCode
    immediate_stars_awarded: int


def normalize_cheat_code(value: str) -> str:
    """
    Приводит введённый код к единому формату.
    """
    return (value or "").strip().upper()


def validate_cheat_availability(
    *,
    cheat: CheatCode,
    user,
    now=None,
):
    """
    Проверяет возможность активации кода.

    Эта функция вызывается внутри транзакции после
    select_for_update(), поэтому лимиты защищены
    от одновременных запросов.
    """
    if now is None:
        now = timezone.now()

    if not cheat.is_active:
        raise CheatCodeInactiveError(
            "Этот код отключён."
        )

    if cheat.valid_from > now:
        raise CheatCodeNotStartedError(
            "Период действия этого кода ещё не начался."
        )

    if (
        cheat.valid_until is not None
        and cheat.valid_until <= now
    ):
        raise CheatCodeExpiredError(
            "Срок активации этого кода закончился."
        )

    if (
        cheat.max_global_activations is not None
        and cheat.activation_count
        >= cheat.max_global_activations
    ):
        raise CheatGlobalLimitReachedError(
            "Лимит активаций этого кода исчерпан."
        )

    user_activation_count = (
        UserCheat.objects
        .filter(
            user=user,
            cheat=cheat,
        )
        .count()
    )

    if (
        user_activation_count
        >= cheat.max_user_activations
    ):
        raise CheatUserLimitReachedError(
            "Вы уже использовали максимально "
            "допустимое количество активаций "
            "этого кода."
        )

    if not cheat.rewards.exists():
        raise CheatHasNoRewardsError(
            "Для этого кода пока не настроены бонусы."
        )


def get_immediate_bonus_stars(
    *,
    cheat: CheatCode,
) -> int:
    """
    Суммирует звёзды, выдаваемые непосредственно
    в момент активации.

    В текущей схеме на один код допускается одна
    награда каждого типа, но функция оставлена
    универсальной.
    """
    total = 0

    rewards = cheat.rewards.filter(
        reward_type=RewardType.BONUS_STAR,
    )

    for reward in rewards:
        value = reward.reward_data.get(
            "stars",
            0,
        )

        if (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
        ):
            total += value

    return total


@transaction.atomic
def activate_cheat_code(
    *,
    user,
    raw_code: str,
    activation_ip=None,
    activation_user_agent="",
) -> CheatActivationResult:
    """
    Безопасно активирует чит-код.

    Все проверки лимитов и увеличение счётчика
    выполняются в одной транзакции.
    """
    normalized_code = normalize_cheat_code(
        raw_code
    )

    if not normalized_code:
        raise CheatCodeNotFoundError(
            "Введите чит-код."
        )

    cheat = (
        CheatCode.objects
        .select_for_update()
        .prefetch_related("rewards")
        .filter(
            code__iexact=normalized_code,
        )
        .first()
    )

    if cheat is None:
        raise CheatCodeNotFoundError(
            "Такой чит-код не найден."
        )

    now = timezone.now()

    validate_cheat_availability(
        cheat=cheat,
        user=user,
        now=now,
    )

    expires_at = cheat.calculate_expiration(
        activated_at=now,
    )

    activation = UserCheat.objects.create(
        user=user,
        cheat=cheat,
        activated_at=now,
        expires_at=expires_at,
        is_active=True,
        activation_ip=activation_ip,
        activation_user_agent=(
            activation_user_agent or ""
        )[:2000],
    )

    CheatCode.objects.filter(
        pk=cheat.pk,
    ).update(
        activation_count=F(
            "activation_count"
        ) + 1,
    )

    cheat.refresh_from_db(
        fields=[
            "activation_count",
        ]
    )

    immediate_stars = get_immediate_bonus_stars(
        cheat=cheat,
    )

    if immediate_stars:
        _award_immediate_stars(
            user=user,
            activation=activation,
            amount=immediate_stars,
        )

    return CheatActivationResult(
        activation=activation,
        cheat=cheat,
        immediate_stars_awarded=immediate_stars,
    )


def _award_immediate_stars(
    *,
    user,
    activation,
    amount: int,
):
    """
    Начисляет мгновенную награду BONUS_STAR.

    Используется существующая игровая статистика
    и журнал операций со звёздами.
    """
    from apps.game.models import (
        StarTransaction,
        UserGameStatistics,
    )

    statistics, _ = (
        UserGameStatistics.objects
        .select_for_update()
        .get_or_create(
            user=user,
        )
    )

    statistics.stars += amount

    statistics.save(
        update_fields=[
            "stars",
            "updated_at",
        ]
    )

    StarTransaction.objects.create(
        user=user,
        amount=amount,
        reason=StarTransaction.Reason.BONUS_CODE,
        description=(
            "Начисление по чит-коду "
            f"{activation.cheat.code}"
        ),
    )