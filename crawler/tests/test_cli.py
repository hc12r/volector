import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import sys, types

# Provide dummy backoff if missing
if "backoff" not in sys.modules:
    import types as _types
    def _on_exception(*args, **kwargs):
        def deco(fn):
            return fn
        return deco
    sys.modules["backoff"] = _types.SimpleNamespace(on_exception=_on_exception, expo=lambda *a, **k: None)

# Ensure httpx exists for import time in dependencies of CLI
if "httpx" not in sys.modules:
    httpx_dummy = types.SimpleNamespace(
        AsyncClient=object,
        ConnectError=Exception,
        ReadTimeout=Exception,
        RemoteProtocolError=Exception,
        Timeout=object,
        Limits=object,
    )
    sys.modules["httpx"] = httpx_dummy

# Skip tests if pydantic not available (cli imports pipelines -> schemas)
try:
    import pydantic  # type: ignore
    _HAS_PYD = True
except Exception:
    _HAS_PYD = False

if _HAS_PYD:
    from crawler import cli as cli_mod
else:
    cli_mod = None  # type: ignore


@unittest.skipIf(not _HAS_PYD, "pydantic not installed")
class TestCLI(unittest.IsolatedAsyncioTestCase):
    async def test_crawl_once_happy_path(self):
        # Mock allowed to True and provide client
        dummy_resp = type("R", (), {"status_code": 200, "text": "<html><title>X</title></html>", "raise_for_status": lambda self: None})()
        client = AsyncMock()
        client.get = AsyncMock(return_value=dummy_resp)
        ctx = AsyncMock()
        ctx.__aenter__.return_value = client
        ctx.__aexit__.return_value = False
        with patch.object(cli_mod, "http_client", return_value=ctx), \
             patch.object(cli_mod, "allowed", return_value=True):
            await cli_mod.crawl_once(["https://example.com"])  # should not raise
        client.get.assert_awaited()

    async def test_run_source_reads_yaml_and_fetches(self):
        # Stub YAML loader via safe_load; force config path to exist and return an entry
        data = {"sources": [{"name": "example-news", "country": "MZ", "language": "pt", "base_urls": ["https://ex.com"], "render": False}]}
        dummy_resp = type("R", (), {"status_code": 200, "text": "<html><title>X</title></html>", "raise_for_status": lambda self: None})()
        client = AsyncMock(); client.get = AsyncMock(return_value=dummy_resp)
        ctx = AsyncMock(); ctx.__aenter__.return_value = client; ctx.__aexit__.return_value = False
        with patch.object(cli_mod, "http_client", return_value=ctx), \
             patch.object(cli_mod, "allowed", return_value=True), \
             patch("crawler.cli.Path.exists", return_value=True), \
             patch("crawler.cli.yaml.safe_load", return_value=data):
            await cli_mod.run_source("example-news", "MZ", 10)
        client.get.assert_awaited()


if __name__ == "__main__":
    asyncio.run(unittest.main())
