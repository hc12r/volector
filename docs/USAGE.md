# Volector Usage Guide

This document explains all the ways you can use Volector: via CLI, programmatically from Python, with optional rendering, metrics, storage to MinIO, scheduling, and Celery workers.

Contents
- CLI usage
- Programmatic usage (Python)
- Rendering options (Playwright / fallback)
- Storage to MinIO/S3 (raw gz + curated Parquet)
- Metrics and tracing
- Scheduling runs (APScheduler)
- Workers with Celery

Prerequisites
- Python 3.10+
- Install dependencies as needed:
  - Core: `pip install -r requirements.txt`
  - Playwright browsers (optional): `python -m playwright install chromium`

Environment variables (commonly used)
- HTTP_USER_AGENT
- REQUESTS_TIMEOUT, MAX_CONCURRENCY, PROXY_URL
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_REGION, S3_FORCE_PATH_STYLE
- CELERY_BROKER_URL

CLI usage
1) Fetch specific URLs (robots-aware)

```
python -m crawler.cli urls https://example.com https://example.org
```

2) Run a configured source from catalog

```
# Optional: enable metrics and raw writes
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ACCESS_KEY=minio
export MINIO_SECRET_KEY=minio123
export MINIO_BUCKET=crawler

python -m crawler.cli run \
  --source example-news \
  --country MZ \
  --max-pages 50 \
  --write-raw \
  --metrics-port 8000
```

Notes
- `--write-raw` requires boto3 and s3fs/pyarrow for storage. If missing, errors are logged but the run continues.
- `--metrics-port` exposes Prometheus metrics if `prometheus-client` is installed.

Programmatic usage (Python)
Fetch and parse ad hoc URLs with connection pooling and politeness:

```python
import asyncio
from crawler.core.fetch import http_client, fetch
from crawler.pipelines.article import to_article
from crawler.core.robots import allowed

async def main():
    async with http_client() as client:
        url = "https://example.com"
        if not allowed(url, agent="AdvancedCrawler/1.0"):
            return
        r = await fetch(url, client)
        art = to_article(url, r.text, country="MZ", language="pt", source="demo")
        print(art.title)

asyncio.run(main())
```

Rendering options (Playwright / fallback)
- When `playwright` and the browser are installed, you can render JS-heavy pages.
- If not installed or if launching fails, Volector can fall back to normal HTTP fetch.

```python
import asyncio
from crawler.core.render import render_html, RenderNotAvailable

async def main():
    try:
        html = await render_html("https://example.com/app")
    except RenderNotAvailable:
        # handle gracefully or choose a different strategy
        html = ""
    print(len(html))

asyncio.run(main())
```

Storage to MinIO/S3
Raw layer (gzipped HTML with metadata):

```python
from datetime import date
from crawler.core.storage import put_gz

key = f"raw/example-news/MZ/dt={date.today():%Y-%m-%d}/page-000001.html.gz"
html_bytes = b"<html>...</html>"
meta = {"content_hash": "...", "status": "200", "source": "example-news", "country": "MZ"}
put_gz(key, html_bytes, metadata=meta)
```

Curated Parquet (articles):

```python
from datetime import datetime
from crawler.pipelines.article import write_curated_articles, to_article

records = [
    to_article("https://ex.com/1", "<html><title>T</title></html>", country="MZ", language="pt", source="example")
]
write_curated_articles(records, country="MZ", dt=datetime.utcnow())
```

Metrics and tracing
- Start Prometheus exporter: `from crawler.ops.metrics import start_metrics_server; start_metrics_server(8000)`
- Increment counters: `from crawler.ops.metrics import crawled_pages_total; crawled_pages_total.labels(source="s", country="MZ").inc()`
- Tracing shim: `from crawler.ops.tracing import span; with span("fetch"): ...`

Scheduling runs (APScheduler)
- The helper can schedule sources defined in the YAML catalog. Requires `APScheduler`.

```python
import asyncio
from pathlib import Path
from crawler.ops.scheduler import start_scheduler
from crawler.cli import run_source

async def main():
    # Start scheduler using existing run_source coroutine
    scheduler = start_scheduler(Path(__file__).resolve().parents[1] / "crawler" / "config" / "sources.yaml", run_source)
    # Keep your app running (e.g., asyncio loop or web server)
    await asyncio.Event().wait()

asyncio.run(main())
```

Workers with Celery (optional)
- A minimal Celery task is provided when `celery` is installed.

```python
# tasks are defined in crawler.workers.tasks
# app may be None if Celery is not installed
from crawler.workers.tasks import app

# Enqueue a task (only when Celery is available and running)
# app.send_task('crawler.workers.tasks.crawl_url', args=[job_dict, url])
```

Troubleshooting
- Missing optional deps: Volector is designed to run with a minimal set; optional features either no-op or raise a clear RuntimeError. Install the required dependency as needed.
- Playwright launch fails: ensure `python -m playwright install chromium` was run.
- MinIO connection: verify MINIO_* env vars and bucket existence.
