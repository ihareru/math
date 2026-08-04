import ipaddress
import re

from django.conf import settings


BROWSER_PATTERNS = [
    (
        "Edge",
        re.compile(
            r"(?:Edg|Edge)/(?P<version>[\d.]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "Opera",
        re.compile(
            r"(?:OPR|Opera)/(?P<version>[\d.]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "Chrome",
        re.compile(
            r"(?:Chrome|CriOS)/(?P<version>[\d.]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "Firefox",
        re.compile(
            r"(?:Firefox|FxiOS)/(?P<version>[\d.]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "Safari",
        re.compile(
            r"Version/(?P<version>[\d.]+).*Safari",
            re.IGNORECASE,
        ),
    ),
]


def normalize_ip(value):
    if not value:
        return None

    value = value.strip()

    try:
        return str(
            ipaddress.ip_address(value)
        )
    except ValueError:
        return None


def get_client_ip(request):
    """
    Возвращает IP посетителя.

    X-Forwarded-For используется только когда это
    явно разрешено настройкой проекта.
    """
    if getattr(
        settings,
        "ANALYTICS_TRUST_X_FORWARDED_FOR",
        False,
    ):
        forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR",
            "",
        )

        if forwarded_for:
            first_ip = forwarded_for.split(",")[0]
            normalized = normalize_ip(first_ip)

            if normalized:
                return normalized

    return normalize_ip(
        request.META.get("REMOTE_ADDR")
    )


def parse_browser(user_agent):
    if not user_agent:
        return "", ""

    for browser_name, pattern in BROWSER_PATTERNS:
        match = pattern.search(user_agent)

        if match:
            return (
                browser_name,
                match.group("version"),
            )

    return "Другой", ""


def parse_operating_system(user_agent):
    if not user_agent:
        return ""

    user_agent_lower = user_agent.lower()

    if "windows nt 10.0" in user_agent_lower:
        return "Windows 10/11"

    if "windows nt 6.3" in user_agent_lower:
        return "Windows 8.1"

    if "windows nt 6.1" in user_agent_lower:
        return "Windows 7"

    if "iphone" in user_agent_lower:
        return "iOS"

    if "ipad" in user_agent_lower:
        return "iPadOS"

    if "android" in user_agent_lower:
        return "Android"

    if (
        "macintosh" in user_agent_lower
        or "mac os x" in user_agent_lower
    ):
        return "macOS"

    if "linux" in user_agent_lower:
        return "Linux"

    return "Другая"


def detect_device_type(user_agent):
    if not user_agent:
        return "unknown"

    user_agent_lower = user_agent.lower()

    bot_markers = (
        "bot",
        "crawler",
        "spider",
        "slurp",
        "headless",
    )

    if any(
        marker in user_agent_lower
        for marker in bot_markers
    ):
        return "bot"

    tablet_markers = (
        "ipad",
        "tablet",
        "kindle",
        "silk/",
    )

    if any(
        marker in user_agent_lower
        for marker in tablet_markers
    ):
        return "tablet"

    mobile_markers = (
        "mobile",
        "iphone",
        "android",
        "windows phone",
    )

    if any(
        marker in user_agent_lower
        for marker in mobile_markers
    ):
        return "mobile"

    return "desktop"


def get_request_client_data(request):
    user_agent = request.META.get(
        "HTTP_USER_AGENT",
        "",
    )[:2000]

    browser_name, browser_version = (
        parse_browser(user_agent)
    )

    return {
        "ip_address": get_client_ip(request),
        "user_agent": user_agent,
        "browser_name": browser_name,
        "browser_version": browser_version,
        "operating_system": (
            parse_operating_system(user_agent)
        ),
        "device_type": (
            detect_device_type(user_agent)
        ),
    }