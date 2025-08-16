from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

# Optional Celery integration; provide a no-op fallback if Celery isn't installed
try:
    from celery import Celery  # type: ignore
except Exception:  # pragma: no cover
    Celery = None  # type: ignore

from ..core.fetch import fetch, http_client
from ..core.render import render_html, RenderNotAvailable
from ..pipelines.article import to_article


BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

if Celery:
    app = Celery("crawler", broker=BROKER_URL)
else:  # pragma: no cover
    app = None  # type: ignore


if app:
    @app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
    def crawl_url(self, job: dict, url: str):  # type: ignore
        """Fetch → (optional) render → parse article → return dict.

        Storage is left to the caller to keep this task pure and testable.
        """
        import asyncio

        async def _run():
            async with http_client() as client:
                if job.get("render"):
                    try:
                        html = await render_html(url)
                    except RenderNotAvailable:
                        # Fallback: simple fetch text
                        r = await fetch(url, client)
                        html = r.text
                else:
                    r = await fetch(url, client)
                    html = r.text
                art = to_article(url, html, country=job.get("country"), language=job.get("language"), source=job.get("source"))
                return art.model_dump()

        return asyncio.run(_run())
