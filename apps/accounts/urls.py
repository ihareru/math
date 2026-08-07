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
        "register/resume/",
        views.resume_registration,
        name="resume_registration",
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

    path(
        "password-reset/",
        views.password_reset_request,
        name="password_reset_request",
    ),
    path(
        "password-reset/verify/",
        views.password_reset_verify,
        name="password_reset_verify",
    ),
    path(
        "password-reset/resend/",
        views.password_reset_resend,
        name="password_reset_resend",
    ),
    path(
        "password-reset/confirm/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),

    path(
        "account/",
        views.account_detail,
        name="account_detail",
    ),
    path(
        "account/edit/",
        views.account_edit,
        name="account_edit",
    ),
]