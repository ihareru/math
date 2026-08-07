from django.test import TestCase

from apps.accounts.models import User
from apps.settings.models import UserSettings


class UserSettingsSignalTests(TestCase):
    def test_settings_created_for_new_user(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

        self.assertTrue(
            UserSettings.objects.filter(
                user=user,
            ).exists()
        )

    def test_only_one_settings_object_is_created(self):
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
            UserSettings.objects.filter(
                user=user,
            ).count(),
            1,
        )