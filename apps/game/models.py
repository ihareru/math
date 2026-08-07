from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
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

    @property
    def end_time(self):
        return (
                self.finished_at
                or self.last_activity_at
        )

    @property
    def duration_seconds(self):
        if not self.started_at:
            return 0

        duration = (
                self.end_time - self.started_at
        )

        return max(
            0,
            round(
                duration.total_seconds(),
            ),
        )

    @property
    def duration_minutes(self):
        return round(
            self.duration_seconds / 60,
            1,
        )

    @property
    def average_response_time_seconds(self):
        annotated_value = getattr(
            self,
            "average_response_time_ms",
            None,
        )

        if annotated_value is None:
            average_ms = (
                    self.questions
                    .filter(
                        answered_at__isnull=False,
                    )
                    .aggregate(
                        value=models.Avg(
                            "response_time_ms"
                        )
                    )["value"]
                    or 0
            )
        else:
            average_ms = annotated_value or 0

        return round(
            average_ms / 1000,
            2,
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

    operands = models.JSONField(
        "Операнды",
        default=list,
        blank=True,
        help_text=(
            "Упорядоченный список чисел примера. "
            "Например: [5, 7, 9]."
        ),
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

    def clean(self):
        super().clean()

        from django.core.exceptions import (
            ValidationError,
        )

        if self.operands in (None, []):
            return

        if not isinstance(self.operands, list):
            raise ValidationError(
                {
                    "operands": (
                        "Операнды должны быть "
                        "JSON-массивом."
                    ),
                }
            )

        if not 2 <= len(self.operands) <= 4:
            raise ValidationError(
                {
                    "operands": (
                        "Пример должен содержать "
                        "от двух до четырёх операндов."
                    ),
                }
            )

        for operand in self.operands:
            if (
                isinstance(operand, bool)
                or not isinstance(operand, int)
            ):
                raise ValidationError(
                    {
                        "operands": (
                            "Все операнды должны быть "
                            "целыми числами."
                        ),
                    }
                )

        if self.operation == self.Operation.DIV:
            for divisor in self.operands[1:]:
                if divisor == 0:
                    raise ValidationError(
                        {
                            "operands": (
                                "Делитель не может "
                                "быть равен нулю."
                            ),
                        }
                    )

    @property
    def effective_operands(self) -> list[int]:
        """
        Возвращает операнды нового или старого вопроса.

        Для старых записей, созданных до появления
        JSON-поля, используются num1 и num2.
        """
        if (
                isinstance(self.operands, list)
                and len(self.operands) >= 2
        ):
            return self.operands

        return [
            self.num1,
            self.num2,
        ]

    @property
    def operation_symbol(self) -> str:
        symbols = {
            self.Operation.ADD: "+",
            self.Operation.SUB: "−",
            self.Operation.MUL: "×",
            self.Operation.DIV: ":",
        }

        return symbols.get(
            self.operation,
            "?",
        )

    @property
    def expression(self) -> str:
        separator = (
            f" {self.operation_symbol} "
        )

        return separator.join(
            str(operand)
            for operand in self.effective_operands
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


class UserGenerationSettings(models.Model):
    """
    Общие настройки генерации примеров пользователя.
    """

    class DifficultyProfile(models.TextChoices):
        EASY = "easy", "Лёгкий"
        MEDIUM = "medium", "Средний"
        HARD = "hard", "Сложный"
        CUSTOM = "custom", "Свой"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generation_settings",
        verbose_name="Пользователь",
    )

    difficulty_profile = models.CharField(
        "Профиль сложности",
        max_length=20,
        choices=DifficultyProfile.choices,
        default=DifficultyProfile.MEDIUM,
    )

    avoid_recent_duplicates = models.BooleanField(
        "Не повторять недавние примеры",
        default=True,
    )

    recent_questions_limit = models.PositiveSmallIntegerField(
        "Размер журнала повторов",
        default=100,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(500),
        ],
        help_text=(
            "Сколько последних примеров учитывать "
            "при проверке повторений."
        ),
    )

    auto_increase_difficulty = models.BooleanField(
        "Автоматически повышать сложность",
        default=False,
    )

    correct_answers_per_level = models.PositiveIntegerField(
        "Правильных ответов до повышения уровня",
        default=50,
        validators=[
            MinValueValidator(1),
        ],
    )

    maximum_difficulty_level = models.PositiveSmallIntegerField(
        "Максимальный уровень сложности",
        default=10,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100),
        ],
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Дата изменения",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Общие настройки генератора"
        verbose_name_plural = (
            "Общие настройки генераторов"
        )

    def __str__(self):
        return (
            "Настройки генератора: "
            f"{self.user.display_name}"
        )

    @property
    def current_difficulty_level(self):
        """
        Возвращает максимальный достигнутый уровень
        среди математических действий.

        Генератор рассчитывает уровень отдельно для
        каждого действия.
        """
        if not self.auto_increase_difficulty:
            return 1

        from apps.game.services.generation_settings import (
            get_all_operation_difficulty_progress,
        )

        progress_items = (
            get_all_operation_difficulty_progress(
                generation_settings=self,
            )
        )

        if not progress_items:
            return 1

        return max(
            item.level
            for item in progress_items
        )


