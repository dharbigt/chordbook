# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import base64
from datetime import timedelta
import os
import time
from urllib.parse import urlparse

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .oauth import oauth
from .services.auth import AuthService
from .services.library import (
    EDITABLE_FIELDS,
    EXTRA_FIELDS,
    GENRE_OPTIONS,
    LibraryService,
    TEMPO_OPTIONS,
    TEXT_FIELDS,
)


main_bp = Blueprint("main", __name__)

# In-memory now-playing state (single entry; cleared on navigate-away or logout)
_now_playing: dict = {}


def _auth_service() -> AuthService:
    return AuthService(current_app.config["DB_PATH"])


def _library_service() -> LibraryService:
    return LibraryService(current_app.config["TEXT_DIR"])


def _load_user_from_request() -> dict | None:
    user = session.get("user")
    if user:
        return user

    token = request.cookies.get("token")
    if not token:
        return None

    record = _auth_service().load_user_by_token(token)
    if not record:
        return None

    user_data = {"user": record.user, "name": record.name, "token": record.token}
    session["user"] = user_data
    return user_data


def _is_safe_redirect_url(target: str) -> bool:
    if not target:
        return False
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        if parsed.netloc != request.host:
            return False
    if target.startswith("//"):
        return False
    return True


def _encode_file_token(filename: str) -> str:
    return base64.urlsafe_b64encode(os.fsencode(filename)).decode("ascii")


def _decode_file_token(token: str) -> str | None:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        return os.fsdecode(raw)
    except Exception:
        return None


def _get_requested_filename() -> str | None:
    token = request.values.get("file_token", "").strip()
    if token:
        return _decode_file_token(token)
    return request.values.get("file")


@main_bp.route("/login", methods=["GET"])
def login() -> Response | str:
    user = _load_user_from_request()
    if user:
        return redirect(url_for("main.dispatch", function="index"))
    return render_template(
        "login.html",
        title="Codex Login",
        user="",
        css_scripts=["css/style.css", "css/login.codex.css"],
        js_scripts=[],
        header_links=[],
    )


