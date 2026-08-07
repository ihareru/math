from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
)
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.db import transaction
from django.db.models import Avg, Q, Case, IntegerField, Value, When
from django.views.decorators.http import (
    require_POST,
)

from .models import (
    GameQuestion,
    GameSession,
    OperationGenerationSettings,
    UserGameStatistics,
)
from .services.exceptions import GameServiceError
from .services.gameplay import (
    finish_active_session,
    get_active_session,
    get_or_create_current_question,
    get_recent_answered_questions,
    start_game_session,
    submit_answer,
)
from .services.review import (
    NoReviewQuestionsError,
    count_unresolved_wrong_questions,
    get_or_create_review_question,
    start_review_session,
)
from .services.statistics import (
    get_statistics_dashboard_data,
)
from .services.generator import (
    operation_is_enabled_for_mode,
)
from .services.generator_exceptions import (
    QuestionGenerationError,
)
from .services.generation_settings import (
    calculate_operation_difficulty_level,
    create_default_generation_settings,
    get_all_operation_difficulty_progress,
)
from .forms import (
    AnswerForm,
    OperationGenerationSettingsFormSet,
    UserGenerationSettingsForm,
)


ALLOWED_GAME_MODES = {
    GameSession.Mode.ADD,
    GameSession.Mode.SUB,
    GameSession.Mode.MUL,
    GameSession.Mode.DIV,
    GameSession.Mode.ALL,
}


@login_required
def mode_select(request):
    statistics, _ = (
        UserGameStatistics.objects.get_or_create(
            user=request.user,
        )
    )

    active_session = get_active_session(
        user=request.user,
    )

    unresolved_errors_count = (
        count_unresolved_wrong_questions(
            user=request.user,
        )
    )

    generation_settings = (
        request.user.generation_settings
    )

    enabled_operations = {
        operation.operation
        for operation
        in generation_settings.operations.filter(
            is_enabled=True,
        )
    }

    mixed_mode_enabled = (
        generation_settings
        .operations
        .filter(
            is_enabled=True,
            mixed_mode_weight__gt=0,
        )
        .exists()
    )

    return render(
        request,
        "game/mode_select.html",
        {
            "modes": [
                {
                    "value": GameSession.Mode.ADD,
                    "title": "Сложение",
                    "symbol": "+",
                    "enabled": (
                        OperationGenerationSettings
                        .Operation
                        .ADD
                        in enabled_operations
                    ),
                },
                {
                    "value": GameSession.Mode.SUB,
                    "title": "Вычитание",
                    "symbol": "−",
                    "enabled": (
                        OperationGenerationSettings
                        .Operation
                        .SUB
                        in enabled_operations
                    ),
                },
                {
                    "value": GameSession.Mode.MUL,
                    "title": "Умножение",
                    "symbol": "×",
                    "enabled": (
                        OperationGenerationSettings
                        .Operation
                        .MUL
                        in enabled_operations
                    ),
                },
                {
                    "value": GameSession.Mode.DIV,
                    "title": "Деление",
                    "symbol": ":",
                    "enabled": (
                        OperationGenerationSettings
                        .Operation
                        .DIV
                        in enabled_operations
                    ),
                },
                {
                    "value": GameSession.Mode.ALL,
                    "title": "Все действия",
                    "symbol": "±",
                    "enabled": mixed_mode_enabled,
                },
            ],
            "statistics": statistics,
            "active_session": active_session,
            "unresolved_errors_count": unresolved_errors_count,
        },
    )


@login_required
@require_POST
def start(request, mode):
    if mode not in ALLOWED_GAME_MODES:
        raise Http404(
            "Неизвестный игровой режим."
        )
    if not operation_is_enabled_for_mode(
            user=request.user,
            mode=mode,
    ):
        messages.error(
            request,
            (
                "Этот игровой режим отключён "
                "в ваших настройках генератора."
            ),
        )

        return redirect("game:mode_select")

    start_game_session(
        user=request.user,
        mode=mode,
    )

    return redirect("game:play")


