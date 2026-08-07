import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import (
    require_POST,
)
from django.contrib.auth.decorators import (
    login_required,
)
from django.contrib.admin.views.decorators import (
    staff_member_required,
)

from .services.sessions import (
    get_or_create_visit_session,
)
from .services.dashboard import (
    dashboard_statistics,
)
from .models import (
    LoginEvent,
    VisitSession,
)


def parse_positive_integer(
    value,
    *,
    maximum,
):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None

    if number < 0 or number > maximum:
        return None

    return number


def parse_pixel_ratio(value):
    try:
        number = Decimal(str(value))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return None

    if number < 0 or number > 20:
        return None

    return number.quantize(
        Decimal("0.01")
    )


@login_required
@require_POST
def client_context(request):
    try:
        payload = json.loads(
            request.body.decode("utf-8")
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return JsonResponse(
            {
                "ok": False,
                "error": "Некорректный JSON.",
            },
            status=400,
        )

    visit_session = get_or_create_visit_session(
        request=request,
        user=request.user,
    )

    visit_session.screen_width = (
        parse_positive_integer(
            payload.get("screen_width"),
            maximum=20000,
        )
    )

    visit_session.screen_height = (
        parse_positive_integer(
            payload.get("screen_height"),
            maximum=20000,
        )
    )

    visit_session.viewport_width = (
        parse_positive_integer(
            payload.get("viewport_width"),
            maximum=20000,
        )
    )

    visit_session.viewport_height = (
        parse_positive_integer(
            payload.get("viewport_height"),
            maximum=20000,
        )
    )

    visit_session.pixel_ratio = (
        parse_pixel_ratio(
            payload.get("pixel_ratio")
        )
    )

    visit_session.browser_language = str(
        payload.get("language") or ""
    )[:30]

    visit_session.timezone_name = str(
        payload.get("timezone") or ""
    )[:100]

    visit_session.touch_points = (
        parse_positive_integer(
            payload.get("touch_points"),
            maximum=100,
        )
        or 0
    )

    visit_session.cpu_cores = (
        parse_positive_integer(
            payload.get("cpu_cores"),
            maximum=1024,
        )
    )

    visit_session.client_context_received_at = (
        timezone.now()
    )

    visit_session.save(
        update_fields=[
            "screen_width",
            "screen_height",
            "viewport_width",
            "viewport_height",
            "pixel_ratio",
            "browser_language",
            "timezone_name",
            "touch_points",
            "cpu_cores",
            "client_context_received_at",
            "last_seen_at",
        ]
    )

    return JsonResponse(
        {
            "ok": True,
        }
    )

@staff_member_required
def dashboard(request):

    context = dashboard_statistics()

    return render(
        request,
        "analytics/dashboard.html",
        context,
    )

@staff_member_required
def online_users(request):

    border = timezone.now() - timedelta(minutes=5)

    sessions = (
        VisitSession.objects
        .select_related("user")
        .filter(
            last_seen_at__gte=border,
            user__isnull=False,
        )
        .order_by("-last_seen_at")
    )

    return render(
        request,
        "analytics/online.html",
        {
            "sessions": sessions,
        },
    )

@staff_member_required
def login_events(request):

    events = (
        LoginEvent.objects
        .select_related("user")
        .order_by("-logged_in_at")
    )

    return render(
        request,
        "analytics/logins.html",
        {
            "events": events,
        },
    )

@staff_member_required
def visit_sessions(request):

    sessions = (
        VisitSession.objects
        .select_related("user")
        .order_by("-last_seen_at")
    )

    return render(
        request,
        "analytics/sessions.html",
        {
            "sessions": sessions,
        },
    )

@staff_member_required
def user_activity(request):

    users = (
        User.objects
        .select_related(
            "game_statistics"
        )
        .order_by("display_name")
    )

    return render(
        request,
        "analytics/users.html",
        {
            "users": users,
        },
    )