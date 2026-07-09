# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(_BASE_DIR / ".env")

class Config:
    BASE_DIR = _BASE_DIR
    TEXT_DIR = Path(BASE_DIR / "app" / "static" / "media" / "text" )
    DB_PATH = Path(BASE_DIR / "instance" / "codex.db" )
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "98cITRous#fleeTly")
    PERMANENT_SESSION_LIFETIME_DAYS = int(os.getenv("CODEX_SESSION_DAYS", "30"))
    MAX_SONG_BYTES = int(os.getenv("CODEX_MAX_SONG_BYTES", str(512 * 1024)))

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    # Optional: pin the exact redirect URI sent to Google.
    # Example: https://chordbook.example.com/authorize/google
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

    # URL generation / reverse proxy support
    TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("1", "true", "yes", "on")
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME")

