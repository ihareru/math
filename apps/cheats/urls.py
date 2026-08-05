from django.urls import path

from . import views


app_name = "cheats"


urlpatterns = [
    # Пользовательская часть
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

    # Административная часть
    path(
        "admin/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
    path(
        "admin/codes/",
        views.admin_code_list,
        name="admin_code_list",
    ),
    path(
        "admin/codes/create/",
        views.admin_code_create,
        name="admin_code_create",
    ),
    path(
        "admin/codes/<int:code_id>/edit/",
        views.admin_code_edit,
        name="admin_code_edit",
    ),
    path(
        "admin/codes/<int:code_id>/toggle/",
        views.admin_code_toggle,
        name="admin_code_toggle",
    ),
    path(
        "admin/codes/<int:code_id>/activations/",
        views.admin_code_activations,
        name="admin_code_activations",
    ),
    path(
        "admin/activations/",
        views.admin_activation_list,
        name="admin_activation_list",
    ),
    path(
        (
            "admin/activations/"
            "<int:activation_id>/disable/"
        ),
        views.admin_activation_disable,
        name="admin_activation_disable",
    ),
]