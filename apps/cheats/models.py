from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class RewardType(models.TextChoices):
    """
    Тип награды или временного игрового бонуса.
    """

    STREAK_TO_STAR = (
        "streak_to_star",
        "Количество правильных ответов до звезды",
    )

    BONUS_STAR = (
        "bonus_star",
        "Выдать звёзды",
    )

    DOUBLE_STARS = (
        "double_stars",
        "Множитель звёзд",
    )

    BONUS_POINTS = (
        "bonus_points",
        "Дополнительные очки",
    )

    XP_MULTIPLIER = (
        "xp_multiplier",
        "Множитель опыта",
    )

    UNLOCK_MODE = (
        "unlock_mode",
        "Открыть игровой режим",
    )

    FREEZE_STREAK = (
        "freeze_streak",
        "Не сбрасывать серию",
    )

    SHOW_CORRECT_ANSWER = (
        "show_correct_answer",
        "Показывать правильный ответ",
    )

    UNLIMITED_HINTS = (
        "unlimited_hints",
        "Безлимитные подсказки",
    )

    UNLIMITED_LIVES = (
        "unlimited_lives",
        "Бесконечные жизни",
    )

    UNLOCK_AVATAR = (
        "unlock_avatar",
        "Разблокировать аватар",
    )

    UNLOCK_THEME = (
        "unlock_theme",
        "Разблокировать тему",
    )

    UNLOCK_BACKGROUND = (
        "unlock_background",
        "Разблокировать фон",
    )

    ENABLE_EVENT = (
        "enable_event",
        "Включить событие",
    )


class CheatCode(models.Model):
    """
    Чит-код, бонусный или событийный код.

    Один код может содержать несколько наград,
    связанных через CheatReward.
    """

    name = models.CharField(
        "Название",
        max_length=100,
    )

    code = models.CharField(
        "Код",
        max_length=50,
        unique=True,
        db_index=True,
        help_text=(
            "Код автоматически сохраняется "
            "в верхнем регистре без пробелов по краям."
        ),
    )

    description = models.TextField(
        "Описание",
        blank=True,
    )

    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    valid_from = models.DateTimeField(
        "Начало периода активации",
        default=timezone.now,
    )

    valid_until = models.DateTimeField(
        "Окончание периода активации",
        null=True,
        blank=True,
        help_text=(
            "После этой даты код нельзя активировать. "
            "Оставьте пустым для отсутствия общей даты окончания."
        ),
    )

    duration_days = models.PositiveIntegerField(
        "Срок бонуса после активации, дней",
        null=True,
        blank=True,
        default=30,
        validators=[
            MinValueValidator(1),
        ],
        help_text=(
            "Оставьте пустым, если бонус после активации "
            "должен действовать бессрочно."
        ),
    )

    max_global_activations = models.PositiveIntegerField(
        "Максимум активаций кода",
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
        ],
        help_text=(
            "Общий лимит для всех пользователей. "
            "Оставьте пустым для отсутствия ограничения."
        ),
    )

    max_user_activations = models.PositiveIntegerField(
        "Максимум активаций одним пользователем",
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    activation_count = models.PositiveIntegerField(
        "Количество успешных активаций",
        default=0,
        editable=False,
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
        ordering = [
            "name",
            "code",
        ]

        verbose_name = "Чит-код"
        verbose_name_plural = "Чит-коды"

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(valid_until__isnull=True)
                    | Q(valid_until__gt=models.F("valid_from"))
                ),
                name="cheat_valid_until_after_from",
            ),
            models.CheckConstraint(
                condition=(
                    Q(max_global_activations__isnull=True)
                    | Q(max_global_activations__gte=1)
                ),
                name="cheat_global_limit_positive",
            ),
            models.CheckConstraint(
                condition=Q(max_user_activations__gte=1),
                name="cheat_user_limit_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(duration_days__isnull=True)
                    | Q(duration_days__gte=1)
                ),
                name="cheat_duration_positive",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        super().clean()

        if not self.code or not self.code.strip():
            raise ValidationError(
                {
                    "code": "Код не может быть пустым.",
                }
            )

        normalized_code = self.code.strip().upper()

        if any(
            character.isspace()
            for character in normalized_code
        ):
            raise ValidationError(
                {
                    "code": (
                        "Код не должен содержать пробелы."
                    ),
                }
            )

        self.code = normalized_code

        if (
            self.valid_until is not None
            and self.valid_until <= self.valid_from
        ):
            raise ValidationError(
                {
                    "valid_until": (
                        "Дата окончания должна быть позже "
                        "даты начала."
                    ),
                }
            )

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()

        super().save(*args, **kwargs)

    @property
    def activation_is_available(self):
        """
        Можно ли активировать код прямо сейчас.

        Пользовательские ограничения здесь не проверяются.
        """
        now = timezone.now()

        if not self.is_active:
            return False

        if self.valid_from > now:
            return False

        if (
            self.valid_until is not None
            and self.valid_until <= now
        ):
            return False

        if (
            self.max_global_activations is not None
            and self.activation_count
            >= self.max_global_activations
        ):
            return False

        return True

    def calculate_expiration(self, *, activated_at=None):
        """
        Вычисляет срок действия бонуса пользователя.
        """
        if activated_at is None:
            activated_at = timezone.now()

        if self.duration_days is None:
            return None

        expires_at = (
            activated_at
            + timedelta(days=self.duration_days)
        )

        # Бонус не должен действовать дольше общей даты
        # окончания кода.
        if (
            self.valid_until is not None
            and expires_at > self.valid_until
        ):
            return self.valid_until

        return expires_at


