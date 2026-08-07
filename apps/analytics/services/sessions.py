from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.analytics.models import VisitSession

from .client import get_request_client_data


def ensure_django_session_key(request):
    if request.session.session_key is None:
        request.session.save()

    return request.session.session_key


@transaction.atomic
def get_or_create_visit_session(
    *,
    request,
    user=None,
):
    session_key = ensure_django_session_key(
        request
    )

    client_data = get_request_client_data(
        request
    )

    defaults = {
        "user": user,
        **client_data,
        "last_path": request.path[:500],
    }

    visit_session, created = (
        VisitSession.objects.get_or_create(
            session_key=session_key,
            defaults=defaults,
        )
    )

    changed_fields = []

    if user is not None and (
        visit_session.user_id != user.pk
    ):
        visit_session.user = user
        changed_fields.append("user")

    for field_name in (
        "ip_address",
        "user_agent",
        "browser_name",
        "browser_version",
        "operating_system",
        "device_type",
    ):
        new_value = client_data[field_name]

        if (
            new_value
            and getattr(
                visit_session,
                field_name,
            ) != new_value
        ):
            setattr(
                visit_session,
                field_name,
                new_value,
            )
            changed_fields.append(field_name)

    current_path = request.path[:500]

    if visit_session.last_path != current_path:
        visit_session.last_path = current_path
        changed_fields.append("last_path")

    if changed_fields:
        visit_session.save(
            update_fields=[
                *changed_fields,
                "last_seen_at",
            ]
        )

    return visit_session


def register_request_activity(
    *,
    request,
):
    if not request.user.is_authenticated:
        return None

    visit_session = get_or_create_visit_session(
        request=request,
        user=request.user,
    )

    VisitSession.objects.filter(
        pk=visit_session.pk,
    ).update(
        request_count=F("request_count") + 1,
        last_seen_at=timezone.now(),
        last_path=request.path[:500],
    )

    return visit_session