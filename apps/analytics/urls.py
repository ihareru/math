from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "online/",
        views.online_users,
        name="online",
    ),

    path(
        "users/",
        views.user_activity,
        name="users",
    ),

    path(
        "sessions/",
        views.visit_sessions,
        name="sessions",
    ),

    path(
        "logins/",
        views.login_events,
        name="logins",
    ),

    path(
        "client-context/",
        views.client_context,
        name="client_context",
    ),
]