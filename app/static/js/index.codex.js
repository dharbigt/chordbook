$(document).ready(function() {
    function updateQueryControl() {
        const field = $("#fieldSelect").val();

        $("#queryText").hide();
        $("#queryGenre").hide();
        $("#queryTempo").hide();

        if (field === "genre") {
            $("#queryGenre").show();
            $("#queryValue").val($("#queryGenre").val() || "");
            return;
        }

        if (field === "tempo") {
            $("#queryTempo").show();
            $("#queryValue").val($("#queryTempo").val() || "");
            return;
        }

        $("#queryText").show();
        $("#queryValue").val($("#queryText").val() || "");
    }

    $("#fieldSelect").on("change", function() {
        updateQueryControl();
    });

    $("#queryText").on("input", function() {
        $("#queryValue").val($(this).val());
    });

    $("#queryGenre").on("change", function() {
        $("#queryValue").val($(this).val());
    });

    $("#queryTempo").on("change", function() {
        $("#queryValue").val($(this).val());
    });

    $("#searchForm").on("submit", function() {
        updateQueryControl();
    });

    updateQueryControl();
});
