from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.game.models import (
    GameQuestion,
    GameSession,
    OperationGenerationSettings,
)
from apps.game.services.generation_settings import (
    calculate_operation_difficulty_level,
    get_all_operation_difficulty_progress,
)
from apps.game.services.generator import (
    generate_question,
)


class OperationDifficultyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="difficulty@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.settings_object = (
            self.user.generation_settings
        )

        self.settings_object.auto_increase_difficulty = True
        self.settings_object.correct_answers_per_level = 10
        self.settings_object.maximum_difficulty_level = 5

        self.settings_object.save()

    def create_correct_questions(
        self,
        *,
        operation,
        count,
    ):
        game_session = GameSession.objects.create(
            user=self.user,
            mode=GameSession.Mode.ALL,
        )

        questions = []

        for index in range(count):
            questions.append(
                GameQuestion(
                    session=game_session,
                    sequence_number=index + 1,
                    operation=operation,
                    num1=1,
                    num2=1,
                    operands=[
                        1,
                        1,
                    ],
                    correct_answer=2,
                    user_answer=2,
                    is_correct=True,
                    shown_at=timezone.now(),
                    answered_at=timezone.now(),
                    response_time_ms=1000,
                )
            )

        GameQuestion.objects.bulk_create(
            questions
        )

    def test_addition_level_does_not_change_multiplication(
        self,
    ):
        self.create_correct_questions(
            operation=GameQuestion.Operation.ADD,
            count=25,
        )

        addition_level = (
            calculate_operation_difficulty_level(
                generation_settings=(
                    self.settings_object
                ),
                operation=(
                    OperationGenerationSettings
                    .Operation.ADD
                ),
            )
        )

        multiplication_level = (
            calculate_operation_difficulty_level(
                generation_settings=(
                    self.settings_object
                ),
                operation=(
                    OperationGenerationSettings
                    .Operation.MUL
                ),
            )
        )

        self.assertEqual(
            addition_level,
            3,
        )

        self.assertEqual(
            multiplication_level,
            1,
        )

    def test_level_is_limited_by_maximum(self):
        self.create_correct_questions(
            operation=GameQuestion.Operation.DIV,
            count=100,
        )

        level = (
            calculate_operation_difficulty_level(
                generation_settings=(
                    self.settings_object
                ),
                operation=(
                    OperationGenerationSettings
                    .Operation.DIV
                ),
            )
        )

        self.assertEqual(
            level,
            5,
        )

    def test_progress_to_next_level(self):
        self.create_correct_questions(
            operation=GameQuestion.Operation.SUB,
            count=14,
        )

        progress_items = (
            get_all_operation_difficulty_progress(
                generation_settings=(
                    self.settings_object
                ),
            )
        )

        subtraction = next(
            item
            for item in progress_items
            if item.operation
            == OperationGenerationSettings
            .Operation.SUB
        )

        self.assertEqual(
            subtraction.level,
            2,
        )

        self.assertEqual(
            subtraction.answers_on_current_level,
            4,
        )

        self.assertEqual(
            subtraction.answers_to_next_level,
            6,
        )

        self.assertEqual(
            subtraction.progress_percent,
            40.0,
        )

    def test_disabled_auto_difficulty_returns_level_one(
        self,
    ):
        self.settings_object.auto_increase_difficulty = False
        self.settings_object.save()

        self.create_correct_questions(
            operation=GameQuestion.Operation.ADD,
            count=100,
        )

        level = (
            calculate_operation_difficulty_level(
                generation_settings=(
                    self.settings_object
                ),
                operation=(
                    OperationGenerationSettings
                    .Operation.ADD
                ),
            )
        )

        self.assertEqual(
            level,
            1,
        )

def test_generator_uses_operation_specific_level(
    self,
):
    self.create_correct_questions(
        operation=GameQuestion.Operation.ADD,
        count=20,
    )

    addition_settings = (
        self.settings_object
        .operations
        .get(
            operation=(
                OperationGenerationSettings
                .Operation.ADD
            )
        )
    )

    addition_settings.first_operand_min = 1
    addition_settings.first_operand_max = 10
    addition_settings.second_operand_min = 1
    addition_settings.second_operand_max = 10
    addition_settings.minimum_answer = None
    addition_settings.maximum_answer = None

    addition_settings.save()

    game_session = GameSession.objects.create(
        user=self.user,
        mode=GameSession.Mode.ADD,
    )

    with patch(
        "apps.game.services.generator.random.randint",
        side_effect=lambda minimum, maximum: maximum,
    ):
        question = generate_question(
            game_session=game_session,
        )

    # Уровень 3:
    # исходный диапазон 1–10;
    # ширина 9;
    # прибавляется по 1 за уровень;
    # максимум становится 12.
    self.assertEqual(
        question.num1,
        12,
    )

    self.assertEqual(
        question.num2,
        12,
    )