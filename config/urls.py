from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "accounts/",
        include(
            "apps.accounts.urls",
            namespace="accounts",
        ),
    ),
    path(
        "settings/",
        include(
            "apps.settings.urls",
            namespace="user_settings",
        ),
    ),
    path(
        "game/",
        include(
            "apps.game.urls",
            namespace="game",
        ),
    ),
    path(
        "analytics/",
        include(
            "apps.analytics.urls",
            namespace="analytics",
        ),
    ),
    path(
        "cheats/",
        include(
            "apps.cheats.urls",
            namespace="cheats",
        ),
    ),
    path(
        "",
        include(
            "apps.dashboard.urls",
            namespace="dashboard",
        ),
    ),

]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
