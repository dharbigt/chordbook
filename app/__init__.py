# SPDX-License-Identifier: GPL-3.0-or-later

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .routes import main_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    secret = str(app.config.get("SECRET_KEY", "")).strip()
    if not secret or secret == "codex-dev-change-me":
        raise RuntimeError("FLASK_SECRET_KEY must be set to a non-default value")

    # Reverse-proxy support (fixes external URL generation / OAuth redirect URIs)
    if app.config.get("TRUST_PROXY_HEADERS"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize OAuth
    from app.oauth import init_oauth
    init_oauth(app)

    # Ensure the database schema is up to date
    from app.services.auth import AuthService
    AuthService(app.config["DB_PATH"]).ensure_schema()

    app.register_blueprint(main_bp)
    return app

