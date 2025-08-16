from __future__ import annotations

import asyncio
from typing import Optional

# We keep Playwright as an optional dependency. If it's not installed,
# render() will raise a helpful error unless the caller requests a fallback.


class RenderNotAvailable(RuntimeError):
    pass


async def render_html(url: str, wait_until: str = "networkidle", timeout_ms: int = 30000,
                      fallback_to_fetch: bool = True) -> str:
    """Render a page with Playwright if available.

    If Playwright is not installed and fallback_to_fetch is True, perform a basic
    HTTP fetch using httpx to return the raw HTML. If fallback_to_fetch is False,
    raise RenderNotAvailable.
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except Exception:
        if fallback_to_fetch:
            # Lazy import httpx to avoid unnecessary hard dependency in callers
            import httpx  # type: ignore
            async with httpx.AsyncClient(timeout=timeout_ms / 1000, follow_redirects=True) as client:
                r = await client.get(url)
                r.raise_for_status()
                return r.text
        raise RenderNotAvailable(
            "Playwright is not installed. Install 'playwright' and browsers to enable rendering."
        )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                html = await page.content()
                return html
            finally:
                # Ensure browser is closed even on errors
                await asyncio.gather(browser.close(), return_exceptions=True)
    except Exception:
        if fallback_to_fetch:
            # If playwright is present but cannot launch (browsers not installed), fallback to httpx
            import httpx  # type: ignore
            async with httpx.AsyncClient(timeout=timeout_ms / 1000, follow_redirects=True) as client:
                r = await client.get(url)
                r.raise_for_status()
                return r.text
        raise RenderNotAvailable("Rendering failed and fallback is disabled.")
