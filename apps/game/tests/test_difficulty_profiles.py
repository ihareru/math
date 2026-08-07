from django.test import TestCase

from apps.accounts.models import User
from apps.game.models import (
    OperationGenerationSettings,
    UserGenerationSettings,
)
from apps.game.services.generation_settings import (
    apply_difficulty_profile,
)


class DifficultyProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profiles@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.settings_object = (
            self.user.generation_settings
        )

    def test_new_user_has_medium_profile(self):
        self.assertEqual(
            self.settings_object
            .difficulty_profile,
            UserGenerationSettings
            .DifficultyProfile.MEDIUM,
        )

    def test_easy_profile_changes_addition_range(
        self,
    ):
        apply_difficulty_profile(
            generation_settings=(
                self.settings_object
            ),
            profile=(
                UserGenerationSettings
                .DifficultyProfile.EASY
            ),
        )

        addition = (
            self.settings_object
            .operations
            .get(
                operation=(
                    OperationGenerationSettings
                    .Operation.ADD
                )
            )
        )

        self.settings_object.refresh_from_db()

        self.assertEqual(
            self.settings_object
            .difficulty_profile,
            UserGenerationSettings
            .DifficultyProfile.EASY,
        )

        self.assertEqual(
            addition.first_operand_max,
            20,
        )

        self.assertEqual(
            addition.operands_count,
            2,
        )

    def test_hard_profile_has_three_operands(
        self,
    ):
        apply_difficulty_profile(
            generation_settings=(
                self.settings_object
            ),
            profile=(
                UserGenerationSettings
                .DifficultyProfile.HARD
            ),
        )

        multiplication = (
            self.settings_object
            .operations
            .get(
                operation=(
                    OperationGenerationSettings
                    .Operation.MUL
                )
            )
        )

        self.assertEqual(
            multiplication.operands_count,
            3,
        )

        self.assertEqual(
            multiplication.first_operand_max,
            20,
        )

    def test_custom_profile_does_not_change_values(
        self,
    ):
        addition = (
            self.settings_object
            .operations
            .get(
                operation=(
                    OperationGenerationSettings
                    .Operation.ADD
                )
            )
        )

        addition.first_operand_max = 777
        addition.save()

        apply_difficulty_profile(
            generation_settings=(
                self.settings_object
            ),
            profile=(
                UserGenerationSettings
                .DifficultyProfile.CUSTOM
            ),
        )

        addition.refresh_from_db()

        self.assertEqual(
            addition.first_operand_max,
            777,
        )

        self.settings_object.refresh_from_db()

        self.assertEqual(
            self.settings_object
            .difficulty_profile,
            UserGenerationSettings
            .DifficultyProfile.CUSTOM,
        )