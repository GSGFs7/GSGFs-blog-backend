from unittest.mock import AsyncMock, patch

from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from api.rate_limit import rate_limit


class RateLimitTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.META["REMOTE_ADDR"] = "127.0.0.1"

    # mock the cache service, not use really redis service
    @patch("api.rate_limit.cache")
    def test_sync_rate_limit_pass(self, mock_cache):
        mock_cache.incr.return_value = 1

        @rate_limit(key_prefix="test_sync", max_requests=2, window=60)
        def test_view(request: HttpRequest):
            return 200, "ok"

        status, res = test_view(self.request)
        self.assertEqual(status, 200)
        self.assertEqual(mock_cache.add.call_count, 1)
        self.assertEqual(mock_cache.incr.call_count, 1)

    @patch("api.rate_limit.cache")
    def test_sync_rate_limit_black(self, mock_cache):
        mock_cache.incr.return_value = 3

        @rate_limit(key_prefix="test_sync", max_requests=2, window=60)
        def test_view(request: HttpRequest):
            return 200, "ok"

        status, res = test_view(self.request)
        self.assertEqual(status, 429)
        self.assertEqual(res.get("message"), "Too many request")

    @patch("api.rate_limit.cache")
    async def test_async_rate_limit_pass(self, mock_cache):
        mock_cache.aincr = AsyncMock(return_value=1)
        mock_cache.aadd = AsyncMock()

        @rate_limit(key_prefix="test_async", max_requests=2, window=60)
        async def test_view(request: HttpRequest):
            return 200, "ok"

        status, res = await test_view(self.request)
        self.assertEqual(status, 200)
        mock_cache.aadd.assert_called_once()
        mock_cache.aincr.assert_called_once()

    @patch("api.rate_limit.cache")
    async def test_async_rate_limit_block(self, mock_cache):
        mock_cache.aincr = AsyncMock(return_value=3)
        mock_cache.aadd = AsyncMock()

        @rate_limit(key_prefix="test_async", max_requests=2, window=60)
        async def test_view(request: HttpRequest):
            return 200, "ok"

        status, res = await test_view(self.request)
        self.assertEqual(status, 429)
        self.assertEqual(res.get("message"), "Too many request")
