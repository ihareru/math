from dataclasses import dataclass

from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.accounts.models import User
from apps.game.models import UserGameStatistics


@dataclass(frozen=True)
class RatingRow:
    """
    Одна публичная строка рейтинга.
    """

    user_id: object
    rank: int
    display_name: str
    stars: int
    total_correct: int
    total_wrong: int
    best_streak: int
    accuracy_percent: float

    @property
    def total_answers(self) -> int:
        return self.total_correct + self.total_wrong


@dataclass(frozen=True)
class PublicRatingSummary:
    """
    Общие публичные показатели приложения.
    """

    registered_users: int
    rating_participants: int
    total_stars: int
    total_correct_answers: int


def calculate_accuracy(
    *,
    correct: int,
    wrong: int,
) -> float:
    total = correct + wrong

    if total == 0:
        return 0.0

    return round(
        correct * 100 / total,
        1,
    )


def get_rating_users_queryset():
    """
    Возвращает пользователей, разрешивших отображение
    в публичном рейтинге и имеющих игровую статистику.

    Пользователь без UserGameStatistics не должен
    ломать публичную главную страницу.
    """
    return (
        User.objects
        .filter(
            is_active=True,
            email_verified=True,
            show_in_rating=True,
            game_statistics__isnull=False,
        )
        .select_related(
            "game_statistics",
        )
        .order_by(
            "-game_statistics__stars",
            "-game_statistics__total_correct",
            "-game_statistics__best_streak",
            "display_name",
        )
    )


def build_public_rating() -> list[RatingRow]:
    """
    Формирует рейтинг с одинаковыми местами для
    пользователей с одинаковым числом звёзд.
    """
    users = get_rating_users_queryset()

    result = []

    current_rank = 0
    previous_stars = None

    for user in users:
        statistics = user.game_statistics

        if (
            previous_stars is None
            or statistics.stars != previous_stars
        ):
            current_rank += 1
            previous_stars = statistics.stars

        result.append(
            RatingRow(
                user_id=user.pk,
                rank=current_rank,
                display_name=user.display_name,
                stars=statistics.stars,
                total_correct=(
                    statistics.total_correct
                ),
                total_wrong=(
                    statistics.total_wrong
                ),
                best_streak=(
                    statistics.best_streak
                ),
                accuracy_percent=calculate_accuracy(
                    correct=statistics.total_correct,
                    wrong=statistics.total_wrong,
                ),
            )
        )

    return result


def get_public_rating_summary() -> PublicRatingSummary:
    """
    Возвращает общие показатели для публичной
    главной страницы.
    """
    registered_users = (
        User.objects
        .filter(
            is_active=True,
            email_verified=True,
        )
        .count()
    )

    participant_user_ids = (
        User.objects
        .filter(
            is_active=True,
            email_verified=True,
            show_in_rating=True,
        )
        .values_list(
            "pk",
            flat=True,
        )
    )

    aggregates = (
        UserGameStatistics.objects
        .filter(
            user_id__in=participant_user_ids,
        )
        .aggregate(
            total_stars=Coalesce(
                Sum("stars"),
                0,
            ),
            total_correct_answers=Coalesce(
                Sum("total_correct"),
                0,
            ),
        )
    )

    return PublicRatingSummary(
        registered_users=registered_users,
        rating_participants=(
            participant_user_ids.count()
        ),
        total_stars=aggregates["total_stars"],
        total_correct_answers=(
            aggregates["total_correct_answers"]
        ),
    )


def find_user_rating_row(
    *,
    rating_rows: list[RatingRow],
    user,
) -> RatingRow | None:
    if not user.is_authenticated:
        return None

    for row in rating_rows:
        if row.user_id == user.pk:
            return row

    return None