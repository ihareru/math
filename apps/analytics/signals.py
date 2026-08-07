from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import LoginEvent
from .services.client import get_request_client_data
from .services.sessions import (
    get_or_create_visit_session,
)


@receiver(user_logged_in)
def record_successful_login(
    sender,
    request,
    user,
    **kwargs,
):
    if request is None:
        return

    client_data = get_request_client_data(
        request
    )

    visit_session = get_or_create_visit_session(
        request=request,
        user=user,
    )

    LoginEvent.objects.create(
        user=user,
        visit_session=visit_session,
        ip_address=client_data["ip_address"],
        user_agent=client_data["user_agent"],
        browser_name=client_data["browser_name"],
        browser_version=(
            client_data["browser_version"]
        ),
        operating_system=(
            client_data["operating_system"]
        ),
        device_type=client_data["device_type"],
        country_code=(
            visit_session.country_code
        ),
        country_name=(
            visit_session.country_name
        ),
        city_name=visit_session.city_name,
    )