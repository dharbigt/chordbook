$(document).ready(function() {
    codex = {
        init: function() {
            $.ajaxSetup({
                type: "POST",
                url: "index.wsgi",
                dataType: "json",
                cache: false,
                timeout: (60 * 1000),
                error: function(jqXHR, textStatus) {
                    if (textStatus === "timeout") alert("Please try again.");
                }
            });
        }
    };
    codex.init();
});
