document.addEventListener(
    "DOMContentLoaded",
    function () {
        "use strict";

        const body = document.body;

        const colorInput = document.getElementById(
            "id_background_color"
        );

        const backgroundSelect = document.getElementById(
            "id_background_image"
        );

        const ranges = [
            {
                inputId: "id_background_volume",
                outputId: "background-volume-value",
                audioId: "background-music",
            },
            {
                inputId: "id_success_volume",
                outputId: "success-volume-value",
                audioId: "success-sound",
            },
            {
                inputId: "id_fail_volume",
                outputId: "fail-volume-value",
                audioId: "fail-sound",
            },
        ];

        if (colorInput) {
            colorInput.addEventListener(
                "input",
                function () {
                    body.style.setProperty(
                        "--user-background-color",
                        colorInput.value
                    );
                }
            );
        }

        if (backgroundSelect) {
            backgroundSelect.addEventListener(
                "change",
                function () {
                    const filename =
                        backgroundSelect.value;

                    if (!filename) {
                        body.style.setProperty(
                            "--user-background-image",
                            "none"
                        );

                        body.classList.remove(
                            "site-body--has-background"
                        );

                        return;
                    }

                    const encodedFilename =
                        filename
                            .split("/")
                            .map(encodeURIComponent)
                            .join("/");

                    body.style.setProperty(
                        "--user-background-image",
                        `url("/static/backgrounds/${encodedFilename}")`
                    );

                    body.classList.add(
                        "site-body--has-background"
                    );
                }
            );
        }

        ranges.forEach(function (item) {
            const input = document.getElementById(
                item.inputId
            );

            const output = document.getElementById(
                item.outputId
            );

            const audio = document.getElementById(
                item.audioId
            );

            if (!input) {
                return;
            }

            function updateValue() {
                const value = Number(input.value);

                if (output) {
                    output.value = value;
                    output.textContent = value;
                }

                if (audio) {
                    audio.volume = Math.min(
                        1,
                        Math.max(0, value / 100)
                    );
                }
            }

            input.addEventListener(
                "input",
                updateValue
            );

            updateValue();
        });
    }
);