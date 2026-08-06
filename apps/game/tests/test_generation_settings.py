from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import User
from apps.game.models import (
    OperationGenerationSettings,
    UserGenerationSettings,
)


class GenerationSettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="generator@example.com",
            password="StrongPassword2026!",
            display_name="Генератор",
            email_verified=True,
            is_active=True,
        )

    def test_settings_are_created_for_new_user(self):
        self.assertTrue(
            UserGenerationSettings.objects.filter(
                user=self.user,
            ).exists()
        )

        settings_object = (
            self.user.generation_settings
        )

        self.assertEqual(
            settings_object.operations.count(),
            4,
        )

    def test_default_multiplication_range(self):
        operation = (
            self.user.generation_settings
            .operations
            .get(
                operation=(
                    OperationGenerationSettings
                    .Operation
                    .MUL
                )
            )
        )

        self.assertEqual(
            operation.first_operand_min,
            1,
        )

        self.assertEqual(
            operation.first_operand_max,
            10,
        )

        self.assertEqual(
            operation.second_operand_max,
            10,
        )

    def test_invalid_operand_range_is_rejected(self):
        operation = (
            self.user.generation_settings
            .operations
            .get(
                operation=(
                    OperationGenerationSettings
                    .Operation
                    .ADD
                )
            )
        )

        operation.first_operand_min = 100
        operation.first_operand_max = 10

        with self.assertRaises(ValidationError):
            operation.full_clean()

    def test_negative_result_only_for_subtraction(self):
        operation = (
            self.user.generation_settings
            .operations
            .get(
                operation=(
                    OperationGenerationSettings
                    .Operation
                    .ADD
                )
            )
        )

        operation.allow_negative_result = True

        with self.assertRaises(ValidationError):
            operation.full_clean()

    def test_remainder_only_for_division(self):
        operation = (
            self.user.generation_settings
            .operations
            .get(
                operation=(
                    OperationGenerationSettings
                    .Operation
                    .MUL
                )
            )
        )

        operation.allow_remainder = True

        with self.assertRaises(ValidationError):
            operation.full_clean()

    def test_automatic_difficulty_level(self):
        settings_object = (
            self.user.generation_settings
        )

        settings_object.auto_increase_difficulty = True
        settings_object.correct_answers_per_level = 50
        settings_object.maximum_difficulty_level = 10
        settings_object.save()

        statistics = self.user.game_statistics
        statistics.total_correct = 125
        statistics.save()

        self.assertEqual(
            settings_object.current_difficulty_level,
            3,
        )