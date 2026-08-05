from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.cheats.services.activation import (
    activate_cheat_code,
)
from apps.accounts.models import User
from apps.cheats.models import (
    CheatCode,
    CheatReward,
    RewardType,
)


class CheatAdminViewTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword2026!"

        self.user = User.objects.create_user(
            email="user@example.com",
            password=self.password,
            display_name="Обычный пользователь",
            email_verified=True,
            is_active=True,
        )

        self.staff_user = User.objects.create_user(
            email="admin@example.com",
            password=self.password,
            display_name="Администратор",
            email_verified=True,
            is_active=True,
            is_staff=True,
        )

    def test_anonymous_user_cannot_open_admin_dashboard(
        self,
    ):
        response = self.client.get(
            reverse("cheats:admin_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_regular_user_cannot_open_admin_dashboard(
        self,
    ):
        self.client.force_login(
            self.user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

        response = self.client.get(
            reverse("cheats:admin_dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_staff_user_can_open_admin_dashboard(
        self,
    ):
        self.client.force_login(
            self.staff_user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

        response = self.client.get(
            reverse("cheats:admin_dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Управление чит-кодами",
        )

    def test_staff_user_can_create_cheat_code(
            self,
    ):
        self.client.force_login(
            self.staff_user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

        valid_from = (
            timezone.localtime()
            .strftime("%Y-%m-%dT%H:%M")
        )

        response = self.client.post(
            reverse("cheats:admin_code_create"),
            {
                "name": "Восемь ответов",
                "code": "eight",
                "description": "Тестовый код",
                "is_active": "on",
                "valid_from": valid_from,
                "valid_until": "",
                "duration_days": "30",
                "max_global_activations": "",
                "max_user_activations": "1",

                "rewards-TOTAL_FORMS": "1",
                "rewards-INITIAL_FORMS": "0",
                "rewards-MIN_NUM_FORMS": "1",
                "rewards-MAX_NUM_FORMS": "1000",

                "rewards-0-reward_type": (
                    RewardType.STREAK_TO_STAR
                ),
                "rewards-0-reward_data": (
                    '{"answers": 8}'
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse("cheats:admin_code_list"),
        )

        cheat = CheatCode.objects.get(
            code="EIGHT",
        )

        reward = CheatReward.objects.get(
            cheat=cheat,
        )

        self.assertEqual(
            reward.reward_data,
            {
                "answers": 8,
            },
        )

    def test_staff_user_can_disable_activation(self):
        cheat = CheatCode.objects.create(
            name="Тестовый код",
            code="TEST",
            duration_days=30,
        )

        CheatReward.objects.create(
            cheat=cheat,
            reward_type=(
                RewardType.STREAK_TO_STAR
            ),
            reward_data={
                "answers": 8,
            },
        )

        activation = activate_cheat_code(
            user=self.user,
            raw_code=cheat.code,
        ).activation

        self.client.force_login(
            self.staff_user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

        response = self.client.post(
            reverse(
                "cheats:admin_activation_disable",
                kwargs={
                    "activation_id": activation.pk,
                },
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "cheats:admin_activation_list"
            ),
        )

        activation.refresh_from_db()

        self.assertFalse(
            activation.is_active
        )