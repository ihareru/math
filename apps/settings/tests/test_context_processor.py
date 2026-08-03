from django.test import RequestFactory, TestCase

from apps.accounts.models import User
from apps.settings.context_processors import (
    user_game_settings,
)
from apps.settings.models import UserSettings


class UserSettingsContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

    def test_anonymous_user_receives_defaults(self):
        request = self.factory.get("/")

        from django.contrib.auth.models import AnonymousUser

        request.user = AnonymousUser()

        context = user_game_settings(request)

        game_settings = context["game_settings"]

        self.assertEqual(
            game_settings["background_color"],
            "#87CEEB",
        )

        self.assertFalse(
            game_settings["background_music"]
        )

    def test_authenticated_user_receives_settings(self):
        settings_object = UserSettings.objects.get(
            user=self.user,
        )

        settings_object.background_color = "#123456"
        settings_object.background_music = True
        settings_object.background_volume = 25

        settings_object.save()

        request = self.factory.get("/")
        request.user = self.user

        context = user_game_settings(request)

        game_settings = context["game_settings"]

        self.assertEqual(
            game_settings["background_color"],
            "#123456",
        )

        self.assertTrue(
            game_settings["background_music"]
        )

        self.assertEqual(
            game_settings["background_volume"],
            25,
        )