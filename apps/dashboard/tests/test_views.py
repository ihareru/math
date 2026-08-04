from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class DashboardViewTests(TestCase):
    def create_user(
        self,
        *,
        email="user@example.com",
        display_name="Игрок",
        stars=5,
        show_in_rating=True,
    ):
        user = User.objects.create_user(
            email=email,
            password="StrongPassword2026!",
            display_name=display_name,
            email_verified=True,
            is_active=True,
            show_in_rating=show_in_rating,
        )

        user.game_statistics.stars = stars
        user.game_statistics.save()

        return user

    def test_dashboard_is_public(self):
        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Общий рейтинг",
        )

    def test_rating_displays_public_user(self):
        self.create_user(
            display_name="Публичный игрок",
            stars=10,
        )

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertContains(
            response,
            "Публичный игрок",
        )

        self.assertContains(
            response,
            "10",
        )

    def test_rating_does_not_display_email(self):
        user = self.create_user(
            email="private@example.com",
            display_name="Публичное имя",
        )

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertContains(
            response,
            user.display_name,
        )

        self.assertNotContains(
            response,
            user.email,
        )

    def test_hidden_user_is_not_displayed(self):
        self.create_user(
            display_name="Скрытый игрок",
            stars=100,
            show_in_rating=False,
        )

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertNotContains(
            response,
            "Скрытый игрок",
        )

    def test_authenticated_user_sees_own_position(self):
        user = self.create_user(
            display_name="Текущий игрок",
            stars=15,
        )

        self.client.force_login(
            user,
            backend=(
                "apps.accounts.backends.EmailBackend"
            ),
        )

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertContains(
            response,
            "Ваше место",
        )

        self.assertContains(
            response,
            "Это вы",
        )

    def test_pagination_uses_twenty_five_rows(self):
        for index in range(30):
            self.create_user(
                email=f"user{index}@example.com",
                display_name=f"Игрок {index}",
                stars=30 - index,
            )

        response = self.client.get(
            reverse("dashboard:home")
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            25,
        )

        self.assertTrue(
            response.context["page_obj"].has_next()
        )