(function () {
    "use strict";

    const body = document.body;

    if (!body) {
        return;
    }

    // Только для авторизованных пользователей
    if (body.dataset.authenticatedUser !== "1") {
        return;
    }

    // URL обработчика
    const analyticsUrl = body.dataset.analyticsUrl;

    if (!analyticsUrl) {
        console.error("Analytics URL не задан.");
        return;
    }

    const storageKey = "mathGameAnalyticsContextSent";

    // Уже отправляли в этой вкладке
    if (sessionStorage.getItem(storageKey) === "1") {
        return;
    }

    /**
     * Получение cookie
     */
    function getCookie(name) {

        const cookies = document.cookie
            ? document.cookie.split(";")
            : [];

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                return decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
            }
        }

        return "";
    }

    const csrfToken = getCookie("csrftoken");

    if (!csrfToken) {
        console.error("CSRF cookie не найдена.");
        return;
    }

    let timezone = "";

    try {
        timezone = Intl.DateTimeFormat()
            .resolvedOptions()
            .timeZone || "";
    }
    catch (e) {
        timezone = "";
    }

    const payload = {

        screen_width: window.screen.width,

        screen_height: window.screen.height,

        viewport_width: window.innerWidth,

        viewport_height: window.innerHeight,

        pixel_ratio: window.devicePixelRatio || 1,

        language: navigator.language || "",

        timezone: timezone,

        touch_points: navigator.maxTouchPoints || 0,

        cpu_cores: navigator.hardwareConcurrency || null

    };

    fetch(analyticsUrl, {

        method: "POST",

        credentials: "same-origin",

        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },

        body: JSON.stringify(payload)

    })
        .then(function (response) {

            if (!response.ok) {
                throw new Error("HTTP " + response.status);
            }

            return response.json();

        })
        .then(function (data) {

            if (!data.ok) {
                throw new Error(data.error || "Ошибка сервера");
            }

            sessionStorage.setItem(storageKey, "1");

            console.log("✓ Параметры браузера успешно сохранены.");

        })
        .catch(function (error) {

            console.error(
                "Ошибка отправки аналитики:",
                error
            );

        });

})();