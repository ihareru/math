from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.settings.models import UserSettings


class UserSettingsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword2026!",
            display_name="Игрок",
            email_verified=True,
            is_active=True,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("user_settings:detail")
        )

        expected_url = (
            reverse("accounts:login")
            + "?next="
            + reverse("user_settings:detail")
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_user_can_open_settings_page(self):
        self.client.force_login(
            self.user,
            backend="apps.accounts.backends.EmailBackend",
        )

        response = self.client.get(
            reverse("user_settings:detail")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Настройки пользователя",
        )

    def test_user_can_update_own_settings(self):
        self.client.force_login(
            self.user,
            backend="apps.accounts.backends.EmailBackend",
        )

        response = self.client.post(
            reverse("user_settings:detail"),
            {
                "background_color": "#123456",
                "background_image": "",
                "background_music": "",
                "success_sound": "on",
                "fail_sound": "",
                "background_volume": "25",
                "success_volume": "70",
                "fail_volume": "10",
            },
        )

        self.assertRedirects(
            response,
            reverse("user_settings:detail"),
        )

        settings_object = UserSettings.objects.get(
            user=self.user,
        )

        self.assertEqual(
            settings_object.background_color,
            "#123456",
        )

        self.assertFalse(
            settings_object.background_music
        )

        self.assertTrue(
            settings_object.success_sound
        )

        self.assertFalse(
            settings_object.fail_sound
        )

        self.assertEqual(
            settings_object.background_volume,
            25,
        )

        self.assertEqual(
            settings_object.success_volume,
            70,
        )

        self.assertEqual(
            settings_object.fail_volume,
            10,
        )

    def test_saved_settings_are_available_in_template_context(
            self,
    ):
        settings_object = UserSettings.objects.get(
            user=self.user,
        )

        settings_object.background_color = "#654321"
        settings_object.background_music = True
        settings_object.background_volume = 35

        settings_object.save()

        self.client.force_login(
            self.user,
            backend="apps.accounts.backends.EmailBackend",
        )

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertEqual(
            response.context["game_settings"][
                "background_color"
            ],
            "#654321",
        )

        self.assertTrue(
            response.context["game_settings"][
                "background_music"
            ]
        )

        self.assertEqual(
            response.context["game_settings"][
                "background_volume"
            ],
            35,
        )