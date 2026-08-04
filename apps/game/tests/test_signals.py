from django.test import TestCase

from apps.accounts.models import User
from apps.game.models import UserGameStatistics


class UserGameStatisticsSignalTests(TestCase):
    def test_statistics_created_for_new_user(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.assertTrue(
            UserGameStatistics.objects.filter(
                user=user,
            ).exists()
        )

    def test_only_one_statistics_record_exists(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        user.display_name = "Новое имя"
        user.save()

        self.assertEqual(
            UserGameStatistics.objects.filter(
                user=user,
            ).count(),
            1,
        )