from django.test import TestCase

from apps.accounts.models import User
from apps.game.models import (
    GameQuestion,
    GameSession,
    OperationGenerationSettings,
)
from apps.game.services.generator import (
    build_identity_key,
    generate_question,
)


class ConfigurableQuestionGeneratorTests(
    TestCase
):
    def setUp(self):
        self.user = User.objects.create_user(
            email="generator@example.com",
            password="StrongPassword2026!",
            display_name="Генератор",
            email_verified=True,
            is_active=True,
        )

    def create_session(self, mode):
        return GameSession.objects.create(
            user=self.user,
            mode=mode,
        )

    def get_operation_settings(
        self,
        operation,
    ):
        return (
            self.user
            .generation_settings
            .operations
            .get(operation=operation)
        )

    def test_addition_uses_configured_ranges(self):
        settings_object = (
            self.get_operation_settings(
                OperationGenerationSettings
                .Operation
                .ADD
            )
        )

        settings_object.first_operand_min = 20
        settings_object.first_operand_max = 20
        settings_object.second_operand_min = 5
        settings_object.second_operand_max = 5
        settings_object.minimum_answer = 25
        settings_object.maximum_answer = 25
        settings_object.save()

        game_session = self.create_session(
            GameSession.Mode.ADD
        )

        question = generate_question(
            game_session=game_session,
        )

        self.assertEqual(question.num1, 20)
        self.assertEqual(question.num2, 5)

        self.assertEqual(
            question.correct_answer,
            25,
        )

    def test_subtraction_does_not_go_negative(
        self,
    ):
        settings_object = (
            self.get_operation_settings(
                OperationGenerationSettings
                .Operation
                .SUB
            )
        )

        settings_object.first_operand_min = 1
        settings_object.first_operand_max = 5
        settings_object.second_operand_min = 6
        settings_object.second_operand_max = 10
        settings_object.allow_negative_result = False
        settings_object.minimum_answer = 0
        settings_object.maximum_answer = 20
        settings_object.save()

        game_session = self.create_session(
            GameSession.Mode.SUB
        )

        for _ in range(50):
            question = generate_question(
                game_session=game_session,
            )

            self.assertGreaterEqual(
                question.correct_answer,
                0,
            )

    def test_subtraction_can_be_negative(self):
        settings_object = (
            self.get_operation_settings(
                OperationGenerationSettings
                .Operation
                .SUB
            )
        )

        settings_object.first_operand_min = 1
        settings_object.first_operand_max = 1
        settings_object.second_operand_min = 5
        settings_object.second_operand_max = 5
        settings_object.allow_negative_result = True
        settings_object.minimum_answer = -10
        settings_object.maximum_answer = 0
        settings_object.save()

        game_session = self.create_session(
            GameSession.Mode.SUB
        )

        question = generate_question(
            game_session=game_session,
        )

        self.assertEqual(
            question.correct_answer,
            -4,
        )

    def test_division_has_no_remainder(self):
        settings_object = (
            self.get_operation_settings(
                OperationGenerationSettings
                .Operation
                .DIV
            )
        )

        settings_object.first_operand_min = 2
        settings_object.first_operand_max = 12
        settings_object.second_operand_min = 2
        settings_object.second_operand_max = 12
        settings_object.minimum_answer = 2
        settings_object.maximum_answer = 12
        settings_object.save()

        game_session = self.create_session(
            GameSession.Mode.DIV
        )

        for _ in range(100):
            question = generate_question(
                game_session=game_session,
            )

            self.assertNotEqual(
                question.num2,
                0,
            )

            self.assertEqual(
                question.num1
                % question.num2,
                0,
            )

            self.assertEqual(
                question.correct_answer,
                question.num1
                // question.num2,
            )

    def test_commutative_examples_share_key(self):
        first_key = build_identity_key(
            operation=GameQuestion.Operation.ADD,
            num1=5,
            num2=9,
        )

        second_key = build_identity_key(
            operation=GameQuestion.Operation.ADD,
            num1=9,
            num2=5,
        )

        self.assertEqual(
            first_key,
            second_key,
        )

    def test_subtraction_keeps_operand_order(self):
        first_key = build_identity_key(
            operation=GameQuestion.Operation.SUB,
            num1=9,
            num2=5,
        )

        second_key = build_identity_key(
            operation=GameQuestion.Operation.SUB,
            num1=5,
            num2=9,
        )

        self.assertNotEqual(
            first_key,
            second_key,
        )

    def test_recent_question_is_avoided(self):
        settings_object = (
            self.get_operation_settings(
                OperationGenerationSettings
                .Operation
                .ADD
            )
        )

        settings_object.first_operand_min = 1
        settings_object.first_operand_max = 2
        settings_object.second_operand_min = 1
        settings_object.second_operand_max = 2
        settings_object.minimum_answer = 2
        settings_object.maximum_answer = 4
        settings_object.save()

        game_session = self.create_session(
            GameSession.Mode.ADD
        )

        recent_key = build_identity_key(
            operation=GameQuestion.Operation.ADD,
            num1=1,
            num2=1,
        )

        for _ in range(30):
            question = generate_question(
                game_session=game_session,
                recent_identity_keys={
                    recent_key,
                },
            )

            self.assertNotEqual(
                question.identity_key,
                recent_key,
            )

    def test_mixed_mode_respects_disabled_operation(
        self,
    ):
        operations = (
            self.user
            .generation_settings
            .operations
        )

        operations.update(
            is_enabled=False,
            mixed_mode_weight=0,
        )

        addition = operations.get(
            operation=(
                OperationGenerationSettings
                .Operation
                .ADD
            )
        )

        addition.is_enabled = True
        addition.mixed_mode_weight = 100
        addition.save()

        game_session = self.create_session(
            GameSession.Mode.ALL
        )

        for _ in range(30):
            question = generate_question(
                game_session=game_session,
            )

            self.assertEqual(
                question.operation,
                GameQuestion.Operation.ADD,
            )