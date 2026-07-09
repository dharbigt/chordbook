$(document).ready(function() {
    nyx = {
        submitLoginForm: function() {
            const form = document.getElementById("form-login");
            if (!form) {
                return;
            }
            // requestSubmit triggers native submit semantics on modern browsers.
            if (typeof form.requestSubmit === "function") {
                form.requestSubmit();
                return;
            }
            form.submit();
        },
        screenKeyHandler: function(event) {
            if (event.key === "Enter" || event.which === 13 || event.keyCode === 13) {
                event.preventDefault();
                nyx.submitLoginForm();
            }
        },
        init: function() {
            $("#input-password").on("keydown", function(event) {
                nyx.screenKeyHandler(event);
            });
            $("#input-name").on("keydown", function(event) {
                nyx.screenKeyHandler(event);
            });
            $("#form-login").on("submit", function() {
                return true;
            });
        }
    };
    nyx.init();
});
