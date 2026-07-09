# SPDX-License-Identifier: GPL-3.0-or-later

import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class UserRecord:
    user: str
    name: str
    token: str


class AuthService:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_schema(self) -> None:
        """Add the google_id column if it doesn't exist yet."""
        with self._connect() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(user)").fetchall()]
            if "google_id" not in cols:
                conn.execute("ALTER TABLE user ADD COLUMN google_id TEXT")
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_google_id "
                    "ON user(google_id) WHERE google_id IS NOT NULL"
                )
                conn.commit()

    def load_user_by_token(self, token: str) -> Optional[UserRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user, name, token FROM user WHERE token = ?", (token,)
            ).fetchone()
        if not row:
            return None
        return UserRecord(user=row["user"], name=row["name"], token=row["token"])

    def find_or_create_by_google(
        self, google_id: str, email: str, name: str
    ) -> Optional[UserRecord]:
        """Find an existing user by google_id (or link by email), or create a new one."""
        if not google_id or not email:
            return None
        with self._connect() as conn:
            # 1. Find by google_id
            row = conn.execute(
                "SELECT user, name, token FROM user WHERE google_id = ?", (google_id,)
            ).fetchone()
            if row:
                return UserRecord(user=row["user"], name=row["name"], token=row["token"])

            # 2. Link an existing account that matches by email
            row = conn.execute(
                "SELECT user, name, token FROM user WHERE user = ?", (email,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE user SET google_id = ? WHERE user = ?", (google_id, email)
                )
                conn.commit()
                return UserRecord(user=row["user"], name=row["name"], token=row["token"])

            # 3. Create a brand-new user
            token = secrets.token_urlsafe(32)
            display_name = name or email
            conn.execute(
                "INSERT INTO user (user, name, token, hash, google_id) VALUES (?, ?, ?, '', ?)",
                (email, display_name, token, google_id),
            )
            conn.commit()
            return UserRecord(user=email, name=display_name, token=token)

