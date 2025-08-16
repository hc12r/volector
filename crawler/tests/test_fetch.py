import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import importlib, sys, types

# Ensure httpx exists for import time in fetch module
# Provide dummy backoff if missing
if "backoff" not in sys.modules:
    import types as _types
    def _on_exception(*args, **kwargs):
        def deco(fn):
            return fn
        return deco
    sys.modules["backoff"] = _types.SimpleNamespace(on_exception=_on_exception, expo=lambda *a, **k: None)

if "httpx" not in sys.modules:
    httpx_dummy = types.SimpleNamespace(
        AsyncClient=object,  # will be patched in tests anyway
        ConnectError=Exception,
        ReadTimeout=Exception,
        RemoteProtocolError=Exception,
        Timeout=object,
        Limits=object,
    )
    sys.modules["httpx"] = httpx_dummy

from crawler.core.fetch import fetch, _polite_delay


class TestFetch(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_uses_provided_client(self):
        class DummyResp:
            def __init__(self):
                self.status_code = 200
                self.text = "ok"
            def raise_for_status(self):
                return None
        dummy_client = AsyncMock()
        dummy_client.get = AsyncMock(return_value=DummyResp())
        with patch("crawler.core.fetch.asyncio.sleep", new=AsyncMock()) as _sleep:
            r = await fetch("https://example.com", client=dummy_client)
        self.assertEqual(r.text, "ok")
        dummy_client.get.assert_awaited()

    def test_polite_delay_in_range(self):
        for _ in range(10):
            d = _polite_delay()
            self.assertGreaterEqual(d, 0.15)
            self.assertLessEqual(d, 0.6)


if __name__ == "__main__":
    asyncio.run(unittest.main())
