from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_settings",
        verbose_name="Пользователь",
    )

    background_color = models.CharField(
        "Цвет фона",
        max_length=7,
        default="#87CEEB",
    )

    background_image = models.CharField(
        "Фоновое изображение",
        max_length=255,
        blank=True,
        default="",
    )

    background_music = models.BooleanField(
        "Фоновая музыка",
        default=True,
    )

    success_sound = models.BooleanField(
        "Звук правильного ответа",
        default=True,
    )

    fail_sound = models.BooleanField(
        "Звук неправильного ответа",
        default=True,
    )

    background_volume = models.PositiveSmallIntegerField(
        "Громкость фоновой музыки",
        default=50,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    success_volume = models.PositiveSmallIntegerField(
        "Громкость правильного ответа",
        default=50,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    fail_volume = models.PositiveSmallIntegerField(
        "Громкость ошибки",
        default=50,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    class Meta:
        verbose_name = "Настройки пользователя"
        verbose_name_plural = "Настройки пользователей"

    def __str__(self):
        return f"Настройки: {self.user.display_name}"