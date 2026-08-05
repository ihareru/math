(function () {
    "use strict";

    const dialog = document.getElementById(
        "secret-code-dialog"
    );

    const input = document.getElementById(
        "secret-code-input"
    );

    if (!dialog || !input) {
        return;
    }

    const closeButtons = dialog.querySelectorAll(
        "[data-secret-code-close]"
    );

    let previousActiveElement = null;

    function openDialog() {
        if (!dialog.hidden) {
            return;
        }

        previousActiveElement = document.activeElement;

        dialog.hidden = false;
        document.body.classList.add(
            "modal-open"
        );

        window.setTimeout(function () {
            input.focus();
        }, 0);
    }

    function closeDialog() {
        if (dialog.hidden) {
            return;
        }

        dialog.hidden = true;
        document.body.classList.remove(
            "modal-open"
        );

        input.value = "";

        if (
            previousActiveElement
            && typeof previousActiveElement.focus
                === "function"
        ) {
            previousActiveElement.focus();
        }
    }

    document.addEventListener(
        "keydown",
        function (event) {
            const pressedSecretCombination = (
                event.ctrlKey
                && event.shiftKey
                && event.code === "KeyC"
            );

            if (pressedSecretCombination) {
                event.preventDefault();
                openDialog();
                return;
            }

            if (
                event.key === "Escape"
                && !dialog.hidden
            ) {
                event.preventDefault();
                closeDialog();
            }
        }
    );

    closeButtons.forEach(function (button) {
        button.addEventListener(
            "click",
            closeDialog
        );
    });
})();