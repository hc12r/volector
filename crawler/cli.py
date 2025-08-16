from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path
from typing import List
from datetime import datetime

from .core.fetch import fetch, http_client
from .core.robots import allowed
from .core.dedup import content_hash
from .ops.logging import configure_logging
from .pipelines.article import to_article
from .ops.metrics import start_metrics_server, crawled_pages_total, fetch_errors_total, bytes_written_total

# Expose yaml at module level so tests can patch crawler.cli.yaml.safe_load
try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore


async def crawl_once(urls: List[str]) -> None:
    configure_logging()
    log = logging.getLogger("crawler")
    async with http_client() as client:
        for url in urls:
            if not allowed(url, agent="AdvancedCrawler/1.0"):
                log.warning("robots_disallow", extra={"message": f"Disallowed by robots: {url}"})
                continue
            try:
                r = await fetch(url, client)
                h = content_hash(r.text)
                art = to_article(url, r.text, country="", language=None, source="cli")
                crawled_pages_total.labels(source="cli", country="").inc()
                log.info("fetched", extra={"message": f"{url} status={r.status_code} hash={h} title={art.title}"})
            except Exception:
                fetch_errors_total.labels(source="cli", country="").inc()
                log.error("fetch_error", exc_info=True)


async def run_source(source: str, country: str, max_pages: int, *, write_raw: bool = False, metrics_port: int | None = None) -> None:
    configure_logging()
    log = logging.getLogger("crawler")

    if metrics_port:
        start_metrics_server(metrics_port)

    # Load YAML sources catalog (lazy dependency)
    if yaml is None:
        log.error("yaml_missing", extra={"message": "PyYAML is required for 'run' mode. Install pyyaml."})
        return

    config_path = Path(__file__).resolve().parent / "config" / "sources.yaml"
    if not config_path.exists():
        log.error("config_missing", extra={"message": f"Sources config not found at {config_path}"})
        return

    data = yaml.safe_load(config_path.read_text()) or {}
    sources = data.get("sources", [])
    entry = next((s for s in sources if s.get("name") == source and s.get("country") == country), None)
    if not entry:
        log.error("source_not_found", extra={"message": f"No source '{source}' for country '{country}' in catalog."})
        return

    base_urls: List[str] = entry.get("base_urls", [])[:max_pages]
    today = datetime.utcnow().date()

    async with http_client() as client:
        for idx, url in enumerate(base_urls, start=1):
            if not allowed(url, agent="AdvancedCrawler/1.0"):
                log.warning("robots_disallow", extra={"message": f"Disallowed by robots: {url}"})
                continue
            try:
                r = await fetch(url, client)
                art = to_article(url, r.text, country=country, language=entry.get("language"), source=source)
                crawled_pages_total.labels(source=source, country=country).inc()
                log.info("fetched_parsed", extra={"message": f"{url} title={art.title!r}"})

                if write_raw:
                    try:
                        from .core.storage import put_gz, S3Config  # lazy import
                        key = f"raw/{source}/{country}/dt={today:%Y-%m-%d}/page-{idx:06d}.html.gz"
                        meta = {
                            "content_hash": content_hash(r.text),
                            "status": str(r.status_code),
                            "source": source,
                            "country": country,
                        }
                        put_gz(key, r.text.encode("utf-8"), metadata=meta)
                        bytes_written_total.labels(layer="raw", source=source, country=country).inc(len(r.text.encode("utf-8")))
                        log.info("raw_written", extra={"message": key})
                    except Exception:
                        log.error("raw_write_failed", exc_info=True)

            except Exception:
                fetch_errors_total.labels(source=source, country=country).inc()
                log.error("run_error", exc_info=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawler CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_urls = sub.add_parser("urls", help="Fetch specific URLs")
    p_urls.add_argument("urls", nargs="+", help="One or more URLs to fetch")

    p_run = sub.add_parser("run", help="Run a configured source from sources.yaml")
    p_run.add_argument("--source", required=True, help="Source name from catalog")
    p_run.add_argument("--country", required=True, help="Country code (e.g., MZ)")
    p_run.add_argument("--max-pages", type=int, default=50, help="Max pages to crawl from base_urls")
    p_run.add_argument("--write-raw", action="store_true", help="Write raw HTML to MinIO if storage deps available")
    p_run.add_argument("--metrics-port", type=int, default=None, help="Expose Prometheus /metrics on this port")

    args = parser.parse_args()

    if args.cmd == "urls":
        asyncio.run(crawl_once(args.urls))
    elif args.cmd == "run":
        asyncio.run(run_source(args.source, args.country, args.max_pages, write_raw=args.write_raw, metrics_port=args.metrics_port))


if __name__ == "__main__":
    main()
