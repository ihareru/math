from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.analytics.models import (
    LoginEvent,
    VisitSession,
)

User = get_user_model()


def dashboard_statistics():
    now = timezone.now()

    today = now.date()

    online_border = now - timedelta(minutes=5)

    return {
        "registered_users":
            User.objects.count(),

        "active_users_today":
            LoginEvent.objects.filter(
                logged_in_at__date=today
            ).values(
                "user"
            ).distinct().count(),

        "login_count_today":
            LoginEvent.objects.filter(
                logged_in_at__date=today
            ).count(),

        "online_users":
            VisitSession.objects.filter(
                last_seen_at__gte=online_border,
                user__isnull=False,
            ).values(
                "user"
            ).distinct().count(),

        "sessions_today":
            VisitSession.objects.filter(
                first_seen_at__date=today
            ).count(),
    }