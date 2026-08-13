from django.db import transaction
from django.db.models import Exists, Max, OuterRef
from django.utils import timezone

from apps.game.models import (
    GameQuestion,
    GameSession,
    UserGameStatistics,
)

from .exceptions import (
    NoActiveGameSessionError,
)
from .gameplay import get_active_session


class NoReviewQuestionsError(Exception):
    """У пользователя нет ошибок для повторения."""


def get_unresolved_wrong_questions(
    *,
    user,
    limit=None,
):
    """
    Возвращает исходные ошибочные ответы пользователя,
    которые ещё не были исправлены правильным повтором.

    Повторные ошибки не используются как новые исходные
    ошибки. Источником всегда является обычный вопрос.
    """
    successful_review_exists = (
        GameQuestion.objects
        .filter(
            source_question_id=OuterRef("pk"),
            is_review=True,
            is_correct=True,
        )
    )

    queryset = (
        GameQuestion.objects
        .filter(
            session__user=user,
            is_review=False,
            is_correct=False,
            answered_at__isnull=False,
        )
        .annotate(
            has_successful_review=Exists(
                successful_review_exists
            )
        )
        .filter(
            has_successful_review=False
        )
        .select_related("session")
        .order_by("answered_at")
    )

    if limit is not None:
        safe_limit = min(
            max(int(limit), 1),
            100,
        )

        queryset = queryset[:safe_limit]

    return queryset


def count_unresolved_wrong_questions(
    *,
    user,
) -> int:
    return get_unresolved_wrong_questions(
        user=user,
    ).count()


@transaction.atomic
def start_review_session(
    *,
    user,
) -> GameSession:
    """
    Создаёт новую сессию повторения ошибок.

    Все предыдущие активные сессии пользователя
    помечаются как прерванные.
    """
    if not get_unresolved_wrong_questions(
        user=user,
    ).exists():
        raise NoReviewQuestionsError(
            "У вас пока нет ошибок для повторения."
        )

    now = timezone.now()

    (
        GameSession.objects
        .select_for_update()
        .filter(
            user=user,
            status=GameSession.Status.ACTIVE,
        )
        .update(
            status=GameSession.Status.ABANDONED,
            finished_at=now,
            last_activity_at=now,
        )
    )

    game_session = GameSession.objects.create(
        user=user,
        mode=GameSession.Mode.REVIEW,
        status=GameSession.Status.ACTIVE,
        last_activity_at=now,
    )

    statistics, _ = (
        UserGameStatistics.objects
        .select_for_update()
        .get_or_create(
            user=user,
        )
    )

    statistics.total_sessions += 1

    statistics.save(
        update_fields=[
            "total_sessions",
            "updated_at",
        ]
    )

    return game_session


@transaction.atomic
def get_or_create_review_question(
    *,
    user,
) -> GameQuestion:
    """
    Возвращает текущий неотвеченный повторный вопрос
    либо создаёт новый на основе старой ошибки.
    """
    game_session = (
        GameSession.objects
        .select_for_update()
        .filter(
            user=user,
            mode=GameSession.Mode.REVIEW,
            status=GameSession.Status.ACTIVE,
        )
        .order_by("-started_at")
        .first()
    )

    if game_session is None:
        raise NoActiveGameSessionError(
            "Активная сессия повторения не найдена."
        )

    unanswered_question = (
        GameQuestion.objects
        .filter(
            session=game_session,
            answered_at__isnull=True,
        )
        .order_by("sequence_number")
        .first()
    )

    if unanswered_question is not None:
        return unanswered_question

    already_used_source_ids = (
        GameQuestion.objects
        .filter(
            session=game_session,
            is_review=True,
            source_question__isnull=False,
        )
        .values_list(
            "source_question_id",
            flat=True,
        )
    )

    source_question = (
        get_unresolved_wrong_questions(
            user=user,
        )
        .exclude(
            pk__in=already_used_source_ids,
        )
        .first()
    )

    if source_question is None:
        raise NoReviewQuestionsError(
            "Все доступные ошибки в этой сессии разобраны."
        )

    maximum_sequence = (
        GameQuestion.objects
        .filter(
            session=game_session,
        )
        .aggregate(
            maximum=Max("sequence_number")
        )["maximum"]
        or 0
    )

    review_question = GameQuestion.objects.create(
        session=game_session,
        sequence_number=maximum_sequence + 1,
        operation=source_question.operation,
        num1=source_question.num1,
        num2=source_question.num2,
        operands=list(
            source_question.effective_operands
        ),
        correct_answer=source_question.correct_answer,
        is_review=True,
        source_question=source_question,
    )

    game_session.last_activity_at = timezone.now()

    game_session.save(
        update_fields=[
            "last_activity_at",
        ]
    )

    return review_question