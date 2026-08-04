from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.game.models import GameSession
from apps.game.services.gameplay import (
    get_or_create_current_question,
    start_game_session,
    submit_answer,
)


class GameViewTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword2026!"

        self.user = User.objects.create_user(
            email="user@example.com",
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

    def test_user_can_open_mode_selection(self):
        response = self.client.get(
            reverse("game:mode_select")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Выберите режим",
        )

    def test_start_mode_creates_session(self):
        response = self.client.post(
            reverse(
                "game:start",
                kwargs={
                    "mode": GameSession.Mode.ADD,
                },
            )
        )

        self.assertRedirects(
            response,
            reverse("game:play"),
        )

        self.assertTrue(
            GameSession.objects.filter(
                user=self.user,
                mode=GameSession.Mode.ADD,
                status=GameSession.Status.ACTIVE,
            ).exists()
        )

    def test_play_page_shows_question(self):
        start_game_session(
            user=self.user,
            mode=GameSession.Mode.ADD,
        )

        response = self.client.get(
            reverse("game:play")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Проверить",
        )

    def test_wrong_answer_result_shows_correct_answer(
        self,
    ):
        start_game_session(
            user=self.user,
            mode=GameSession.Mode.ADD,
        )

        question = get_or_create_current_question(
            user=self.user,
        )

        wrong_answer = (
            question.correct_answer + 1
        )

        response = self.client.post(
            reverse(
                "game:answer",
                kwargs={
                    "question_id": question.pk,
                },
            ),
            {
                "answer": wrong_answer,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "game:question_result",
                kwargs={
                    "question_id": question.pk,
                },
            ),
        )

        response = self.client.get(
            reverse(
                "game:question_result",
                kwargs={
                    "question_id": question.pk,
                },
            )
        )

        self.assertContains(
            response,
            "Правильный ответ",
        )

        self.assertContains(
            response,
            str(question.correct_answer),
        )

    def test_review_button_shows_unresolved_count(self):
        game_session = start_game_session(
            user=self.user,
            mode=GameSession.Mode.ADD,
        )

        question = get_or_create_current_question(
            user=self.user,
        )

        submit_answer(
            user=self.user,
            question_id=question.pk,
            user_answer=question.correct_answer + 1,
        )

        response = self.client.get(
            reverse("game:mode_select")
        )

        self.assertContains(
            response,
            "Не разобрано ошибок",
        )

        self.assertContains(
            response,
            "1",
        )

    def test_user_can_start_review_mode(self):
        game_session = start_game_session(
            user=self.user,
            mode=GameSession.Mode.ADD,
        )

        question = get_or_create_current_question(
            user=self.user,
        )

        submit_answer(
            user=self.user,
            question_id=question.pk,
            user_answer=question.correct_answer + 1,
        )

        response = self.client.post(
            reverse("game:start_review")
        )

        self.assertRedirects(
            response,
            reverse("game:play"),
        )

        self.assertTrue(
            GameSession.objects.filter(
                user=self.user,
                mode=GameSession.Mode.REVIEW,
                status=GameSession.Status.ACTIVE,
            ).exists()
        )