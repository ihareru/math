from dataclasses import dataclass

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.game.models import (
    GameQuestion,
    GameSession,
    StarTransaction,
    UserGameStatistics,
)
from apps.cheats.services.rewards import (
    get_active_game_rewards,
)
from .exceptions import (
    ActiveQuestionNotFoundError,
    NoActiveGameSessionError,
    QuestionAlreadyAnsweredError,
    QuestionDoesNotBelongToUserError,
)
from .generator import generate_question


DEFAULT_CORRECT_ANSWERS_PER_STAR = 10


@dataclass(frozen=True)
class AnswerResult:
    question_id: int
    is_correct: bool
    user_answer: int
    correct_answer: int
    current_streak: int
    best_streak: int
    awarded_stars: int
    total_stars: int
    response_time_ms: int
    review_completed: bool

    @property
    def star_awarded(self) -> bool:
        """
        Обратная совместимость с существующим кодом.
        """
        return self.awarded_stars > 0


@transaction.atomic
def start_game_session(
    *,
    user,
    mode: str,
) -> GameSession:
    """
    Завершает предыдущие активные сессии пользователя
    как прерванные и создаёт новую.
    """
    if mode not in {
        GameSession.Mode.ADD,
        GameSession.Mode.SUB,
        GameSession.Mode.MUL,
        GameSession.Mode.DIV,
        GameSession.Mode.ALL,
    }:
        raise ValueError(
            "Выбран неизвестный игровой режим."
        )

    now = timezone.now()

    active_sessions = (
        GameSession.objects
        .select_for_update()
        .filter(
            user=user,
            status=GameSession.Status.ACTIVE,
        )
    )

    active_sessions.update(
        status=GameSession.Status.ABANDONED,
        finished_at=now,
        last_activity_at=now,
    )

    game_session = GameSession.objects.create(
        user=user,
        mode=mode,
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


def get_active_session(*, user) -> GameSession | None:
    return (
        GameSession.objects
        .filter(
            user=user,
            status=GameSession.Status.ACTIVE,
        )
        .order_by("-started_at")
        .first()
    )


@transaction.atomic
def get_or_create_current_question(
    *,
    user,
) -> GameQuestion:
    """
    Возвращает уже показанный, но ещё не отвеченный
    пример. Если такого нет — создаёт новый.

    Поэтому обычное обновление страницы не создаёт
    новый пример и не пропускает предыдущий.
    """
    game_session = (
        GameSession.objects
        .select_for_update()
        .filter(
            user=user,
            status=GameSession.Status.ACTIVE,
        )
        .order_by("-started_at")
        .first()
    )

    if game_session is None:
        raise NoActiveGameSessionError(
            "Активная игровая сессия не найдена."
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

    if game_session.mode == GameSession.Mode.REVIEW:
        raise ValueError(
            "Для режима повторения используйте "
            "get_or_create_review_question()."
        )

    max_sequence = (
        GameQuestion.objects
        .filter(session=game_session)
        .aggregate(
            maximum=Max("sequence_number")
        )["maximum"]
        or 0
    )

    generated = generate_question(
        game_session.mode
    )

    question = GameQuestion.objects.create(
        session=game_session,
        sequence_number=max_sequence + 1,
        operation=generated.operation,
        num1=generated.num1,
        num2=generated.num2,
        correct_answer=generated.correct_answer,
    )

    game_session.last_activity_at = timezone.now()

    game_session.save(
        update_fields=[
            "last_activity_at",
        ]
    )

    return question


@transaction.atomic
def submit_answer(
    *,
    user,
    question_id: int,
    user_answer: int,
) -> AnswerResult:
    """
    Проверяет и сохраняет ответ пользователя.

    Одновременно обновляет:
    - текущую игровую сессию;
    - общую статистику;
    - серию правильных ответов;
    - историю звёзд.
    """
    question = (
        GameQuestion.objects
        .select_for_update()
        .select_related(
            "session",
            "session__user",
        )
        .filter(pk=question_id)
        .first()
    )

    if question is None:
        raise ActiveQuestionNotFoundError(
            "Игровой пример не найден."
        )

    if question.session.user_id != user.pk:
        raise QuestionDoesNotBelongToUserError(
            "Этот пример принадлежит другому пользователю."
        )

    if question.is_answered:
        raise QuestionAlreadyAnsweredError(
            "Ответ на этот пример уже сохранён."
        )

    game_session = (
        GameSession.objects
        .select_for_update()
        .get(pk=question.session_id)
    )

    if game_session.status != GameSession.Status.ACTIVE:
        raise NoActiveGameSessionError(
            "Игровая сессия уже завершена."
        )

    now = timezone.now()

    response_time_ms = max(
        0,
        int(
            (
                now - question.shown_at
            ).total_seconds()
            * 1000
        ),
    )

    is_correct = (
        user_answer == question.correct_answer
    )

    question.user_answer = user_answer
    question.is_correct = is_correct
    question.answered_at = now
    question.response_time_ms = response_time_ms

    question.save(
        update_fields=[
            "user_answer",
            "is_correct",
            "answered_at",
            "response_time_ms",
        ]
    )

    statistics, _ = (
        UserGameStatistics.objects
        .select_for_update()
        .get_or_create(
            user=user,
        )
    )

    active_rewards = get_active_game_rewards(
        user=user,
    )

    awarded_stars = 0

    if is_correct:
        game_session.correct_count += 1
        game_session.current_streak += 1

        game_session.best_streak = max(
            game_session.best_streak,
            game_session.current_streak,
        )

        statistics.total_correct += 1

        statistics.best_streak = max(
            statistics.best_streak,
            game_session.current_streak,
        )

        if (
            game_session.current_streak
            % active_rewards.streak_to_star
            == 0
        ):
            awarded_stars = (
                active_rewards.star_multiplier
            )

            game_session.stars_earned += awarded_stars
            statistics.stars += awarded_stars

            StarTransaction.objects.create(
                user=user,
                session=game_session,
                amount=awarded_stars,
                reason=StarTransaction.Reason.STREAK,
                description=(
                    "Звёзды за серию из "
                    f"{active_rewards.streak_to_star} "
                    "правильных ответов подряд"
                ),
            )
    else:
        game_session.wrong_count += 1

        if not active_rewards.freeze_streak:
            game_session.current_streak = 0

        statistics.total_wrong += 1

    game_session.last_activity_at = now

    game_session.save(
        update_fields=[
            "correct_count",
            "wrong_count",
            "current_streak",
            "best_streak",
            "stars_earned",
            "last_activity_at",
        ]
    )

    statistics.total_answer_time_ms += (
        response_time_ms
    )

    statistics.save(
        update_fields=[
            "stars",
            "total_correct",
            "total_wrong",
            "best_streak",
            "total_answer_time_ms",
            "updated_at",
        ]
    )

    return AnswerResult(
        question_id=question.pk,
        is_correct=is_correct,
        user_answer=user_answer,
        correct_answer=question.correct_answer,
        current_streak=game_session.current_streak,
        best_streak=game_session.best_streak,
        awarded_stars=awarded_stars,
        total_stars=statistics.stars,
        response_time_ms=response_time_ms,
        review_completed=(
                question.is_review
                and is_correct
        ),
    )


def get_recent_answered_questions(
    *,
    user,
    limit: int = 10,
):
    """
    Возвращает последние отвеченные примеры пользователя.
    """
    safe_limit = min(
        max(limit, 1),
        100,
    )

    return (
        GameQuestion.objects
        .filter(
            session__user=user,
            answered_at__isnull=False,
        )
        .select_related("session")
        .order_by(
            "-answered_at",
        )[:safe_limit]
    )


@transaction.atomic
def finish_active_session(
    *,
    user,
    status: str = GameSession.Status.COMPLETED,
) -> GameSession:
    game_session = (
        GameSession.objects
        .select_for_update()
        .filter(
            user=user,
            status=GameSession.Status.ACTIVE,
        )
        .order_by("-started_at")
        .first()
    )

    if game_session is None:
        raise NoActiveGameSessionError(
            "Активная игровая сессия не найдена."
        )

    game_session.finish(status=status)

    return game_session