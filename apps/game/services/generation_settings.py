from dataclasses import dataclass

from django.db import transaction
from django.db.models import Count, Q

from apps.game.models import (
    GameQuestion,
    OperationGenerationSettings,
    UserGenerationSettings,
)


DEFAULT_OPERATION_SETTINGS = {
    OperationGenerationSettings.Operation.ADD: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 100,
        "second_operand_min": 1,
        "second_operand_max": 100,
        "operands_count": 2,
        "minimum_answer": None,
        "maximum_answer": 200,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
    OperationGenerationSettings.Operation.SUB: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 100,
        "second_operand_min": 1,
        "second_operand_max": 100,
        "operands_count": 2,
        "minimum_answer": 0,
        "maximum_answer": 100,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
    OperationGenerationSettings.Operation.MUL: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 10,
        "second_operand_min": 1,
        "second_operand_max": 10,
        "operands_count": 2,
        "minimum_answer": 1,
        "maximum_answer": 100,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
    OperationGenerationSettings.Operation.DIV: {
        "is_enabled": True,
        "mixed_mode_weight": 25,
        "first_operand_min": 1,
        "first_operand_max": 10,
        "second_operand_min": 1,
        "second_operand_max": 10,
        "operands_count": 2,
        "minimum_answer": 1,
        "maximum_answer": 10,
        "allow_negative_result": False,
        "allow_remainder": False,
    },
}

