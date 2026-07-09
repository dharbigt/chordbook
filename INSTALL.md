# Installation

This document covers local setup and runtime configuration for Chordbook.

## Requirements

- Python 3.12+
- `pip`
- Access to the song text directory and SQLite database used by the app

## Local Setup

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create an `.env` file in the project root.

```bash
# Required
FLASK_SECRET_KEY="your-secret-key-here"
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"

# Set this to your callback URL registered in Google Cloud Console
GOOGLE_REDIRECT_URI="https://yourhost/authorize/google"

# Optional
CODEX_SESSION_DAYS=30
CODEX_MAX_SONG_BYTES=524288

# Needed behind a reverse proxy (nginx/Apache)
TRUST_PROXY_HEADERS=true
PREFERRED_URL_SCHEME=https
```

### Google Cloud Console setup

1. Create an OAuth 2.0 client ID at <https://console.cloud.google.com/> (Application type: Web application).
2. Add your callback URL as an **Authorized redirect URI**:
   ```
   https://yourhost/authorize/google
   ```
3. Copy the client ID and secret into `.env`.

4. Start the development server.

```bash
flask run
```

## WSGI Deployment

The project includes WSGI entrypoints:

- `wsgi.py`
- `index.wsgi`

Use the entrypoint that matches your host configuration.

## Notes

- Song files are served from `app/static/media/text/`. Populate this directory with your own chord chart files.
- The SQLite database is created at `instance/codex.db` and schema migrations run automatically on startup.
- `CODEX_MAX_SONG_BYTES` caps upload/edit payload sizes for song content.
- `FLASK_SECRET_KEY` is required; app startup will fail if it is unset.
