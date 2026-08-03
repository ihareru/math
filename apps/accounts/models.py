import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class RegistrationMethod(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Телефон"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID",
    )

    email = models.EmailField(
        "Email",
        unique=True,
        null=True,
        blank=True,
    )

    phone = PhoneNumberField(
        "Телефон",
        unique=True,
        null=True,
        blank=True,
        region="EE",
    )

    display_name = models.CharField(
        "Имя в рейтинге",
        max_length=100,
    )

    registration_method = models.CharField(
        "Способ регистрации",
        max_length=10,
        choices=RegistrationMethod.choices,
    )

    email_verified = models.BooleanField(
        "Email подтверждён",
        default=False,
    )

    phone_verified = models.BooleanField(
        "Телефон подтверждён",
        default=False,
    )

    show_in_rating = models.BooleanField(
        "Показывать в общем рейтинге",
        default=True,
    )

    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    is_staff = models.BooleanField(
        "Доступ в административную панель",
        default=False,
    )

    date_joined = models.DateTimeField(
        "Дата регистрации",
        default=timezone.now,
    )

    last_activity_at = models.DateTimeField(
        "Последняя активность",
        null=True,
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "display_name",
    ]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = [
            "-date_joined",
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                        models.Q(email__isnull=False)
                        | models.Q(phone__isnull=False)
                ),
                name="accounts_user_email_or_phone_required",
            ),
        ]

    def __str__(self):
        return self.display_name

    def clean(self):
        super().clean()

        if not self.email and not self.phone:
            raise ValidationError(
                "У пользователя должен быть email или телефон."
            )

        if self.email:
            self.email = self.email.strip().lower()

        if (
            self.registration_method
            == self.RegistrationMethod.EMAIL
            and not self.email
        ):
            raise ValidationError(
                {
                    "email": (
                        "При регистрации по email необходимо "
                        "указать email."
                    )
                }
            )

        if (
            self.registration_method
            == self.RegistrationMethod.PHONE
            and not self.phone
        ):
            raise ValidationError(
                {
                    "phone": (
                        "При регистрации по телефону необходимо "
                        "указать телефон."
                    )
                }
            )

    @property
    def primary_login(self):
        if (
            self.registration_method
            == self.RegistrationMethod.PHONE
        ):
            return str(self.phone)

        return self.email or str(self.phone)

    @property
    def registration_confirmed(self):
        if (
            self.registration_method
            == self.RegistrationMethod.EMAIL
        ):
            return self.email_verified

        return self.phone_verified


class VerificationCode(models.Model):
    class Purpose(models.TextChoices):
        REGISTRATION = (
            "registration",
            "Подтверждение регистрации",
        )
        LOGIN = (
            "login",
            "Подтверждение входа",
        )
        PASSWORD_RESET = (
            "password_reset",
            "Восстановление пароля",
        )
        CHANGE_EMAIL = (
            "change_email",
            "Изменение email",
        )
        CHANGE_PHONE = (
            "change_phone",
            "Изменение телефона",
        )

    class DeliveryMethod(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_codes",
        verbose_name="Пользователь",
    )

    purpose = models.CharField(
        "Назначение",
        max_length=30,
        choices=Purpose.choices,
    )

    delivery_method = models.CharField(
        "Способ доставки",
        max_length=10,
        choices=DeliveryMethod.choices,
    )

    code_hash = models.CharField(
        "Хеш кода",
        max_length=128,
    )

    destination = models.CharField(
        "Адрес назначения",
        max_length=255,
    )

    expires_at = models.DateTimeField(
        "Срок действия",
    )

    attempts = models.PositiveSmallIntegerField(
        "Количество попыток",
        default=0,
    )

    max_attempts = models.PositiveSmallIntegerField(
        "Максимальное количество попыток",
        default=5,
    )

    used_at = models.DateTimeField(
        "Дата использования",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Код подтверждения"
        verbose_name_plural = "Коды подтверждения"
        ordering = [
            "-created_at",
        ]
        indexes = [
            models.Index(
                fields=[
                    "user",
                    "purpose",
                    "created_at",
                ],
                name="verification_user_purpose_idx",
            ),
            models.Index(
                fields=[
                    "expires_at",
                ],
                name="verification_expires_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user} — "
            f"{self.get_purpose_display()}"
        )

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def has_attempts_left(self):
        return self.attempts < self.max_attempts