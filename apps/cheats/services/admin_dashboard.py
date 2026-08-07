from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.cheats.models import (
    CheatCode,
    UserCheat,
)


def get_cheat_admin_statistics():
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    codes = CheatCode.objects.all()
    activations = UserCheat.objects.all()

    active_activations_filter = (
        Q(is_active=True)
        & (
            Q(expires_at__isnull=True)
            | Q(expires_at__gt=now)
        )
    )

    return {
        "total_codes": codes.count(),
        "enabled_codes": codes.filter(
            is_active=True,
        ).count(),
        "available_codes": sum(
            1
            for cheat in codes
            if cheat.activation_is_available
        ),
        "total_activations": (
            activations.count()
        ),
        "active_activations": (
            activations
            .filter(active_activations_filter)
            .count()
        ),
        "activations_last_30_days": (
            activations
            .filter(
                activated_at__gte=thirty_days_ago
            )
            .count()
        ),
        "unique_users": (
            activations
            .values("user_id")
            .distinct()
            .count()
        ),
    }


def get_popular_cheat_codes(*, limit=10):
    return (
        CheatCode.objects
        .annotate(
            real_activation_count=Count(
                "user_activations"
            ),
            unique_user_count=Count(
                "user_activations__user",
                distinct=True,
            ),
            active_user_count=Count(
                "user_activations",
                filter=Q(
                    user_activations__is_active=True,
                )
                & (
                    Q(
                        user_activations__expires_at__isnull=True
                    )
                    | Q(
                        user_activations__expires_at__gt=timezone.now()
                    )
                ),
            ),
        )
        .order_by(
            "-real_activation_count",
            "name",
        )[:limit]
    )