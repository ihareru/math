(function () {
    "use strict";

    const body = document.body;

    if (!body) {
        return;
    }

    const backgroundMusic = document.getElementById(
        "background-music"
    );

    const successSound = document.getElementById(
        "success-sound"
    );

    const failSound = document.getElementById(
        "fail-sound"
    );

    function isEnabled(value) {
    return String(value).trim() === "1";
}

    function normalizeVolume(value, fallback = 50) {
        const numberValue = Number(value);

        if (Number.isNaN(numberValue)) {
            return fallback / 100;
        }

        const limitedValue = Math.min(
            100,
            Math.max(0, numberValue)
        );

        return limitedValue / 100;
    }

    const configuration = {
        backgroundMusicEnabled: isEnabled(
            body.dataset.backgroundMusicEnabled
        ),

        successSoundEnabled: isEnabled(
            body.dataset.successSoundEnabled
        ),

        failSoundEnabled: isEnabled(
            body.dataset.failSoundEnabled
        ),

        backgroundVolume: normalizeVolume(
            body.dataset.backgroundVolume
        ),

        successVolume: normalizeVolume(
            body.dataset.successVolume
        ),

        failVolume: normalizeVolume(
            body.dataset.failVolume
        ),
    };
    
    console.log(
        "Math Game audio configuration:",
        configuration
    );

    if (backgroundMusic) {
        backgroundMusic.volume =
            configuration.backgroundVolume;
    }

    if (successSound) {
        successSound.volume =
            configuration.successVolume;
    }

    if (failSound) {
        failSound.volume =
            configuration.failVolume;
    }

    async function playAudio(audioElement) {
        if (!audioElement) {
            return;
        }

        try {
            audioElement.currentTime = 0;
            await audioElement.play();
        } catch (error) {
            console.debug(
                "Браузер заблокировал воспроизведение звука:",
                error
            );
        }
    }

    function stopAudio(audioElement) {
        if (!audioElement) {
            return;
        }

        audioElement.pause();
        audioElement.currentTime = 0;
    }

    async function startBackgroundMusic() {
        if (
            !configuration.backgroundMusicEnabled
            || !backgroundMusic
        ) {
            return;
        }

        try {
            await backgroundMusic.play();
        } catch (error) {
            /*
             * Современные браузеры обычно запрещают
             * автоматический запуск музыки до первого
             * взаимодействия пользователя со страницей.
             */
        }
    }

    function unlockBackgroundMusic() {
        if (!configuration.backgroundMusicEnabled) {
            return;
        }

        startBackgroundMusic();
    }

    if (configuration.backgroundMusicEnabled) {
        startBackgroundMusic();

        document.addEventListener(
            "click",
            unlockBackgroundMusic,
            { once: true }
        );

        document.addEventListener(
            "keydown",
            unlockBackgroundMusic,
            { once: true }
        );

        document.addEventListener(
            "touchstart",
            unlockBackgroundMusic,
            {
                once: true,
                passive: true,
            }
        );
    } else {
        stopAudio(backgroundMusic);
    }

    window.MathGameAudio = {
        playSuccess: function () {
            if (!configuration.successSoundEnabled) {
                return;
            }

            playAudio(successSound);
        },

        playFail: function () {
            if (!configuration.failSoundEnabled) {
                return;
            }

            playAudio(failSound);
        },

        startBackground: function () {
            startBackgroundMusic();
        },

        stopBackground: function () {
            stopAudio(backgroundMusic);
        },

        configuration: configuration,
    };
})();