@main_bp.route("/login/google")
def login_google() -> Response:
    """Redirect to Google for login."""
    next_url = request.args.get("next")
    if next_url and _is_safe_redirect_url(next_url):
        session["login_next"] = next_url

    redirect_uri = current_app.config.get("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        preferred_scheme = current_app.config.get("PREFERRED_URL_SCHEME")
        url_kwargs: dict = {"_external": True}
        if preferred_scheme:
            url_kwargs["_scheme"] = preferred_scheme
        redirect_uri = url_for("main.authorize_google", **url_kwargs)

    current_app.logger.info("Google OAuth redirect_uri=%s", redirect_uri)
    return oauth.google.authorize_redirect(redirect_uri, prompt="select_account")


@main_bp.route("/authorize/google")
def authorize_google() -> Response:
    """Handle Google OAuth callback."""
    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo")

    if not user_info:
        return redirect(url_for("main.login"))

    record = _auth_service().find_or_create_by_google(
        google_id=user_info.get("sub", ""),
        email=user_info.get("email", ""),
        name=user_info.get("name", ""),
    )
    if not record:
        return redirect(url_for("main.login"))

    user = {"user": record.user, "name": record.name, "token": record.token}
    session["user"] = user
    session.permanent = True
    session_lifetime_days = current_app.config["PERMANENT_SESSION_LIFETIME_DAYS"]
    current_app.permanent_session_lifetime = timedelta(days=session_lifetime_days)

    next_url = session.pop("login_next", None)
    target = next_url if next_url else url_for("main.dispatch", function="index")
    resp = make_response(redirect(target))
    resp.set_cookie("token", record.token, max_age=60 * 60 * 24 * 30, httponly=True, samesite="Lax")
    return resp




@main_bp.route("/", methods=["GET"])
def landing() -> Response | str:
    user = _load_user_from_request()
    if user:
        return redirect(url_for("main.dispatch", function="index"))
    now_playing = _now_playing.get("song")
    return render_template(
        "blank.html",
        title="Codex",
        user="",
        css_scripts=["css/style.css", "css/landing.css"],
        js_scripts=[],
        header_links=[("Login", url_for("main.login"))],
        now_playing=now_playing,
    )


@main_bp.route("/index.wsgi", methods=["GET", "POST"])
@main_bp.route("/index.php", methods=["GET", "POST"])
def dispatch() -> Response | str:
    function = request.values.get("function", "view")
    action = request.values.get("action", "")

    if function == "logout":
        session.clear()
        _now_playing.clear()
        resp = make_response(redirect(url_for("main.landing")))
        resp.delete_cookie("token")
        return resp

    user = _load_user_from_request()

    if not user:
        return redirect(url_for("main.login"))

    if function == "sse":
        payload = f"event: ping\ndata: {{\"data\": \"ping\"}}\nid: {int(time.time())}\nretry: 10000\n\n"
        return Response(payload, mimetype="text/event-stream")

    if function == "ajax":
        return _handle_ajax(action, user)

    if function == "index":
        return _render_index(user)

    return _render_view(user)


def _render_index(user: dict) -> str:
    sort_by = request.args.get("sortby", "count").lower()
    order = request.args.get("order", "DESC").upper()
    if order not in {"ASC", "DESC"}:
        order = "DESC"

    try:
        min_count = int(request.args.get("count", -1))
    except ValueError:
        min_count = -1

    try:
        min_rating = int(request.args.get("rating", -1))
    except ValueError:
        min_rating = -1

    query = request.args.get("q", "").strip()
    query_field = request.args.get("field", "*").strip().lower() or "*"

    lib = _library_service()
    rows, fields, facets = lib.build_index_rows(
        sort_by=sort_by,
        order=order,
        min_count=min_count,
        min_rating=min_rating,
        query=query,
        query_field=query_field,
    )

    field_options = ["*"] + sorted(f for f in fields if f not in {"title", "count", "rating"})
    genre_options = [{"value": option, "count": facets["genre"].get(option, 0)} for option in GENRE_OPTIONS]
    genre_options.append({"value": "_unset", "count": facets["genre"].get("_unset", 0)})
    tempo_options = [{"value": option, "count": facets["tempo"].get(option, 0)} for option in TEMPO_OPTIONS]

    return render_template(
        "index.html",
        title="Codex - Index",
        user=user["name"],
        css_scripts=["css/style.css", "css/index.codex.css"],
        js_scripts=["js/default.codex.js", "js/index.codex.js"],
        header_links=[
            ("Upload", url_for("main.dispatch", function="view", new="1")),
            ("Random", url_for("main.dispatch", function="view")),
            ("Logout", url_for("main.dispatch", function="logout")),
        ],
        rows=rows,
        sort_by=sort_by,
        order=order,
        min_count=min_count,
        min_rating=min_rating,
        query=query,
        query_field=query_field,
        field_options=field_options,
        genre_options=genre_options,
        tempo_options=tempo_options,
    )


def _render_view(user: dict) -> str:
    filename = _get_requested_filename()
    new_mode = request.values.get("new", "").strip() == "1"
    filter_q = request.values.get("filter_q", "").strip()
    filter_field = request.values.get("filter_field", "").strip()
    lib = _library_service()
    if not filename and not new_mode:
        if filter_q and filter_field:
            filename = lib.get_random_filtered_file(filter_q, filter_field)
        else:
            filename = lib.get_random_file()

    if not filename and not new_mode:
        return render_template(
            "view.html",
            title="Codex - Empty",
            user=user["name"],
            css_scripts=["css/style.css", "vendor/codemirror/codemirror.min.css", "css/view.codex.css"],
            js_scripts=[
                "vendor/codemirror/codemirror.min.js",
                "vendor/codemirror/keymap/emacs.min.js",
                "vendor/codemirror/addon/search/searchcursor.js",
                "vendor/codemirror/addon/search/search.js",
                "js/view.codex.js",
            ],
            header_links=[
                ("Index", url_for("main.dispatch", function="index")),
                ("Random", url_for("main.dispatch", function="view")),
                ("Logout", url_for("main.dispatch", function="logout")),
            ],
            filename="",
            filename_token="",
            content="No files found.",
            raw_content="",
            header={},
            fields=TEXT_FIELDS + EXTRA_FIELDS,
            load_timestamp=int(time.time()),
            filter_q=filter_q,
            filter_field=filter_field,
            new_mode=False,
        )

    if new_mode and not filename:
        return render_template(
            "view.html",
            title="Codex - Upload",
            user=user["name"],
            css_scripts=["css/style.css", "vendor/codemirror/codemirror.min.css", "css/view.codex.css"],
            js_scripts=[
                "vendor/codemirror/codemirror.min.js",
                "vendor/codemirror/keymap/emacs.min.js",
                "vendor/codemirror/addon/search/searchcursor.js",
                "vendor/codemirror/addon/search/search.js",
                "js/view.codex.js",
            ],
            header_links=[
                ("Index", url_for("main.dispatch", function="index")),
                ("Random", url_for("main.dispatch", function="view")),
                ("Logout", url_for("main.dispatch", function="logout")),
            ],
            filename="",
            filename_token="",
            content="Press U to upload a new chord chart.",
            raw_content="",
            header={},
            fields=TEXT_FIELDS + EXTRA_FIELDS,
            load_timestamp=int(time.time()),
            filter_q="",
            filter_field="",
            is_now_playing=False,
            new_mode=True,
        )

    header = lib.parse_header(filename)
    raw_contents = lib.get_file_contents(filename)
    contents = lib.escape_text(raw_contents)
    is_now_playing = _now_playing.get("song", {}).get("filename") == filename

    return render_template(
        "view.html",
        title=f"Codex - {header.get('title', '')}",
        user=user["name"],
        css_scripts=["css/style.css", "vendor/codemirror/codemirror.min.css", "css/view.codex.css"],
        js_scripts=[
            "vendor/codemirror/codemirror.min.js",
            "vendor/codemirror/keymap/emacs.min.js",
            "vendor/codemirror/addon/search/searchcursor.js",
            "vendor/codemirror/addon/search/search.js",
            "js/view.codex.js",
        ],
        header_links=[
            ("Index", url_for("main.dispatch", function="index")),
            ("Random", url_for("main.dispatch", function="view")),
            ("Logout", url_for("main.dispatch", function="logout")),
        ],
        filename=filename,
        filename_token=_encode_file_token(filename),
        content=contents,
        raw_content=raw_contents,
        header=header,
        fields=TEXT_FIELDS + EXTRA_FIELDS,
        load_timestamp=int(time.time()),
        filter_q=filter_q,
        filter_field=filter_field,
        is_now_playing=is_now_playing,
        new_mode=False,
    )


def _handle_ajax(action: str, user: dict) -> Response:
    lib = _library_service()
    filename = _get_requested_filename() or ""
    max_song_bytes = int(current_app.config.get("MAX_SONG_BYTES", 512 * 1024))

    def _payload_too_large(value: str) -> bool:
        return len(value.encode("utf-8", errors="ignore")) > max_song_bytes

    if action == "savecontent" and filename:
        body = request.values.get("content", "")
        if _payload_too_large(body):
            return jsonify({"action": action, "success": False, "information": "Content exceeds size limit"})
        try:
            lib.save_file_content(filename, body)
        except (FileNotFoundError, ValueError) as exc:
            return jsonify({"action": action, "success": False, "information": str(exc)})
        current_app.logger.info(f"codex: {user['user']} updated content for {filename}")
        return jsonify({"action": action, "success": True, "information": "SUCCESS"})

    if action == "uploadfile":
        requested_name = request.values.get("filename", "")
        body = request.values.get("content", "")
        if _payload_too_large(body):
            return jsonify({"action": action, "success": False, "information": "Content exceeds size limit"})
        try:
            created_name = lib.create_file(requested_name, body)
        except (ValueError, FileExistsError) as exc:
            return jsonify({"action": action, "success": False, "information": str(exc)})
        current_app.logger.info(f"codex: {user['user']} uploaded {created_name}")
        return jsonify(
            {
                "action": action,
                "success": True,
                "information": "SUCCESS",
                "filename": created_name,
                "file_token": _encode_file_token(created_name),
            }
        )

    if action == "setnowplaying" and filename:
        header = lib.parse_header(filename)
        _now_playing["song"] = {
            "filename": filename,
            "title": header.get("title", ""),
            "artist": header.get("artist", ""),
            "genre": header.get("genre", ""),
        }
        current_app.logger.info(f"codex: {user['user']} set now playing: {filename}")
        return jsonify({"action": "setnowplaying", "active": True, "success": True})

    if action == "clearnowplaying":
        _now_playing.clear()
        return jsonify({"action": "clearnowplaying", "active": False, "success": True})

    if action in EDITABLE_FIELDS and filename:
        value = request.values.get(action, "")
        if action == "rating":
            try:
                value = int(value)
            except ValueError:
                value = 0
        lib.update_file_header(filename, action, value)
        current_app.logger.info(f"codex: {user['user']} updated {action} for {filename}")
        return jsonify(
            {
                "function": "ajax",
                "action": action,
                "user": user["user"],
                "success": True,
                "information": "SUCCESS",
            }
        )

    if action == "incrementcount" and filename:
        try:
            load_time = int(request.values.get("loadtime", "0"))
        except ValueError:
            load_time = 0
        now = int(time.time())
        if load_time > 0 and now - load_time >= 60:
            header = lib.parse_header(filename)
            count = int(header.get("count", 0)) + 1
            lib.update_file_header(filename, "count", count)
            current_app.logger.info(f"codex: {user['user']} incremented count for {filename}")

        return jsonify(
            {
                "function": "ajax",
                "action": action,
                "user": user["user"],
                "success": True,
                "information": "SUCCESS",
            }
        )

    return jsonify(
        {
            "function": "ajax",
            "action": action,
            "user": user["user"],
            "success": False,
            "information": "ERROR",
        }
    )
