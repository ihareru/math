from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .services.sessions import (
    register_request_activity,
)


class AnalyticsMiddleware:
    """
    Обновляет аналитическую сессию и последнюю
    активность авторизованного пользователя.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not getattr(
            settings,
            "ANALYTICS_ENABLED",
            True,
        ):
            return response

        if not request.user.is_authenticated:
            return response

        excluded_prefixes = getattr(
            settings,
            "ANALYTICS_EXCLUDED_PATH_PREFIXES",
            [],
        )

        if any(
            request.path.startswith(prefix)
            for prefix in excluded_prefixes
        ):
            return response

        try:
            register_request_activity(
                request=request,
            )

            self._update_user_last_activity(
                request.user
            )
        except Exception:
            # Ошибка аналитики не должна нарушать
            # работу игры или авторизации.
            pass

        return response

    @staticmethod
    def _update_user_last_activity(user):
        interval_seconds = getattr(
            settings,
            "ANALYTICS_ACTIVITY_UPDATE_SECONDS",
            60,
        )

        now = timezone.now()

        if (
            user.last_activity_at is not None
            and user.last_activity_at
            >= now - timedelta(
                seconds=interval_seconds
            )
        ):
            return

        user.last_activity_at = now

        user.save(
            update_fields=[
                "last_activity_at",
            ]
        )