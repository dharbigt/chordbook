# SPDX-License-Identifier: GPL-3.0-or-later

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.services.auth import AuthService


class AuthServiceSchemaTests(unittest.TestCase):
    def test_ensure_schema_creates_user_table_for_new_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "codex.db"

            AuthService(db_path).ensure_schema()

            with sqlite3.connect(db_path) as conn:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(user)").fetchall()]
                self.assertIn("google_id", cols)

    def test_ensure_schema_adds_google_id_to_existing_user_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "codex.db"
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "CREATE TABLE user (user TEXT PRIMARY KEY, name TEXT, token TEXT, hash TEXT)"
                )
                conn.commit()

            AuthService(db_path).ensure_schema()

            with sqlite3.connect(db_path) as conn:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(user)").fetchall()]
                self.assertIn("google_id", cols)


if __name__ == "__main__":
    unittest.main()
