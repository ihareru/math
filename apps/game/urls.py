from django.urls import path

from . import views


app_name = "game"


urlpatterns = [
    path(
        "",
        views.mode_select,
        name="mode_select",
    ),
    path(
        "settings/",
        views.generation_settings,
        name="generation_settings",
    ),
    path(
        "settings/profile/",
        views.apply_generation_profile,
        name="apply_generation_profile",
    ),
    path(
        "statistics/",
        views.statistics_dashboard,
        name="statistics",
    ),
    path(
        "sessions/",
        views.session_list,
        name="session_list",
    ),
    path(
        "sessions/<int:session_id>/",
        views.session_detail,
        name="session_detail",
    ),
    path(
        "start/<str:mode>/",
        views.start,
        name="start",
    ),
    path(
        "review/start/",
        views.start_review,
        name="start_review",
    ),
    path(
        "play/",
        views.play,
        name="play",
    ),
    path(
        "questions/<int:question_id>/answer/",
        views.answer,
        name="answer",
    ),
    path(
        "questions/<int:question_id>/result/",
        views.question_result,
        name="question_result",
    ),
    path(
        "next/",
        views.next_question,
        name="next_question",
    ),
    path(
        "finish/",
        views.finish,
        name="finish",
    ),
    path(
        "history/",
        views.history,
        name="history",
    ),
]