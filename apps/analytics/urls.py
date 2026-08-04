from django.urls import path

from . import views


app_name = "analytics"


urlpatterns = [
    path(
        "client-context/",
        views.client_context,
        name="client_context",
    ),
]