@login_required
def play(request):
    game_session = get_active_session(
        user=request.user,
    )

    if game_session is None:
        messages.warning(
            request,
            "Сначала выберите режим игры.",
        )

        return redirect("game:mode_select")

    try:
        if (
            game_session.mode
            == GameSession.Mode.REVIEW
        ):
            question = get_or_create_review_question(
                user=request.user,
            )
        else:
            question = get_or_create_current_question(
                user=request.user,
            )

    except NoReviewQuestionsError:
        game_session.finish(
            status=GameSession.Status.COMPLETED
        )

        messages.success(
            request,
            (
                "Повторение завершено. "
                "Все выбранные ошибки разобраны."
            ),
        )

        return redirect("game:mode_select")

    except QuestionGenerationError as error:
        messages.error(
            request,
            (
                "Не удалось создать пример: "
                f"{error}"
            ),
        )

        return redirect(
            "game:mode_select"
        )

    except GameServiceError:
        messages.warning(
            request,
            "Сначала выберите режим игры.",
        )

        return redirect("game:mode_select")

    game_session = question.session

    operation_settings = (
        request.user
        .generation_settings
        .operations
        .filter(
            operation=question.operation,
        )
        .first()
    )

    if operation_settings is not None:
        difficulty_level = (
            calculate_operation_difficulty_level(
                generation_settings=(
                    request.user
                    .generation_settings
                ),
                operation=(
                    operation_settings.operation
                ),
            )
        )
    else:
        difficulty_level = 1

    question_to_settings_operation = {
        GameQuestion.Operation.ADD: (
            OperationGenerationSettings
            .Operation.ADD
        ),
        GameQuestion.Operation.SUB: (
            OperationGenerationSettings
            .Operation.SUB
        ),
        GameQuestion.Operation.MUL: (
            OperationGenerationSettings
            .Operation.MUL
        ),
        GameQuestion.Operation.DIV: (
            OperationGenerationSettings
            .Operation.DIV
        ),
    }

    settings_operation = (
        question_to_settings_operation.get(
            question.operation
        )
    )

    if settings_operation is not None:
        difficulty_level = (
            calculate_operation_difficulty_level(
                generation_settings=(
                    request.user
                    .generation_settings
                ),
                operation=settings_operation,
            )
        )
    else:
        difficulty_level = 1

    recent_questions = (
        get_recent_answered_questions(
            user=request.user,
            limit=10,
        )
    )

    return render(
        request,
        "game/play.html",
        {
            "question": question,
            "game_session": game_session,
            "form": AnswerForm(),
            "recent_questions": recent_questions,
            "difficulty_level": difficulty_level,

        },
    )


@login_required
@require_POST
def answer(request, question_id):
    question = get_object_or_404(
        GameQuestion,
        pk=question_id,
        session__user=request.user,
    )

    form = AnswerForm(request.POST)

    if not form.is_valid():
        recent_questions = (
            get_recent_answered_questions(
                user=request.user,
                limit=10,
            )
        )

        return render(
            request,
            "game/play.html",
            {
                "question": question,
                "game_session": question.session,
                "form": form,
                "recent_questions": recent_questions,
            },
            status=400,
        )

    try:
        answer_result = submit_answer(
            user=request.user,
            question_id=question.pk,
            user_answer=form.cleaned_data[
                "answer"
            ],
        )

        request.session[
            f"question_{question.pk}_awarded_stars"
        ] = answer_result.awarded_stars

    except GameServiceError as error:
        messages.warning(
            request,
            str(error),
        )

    return redirect(
        "game:question_result",
        question_id=question.pk,
    )


@login_required
def question_result(
    request,
    question_id,
):
    question = get_object_or_404(
        GameQuestion.objects.select_related(
            "session",
        ),
        pk=question_id,
        session__user=request.user,
        answered_at__isnull=False,
    )

    recent_questions = (
        get_recent_answered_questions(
            user=request.user,
            limit=10,
        )
    )

    statistics, _ = (
        UserGameStatistics.objects.get_or_create(
            user=request.user,
        )
    )

    awarded_stars = request.session.pop(
        f"question_{question.pk}_awarded_stars",
        0,
    )

    return render(
        request,
        "game/question_result.html",
        {
            "question": question,
            "game_session": question.session,
            "statistics": statistics,
            "recent_questions": recent_questions,
            "awarded_stars": awarded_stars,
        },
    )


@login_required
@require_POST
def next_question(request):
    if get_active_session(
        user=request.user,
    ) is None:
        messages.warning(
            request,
            "Активная игровая сессия не найдена.",
        )

        return redirect("game:mode_select")

    return redirect("game:play")


