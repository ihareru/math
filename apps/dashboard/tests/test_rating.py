from django.test import TestCase

from apps.accounts.models import User
from apps.dashboard.services.rating import (
    build_public_rating,
    get_public_rating_summary,
)


class PublicRatingServiceTests(TestCase):
    def create_user(
        self,
        *,
        email,
        display_name,
        stars=0,
        correct=0,
        wrong=0,
        best_streak=0,
        show_in_rating=True,
        is_active=True,
        email_verified=True,
    ):
        user = User.objects.create_user(
            email=email,
            password="StrongPassword2026!",
            display_name=display_name,
            email_verified=email_verified,
            is_active=is_active,
            show_in_rating=show_in_rating,
        )

        statistics = user.game_statistics

        statistics.stars = stars
        statistics.total_correct = correct
        statistics.total_wrong = wrong
        statistics.best_streak = best_streak

        statistics.save()

        return user

    def test_users_are_sorted_by_stars(self):
        self.create_user(
            email="first@example.com",
            display_name="Первый",
            stars=10,
        )

        self.create_user(
            email="second@example.com",
            display_name="Второй",
            stars=20,
        )

        rating = build_public_rating()

        self.assertEqual(
            rating[0].display_name,
            "Второй",
        )

        self.assertEqual(
            rating[0].rank,
            1,
        )

        self.assertEqual(
            rating[1].display_name,
            "Первый",
        )

        self.assertEqual(
            rating[1].rank,
            2,
        )

    def test_equal_stars_have_equal_rank(self):
        self.create_user(
            email="one@example.com",
            display_name="Игрок 1",
            stars=10,
            correct=100,
        )

        self.create_user(
            email="two@example.com",
            display_name="Игрок 2",
            stars=10,
            correct=80,
        )

        self.create_user(
            email="three@example.com",
            display_name="Игрок 3",
            stars=5,
        )

        rating = build_public_rating()

        self.assertEqual(
            rating[0].rank,
            1,
        )

        self.assertEqual(
            rating[1].rank,
            1,
        )

        self.assertEqual(
            rating[2].rank,
            2,
        )

    def test_hidden_user_is_not_in_rating(self):
        hidden_user = self.create_user(
            email="hidden@example.com",
            display_name="Скрытый",
            stars=100,
            show_in_rating=False,
        )

        rating = build_public_rating()

        rating_user_ids = {
            row.user_id
            for row in rating
        }

        self.assertNotIn(
            hidden_user.pk,
            rating_user_ids,
        )

    def test_inactive_user_is_not_in_rating(self):
        inactive_user = self.create_user(
            email="inactive@example.com",
            display_name="Неактивный",
            stars=100,
            is_active=False,
        )

        rating = build_public_rating()

        rating_user_ids = {
            row.user_id
            for row in rating
        }

        self.assertNotIn(
            inactive_user.pk,
            rating_user_ids,
        )

    def test_unverified_user_is_not_in_rating(self):
        user = self.create_user(
            email="unverified@example.com",
            display_name="Неподтверждённый",
            stars=100,
            email_verified=False,
        )

        rating = build_public_rating()

        rating_user_ids = {
            row.user_id
            for row in rating
        }

        self.assertNotIn(
            user.pk,
            rating_user_ids,
        )

    def test_summary_counts_public_statistics(self):
        self.create_user(
            email="one@example.com",
            display_name="Первый",
            stars=5,
            correct=20,
        )

        self.create_user(
            email="two@example.com",
            display_name="Второй",
            stars=7,
            correct=30,
        )

        summary = get_public_rating_summary()

        self.assertEqual(
            summary.rating_participants,
            2,
        )

        self.assertEqual(
            summary.total_stars,
            12,
        )

        self.assertEqual(
            summary.total_correct_answers,
            50,
        )