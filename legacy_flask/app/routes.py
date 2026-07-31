from app import app
from flask import render_template, session, redirect, request, url_for
import os
from app.settings_manager import load_settings, save_settings
from app.profiles_manager import load_profiles, save_profiles
from app.math_generator import generate_example
import smtplib
from email.mime.text import MIMEText
from flask import current_app


@app.route("/")
def index():

    session.setdefault("streak", 0)

    message = session.pop("message", "")

    return render_template(
        "index.html",
        message=message
    )


@app.route("/select/<mode>")
def select(mode):
    session["mode"] = mode
    return redirect(url_for("game"))


@app.route("/game")
def game():

    example = generate_example(session["mode"])

    session["answer"] = example["answer"]

    message = session.pop("message", "")
    success = session.pop("success", None)
    profile_stars = 0
    profile_correct = 0
    profile_wrong = 0

    if "profile_index" in session:

        profiles = load_profiles()
        index = session["profile_index"]

        if 0 <= index < len(profiles):

            profile = profiles[index]

            profile_stars = profile["stars"]
            profile_correct = profile["correct"]
            profile_wrong = profile["wrong"]

    return render_template(
        "game.html",
        title=example["title"],
        num1=example["num1"],
        num2=example["num2"],
        operation=example["operation"],
        correct=profile_correct,
        wrong=profile_wrong,
        stars=profile_stars,
        streak=session["streak"],
        message=message,
        success=success
    )


@app.route("/check", methods=["POST"])
def check():

    user_answer = int(request.form["answer"])

    profiles = load_profiles()

    current_profile = None

    if "profile_index" in session:

        index = session["profile_index"]

        if 0 <= index < len(profiles):
            current_profile = profiles[index]

    if user_answer == session["answer"]:

        session["streak"] += 1
        session["message"] = "🎉 Молодец!"
        session["success"] = True

        if current_profile:
            current_profile["correct"] += 1
        
            # каждые 10 подряд = звезда
            if session["streak"] % 10 == 0:
                current_profile["stars"] += 1

            # рекорд серии
            if session["streak"] > current_profile["record"]:
                current_profile["record"] = session["streak"]

    else:

        session["streak"] = 0

        session["message"] = "🙂 Попробуй ещё"
        session["success"] = False

        if current_profile:
            current_profile["wrong"] += 1

    save_profiles(profiles)

    return redirect(url_for("game"))


@app.route("/settings")
def settings():

    settings = load_settings()

    os.makedirs("backgrounds", exist_ok=True)

    images = os.listdir("app/static/backgrounds")

    return render_template(
        "settings.html",
        settings=settings,
        images=images
    )


@app.route("/save_settings", methods=["POST"])
def save_settings_route():

    settings = load_settings()

    settings["background_color"] = request.form["background_color"]
    settings["background_image"] = request.form["background_image"]

    settings["background_music"] = (
        "background_music" in request.form
    )

    settings["success_sound"] = (
        "success_sound" in request.form
    )

    settings["fail_sound"] = (
        "fail_sound" in request.form
    )

    settings["background_volume"] = int(
    request.form.get("background_volume", 50)
    )

    settings["success_volume"] = int(
        request.form.get("success_volume", 100)
    )

    settings["fail_volume"] = int(
        request.form.get("fail_volume", 100)
    )

    save_settings(settings)

    return redirect(url_for("settings"))


@app.route("/profiles")
def profiles():

    profiles = load_profiles()

    return render_template(
        "profiles.html",
        profiles=profiles
    )


@app.route("/add_profile", methods=["POST"])
def add_profile():

    profiles = load_profiles()

    profiles.append(
        {
            "name": request.form["name"],
            "stars": 0,
            "correct": 0,
            "wrong": 0,
            "record": 0
        }
    )

    save_profiles(profiles)

    return redirect(url_for("profiles"))


@app.route("/select_profile/<int:index>")
def select_profile(index):

    profiles = load_profiles()

    if 0 <= index < len(profiles):

        profile = profiles[index]

        session["profile_index"] = index

        # статистика профиля
        session["correct"] = profile["correct"]
        session["wrong"] = profile["wrong"]

        # серия всегда начинается заново
        session["streak"] = 0

    return redirect(url_for("index"))


@app.context_processor
def inject_profile():

    profiles = load_profiles()

    current = None

    if "profile_index" in session:

        index = session["profile_index"]

        if 0 <= index < len(profiles):
            current = profiles[index]

    return dict(current_profile=current)


@app.route("/delete_profile/<int:index>")
def delete_profile(index):

    profiles = load_profiles()

    if 0 <= index < len(profiles):
        profiles.pop(index)
        save_profiles(profiles)

    session.pop("profile_index", None)

    return redirect(url_for("profiles"))


@app.route("/statistics")
def statistics():

    profiles = load_profiles()

    stat = {
        "correct": 0,
        "wrong": 0,
        "record": 0,
        "stars": 0
    }

    if "profile_index" in session:

        index = session["profile_index"]

        if 0 <= index < len(profiles):
            stat = profiles[index]

    return render_template(
        "statistics.html",
        stat=stat
    )


@app.route("/reset_statistics")
def reset_statistics():

    session["streak"] = 0

    if "profile_index" in session:

        profiles = load_profiles()
        index = session["profile_index"]

        if 0 <= index < len(profiles):

            profiles[index]["correct"] = 0
            profiles[index]["wrong"] = 0
            profiles[index]["stars"] = 0
            profiles[index]["record"] = 0

            save_profiles(profiles)

    return redirect(url_for("statistics"))


@app.route("/feedback")
def feedback():
    return render_template("feedback.html")


@app.route("/send_feedback", methods=["POST"])
def send_feedback():

    name = request.form["name"]
    email = request.form.get("email", "")
    message = request.form["message"]

    body = f"""
Новое сообщение из Math Game

Имя: {name}

E-mail: {email}

Сообщение:
{message}
"""

    msg = MIMEText(body, "plain", "utf-8")

    msg["Subject"] = "Обратная связь Math Game"
    msg["From"] = current_app.config["SMTP_LOGIN"]
    msg["To"] = current_app.config["SUPPORT_EMAIL"]

    try:
        with smtplib.SMTP_SSL(
            current_app.config["SMTP_SERVER"],
            current_app.config["SMTP_PORT"]
        ) as server:

            server.login(
                current_app.config["SMTP_LOGIN"],
                current_app.config["SMTP_PASSWORD"]
            )

            server.send_message(msg)

        session["message"] = "✅ Спасибо! Ваше сообщение успешно отправлено."

    except Exception as e:
        print(e)
        session["message"] = "❌ Не удалось отправить сообщение. Попробуйте позже."

    return redirect(url_for("index"))