class OperationGenerationSettings(models.Model):
    """
    Настройки генерации одного математического
    действия для конкретного пользователя.
    """

    class Operation(models.TextChoices):
        ADD = "add", "Сложение"
        SUB = "sub", "Вычитание"
        MUL = "mul", "Умножение"
        DIV = "div", "Деление"

    generation_settings = models.ForeignKey(
        UserGenerationSettings,
        on_delete=models.CASCADE,
        related_name="operations",
        verbose_name="Общие настройки",
    )

    operation = models.CharField(
        "Математическое действие",
        max_length=3,
        choices=Operation.choices,
    )

    is_enabled = models.BooleanField(
        "Использовать действие",
        default=True,
    )

    mixed_mode_weight = models.PositiveSmallIntegerField(
        "Вес в смешанном режиме",
        default=25,
        validators=[
            MinValueValidator(0),
        ],
        help_text=(
            "Чем больше значение, тем чаще действие "
            "появляется в режиме «Все действия»."
        ),
    )

    first_operand_min = models.IntegerField(
        "Минимальное первое число",
        default=1,
    )

    first_operand_max = models.IntegerField(
        "Максимальное первое число",
        default=100,
    )

    second_operand_min = models.IntegerField(
        "Минимальное второе число",
        default=1,
    )

    second_operand_max = models.IntegerField(
        "Максимальное второе число",
        default=100,
    )

    operands_count = models.PositiveSmallIntegerField(
        "Количество операндов",
        default=2,
        validators=[
            MinValueValidator(2),
            MaxValueValidator(4),
        ],
        help_text=(
            "Для первой версии поддерживаются "
            "значения от 2 до 4."
        ),
    )

    minimum_answer = models.IntegerField(
        "Минимальный результат",
        null=True,
        blank=True,
    )

    maximum_answer = models.IntegerField(
        "Максимальный результат",
        null=True,
        blank=True,
    )

    allow_negative_result = models.BooleanField(
        "Разрешать отрицательный результат",
        default=False,
        help_text=(
            "Применяется только к вычитанию."
        ),
    )

    allow_remainder = models.BooleanField(
        "Разрешать деление с остатком",
        default=False,
        help_text=(
            "Зарезервировано для будущего режима "
            "с десятичными ответами."
        ),
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "Дата изменения",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Настройки математического действия"
        verbose_name_plural = (
            "Настройки математических действий"
        )

        ordering = [
            "generation_settings",
            "operation",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "generation_settings",
                    "operation",
                ],
                name="game_unique_generation_operation",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    first_operand_max__gte=models.F(
                        "first_operand_min"
                    )
                ),
                name="game_first_operand_range_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    second_operand_max__gte=models.F(
                        "second_operand_min"
                    )
                ),
                name="game_second_operand_range_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(minimum_answer__isnull=True)
                    | models.Q(maximum_answer__isnull=True)
                    | models.Q(
                        maximum_answer__gte=models.F(
                            "minimum_answer"
                        )
                    )
                ),
                name="game_answer_range_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    operands_count__gte=2,
                    operands_count__lte=4,
                ),
                name="game_operands_count_valid",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "generation_settings",
                    "operation",
                ],
                name="game_generation_operation_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.generation_settings.user.display_name}: "
            f"{self.get_operation_display()}"
        )

    def clean(self):
        super().clean()

        from django.core.exceptions import ValidationError

        errors = {}

        if self.first_operand_max < self.first_operand_min:
            errors["first_operand_max"] = (
                "Максимальное значение не может быть "
                "меньше минимального."
            )

        if self.second_operand_max < self.second_operand_min:
            errors["second_operand_max"] = (
                "Максимальное значение не может быть "
                "меньше минимального."
            )

        if (
            self.minimum_answer is not None
            and self.maximum_answer is not None
            and self.maximum_answer
            < self.minimum_answer
        ):
            errors["maximum_answer"] = (
                "Максимальный результат не может быть "
                "меньше минимального."
            )

        if not 2 <= self.operands_count <= 4:
            errors["operands_count"] = (
                "Количество операндов должно быть "
                "от 2 до 4."
            )

        if (
            self.operation != self.Operation.SUB
            and self.allow_negative_result
        ):
            errors["allow_negative_result"] = (
                "Отрицательный результат можно разрешить "
                "только для вычитания."
            )

        if (
            self.operation != self.Operation.DIV
            and self.allow_remainder
        ):
            errors["allow_remainder"] = (
                "Деление с остатком относится только "
                "к операции деления."
            )

        if errors:
            raise ValidationError(errors)