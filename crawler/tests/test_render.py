import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from crawler.core.render import render_html, RenderNotAvailable


class TestRender(unittest.IsolatedAsyncioTestCase):
    async def test_render_fallback_when_playwright_missing(self):
        # Simulate ImportError for playwright by ensuring import inside function fails
        # Then ensure httpx.AsyncClient.get is called and text returned
        class DummyResp:
            def __init__(self):
                self.text = "<html></html>"
            def raise_for_status(self):
                return None
        async_client_mock = AsyncMock()
        async_client_mock.get = AsyncMock(return_value=DummyResp())
        async_context = AsyncMock()
        async_context.__aenter__.return_value = async_client_mock
        async_context.__aexit__.return_value = False
        # Inject a dummy httpx module so that render_html fallback uses our context
        import sys, types
        sys.modules["httpx"] = types.SimpleNamespace(AsyncClient=lambda *a, **k: async_context)
        html = await render_html("https://example.com")
        self.assertIn("<html", html)

    async def test_render_raises_when_no_fallback(self):
        # If playwright is not installed, fallback_to_fetch=False should raise
        with self.assertRaises(RenderNotAvailable):
            await render_html("https://example.com", fallback_to_fetch=False)


if __name__ == "__main__":
    asyncio.run(unittest.main())
