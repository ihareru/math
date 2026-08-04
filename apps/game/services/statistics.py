from dataclasses import dataclass
from datetime import timedelta

from django.db.models import (
    Avg,
    Count,
    Max,
    Q,
)
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.game.models import (
    GameQuestion,
    GameSession,
    UserGameStatistics,
)

from .review import count_unresolved_wrong_questions


@dataclass(frozen=True)
class OperationStatistics:
    operation: str
    title: str
    symbol: str
    correct_count: int
    wrong_count: int
    total_count: int
    accuracy_percent: float
    average_response_time_seconds: float


@dataclass(frozen=True)
class DailyStatistics:
    date: object
    correct_count: int
    wrong_count: int
    total_count: int
    accuracy_percent: float


OPERATION_PRESENTATION = {
    GameQuestion.Operation.ADD: {
        "title": "Сложение",
        "symbol": "+",
    },
    GameQuestion.Operation.SUB: {
        "title": "Вычитание",
        "symbol": "−",
    },
    GameQuestion.Operation.MUL: {
        "title": "Умножение",
        "symbol": "×",
    },
    GameQuestion.Operation.DIV: {
        "title": "Деление",
        "symbol": ":",
    },
}


def calculate_accuracy(
    correct_count: int,
    total_count: int,
) -> float:
    if total_count == 0:
        return 0.0

    return round(
        correct_count * 100 / total_count,
        1,
    )


def get_user_statistics(*, user):
    statistics, _ = (
        UserGameStatistics.objects.get_or_create(
            user=user,
        )
    )

    return statistics


def get_operation_statistics(*, user):
    """
    Возвращает показатели отдельно по каждому
    математическому действию.

    В статистику входят как обычные вопросы,
    так и повторения ошибок.
    """
    rows = (
        GameQuestion.objects
        .filter(
            session__user=user,
            answered_at__isnull=False,
        )
        .values("operation")
        .annotate(
            total_count=Count("id"),
            correct_count=Count(
                "id",
                filter=Q(is_correct=True),
            ),
            wrong_count=Count(
                "id",
                filter=Q(is_correct=False),
            ),
            average_response_time_ms=Avg(
                "response_time_ms"
            ),
        )
    )

    rows_by_operation = {
        row["operation"]: row
        for row in rows
    }

    result = []

    for operation, presentation in (
        OPERATION_PRESENTATION.items()
    ):
        row = rows_by_operation.get(
            operation,
            {},
        )

        total_count = row.get(
            "total_count",
            0,
        )

        correct_count = row.get(
            "correct_count",
            0,
        )

        wrong_count = row.get(
            "wrong_count",
            0,
        )

        average_response_time_ms = (
            row.get("average_response_time_ms")
            or 0
        )

        result.append(
            OperationStatistics(
                operation=operation,
                title=presentation["title"],
                symbol=presentation["symbol"],
                correct_count=correct_count,
                wrong_count=wrong_count,
                total_count=total_count,
                accuracy_percent=calculate_accuracy(
                    correct_count,
                    total_count,
                ),
                average_response_time_seconds=round(
                    average_response_time_ms / 1000,
                    2,
                ),
            )
        )

    return result


def get_recent_sessions(
    *,
    user,
    limit=10,
):
    safe_limit = min(
        max(int(limit), 1),
        100,
    )

    return (
        GameSession.objects
        .filter(user=user)
        .annotate(
            average_response_time_ms=Avg(
                "questions__response_time_ms",
                filter=Q(
                    questions__answered_at__isnull=False
                ),
            )
        )
        .order_by("-started_at")[:safe_limit]
    )


def get_frequent_errors(
    *,
    user,
    limit=10,
):
    safe_limit = min(
        max(int(limit), 1),
        50,
    )

    rows = (
        GameQuestion.objects
        .filter(
            session__user=user,
            is_correct=False,
            answered_at__isnull=False,
        )
        .values(
            "operation",
            "num1",
            "num2",
            "correct_answer",
        )
        .annotate(
            error_count=Count("id"),
            latest_error_at=Max(
                "answered_at"
            ),
        )
        .order_by(
            "-error_count",
            "operation",
            "num1",
            "num2",
        )[:safe_limit]
    )

    return [
        {
            **row,
            "expression": build_expression(
                operation=row["operation"],
                num1=row["num1"],
                num2=row["num2"],
            ),
        }
        for row in rows
    ]


def get_daily_statistics(
    *,
    user,
    days=30,
):
    """
    Возвращает статистику по дням за последние
    N календарных дней.
    """
    safe_days = min(
        max(int(days), 1),
        365,
    )

    start_date = (
        timezone.localdate()
        - timedelta(days=safe_days - 1)
    )

    rows = (
        GameQuestion.objects
        .filter(
            session__user=user,
            answered_at__date__gte=start_date,
            answered_at__isnull=False,
        )
        .annotate(
            answer_date=TruncDate("answered_at")
        )
        .values("answer_date")
        .annotate(
            total_count=Count("id"),
            correct_count=Count(
                "id",
                filter=Q(is_correct=True),
            ),
            wrong_count=Count(
                "id",
                filter=Q(is_correct=False),
            ),
        )
        .order_by("answer_date")
    )

    return [
        DailyStatistics(
            date=row["answer_date"],
            correct_count=row["correct_count"],
            wrong_count=row["wrong_count"],
            total_count=row["total_count"],
            accuracy_percent=calculate_accuracy(
                row["correct_count"],
                row["total_count"],
            ),
        )
        for row in rows
    ]


def get_statistics_dashboard_data(*, user):
    statistics = get_user_statistics(
        user=user,
    )

    return {
        "statistics": statistics,
        "operation_statistics": (
            get_operation_statistics(
                user=user,
            )
        ),
        "recent_sessions": get_recent_sessions(
            user=user,
            limit=10,
        ),
        "frequent_errors": get_frequent_errors(
            user=user,
            limit=10,
        ),
        "daily_statistics": get_daily_statistics(
            user=user,
            days=30,
        ),
        "unresolved_errors_count": (
            count_unresolved_wrong_questions(
                user=user,
            )
        ),
    }

def get_operation_symbol(
    operation: str,
) -> str:
    presentation = OPERATION_PRESENTATION.get(
        operation
    )

    if presentation is None:
        return "?"

    return presentation["symbol"]


def build_expression(
    *,
    operation: str,
    num1: int,
    num2: int,
) -> str:
    return (
        f"{num1} "
        f"{get_operation_symbol(operation)} "
        f"{num2}"
    )