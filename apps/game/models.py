from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class UserGameStatistics(models.Model):
    """
    Общая накопительная статистика пользователя.

    Здесь хранятся итоговые показатели за всё время.
    Подробная история находится в GameSession
    и GameQuestion.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_statistics",
        verbose_name="Пользователь",
    )

    stars = models.PositiveIntegerField(
        "Всего звёзд",
        default=0,
    )

    total_correct = models.PositiveBigIntegerField(
        "Всего правильных ответов",
        default=0,
    )

    total_wrong = models.PositiveBigIntegerField(
        "Всего неправильных ответов",
        default=0,
    )

    best_streak = models.PositiveIntegerField(
        "Лучшая серия",
        default=0,
    )

    total_sessions = models.PositiveIntegerField(
        "Количество игровых сессий",
        default=0,
    )

    total_answer_time_ms = models.PositiveBigIntegerField(
        "Общее время ответов, мс",
        default=0,
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Дата обновления",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Игровая статистика пользователя"
        verbose_name_plural = "Игровая статистика пользователей"

    def __str__(self):
        return (
            f"{self.user.display_name}: "
            f"{self.stars} зв."
        )

    @property
    def total_answers(self):
        return self.total_correct + self.total_wrong

    @property
    def accuracy_percent(self):
        total = self.total_answers

        if total == 0:
            return 0

        return round(
            self.total_correct * 100 / total,
            1,
        )

    @property
    def average_answer_time_seconds(self):
        total = self.total_answers

        if total == 0:
            return 0

        return round(
            self.total_answer_time_ms / total / 1000,
            2,
        )


class GameSession(models.Model):
    """
    Одна игровая сессия пользователя.

    Сессия начинается при выборе режима игры
    и завершается при выходе из игры либо явном
    нажатии кнопки завершения.
    """

    class Mode(models.TextChoices):
        ADD = "add", "Сложение"
        SUB = "sub", "Вычитание"
        MUL = "mul", "Умножение"
        DIV = "div", "Деление"
        ALL = "all", "Все действия"
        REVIEW = "review", "Повтор ошибок"

    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        COMPLETED = "completed", "Завершена"
        ABANDONED = "abandoned", "Прервана"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_sessions",
        verbose_name="Пользователь",
    )

    mode = models.CharField(
        "Режим",
        max_length=10,
        choices=Mode.choices,
    )

    status = models.CharField(
        "Статус",
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    correct_count = models.PositiveIntegerField(
        "Правильных ответов",
        default=0,
    )

    wrong_count = models.PositiveIntegerField(
        "Неправильных ответов",
        default=0,
    )

    current_streak = models.PositiveIntegerField(
        "Текущая серия",
        default=0,
    )

    best_streak = models.PositiveIntegerField(
        "Лучшая серия сессии",
        default=0,
    )

    stars_earned = models.PositiveIntegerField(
        "Заработано звёзд",
        default=0,
    )

    started_at = models.DateTimeField(
        "Начало",
        auto_now_add=True,
    )

    last_activity_at = models.DateTimeField(
        "Последняя активность",
        default=timezone.now,
    )

    finished_at = models.DateTimeField(
        "Завершение",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Игровая сессия"
        verbose_name_plural = "Игровые сессии"
        ordering = [
            "-started_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "user",
                    "status",
                ],
                name="game_session_user_status_idx",
            ),
            models.Index(
                fields=[
                    "user",
                    "started_at",
                ],
                name="game_session_user_started_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.display_name} — "
            f"{self.get_mode_display()} — "
            f"{self.started_at:%d.%m.%Y %H:%M}"
        )

    @property
    def total_answers(self):
        return self.correct_count + self.wrong_count

    @property
    def accuracy_percent(self):
        total = self.total_answers

        if total == 0:
            return 0

        return round(
            self.correct_count * 100 / total,
            1,
        )

    def finish(self, status=None):
        if status is None:
            status = self.Status.COMPLETED

        self.status = status
        self.finished_at = timezone.now()
        self.last_activity_at = timezone.now()

        self.save(
            update_fields=[
                "status",
                "finished_at",
                "last_activity_at",
            ]
        )


class GameQuestion(models.Model):
    """
    Каждый пример, показанный пользователю.

    Запись создаётся при отображении примера.
    После отправки ответа она дополняется ответом,
    результатом и временем решения.
    """

    class Operation(models.TextChoices):
        ADD = "add", "Сложение"
        SUB = "sub", "Вычитание"
        MUL = "mul", "Умножение"
        DIV = "div", "Деление"

    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Игровая сессия",
    )

    sequence_number = models.PositiveIntegerField(
        "Номер примера в сессии",
        validators=[
            MinValueValidator(1),
        ],
    )

    operation = models.CharField(
        "Действие",
        max_length=3,
        choices=Operation.choices,
    )

    num1 = models.IntegerField(
        "Первое число",
    )

    num2 = models.IntegerField(
        "Второе число",
    )

    correct_answer = models.IntegerField(
        "Правильный ответ",
    )

    user_answer = models.IntegerField(
        "Ответ пользователя",
        null=True,
        blank=True,
    )

    is_correct = models.BooleanField(
        "Ответ правильный",
        null=True,
        blank=True,
    )

    shown_at = models.DateTimeField(
        "Время показа",
        auto_now_add=True,
    )

    answered_at = models.DateTimeField(
        "Время ответа",
        null=True,
        blank=True,
    )

    response_time_ms = models.PositiveIntegerField(
        "Время ответа, мс",
        null=True,
        blank=True,
    )

    is_review = models.BooleanField(
        "Повтор ошибки",
        default=False,
    )

    source_question = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="review_attempts",
        verbose_name="Исходный ошибочный пример",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Игровой пример"
        verbose_name_plural = "Игровые примеры"
        ordering = [
            "sequence_number",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "session",
                    "sequence_number",
                ],
                name="game_unique_question_number",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        user_answer__isnull=True,
                        is_correct__isnull=True,
                        answered_at__isnull=True,
                    )
                    |
                    Q(
                        user_answer__isnull=False,
                        is_correct__isnull=False,
                        answered_at__isnull=False,
                    )
                ),
                name="game_question_answer_state_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=[
                    "session",
                    "answered_at",
                ],
                name="game_q_sess_answer_idx",
            ),
            models.Index(
                fields=[
                    "session",
                    "is_correct",
                ],
                name="game_q_sess_result_idx",
            ),
            models.Index(
                fields=[
                    "operation",
                    "is_correct",
                ],
                name="game_q_oper_result_idx",
            ),
        ]

    def __str__(self):
        return (
            f"№{self.sequence_number}: "
            f"{self.expression}"
        )

    @property
    def operator_symbol(self):
        symbols = {
            self.Operation.ADD: "+",
            self.Operation.SUB: "−",
            self.Operation.MUL: "×",
            self.Operation.DIV: ":",
        }

        return symbols[self.operation]

    @property
    def expression(self):
        return (
            f"{self.num1} "
            f"{self.operator_symbol} "
            f"{self.num2}"
        )

    @property
    def is_answered(self):
        return self.answered_at is not None

    @property
    def response_time_seconds(self):
        if self.response_time_ms is None:
            return None

        return round(
            self.response_time_ms / 1000,
            2,
        )


class StarTransaction(models.Model):
    """
    История начисления и списания звёзд.

    Позже сюда будут записываться начисления
    за серии, достижения, бонус-коды и события.
    """

    class Reason(models.TextChoices):
        STREAK = "streak", "Серия правильных ответов"
        ACHIEVEMENT = "achievement", "Достижение"
        BONUS_CODE = "bonus_code", "Бонус-код"
        EVENT = "event", "Событие"
        ADMIN = "admin", "Изменение администратором"
        CORRECTION = "correction", "Корректировка"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="star_transactions",
        verbose_name="Пользователь",
    )

    session = models.ForeignKey(
        GameSession,
        on_delete=models.SET_NULL,
        related_name="star_transactions",
        verbose_name="Игровая сессия",
        null=True,
        blank=True,
    )

    amount = models.SmallIntegerField(
        "Количество звёзд",
    )

    reason = models.CharField(
        "Причина",
        max_length=20,
        choices=Reason.choices,
    )

    description = models.CharField(
        "Описание",
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        "Дата",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Операция со звёздами"
        verbose_name_plural = "Операции со звёздами"
        ordering = [
            "-created_at",
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(amount=0),
                name="game_star_transaction_nonzero",
            ),
        ]
        indexes = [
            models.Index(
                fields=[
                    "user",
                    "created_at",
                ],
                name="game_star_user_created_idx",
            ),
        ]

    def __str__(self):
        sign = "+" if self.amount > 0 else ""

        return (
            f"{self.user.display_name}: "
            f"{sign}{self.amount}"
        )