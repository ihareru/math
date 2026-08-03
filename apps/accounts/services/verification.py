import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import VerificationCode


class VerificationError(Exception):
    """Базовая ошибка подтверждения."""


class VerificationExpiredError(VerificationError):
    """Срок действия кода истёк."""


class VerificationAttemptsExceededError(VerificationError):
    """Превышено количество попыток."""


class VerificationInvalidCodeError(VerificationError):
    """Введён неверный код."""


class VerificationResendTooEarlyError(VerificationError):
    """Повторный код запрошен слишком рано."""


def generate_numeric_code() -> str:
    code_length = settings.VERIFICATION_CODE_LENGTH

    minimum = 10 ** (code_length - 1)
    maximum = (10 ** code_length) - 1

    return str(
        secrets.randbelow(maximum - minimum + 1)
        + minimum
    )


def create_registration_code(user):
    return create_verification_code(
        user=user,
        purpose=VerificationCode.Purpose.REGISTRATION,
        delivery_method=VerificationCode.DeliveryMethod.EMAIL,
        destination=user.email,
    )


def create_password_reset_code(user):
    return create_verification_code(
        user=user,
        purpose=VerificationCode.Purpose.PASSWORD_RESET,
        delivery_method=VerificationCode.DeliveryMethod.EMAIL,
        destination=user.email,
    )


@transaction.atomic
def create_verification_code(
    *,
    user,
    purpose,
    delivery_method,
    destination,
):
    now = timezone.now()

    latest_code = (
        VerificationCode.objects
        .filter(
            user=user,
            purpose=purpose,
            delivery_method=delivery_method,
        )
        .order_by("-created_at")
        .first()
    )

    if latest_code:
        cooldown_until = (
            latest_code.created_at
            + timedelta(
                seconds=(
                    settings
                    .VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS
                )
            )
        )

        if now < cooldown_until:
            remaining_seconds = max(
                1,
                int(
                    (
                        cooldown_until - now
                    ).total_seconds()
                ),
            )

            raise VerificationResendTooEarlyError(
                "Повторный код можно запросить "
                f"через {remaining_seconds} сек."
            )

    # Все ранее выданные и ещё не использованные коды
    # такого же назначения помечаем использованными.
    VerificationCode.objects.filter(
        user=user,
        purpose=purpose,
        used_at__isnull=True,
    ).update(
        used_at=now,
    )

    raw_code = generate_numeric_code()

    verification = VerificationCode.objects.create(
        user=user,
        purpose=purpose,
        delivery_method=delivery_method,
        code_hash=make_password(raw_code),
        destination=destination,
        expires_at=(
            now
            + timedelta(
                minutes=(
                    settings
                    .VERIFICATION_CODE_LIFETIME_MINUTES
                )
            )
        ),
        max_attempts=(
            settings.VERIFICATION_CODE_MAX_ATTEMPTS
        ),
    )

    deliver_verification_code(
        verification=verification,
        raw_code=raw_code,
    )

    return verification


def deliver_verification_code(
    *,
    verification,
    raw_code,
):
    if (
        verification.purpose
        == VerificationCode.Purpose.PASSWORD_RESET
    ):
        subject = "Восстановление пароля Math Game"

        message = (
            "Вы запросили восстановление пароля "
            "в Math Game.\n\n"
            f"Код подтверждения: {raw_code}\n\n"
            "Код действует "
            f"{settings.VERIFICATION_CODE_LIFETIME_MINUTES} "
            "минут.\n\n"
            "Если вы не запрашивали восстановление пароля, "
            "проигнорируйте это сообщение."
        )
    else:
        subject = "Код подтверждения Math Game"

        message = (
            "Ваш код подтверждения Math Game: "
            f"{raw_code}\n\n"
            "Код действует "
            f"{settings.VERIFICATION_CODE_LIFETIME_MINUTES} "
            "минут.\n\n"
            "Если вы не регистрировались, "
            "проигнорируйте это сообщение."
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[
            verification.destination,
        ],
        fail_silently=False,
    )


@transaction.atomic
def verify_code(
    *,
    user,
    purpose,
    raw_code,
):
    verification = (
        VerificationCode.objects
        .select_for_update()
        .filter(
            user=user,
            purpose=purpose,
            used_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )

    if verification is None:
        raise VerificationExpiredError(
            "Действующий код подтверждения не найден."
        )

    if verification.is_expired:
        verification.used_at = timezone.now()

        verification.save(
            update_fields=[
                "used_at",
            ]
        )

        raise VerificationExpiredError(
            "Срок действия кода истёк."
        )

    if not verification.has_attempts_left:
        verification.used_at = timezone.now()

        verification.save(
            update_fields=[
                "used_at",
            ]
        )

        raise VerificationAttemptsExceededError(
            "Превышено допустимое количество попыток. "
            "Запросите новый код."
        )

    verification.attempts += 1

    if not check_password(
        raw_code,
        verification.code_hash,
    ):
        update_fields = [
            "attempts",
        ]

        if (
            verification.attempts
            >= verification.max_attempts
        ):
            verification.used_at = timezone.now()
            update_fields.append("used_at")

        verification.save(
            update_fields=update_fields,
        )

        raise VerificationInvalidCodeError(
            "Введён неверный код."
        )

    verification.used_at = timezone.now()

    verification.save(
        update_fields=[
            "attempts",
            "used_at",
        ]
    )

    return verification


@transaction.atomic
def verify_registration_code(
    *,
    user,
    raw_code,
):
    verify_code(
        user=user,
        purpose=VerificationCode.Purpose.REGISTRATION,
        raw_code=raw_code,
    )

    user.email_verified = True
    user.is_active = True

    user.save(
        update_fields=[
            "email_verified",
            "is_active",
        ]
    )

    return user


def verify_password_reset_code(
    *,
    user,
    raw_code,
):
    return verify_code(
        user=user,
        purpose=VerificationCode.Purpose.PASSWORD_RESET,
        raw_code=raw_code,
    )