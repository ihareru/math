from django.urls import path

from . import views


app_name = "cheats"


urlpatterns = [
    path(
        "",
        views.cheat_codes,
        name="codes",
    ),
    path(
        "activate/",
        views.activate,
        name="activate",
    ),
]