DIFFICULTY_PROFILES = {
    UserGenerationSettings.DifficultyProfile.EASY: {
        "general": {
            "avoid_recent_duplicates": True,
            "recent_questions_limit": 50,
            "auto_increase_difficulty": False,
            "correct_answers_per_level": 50,
            "maximum_difficulty_level": 5,
        },
        "operations": {
            OperationGenerationSettings.Operation.ADD: {
                "is_enabled": True,
                "mixed_mode_weight": 35,
                "first_operand_min": 1,
                "first_operand_max": 20,
                "second_operand_min": 1,
                "second_operand_max": 20,
                "operands_count": 2,
                "minimum_answer": 0,
                "maximum_answer": 40,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.SUB: {
                "is_enabled": True,
                "mixed_mode_weight": 35,
                "first_operand_min": 1,
                "first_operand_max": 20,
                "second_operand_min": 1,
                "second_operand_max": 20,
                "operands_count": 2,
                "minimum_answer": 0,
                "maximum_answer": 20,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.MUL: {
                "is_enabled": True,
                "mixed_mode_weight": 20,
                "first_operand_min": 1,
                "first_operand_max": 5,
                "second_operand_min": 1,
                "second_operand_max": 5,
                "operands_count": 2,
                "minimum_answer": 1,
                "maximum_answer": 25,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.DIV: {
                "is_enabled": True,
                "mixed_mode_weight": 10,
                "first_operand_min": 1,
                "first_operand_max": 5,
                "second_operand_min": 1,
                "second_operand_max": 5,
                "operands_count": 2,
                "minimum_answer": 1,
                "maximum_answer": 5,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
        },
    },

    UserGenerationSettings.DifficultyProfile.MEDIUM: {
        "general": {
            "avoid_recent_duplicates": True,
            "recent_questions_limit": 100,
            "auto_increase_difficulty": True,
            "correct_answers_per_level": 50,
            "maximum_difficulty_level": 10,
        },
        "operations": {
            OperationGenerationSettings.Operation.ADD: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 1,
                "first_operand_max": 100,
                "second_operand_min": 1,
                "second_operand_max": 100,
                "operands_count": 2,
                "minimum_answer": None,
                "maximum_answer": 200,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.SUB: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 1,
                "first_operand_max": 100,
                "second_operand_min": 1,
                "second_operand_max": 100,
                "operands_count": 2,
                "minimum_answer": 0,
                "maximum_answer": 100,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.MUL: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 1,
                "first_operand_max": 10,
                "second_operand_min": 1,
                "second_operand_max": 10,
                "operands_count": 2,
                "minimum_answer": 1,
                "maximum_answer": 100,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.DIV: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 1,
                "first_operand_max": 10,
                "second_operand_min": 1,
                "second_operand_max": 10,
                "operands_count": 2,
                "minimum_answer": 1,
                "maximum_answer": 10,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
        },
    },

    UserGenerationSettings.DifficultyProfile.HARD: {
        "general": {
            "avoid_recent_duplicates": True,
            "recent_questions_limit": 150,
            "auto_increase_difficulty": True,
            "correct_answers_per_level": 30,
            "maximum_difficulty_level": 15,
        },
        "operations": {
            OperationGenerationSettings.Operation.ADD: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 10,
                "first_operand_max": 500,
                "second_operand_min": 10,
                "second_operand_max": 500,
                "operands_count": 3,
                "minimum_answer": None,
                "maximum_answer": None,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.SUB: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 100,
                "first_operand_max": 1000,
                "second_operand_min": 10,
                "second_operand_max": 300,
                "operands_count": 3,
                "minimum_answer": None,
                "maximum_answer": None,
                "allow_negative_result": True,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.MUL: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 2,
                "first_operand_max": 20,
                "second_operand_min": 2,
                "second_operand_max": 20,
                "operands_count": 3,
                "minimum_answer": None,
                "maximum_answer": None,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
            OperationGenerationSettings.Operation.DIV: {
                "is_enabled": True,
                "mixed_mode_weight": 25,
                "first_operand_min": 2,
                "first_operand_max": 50,
                "second_operand_min": 2,
                "second_operand_max": 20,
                "operands_count": 2,
                "minimum_answer": 2,
                "maximum_answer": 50,
                "allow_negative_result": False,
                "allow_remainder": False,
            },
        },
    },
}

QUESTION_OPERATION_MAP = {
    OperationGenerationSettings.Operation.ADD: (
        GameQuestion.Operation.ADD
    ),
    OperationGenerationSettings.Operation.SUB: (
        GameQuestion.Operation.SUB
    ),
    OperationGenerationSettings.Operation.MUL: (
        GameQuestion.Operation.MUL
    ),
    OperationGenerationSettings.Operation.DIV: (
        GameQuestion.Operation.DIV
    ),
}


@transaction.atomic
def create_default_generation_settings(*, user):
    generation_settings, created = (
        UserGenerationSettings.objects.get_or_create(
            user=user,
        )
    )

    for operation, defaults in (
        DEFAULT_OPERATION_SETTINGS.items()
    ):
        (
            OperationGenerationSettings.objects
            .get_or_create(
                generation_settings=(
                    generation_settings
                ),
                operation=operation,
                defaults=defaults,
            )
        )

    if created:
        apply_difficulty_profile(
            generation_settings=(
                generation_settings
            ),
            profile=(
                UserGenerationSettings
                .DifficultyProfile.MEDIUM
            ),
        )

    return generation_settings


@dataclass(frozen=True)
class OperationDifficultyProgress:
    operation: str
    title: str
    level: int
    correct_answers: int
    answers_on_current_level: int
    answers_to_next_level: int
    progress_percent: float
    maximum_level_reached: bool


def get_operation_correct_answers(
    *,
    user,
    operation: str,
) -> int:
    """
    Возвращает количество правильных ответов
    пользователя для выбранного действия.

    Повторения ошибок также учитываются, поскольку
    являются полноценными решёнными примерами.
    """
    question_operation = (
        QUESTION_OPERATION_MAP.get(operation)
    )

    if question_operation is None:
        return 0

    return (
        GameQuestion.objects
        .filter(
            session__user=user,
            operation=question_operation,
            answered_at__isnull=False,
            is_correct=True,
        )
        .count()
    )

def calculate_operation_difficulty_level(
    *,
    generation_settings:
        UserGenerationSettings,
    operation: str,
) -> int:
    """
    Рассчитывает уровень сложности конкретного
    математического действия.
    """
    if not generation_settings.auto_increase_difficulty:
        return 1

    correct_answers = (
        get_operation_correct_answers(
            user=generation_settings.user,
            operation=operation,
        )
    )

    answers_per_level = max(
        1,
        generation_settings.correct_answers_per_level,
    )

    calculated_level = (
        correct_answers
        // answers_per_level
        + 1
    )

    return min(
        calculated_level,
        generation_settings.maximum_difficulty_level,
    )

def get_operation_difficulty_progress(
    *,
    generation_settings:
        UserGenerationSettings,
    operation_settings:
        OperationGenerationSettings,
) -> OperationDifficultyProgress:
    correct_answers = (
        get_operation_correct_answers(
            user=generation_settings.user,
            operation=operation_settings.operation,
        )
    )

    level = calculate_operation_difficulty_level(
        generation_settings=generation_settings,
        operation=operation_settings.operation,
    )

    answers_per_level = max(
        1,
        generation_settings.correct_answers_per_level,
    )

    maximum_level_reached = (
        level
        >= generation_settings.maximum_difficulty_level
    )

    if (
        not generation_settings.auto_increase_difficulty
        or maximum_level_reached
    ):
        answers_on_current_level = 0
        answers_to_next_level = 0
        progress_percent = (
            100.0
            if maximum_level_reached
            else 0.0
        )
    else:
        answers_on_current_level = (
            correct_answers
            % answers_per_level
        )

        answers_to_next_level = (
            answers_per_level
            - answers_on_current_level
        )

        progress_percent = round(
            answers_on_current_level
            * 100
            / answers_per_level,
            1,
        )

    return OperationDifficultyProgress(
        operation=operation_settings.operation,
        title=(
            operation_settings
            .get_operation_display()
        ),
        level=level,
        correct_answers=correct_answers,
        answers_on_current_level=(
            answers_on_current_level
        ),
        answers_to_next_level=(
            answers_to_next_level
        ),
        progress_percent=progress_percent,
        maximum_level_reached=(
            maximum_level_reached
        ),
    )

def get_all_operation_difficulty_progress(
    *,
    generation_settings:
        UserGenerationSettings,
):
    operation_order = {
        OperationGenerationSettings.Operation.ADD: 1,
        OperationGenerationSettings.Operation.SUB: 2,
        OperationGenerationSettings.Operation.MUL: 3,
        OperationGenerationSettings.Operation.DIV: 4,
    }

    correct_answers_by_operation = (
        get_correct_answers_by_operation(
            user=generation_settings.user,
        )
    )

    operation_settings = sorted(
        generation_settings.operations.all(),
        key=lambda item: operation_order.get(
            item.operation,
            99,
        ),
    )

    result = []

    for item in operation_settings:
        question_operation = (
            QUESTION_OPERATION_MAP.get(
                item.operation
            )
        )

        correct_answers = (
            correct_answers_by_operation.get(
                question_operation,
                0,
            )
        )

        result.append(
            build_operation_difficulty_progress(
                generation_settings=(
                    generation_settings
                ),
                operation_settings=item,
                correct_answers=correct_answers,
            )
        )

    return result

def get_correct_answers_by_operation(
    *,
    user,
) -> dict[str, int]:
    rows = (
        GameQuestion.objects
        .filter(
            session__user=user,
            answered_at__isnull=False,
            is_correct=True,
        )
        .values("operation")
        .annotate(
            correct_count=Count("id")
        )
    )

    return {
        row["operation"]: row["correct_count"]
        for row in rows
    }

def build_operation_difficulty_progress(
    *,
    generation_settings:
        UserGenerationSettings,
    operation_settings:
        OperationGenerationSettings,
    correct_answers: int,
) -> OperationDifficultyProgress:
    if generation_settings.auto_increase_difficulty:
        answers_per_level = max(
            1,
            generation_settings
            .correct_answers_per_level,
        )

        level = min(
            (
                correct_answers
                // answers_per_level
                + 1
            ),
            generation_settings
            .maximum_difficulty_level,
        )
    else:
        answers_per_level = max(
            1,
            generation_settings
            .correct_answers_per_level,
        )

        level = 1

    maximum_level_reached = (
        level
        >= generation_settings
        .maximum_difficulty_level
    )

    if (
        not generation_settings
        .auto_increase_difficulty
    ):
        answers_on_current_level = 0
        answers_to_next_level = 0
        progress_percent = 0.0

    elif maximum_level_reached:
        answers_on_current_level = (
            answers_per_level
        )

        answers_to_next_level = 0
        progress_percent = 100.0

    else:
        answers_on_current_level = (
            correct_answers
            % answers_per_level
        )

        answers_to_next_level = (
            answers_per_level
            - answers_on_current_level
        )

        progress_percent = round(
            answers_on_current_level
            * 100
            / answers_per_level,
            1,
        )

    return OperationDifficultyProgress(
        operation=operation_settings.operation,
        title=(
            operation_settings
            .get_operation_display()
        ),
        level=level,
        correct_answers=correct_answers,
        answers_on_current_level=(
            answers_on_current_level
        ),
        answers_to_next_level=(
            answers_to_next_level
        ),
        progress_percent=progress_percent,
        maximum_level_reached=(
            maximum_level_reached
        ),
    )

@transaction.atomic
def apply_difficulty_profile(
    *,
    generation_settings,
    profile,
):
    """
    Применяет готовый профиль к настройкам пользователя.

    CUSTOM не изменяет существующие параметры.
    """
    if (
        profile
        == UserGenerationSettings
        .DifficultyProfile.CUSTOM
    ):
        generation_settings.difficulty_profile = (
            UserGenerationSettings
            .DifficultyProfile.CUSTOM
        )

        generation_settings.save(
            update_fields=[
                "difficulty_profile",
                "updated_at",
            ]
        )

        return generation_settings

    profile_data = DIFFICULTY_PROFILES.get(
        profile
    )

    if profile_data is None:
        raise ValueError(
            "Неизвестный профиль сложности."
        )

    general = profile_data["general"]

    generation_settings.difficulty_profile = profile

    for field_name, value in general.items():
        setattr(
            generation_settings,
            field_name,
            value,
        )

    generation_settings.save(
        update_fields=[
            "difficulty_profile",
            *general.keys(),
            "updated_at",
        ]
    )

    operations = profile_data["operations"]

    for operation, values in operations.items():
        operation_settings, _ = (
            OperationGenerationSettings.objects
            .get_or_create(
                generation_settings=(
                    generation_settings
                ),
                operation=operation,
            )
        )

        for field_name, value in values.items():
            setattr(
                operation_settings,
                field_name,
                value,
            )

        operation_settings.full_clean()
        operation_settings.save()

    return generation_settings