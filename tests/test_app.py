# SPDX-License-Identifier: GPL-3.0-or-later

import os
import unittest

from app import create_app


class AppSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")

    def setUp(self) -> None:
        self.app = create_app()
        self.client = self.app.test_client()

    def test_landing_page_is_public(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_index_requires_authentication(self) -> None:
        response = self.client.get("/index.wsgi?function=index", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

    def test_login_page_renders(self) -> None:
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
