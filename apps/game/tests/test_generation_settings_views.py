from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.game.models import (
    OperationGenerationSettings,
)


OPERATION_ORDER = [
    OperationGenerationSettings.Operation.ADD,
    OperationGenerationSettings.Operation.SUB,
    OperationGenerationSettings.Operation.MUL,
    OperationGenerationSettings.Operation.DIV,
]


class GenerationSettingsViewTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword2026!"

        self.user = User.objects.create_user(
            email="settings@example.com",
            password=self.password,
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.client.force_login(
            self.user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

    def test_page_requires_authentication(self):
        self.client.logout()

        response = self.client.get(
            reverse(
                "game:generation_settings"
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_can_open_settings_page(self):
        response = self.client.get(
            reverse(
                "game:generation_settings"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Настройки примеров",
        )

        self.assertEqual(
            len(
                response.context[
                    "operation_formset"
                ].forms
            ),
            4,
        )

    def build_post_data(self):
        settings_object = (
            self.user.generation_settings
        )

        operations_by_code = {
            operation.operation: operation
            for operation
            in settings_object.operations.all()
        }

        operations = [
            operations_by_code[operation_code]
            for operation_code in OPERATION_ORDER
        ]

        data = {
            "avoid_recent_duplicates": "on",
            "recent_questions_limit": "75",
            "auto_increase_difficulty": "on",
            "correct_answers_per_level": "25",
            "maximum_difficulty_level": "8",

            "operations-TOTAL_FORMS": "4",
            "operations-INITIAL_FORMS": "4",
            "operations-MIN_NUM_FORMS": "4",
            "operations-MAX_NUM_FORMS": "4",
        }

        for index, operation in enumerate(
            operations
        ):
            prefix = f"operations-{index}"

            data[f"{prefix}-id"] = str(
                operation.pk
            )

            data[
                f"{prefix}-is_enabled"
            ] = "on"

            data[
                f"{prefix}-mixed_mode_weight"
            ] = "25"

            data[
                f"{prefix}-first_operand_min"
            ] = str(
                operation.first_operand_min
            )

            data[
                f"{prefix}-first_operand_max"
            ] = str(
                operation.first_operand_max
            )

            data[
                f"{prefix}-second_operand_min"
            ] = str(
                operation.second_operand_min
            )

            data[
                f"{prefix}-second_operand_max"
            ] = str(
                operation.second_operand_max
            )

            data[
                f"{prefix}-minimum_answer"
            ] = (
                ""
                if operation.minimum_answer
                is None
                else str(
                    operation.minimum_answer
                )
            )

            data[
                f"{prefix}-maximum_answer"
            ] = (
                ""
                if operation.maximum_answer
                is None
                else str(
                    operation.maximum_answer
                )
            )

            if (
                operation.operation
                == OperationGenerationSettings
                .Operation.SUB
            ):
                data[
                    f"{prefix}-allow_negative_result"
                ] = ""

        return data

    def test_user_can_save_general_settings(
        self,
    ):
        data = self.build_post_data()

        response = self.client.post(
            reverse(
                "game:generation_settings"
            ),
            data,
        )

        self.assertRedirects(
            response,
            reverse(
                "game:generation_settings"
            ),
        )

        settings_object = (
            self.user.generation_settings
        )

        settings_object.refresh_from_db()

        self.assertEqual(
            settings_object
            .recent_questions_limit,
            75,
        )

        self.assertTrue(
            settings_object
            .auto_increase_difficulty
        )

        self.assertEqual(
            settings_object
            .correct_answers_per_level,
            25,
        )

        self.assertEqual(
            settings_object
            .maximum_difficulty_level,
            8,
        )

    def test_cannot_disable_all_operations(
            self,
    ):
        data = self.build_post_data()

        for index in range(4):
            data.pop(
                f"operations-{index}-is_enabled",
                None,
            )

        response = self.client.post(
            reverse(
                "game:generation_settings"
            ),
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        formset = response.context[
            "operation_formset"
        ]

        self.assertIn(
            (
                "Необходимо включить хотя бы одно "
                "математическое действие."
            ),
            formset.non_form_errors(),
        )

        enabled_count = (
            self.user.generation_settings
            .operations
            .filter(is_enabled=True)
            .count()
        )

        self.assertEqual(
            enabled_count,
            4,
        )

    def test_division_rejects_zero_divisor_range(
            self,
    ):
        data = self.build_post_data()

        division_index = 3

        data[
            (
                f"operations-{division_index}-"
                "second_operand_min"
            )
        ] = "0"

        response = self.client.post(
            reverse(
                "game:generation_settings"
            ),
            data,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        division_form = response.context[
            "operation_formset"
        ].forms[division_index]

        self.assertIn(
            "second_operand_min",
            division_form.errors,
        )