@login_required
@require_POST
def finish(request):
    try:
        game_session = finish_active_session(
            user=request.user,
        )
    except GameServiceError:
        messages.warning(
            request,
            "Активная игровая сессия не найдена.",
        )

        return redirect("game:mode_select")

    messages.success(
        request,
        (
            "Игровая сессия завершена. "
            f"Правильных ответов: "
            f"{game_session.correct_count}, "
            f"ошибок: {game_session.wrong_count}."
        ),
    )

    return redirect("game:mode_select")


@login_required
def history(request):
    questions = (
        GameQuestion.objects
        .filter(
            session__user=request.user,
            answered_at__isnull=False,
        )
        .select_related("session")
        .order_by("-answered_at")
    )

    return render(
        request,
        "game/history.html",
        {
            "questions": questions[:100],
        },
    )

@login_required
@require_POST
def start_review(request):
    try:
        start_review_session(
            user=request.user,
        )
    except NoReviewQuestionsError as error:
        messages.info(
            request,
            str(error),
        )

        return redirect("game:mode_select")

    return redirect("game:play")

@login_required
def statistics_dashboard(request):
    context = get_statistics_dashboard_data(
        user=request.user,
    )

    return render(
        request,
        "game/statistics_dashboard.html",
        context,
    )

@login_required
def session_list(request):
    sessions = (
        GameSession.objects
        .filter(user=request.user)
        .annotate(
            average_response_time_ms=Avg(
                "questions__response_time_ms",
                filter=Q(
                    questions__answered_at__isnull=False
                ),
            )
        )
        .order_by("-started_at")
    )

    paginator = Paginator(
        sessions,
        20,
    )

    page = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "game/session_list.html",
        {
            "page_obj": page,
        },
    )

@login_required
def session_detail(
    request,
    session_id,
):
    game_session = get_object_or_404(
        GameSession.objects.annotate(
            average_response_time_ms=Avg(
                "questions__response_time_ms",
                filter=Q(
                    questions__answered_at__isnull=False
                ),
            )
        ),
        pk=session_id,
        user=request.user,
    )

    questions = (
        game_session.questions
        .filter(
            answered_at__isnull=False,
        )
        .select_related(
            "source_question",
        )
        .order_by("sequence_number")
    )

    paginator = Paginator(
        questions,
        25,
    )

    page = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "game/session_detail.html",
        {
            "game_session": game_session,
            "page_obj": page,
        },
    )

@login_required
@transaction.atomic
def generation_settings(request):
    settings_object = (
        create_default_generation_settings(
            user=request.user,
        )
    )

    operations_queryset = (
        settings_object
        .operations
        .annotate(
            display_order=Case(
                When(
                    operation=(
                        OperationGenerationSettings
                        .Operation.ADD
                    ),
                    then=Value(1),
                ),
                When(
                    operation=(
                        OperationGenerationSettings
                        .Operation.SUB
                    ),
                    then=Value(2),
                ),
                When(
                    operation=(
                        OperationGenerationSettings
                        .Operation.MUL
                    ),
                    then=Value(3),
                ),
                When(
                    operation=(
                        OperationGenerationSettings
                        .Operation.DIV
                    ),
                    then=Value(4),
                ),
                default=Value(99),
                output_field=IntegerField(),
            )
        )
        .order_by("display_order")
    )

    if request.method == "POST":
        form = UserGenerationSettingsForm(
            request.POST,
            instance=settings_object,
        )

        operation_formset = (
            OperationGenerationSettingsFormSet(
                request.POST,
                instance=settings_object,
                queryset=operations_queryset,
                prefix="operations",
            )
        )

        if (
            form.is_valid()
            and operation_formset.is_valid()
        ):
            settings_object = form.save()

            operation_formset.instance = (
                settings_object
            )

            operation_formset.save()

            messages.success(
                request,
                (
                    "Настройки генерации примеров "
                    "сохранены."
                ),
            )

            return redirect(
                "game:generation_settings"
            )
    else:
        form = UserGenerationSettingsForm(
            instance=settings_object,
        )

        operation_formset = (
            OperationGenerationSettingsFormSet(
                instance=settings_object,
                queryset=operations_queryset,
                prefix="operations",
            )
        )

    difficulty_progress = (
        get_all_operation_difficulty_progress(
            generation_settings=(
                settings_object
            ),
        )
    )

    return render(
        request,
        "game/generation_settings.html",
        {
            "form": form,
            "operation_formset": (
                operation_formset
            ),
            "settings_object": (
                settings_object
            ),
            "difficulty_progress": (
                difficulty_progress
            ),
        },
    )