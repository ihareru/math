from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path(
        "register/",
        views.register,
        name="register",
    ),
    path(
        "verify/",
        views.verify_registration,
        name="verify_registration",
    ),
    path(
        "verify/resend/",
        views.resend_registration_code,
        name="resend_registration_code",
    ),
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
]