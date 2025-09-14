from django.test import TestCase


class TestRoot(TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_root_endpoint(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 418)
