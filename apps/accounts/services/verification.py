import logging
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


logger = logging.getLogger(__name__)


CODE_LENGTH = 6
CODE_LIFETIME_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60


class VerificationError(Exception):
    """Базовая ошибка подтверждения."""


class VerificationExpiredError(VerificationError):
    """Срок действия кода истёк."""


class VerificationAttemptsExceededError(VerificationError):
    """Превышено количество попыток."""


class VerificationInvalidCodeError(VerificationError):
    """Введён неправильный код."""


class VerificationResendTooEarlyError(VerificationError):
    """Повторный код запрошен слишком рано."""


def generate_numeric_code():
    minimum = 10 ** (CODE_LENGTH - 1)
    maximum = (10 ** CODE_LENGTH) - 1

    return str(
        secrets.randbelow(maximum - minimum + 1)
        + minimum
    )


def create_registration_code(user):
    return create_verification_code(
        user=user,
        purpose=VerificationCode.Purpose.REGISTRATION,
        delivery_method=(
            VerificationCode.DeliveryMethod.EMAIL
        ),
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
                seconds=RESEND_COOLDOWN_SECONDS,
            )
        )

        if now < cooldown_until:
            remaining = int(
                (cooldown_until - now).total_seconds()
            )

            raise VerificationResendTooEarlyError(
                f"Повторный код можно запросить "
                f"через {remaining} сек."
            )

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
                minutes=CODE_LIFETIME_MINUTES,
            )
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
    send_email_code(
        destination=verification.destination,
        code=raw_code,
    )


def send_email_code(
    *,
    destination,
    code,
):
    send_mail(
        subject="Код подтверждения Math Game",
        message=(
            "Ваш код подтверждения Math Game: "
            f"{code}\n\n"
            f"Код действует "
            f"{CODE_LIFETIME_MINUTES} минут.\n\n"
            "Если вы не регистрировались, "
            "проигнорируйте это сообщение."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[
            destination,
        ],
        fail_silently=False,
    )


def send_sms_code(
    *,
    destination,
    code,
):
    if settings.DEBUG:
        logger.warning(
            "DEV SMS для %s: код %s",
            destination,
            code,
        )

        print(
            "\n"
            "========================================\n"
            f"DEV SMS для {destination}\n"
            f"Код подтверждения: {code}\n"
            "========================================\n"
        )
        return

    raise VerificationError(
        "SMS-провайдер пока не настроен."
    )


@transaction.atomic
def verify_registration_code(
    *,
    user,
    raw_code,
):
    verification = (
        VerificationCode.objects
        .select_for_update()
        .filter(
            user=user,
            purpose=(
                VerificationCode.Purpose.REGISTRATION
            ),
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
        raise VerificationAttemptsExceededError(
            "Превышено количество попыток."
        )

    verification.attempts += 1

    if not check_password(
        raw_code,
        verification.code_hash,
    ):
        verification.save(
            update_fields=[
                "attempts",
            ]
        )

        raise VerificationInvalidCodeError(
            "Введён неправильный код."
        )

    verification.used_at = timezone.now()
    verification.save(
        update_fields=[
            "attempts",
            "used_at",
        ]
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