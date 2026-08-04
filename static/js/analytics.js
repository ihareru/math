(function () {
    "use strict";

    if (!document.body.dataset.authenticatedUser) {
        return;
    }

    const storageKey = "mathGameAnalyticsContextSent";

    if (sessionStorage.getItem(storageKey) === "1") {
        return;
    }

    function getCookie(name) {
        const cookies = document.cookie
            ? document.cookie.split(";")
            : [];

        for (const rawCookie of cookies) {
            const cookie = rawCookie.trim();

            if (
                cookie.startsWith(
                    `${encodeURIComponent(name)}=`
                )
            ) {
                return decodeURIComponent(
                    cookie.substring(
                        name.length + 1
                    )
                );
            }
        }

        return "";
    }

    const timezone =
        Intl.DateTimeFormat()
            .resolvedOptions()
            .timeZone || "";

    const payload = {
        screen_width: window.screen.width,
        screen_height: window.screen.height,
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        pixel_ratio: window.devicePixelRatio || 1,
        language: navigator.language || "",
        timezone: timezone,
        touch_points: navigator.maxTouchPoints || 0,
        cpu_cores: navigator.hardwareConcurrency || null,
    };

    fetch("/analytics/client-context/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(payload),
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            sessionStorage.setItem(
                storageKey,
                "1"
            );
        })
        .catch(function (error) {
            console.debug(
                "Не удалось отправить параметры экрана:",
                error
            );
        });
})();