import json
from django.test import TestCase, override_settings

from api.auth import TimeBaseAuth


@override_settings(SECURE_SSL_REDIRECT=False)
class TestAuth(TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_auth(self) -> None:
        response = self.client.get("/api/test/auth")
        self.assertEqual(response.status_code, 401)

        token = TimeBaseAuth.create_token("test")
        response = self.client.get(
            "/api/test/auth",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertContains(response, json.dumps({"message": "authenticated"}), status_code=200)