class CheatReward(models.Model):
    """
    Одна награда, предоставляемая чит-кодом.

    Формат reward_data зависит от reward_type.
    """

    cheat = models.ForeignKey(
        CheatCode,
        on_delete=models.CASCADE,
        related_name="rewards",
        verbose_name="Чит-код",
    )

    reward_type = models.CharField(
        "Тип награды",
        max_length=50,
        choices=RewardType.choices,
    )

    reward_data = models.JSONField(
        "Параметры награды",
        default=dict,
        help_text=(
            'Например: {"answers": 8}, '
            '{"multiplier": 2} или {"stars": 5}.'
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
        verbose_name = "Награда чит-кода"
        verbose_name_plural = "Награды чит-кодов"

        ordering = [
            "cheat",
            "reward_type",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cheat",
                    "reward_type",
                ],
                name="cheat_unique_reward_type",
            ),
        ]

    def __str__(self):
        return (
            f"{self.cheat.code} → "
            f"{self.get_reward_type_display()}"
        )

    def clean(self):
        super().clean()

        if not isinstance(self.reward_data, dict):
            raise ValidationError(
                {
                    "reward_data": (
                        "Параметры награды должны быть "
                        "JSON-объектом."
                    ),
                }
            )

        validators = {
            RewardType.STREAK_TO_STAR: (
                self._validate_streak_to_star
            ),
            RewardType.BONUS_STAR: (
                self._validate_bonus_star
            ),
            RewardType.DOUBLE_STARS: (
                self._validate_star_multiplier
            ),
            RewardType.UNLOCK_MODE: (
                self._validate_unlock_mode
            ),
            RewardType.FREEZE_STREAK: (
                self._validate_boolean_enabled
            ),
            RewardType.SHOW_CORRECT_ANSWER: (
                self._validate_boolean_enabled
            ),
            RewardType.UNLIMITED_HINTS: (
                self._validate_boolean_enabled
            ),
            RewardType.UNLIMITED_LIVES: (
                self._validate_boolean_enabled
            ),
        }

        validator = validators.get(
            self.reward_type
        )

        if validator is not None:
            validator()

    def _require_positive_integer(
        self,
        key,
        *,
        minimum=1,
        maximum=None,
    ):
        value = self.reward_data.get(key)

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
        ):
            raise ValidationError(
                {
                    "reward_data": (
                        f'Параметр "{key}" должен быть '
                        "целым числом."
                    ),
                }
            )

        if value < minimum:
            raise ValidationError(
                {
                    "reward_data": (
                        f'Параметр "{key}" должен быть '
                        f"не меньше {minimum}."
                    ),
                }
            )

        if maximum is not None and value > maximum:
            raise ValidationError(
                {
                    "reward_data": (
                        f'Параметр "{key}" должен быть '
                        f"не больше {maximum}."
                    ),
                }
            )

        return value

    def _validate_streak_to_star(self):
        self._require_positive_integer(
            "answers",
            minimum=2,
            maximum=1000,
        )

    def _validate_bonus_star(self):
        self._require_positive_integer(
            "stars",
            minimum=1,
            maximum=100000,
        )

    def _validate_star_multiplier(self):
        self._require_positive_integer(
            "multiplier",
            minimum=2,
            maximum=100,
        )

    def _validate_unlock_mode(self):
        mode = self.reward_data.get("mode")

        if not isinstance(mode, str) or not mode.strip():
            raise ValidationError(
                {
                    "reward_data": (
                        'Для награды открытия режима '
                        'необходимо указать строковый '
                        'параметр "mode".'
                    ),
                }
            )

    def _validate_boolean_enabled(self):
        enabled = self.reward_data.get("enabled")

        if not isinstance(enabled, bool):
            raise ValidationError(
                {
                    "reward_data": (
                        'Необходимо указать логический '
                        'параметр "enabled".'
                    ),
                }
            )


class UserCheat(models.Model):
    """
    Одна успешная активация чит-кода пользователем.

    Повторная активация того же кода создаёт отдельную
    запись, если это разрешено max_user_activations.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cheat_activations",
        verbose_name="Пользователь",
    )

    cheat = models.ForeignKey(
        CheatCode,
        on_delete=models.PROTECT,
        related_name="user_activations",
        verbose_name="Чит-код",
    )

    activated_at = models.DateTimeField(
        "Дата активации",
        default=timezone.now,
        editable=False,
    )

    expires_at = models.DateTimeField(
        "Дата окончания бонуса",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    activation_ip = models.GenericIPAddressField(
        "IP при активации",
        null=True,
        blank=True,
    )

    activation_user_agent = models.TextField(
        "User-Agent при активации",
        blank=True,
    )

    created_at = models.DateTimeField(
        "Дата создания записи",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Активация чит-кода"
        verbose_name_plural = "Активации чит-кодов"

        ordering = [
            "-activated_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "is_active",
                ],
                name="cheat_user_active_idx",
            ),
            models.Index(
                fields=[
                    "cheat",
                    "activated_at",
                ],
                name="cheat_code_activated_idx",
            ),
            models.Index(
                fields=[
                    "expires_at",
                ],
                name="cheat_expiration_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(expires_at__isnull=True)
                    | Q(expires_at__gt=models.F("activated_at"))
                ),
                name="cheat_expiry_after_activation",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.display_name} → "
            f"{self.cheat.code}"
        )

    @property
    def currently_active(self):
        if not self.is_active:
            return False

        if (
            self.expires_at is not None
            and self.expires_at <= timezone.now()
        ):
            return False

        return True