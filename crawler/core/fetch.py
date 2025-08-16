from __future__ import annotations

import asyncio
import os
import random
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import httpx
from backoff import on_exception, expo

DEFAULT_TIMEOUT = float(os.getenv("REQUESTS_TIMEOUT", "30"))
USER_AGENT = os.getenv("HTTP_USER_AGENT", "AdvancedCrawler/1.0 (+contact@example.org)")
PROXY_URL = os.getenv("PROXY_URL") or None
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "8"))


@asynccontextmanager
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    timeout = httpx.Timeout(DEFAULT_TIMEOUT)
    headers = {"User-Agent": USER_AGENT}
    limits = httpx.Limits(max_keepalive_connections=MAX_CONCURRENCY, max_connections=MAX_CONCURRENCY)
    async with httpx.AsyncClient(
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
        limits=limits,
        proxies=PROXY_URL,
    ) as client:
        yield client


def _polite_delay() -> float:
    # jitter to reduce burstiness per host
    return random.uniform(0.15, 0.6)


@on_exception(expo, (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError), max_tries=5, jitter=None)
async def _get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    r = await client.get(url)
    r.raise_for_status()
    await asyncio.sleep(_polite_delay())
    return r


async def fetch(url: str, client: Optional[httpx.AsyncClient] = None) -> httpx.Response:
    """Fetch a URL with retries, backoff, and politeness delay.

    If a client is provided, it will be used; otherwise an ephemeral client
    is created to ensure connection pooling for single calls.
    """
    if client is not None:
        return await _get(client, url)

    async with http_client() as c:
        return await _get(c, url)
