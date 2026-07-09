$(document).ready(function() {

    const STAR = 0x2B50;

    const TEMPO = {
        "A": "Larghissimo (24 BPM and under)",
        "B": "Grave (25-45 BPM)",
        "C": "Lento (45-50 BPM)",
        "D": "Largo (50-55 BPM)",
        "E": "Larghetto (55-60 BPM)",
        "F": "Adagio (60-72 BPM)",
        "G": "Adagretto (72-80 BPM)",
        "H": "Andantino (80-84 BPM)",
        "I": "Andante (84-90 BPM)",
        "J": "Andante moderato (90-96 BPM)",
        "K": "Marcia moderato (83-85 BPM)",
        "L": "Moderato (96-108 BPM)",
        "M": "Allegro moderato (108-112 BPM)",
        "N": "Allegretto (112-120 BPM)",
        "O": "Allegro (120-128 BPM)",
        "P": "Vivace (132-144 BPM)",
        "Q": "Vivacissimo (144-160 BPM)",
        "R": "Allegrissimo (145-167 BPM)",
        "S": "Presto (168-200 BPM)",
        "T": "Prestissimo (200 BPM and over)"
    };

    const GENRE = {
        "B": "Blues",
        "C": "Country/Bluegrass",
        "D": "Dance/Electronica",
        "F": "Formal/Classical",
        "I": "Industrial/Post-Rock",
        "J": "Jazz",
        "M": "Musical/Soundtrack",
        "P": "Pop/Rock",
        "R": "Reggae/Soca/Calypso",
        "S": "Soul/R&B",
        "T": "Traditional/Folk/Roots"
    };

    const CONTROLS = {
        "B": "Scroll Back One Page",
        "E": "Edit Text Fields",
        "G": "Select Genre",
        "I": "Select Instrument",
        "P": "Set/Clear Now Playing",
        "Q": "Quit and Load a New Document",
        "R": "Refresh Current Document",
        "U": "Upload New Document",
        "X": "Edit Current Document",
        "T": "Scroll to Top of Document",
        "?": "Help"
    };

    const INSTRUMENT = {
        "1": "House Piano",
        "2": "Steinway Piano",
        "3": "Bosendorfer Piano",
        "4": "Yamaha Piano",
        "5": "Classical Piano",
        "6": "Latin Piano",
        "7": "Gag Piano",
        "C": "Celesta",
        "D": "Diamond Electric Piano",
        "E": "Electric Piano",
        "F": "Funky Clavichord",
        "G": "Glockenspiel",
        "H": "Harpsichord",
        "O": "Organ",
        "R": "Rock Harpsichord",
        "V": "Vibrophone",
        "W": "Wurlitzer",
        "X": "Xylophone"
    };

    const TEXTFIELDS = {
        "T": "Title",
        "0": "Contributor",
        "1": "Author",
        "2": "Songwriter",
        "3": "Artist",
        "4": "Composer",
        "5": "Lyricist",
        "6": "Production",
        "7": "Album",
        "8": "Year",
        "9": "Comment"
    };

    codex = {
        editor: null,
        uploaderEditor: null,
        createCodeMirror: function(textareaId) {
            if (typeof CodeMirror === "undefined") {
                return null;
            }
            const host = document.getElementById(textareaId);
            if (!host) {
                return null;
            }
            const instance = CodeMirror.fromTextArea(host, {
                lineNumbers: true,
                lineWrapping: false,
                keyMap: "emacs",
                indentUnit: 4,
                tabSize: 4,
                autofocus: false,
                viewportMargin: Infinity,
                extraKeys: {
                    "Ctrl-S": function() {
                        if (textareaId === "editorText") {
                            codex.saveEditor();
                        } else {
                            codex.uploadNewFile();
                        }
                    },
                    "Esc": function(cm) {
                        cm.getInputField().blur();
                        codex.closeEditor();
                        codex.closeUploader();
                    }
                }
            });
            return instance;
        },
        ensureEditor: function() {
            if (!codex.editor) {
                codex.editor = codex.createCodeMirror("editorText");
            }
            return codex.editor;
        },
        ensureUploaderEditor: function() {
            if (!codex.uploaderEditor) {
                codex.uploaderEditor = codex.createCodeMirror("uploadText");
            }
            return codex.uploaderEditor;
        },
        isOverlayOpen: function() {
            return $("#editorPanel").is(":visible") || $("#uploadPanel").is(":visible");
        },
        openEditor: function() {
            const fileToken = $("#fileToken").val();
            if (!fileToken) {
                alert("No file selected to edit.");
                return;
            }
            const editor = codex.ensureEditor();
            if (editor) {
                editor.setValue($("#rawDocument").val());
            } else {
                $("#editorText").val($("#rawDocument").val());
            }
            $("#editorPanel").css("display", "block");
            if (editor) {
                editor.refresh();
                editor.focus();
            } else {
                $("#editorText").trigger("focus");
            }
        },
        closeEditor: function() {
            $("#editorPanel").css("display", "none");
            $("#container").trigger("focus");
        },
        saveEditor: function() {
            const fileToken = $("#fileToken").val();
            const editor = codex.ensureEditor();
            const content = editor ? editor.getValue() : $("#editorText").val();
            $.ajax({
                data: {
                    action: "savecontent",
                    file_token: fileToken,
                    content: content
                },
                success: function(resp) {
                    if (!resp || !resp.success) {
                        alert((resp && resp.information) || "Save failed.");
                        return;
                    }
                    $("#rawDocument").val(content);
                    $("#editorPanel").css("display", "none");
                    window.location.reload();
                }
            });
        },
        openUploader: function() {
            $("#uploadPanel").css("display", "block");
            const uploader = codex.ensureUploaderEditor();
            if ($("#newMode").val() === "1") {
                if (uploader) {
                    uploader.setValue($("#rawDocument").val());
                } else {
                    $("#uploadText").val($("#rawDocument").val());
                }
            }
            if (uploader) {
                uploader.refresh();
            }
            $("#uploadFilename").trigger("focus");
        },
        closeUploader: function() {
            $("#uploadPanel").css("display", "none");
            $("#container").trigger("focus");
        },
        uploadNewFile: function() {
            const filename = $("#uploadFilename").val().trim();
            const uploader = codex.ensureUploaderEditor();
            const content = uploader ? uploader.getValue() : $("#uploadText").val();
            if (!filename) {
                alert("Filename is required.");
                return;
            }
            $.ajax({
                data: {
                    action: "uploadfile",
                    filename: filename,
                    content: content
                },
                success: function(resp) {
                    if (!resp || !resp.success) {
                        alert((resp && resp.information) || "Upload failed.");
                        return;
                    }
                    const nextUrl = "index.wsgi?function=view&file_token=" + encodeURIComponent(resp.file_token || "");
                    window.location.href = nextUrl;
                }
            });
        },
        screenKeyHandler: function(event) {
            if (codex.isOverlayOpen()) {
                if (event.which === 27) {
                    codex.closeEditor();
                    codex.closeUploader();
                }
                return;
            }

            if ($("#togglebar").css("display") === "block") {
                if ($("#selectionTitle").html() === "genre") {
                    if (event.which >= 65 && event.which <= 90) {
                        const letter = String.fromCharCode(event.which);
                        Object.entries(GENRE).forEach(entry => {
                            if (letter === entry[0]) {
                                codex.setField("Genre", entry[1]);
                                $("#togglebar").css("display", "none");
                                $("#container").trigger("focus");
                            }
                        });
                    } else if (event.which === 27 || event.which === 32 || event.which === 13) {
                        $("#togglebar").css("display", "none");
                        $("#container").trigger("focus");
                    }
                } else if ($("#selectionTitle").html() === "tempo") {
                    if (event.which >= 65 && event.which <= 90) {
                        const letter = String.fromCharCode(event.which);
                        Object.entries(TEMPO).forEach(entry => {
                            if (letter === entry[0]) {
                                codex.setField("Tempo", entry[1]);
                                $("#togglebar").css("display", "none");
                                $("#container").trigger("focus");
                            }
                        });
                    } else if (event.which === 27 || event.which === 32 || event.which === 13) {
                        $("#togglebar").css("display", "none");
                        $("#container").trigger("focus");
                    }
                } else if ($("#selectionTitle").html() === "instrument") {
                    if ((event.which >= 65 && event.which <= 90) || (event.which >= 48 && event.which <= 57)) {
                        const letter = String.fromCharCode(event.which);
                        Object.entries(INSTRUMENT).forEach(entry => {
                            if (letter === entry[0]) {
                                codex.setField("Instrument", entry[1]);
                                $("#togglebar").css("display", "none");
                                $("#container").trigger("focus");
                            }
                        });
                    } else if (event.which === 27 || event.which === 32 || event.which === 13) {
                        $("#togglebar").css("display", "none");
                        $("#container").trigger("focus");
                    }
                } else if ($("#selectionTitle").html() === "textfields") {
                    if (event.which >= 48 && event.which <= 57) {
                        const keynum = event.which - 48;
                        Object.entries(TEXTFIELDS).forEach(entry => {
                            if (String(keynum) === entry[0]) {
                                codex.editTextField(entry[1]);
                            }
                        });
                    } else if (event.which === 84) {
                        codex.editTextField("Title");
                    } else if (event.which === 27 || event.which === 32 || event.which === 13) {
                        $("#togglebar").css("display", "none");
                        $("#container").trigger("focus");
                    }
                } else if ($("#selectionTitle").html() === "controls") {
                    $("#togglebar").css("display", "none");
                    $("#container").trigger("focus");
                }
                return;
            }

            if (event.which >= 48 && event.which <= 57) {
                const rating = event.which > 48 ? event.which - 48 : 10;
                codex.setRating(rating);
                return;
            }

            if (event.which === 191) {
                $("html, body").animate({ scrollTop: 50 }, 50);
                codex.populateToggleBar(CONTROLS, "controls");
                $("#togglebar").css("display", "block");
                return;
            }

            if (event.which >= 65 && event.which <= 90) {
                const eventLetter = String.fromCharCode(event.which);
                if (eventLetter === "G") {
                    $("html, body").animate({ scrollTop: 50 }, 50);
                    codex.populateToggleBar(GENRE, "genre");
                    $("#togglebar").css("display", "block");
                }
                if (eventLetter === "I") {
                    $("html, body").animate({ scrollTop: 50 }, 50);
                    codex.populateToggleBar(INSTRUMENT, "instrument");
                    $("#togglebar").css("display", "block");
                }
                if (eventLetter === "E") {
                    $("html, body").animate({ scrollTop: 50 }, 50);
                    codex.populateToggleBar(TEXTFIELDS, "textfields");
                    $("#togglebar").css("display", "block");
                }
                if (eventLetter === "P") {
                    const fileToken = $("#fileToken").val();
                    const isActive = $("#isNowPlaying").val() === "1";
                    const npAction = isActive ? "clearnowplaying" : "setnowplaying";
                    $.ajax({
                        url: "index.wsgi?function=ajax&action=" + npAction,
                        type: "POST",
                        data: { file_token: fileToken },
                        success: function() {
                            if (!isActive) {
                                $("#nowPlayingIndicator").addClass("active").html("\u266B now playing");
                                $("#isNowPlaying").val("1");
                            } else {
                                $("#nowPlayingIndicator").removeClass("active").html("");
                                $("#isNowPlaying").val("");
                            }
                        }
                    });
                }
                if (eventLetter === "Q") {
                    const fileToken = $("#fileToken").val();
                    const loadTime = $("#loadTimestamp").val();
                    const filterQ = $("#filterQ").val();
                    const filterField = $("#filterField").val();
                    let nextUrl = "index.wsgi?function=view";
                    if (filterQ) {
                        nextUrl += "&filter_q=" + encodeURIComponent(filterQ) + "&filter_field=" + encodeURIComponent(filterField);
                    }
                    $.ajax({
                        url: "index.wsgi?function=ajax&action=incrementcount",
                        type: "POST",
                        data: { file_token: fileToken, loadtime: loadTime },
                        success: function() {
                            $.ajax({
                                url: "index.wsgi?function=ajax&action=clearnowplaying",
                                type: "POST",
                                complete: function() { window.location.href = nextUrl; }
                            });
                        },
                        error: function() { window.location.href = nextUrl; }
                    });
                }
                if (eventLetter === "B") {
                    const n = $(window).scrollTop() - $(window).height() - 100;
                    $("html, body").animate({ scrollTop: n }, 50);
                }
                if (eventLetter === "R") {
                    const fileToken = $("#fileToken").val();
                    const filterQ = $("#filterQ").val();
                    const filterField = $("#filterField").val();
                    let refreshUrl = "index.wsgi?function=view&file_token=" + encodeURIComponent(fileToken);
                    if (filterQ) {
                        refreshUrl += "&filter_q=" + encodeURIComponent(filterQ) + "&filter_field=" + encodeURIComponent(filterField);
                    }
                    window.location.href = refreshUrl;
                }
                if (eventLetter === "U") {
                    codex.openUploader();
                }
                if (eventLetter === "X") {
                    codex.openEditor();
                }
                if (eventLetter === "T") {
                    $("html, body").animate({ scrollTop: 50 }, 50);
                    codex.populateToggleBar(TEMPO, "tempo");
                    $("#togglebar").css("display", "block");
                }
                return;
            }

            if (event.which === 32 || event.which === 13) {
                event.preventDefault();
                if ($(window).height() + $(window).scrollTop() >= $(document).height()) {
                    $("html, body").animate({ scrollTop: 50 }, 50);
                } else {
                    const n = $(window).scrollTop() + $(window).height() - 100;
                    $("html, body").animate({ scrollTop: n }, 50);
                }
            } else if (event.which === 187) {
                const f = parseInt($("#document").css("font-size").split("px")[0], 10);
                $("#document").css("font-size", (f + 2) + "px");
            } else if (event.which === 189) {
                const f = parseInt($("#document").css("font-size").split("px")[0], 10);
                $("#document").css("font-size", (f - 2) + "px");
            }
        },
        editTextField: function(textfield) {
            $("#togglebar").empty();
            const fieldValue = $("#" + textfield.toLowerCase() + "Value").html();
            $("#togglebar").append(
                $("<h1 />").attr("id", "selectionTitle").html(textfield).append(
                    $("<form />").append(
                        $("<input />")
                            .attr("value", fieldValue)
                            .attr("type", "text")
                            .attr("id", textfield.toLowerCase() + "Input")
                            .attr("name", textfield.toLowerCase()),
                        $("<input />").attr("type", "hidden").attr("name", "action")
                    )
                        .on("submit", function(event) {
                            event.preventDefault();
                        })
                        .on("keyup", function(event) {
                            if (event.which === 13) {
                                event.preventDefault();
                                const newValue = $("#" + textfield.toLowerCase() + "Input").val();
                                codex.setField(textfield, newValue);
                                $("#togglebar").css("display", "none");
                                $("#container").trigger("focus");
                            } else if (event.which === 27) {
                                event.preventDefault();
                                $("#togglebar").css("display", "none");
                                $("#container").trigger("focus");
                            }
                        })
                )
            );
            $("#" + textfield.toLowerCase() + "Input").trigger("focus");
        },
        populateToggleBar: function(selections, type) {
            $("#togglebar").empty();
            $("#togglebar").append(
                $("<h1 />").attr("id", "selectionTitle").html(type),
                $("<table/>").attr("id", "selectionTable")
            );

            Object.entries(selections).forEach(entry => {
                $("#selectionTable").append(
                    $("<tr/>").addClass("selection").append(
                        $("<td/>").addClass("selectionTag").html(entry[0]),
                        $("<td/>").addClass("selectionName").html(entry[1])
                    )
                );
            });
        },
        setRating: function(rating) {
            const fileToken = $("#fileToken").val();
            const codeString = "action=rating&file_token=" + encodeURIComponent(fileToken) + "&rating=" + rating;
            const star = String.fromCodePoint(STAR);
            $.ajax({
                data: codeString,
                success: function() {
                    $("#rating").html(star.repeat(rating));
                }
            });
        },
        setField: function(textfield, fieldvalue) {
            const fileToken = $("#fileToken").val();
            const key = textfield.toLowerCase();
            const codeString = "action=" + key + "&file_token=" + encodeURIComponent(fileToken) + "&" + key + "=" + encodeURIComponent(fieldvalue);
            $.ajax({
                data: codeString,
                success: function() {
                    $("#" + key + "Value").html(fieldvalue);
                    $("#" + key + "Label").html(textfield + ": ");
                    $("#" + key).css("display", "block");
                }
            });
        },
        init: function() {
            $.ajaxSetup({
                type: "POST",
                url: "index.wsgi?function=ajax",
                dataType: "json",
                cache: false,
                timeout: (60 * 1000),
                error: function(jqXHR, textStatus) {
                    if (textStatus === "timeout") {
                        alert("Please try again.");
                    }
                }
            });

            const fileToken = $("#fileToken").val();
            const filterQ = $("#filterQ").val();
            const filterField = $("#filterField").val();
            let historyUrl = "index.wsgi?function=view&file_token=" + encodeURIComponent(fileToken);
            if (filterQ) {
                historyUrl += "&filter_q=" + encodeURIComponent(filterQ) + "&filter_field=" + encodeURIComponent(filterField);
            }
            window.history.pushState({ id: "100" }, null, historyUrl);

            $("#editorSave").on("click", codex.saveEditor);
            $("#editorCancel").on("click", codex.closeEditor);
            $("#uploadSave").on("click", codex.uploadNewFile);
            $("#uploadCancel").on("click", codex.closeUploader);

            $("#editorText, #uploadText, #uploadFilename").on("keydown", function(event) {
                if (event.key === "Escape") {
                    event.preventDefault();
                    codex.closeEditor();
                    codex.closeUploader();
                }
            });

            if ($("#newMode").val() === "1") {
                codex.openUploader();
            }

            $("#container").on("keydown", function(event) {
                const tagName = (event.target && event.target.tagName) ? event.target.tagName.toUpperCase() : "";
                if (tagName === "INPUT" || tagName === "TEXTAREA") {
                    return;
                }
                event.preventDefault();
                codex.screenKeyHandler(event);
            });
            $("html, body").animate({ scrollTop: 50 }, 50);
            $("#container").trigger("focus");
        }
    };
    codex.init();
});
