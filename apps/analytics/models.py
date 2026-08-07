from django.conf import settings
from django.db import models


class VisitSession(models.Model):
    """
    Одна браузерная сессия пользователя.

    Запись объединяет множество HTTP-запросов,
    сделанных в рамках одной Django-сессии.
    """

    class DeviceType(models.TextChoices):
        DESKTOP = "desktop", "Стационарный компьютер"
        TABLET = "tablet", "Планшет"
        MOBILE = "mobile", "Смартфон"
        BOT = "bot", "Робот"
        UNKNOWN = "unknown", "Не определено"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="visit_sessions",
        verbose_name="Пользователь",
        null=True,
        blank=True,
    )

    session_key = models.CharField(
        "Ключ Django-сессии",
        max_length=40,
        unique=True,
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(
        "IP-адрес",
        null=True,
        blank=True,
    )

    country_code = models.CharField(
        "Код страны",
        max_length=2,
        blank=True,
    )

    country_name = models.CharField(
        "Страна",
        max_length=100,
        blank=True,
    )

    city_name = models.CharField(
        "Город",
        max_length=120,
        blank=True,
    )

    user_agent = models.TextField(
        "User-Agent",
        blank=True,
    )

    browser_name = models.CharField(
        "Браузер",
        max_length=100,
        blank=True,
    )

    browser_version = models.CharField(
        "Версия браузера",
        max_length=50,
        blank=True,
    )

    operating_system = models.CharField(
        "Операционная система",
        max_length=100,
        blank=True,
    )

    device_type = models.CharField(
        "Тип устройства",
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.UNKNOWN,
    )

    screen_width = models.PositiveIntegerField(
        "Ширина экрана",
        null=True,
        blank=True,
    )

    screen_height = models.PositiveIntegerField(
        "Высота экрана",
        null=True,
        blank=True,
    )

    viewport_width = models.PositiveIntegerField(
        "Ширина окна браузера",
        null=True,
        blank=True,
    )

    viewport_height = models.PositiveIntegerField(
        "Высота окна браузера",
        null=True,
        blank=True,
    )

    pixel_ratio = models.DecimalField(
        "Плотность пикселей",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    browser_language = models.CharField(
        "Язык браузера",
        max_length=30,
        blank=True,
    )

    timezone_name = models.CharField(
        "Часовой пояс браузера",
        max_length=100,
        blank=True,
    )

    touch_points = models.PositiveSmallIntegerField(
        "Количество точек касания",
        default=0,
    )

    cpu_cores = models.PositiveSmallIntegerField(
        "Логических процессоров",
        null=True,
        blank=True,
    )

    first_seen_at = models.DateTimeField(
        "Первое действие",
        auto_now_add=True,
    )

    last_seen_at = models.DateTimeField(
        "Последнее действие",
        auto_now=True,
    )

    request_count = models.PositiveBigIntegerField(
        "Количество запросов",
        default=0,
    )

    last_path = models.CharField(
        "Последняя страница",
        max_length=500,
        blank=True,
    )

    client_context_received_at = models.DateTimeField(
        "Получены данные браузера",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Сессия посещения"
        verbose_name_plural = "Сессии посещений"
        ordering = [
            "-last_seen_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "user",
                    "last_seen_at",
                ],
                name="analytics_user_last_seen_idx",
            ),
            models.Index(
                fields=[
                    "ip_address",
                    "last_seen_at",
                ],
                name="analytics_ip_last_seen_idx",
            ),
            models.Index(
                fields=[
                    "country_code",
                    "last_seen_at",
                ],
                name="analytics_country_seen_idx",
            ),
        ]

    def __str__(self):
        user_name = (
            self.user.display_name
            if self.user
            else "Анонимный пользователь"
        )

        return (
            f"{user_name} — "
            f"{self.ip_address or 'IP не определён'}"
        )

    @property
    def screen_resolution(self):
        if (
            self.screen_width is None
            or self.screen_height is None
        ):
            return "Не определено"

        return (
            f"{self.screen_width}"
            f"×"
            f"{self.screen_height}"
        )

    @property
    def browser_display(self):
        parts = [
            self.browser_name,
            self.browser_version,
        ]

        return " ".join(
            part
            for part in parts
            if part
        ) or "Не определён"


class LoginEvent(models.Model):
    """
    Успешный вход пользователя в систему.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_events",
        verbose_name="Пользователь",
    )

    visit_session = models.ForeignKey(
        VisitSession,
        on_delete=models.SET_NULL,
        related_name="login_events",
        verbose_name="Сессия посещения",
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        "IP-адрес",
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        "User-Agent",
        blank=True,
    )

    browser_name = models.CharField(
        "Браузер",
        max_length=100,
        blank=True,
    )

    browser_version = models.CharField(
        "Версия браузера",
        max_length=50,
        blank=True,
    )

    operating_system = models.CharField(
        "Операционная система",
        max_length=100,
        blank=True,
    )

    device_type = models.CharField(
        "Тип устройства",
        max_length=20,
        choices=VisitSession.DeviceType.choices,
        default=VisitSession.DeviceType.UNKNOWN,
    )

    country_code = models.CharField(
        "Код страны",
        max_length=2,
        blank=True,
    )

    country_name = models.CharField(
        "Страна",
        max_length=100,
        blank=True,
    )

    city_name = models.CharField(
        "Город",
        max_length=120,
        blank=True,
    )

    logged_in_at = models.DateTimeField(
        "Время входа",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Успешный вход"
        verbose_name_plural = "Успешные входы"
        ordering = [
            "-logged_in_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "user",
                    "logged_in_at",
                ],
                name="analytics_login_user_time_idx",
            ),
            models.Index(
                fields=[
                    "ip_address",
                    "logged_in_at",
                ],
                name="analytics_login_ip_time_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.display_name} — "
            f"{self.logged_in_at:%d.%m.%Y %H:%M}"
        )