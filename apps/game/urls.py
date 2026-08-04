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
        "start/<str:mode>/",
        views.start,
        name="start",
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