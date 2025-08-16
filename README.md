# Volector: Advanced Web Crawler (MinIO‑First)

Volector is a production‑minded, extensible web crawler scaffold optimized for quality and performance, with optional dependencies kept lazy. It provides a minimal but practical implementation you can extend and adapt.

Highlights:
- Async HTTP fetching (httpx) with retries (backoff), politeness jitter, and connection pooling.
- Robots.txt compliance with LRU caching.
- Optional JS rendering (Playwright) with graceful fallback to static fetch.
- Lightweight parsing by default, with optional readability + BeautifulSoup when installed.
- Pydantic data models for jobs and content entities (Article).
- MinIO/S3 writers for raw gzip objects and curated Parquet (optional deps).
- Observability: JSON logging, optional Prometheus metrics and OpenTelemetry traces (no‑op fallbacks).
- CLI to fetch URLs or run configured sources from YAML.
- Celery worker task stub for distributed crawling (optional dep).


## 1. Project Layout

```
crawler/
  cli.py                 # CLI entry point (urls, run)
  config/sources.yaml    # Example source catalog
  core/
    fetch.py             # Async HTTP client + retries + politeness
    robots.py            # Robots.txt allowance with caching
    render.py            # JS rendering (Playwright) with fallback
    parse.py             # Basic parser; upgrades to readability/BS when available
    storage.py           # MinIO/S3 writers (gz, Parquet)
    dedup.py             # URL canonicalization and content fingerprinting
  models/schemas.py      # Pydantic schemas (CrawlJob, PageRaw, Article)
  pipelines/article.py   # Parse→normalize Article and write curated Parquet
  ops/
    logging.py           # Structured JSON logging
    metrics.py           # Prometheus counters + start_metrics_server helper
    tracing.py           # OpenTelemetry shim (no‑op if not installed)
    scheduler.py         # APScheduler helper (optional)
  tests/
    ...                  # Unit tests covering fetch, render, storage, metrics, scheduler, CLI, workers, models, parsing, and dedup
```


## 2. Quickstart

- Python 3.10+ recommended.
- Install dependencies:

```
pip install -r requirements.txt
# For JS rendering, install browsers once:
python -m playwright install chromium
```

Note: Many features are optional with graceful fallbacks (metrics, tracing, storage, rendering). Install only what you need from requirements.txt; tests will skip features if optional deps are missing.

- Run simple fetch of specific URLs:

```
python -m crawler.cli urls https://example.com https://example.org
```

- Run a configured source (from YAML):

```
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ACCESS_KEY=minio
export MINIO_SECRET_KEY=minio123
export MINIO_BUCKET=crawler

python -m crawler.cli run --source example-news --country MZ --max-pages 10 \
  --write-raw --metrics-port 8000
```


## 3. Configuration

Environment variables (commonly used):
- HTTP_USER_AGENT: default User‑Agent.
- REQUESTS_TIMEOUT: request timeout seconds (default 30).
- MAX_CONCURRENCY: connection pool size for httpx.
- PROXY_URL: outbound proxy (optional). 
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_REGION, S3_FORCE_PATH_STYLE: MinIO/S3.
- CELERY_BROKER_URL: Redis/RabbitMQ URL for Celery workers.

YAML catalog: see crawler/config/sources.yaml for the structure. Each source includes base_urls, country, language, render flag, path allow/deny lists, cron schedule, and max_pages.


## 4. How It Works (Modules)

- core/fetch.py
  - http_client(): an async contextmanager configuring httpx AsyncClient with:
    - Connection pooling (max_connections=max_keepalive=MAX_CONCURRENCY)
    - Follow‑redirects, timeout, optional proxy, and a custom User‑Agent.
  - fetch(): wraps GET with backoff retry on transient errors and adds politeness jitter (0.15–0.6s) after successful requests for host friendliness.

- core/robots.py
  - robots_for(): caches robots.txt parsers per host using lru_cache.
  - allowed(url, agent): returns robots allowance; fails open when robots can’t be read, to avoid false negatives.

- core/render.py
  - render_html(): renders via Playwright if installed; otherwise, by default falls back to a standard fetch. Set fallback_to_fetch=False to raise a RenderNotAvailable error instead.

- core/parse.py
  - parse_article(): attempts readability + BeautifulSoup if present; on any error, falls back to a built‑in lightweight HTML parser (_TitleTextParser) that extracts <title> and visible text.

- core/dedup.py
  - canonical(url): normalizes URLs by lowercasing host, stripping trailing slashes, and removing tracking query params (utm_*, gclid, fbclid), while sorting the remaining query parameters.
  - content_hash(text): deterministic sha256 64‑character hex digest for consistent fingerprints across environments.

- core/storage.py
  - S3Config: reads MinIO/S3 settings from env.
  - put_gz(key, data, ...): gzip compresses bytes and writes to S3 with metadata and correct content encoding.
  - write_parquet(path, records): writes a Parquet file to S3 via s3fs/pyarrow; raises a clear error if optional deps are missing.

- pipelines/article.py
  - to_article(url, html, ...): converts HTML into a normalized Article (Pydantic) with a derived content_hash from the parsed title+text.
  - write_curated_articles(...): writes a partitioned Parquet dataset under curated/articles/{country}/dt=YYYY-MM-DD.

- ops/logging.py
  - configure_logging(): sets structured JSON logs to stdout, including context fields (job_id, source, country) when provided.

- ops/metrics.py
  - Exposes Prometheus counters with no‑op fallbacks if prometheus_client isn’t installed.
  - start_metrics_server(port=8000): starts the Prometheus HTTP exporter if available; otherwise, it’s a no‑op.

- ops/tracing.py
  - get_tracer()/span(): lightweight OpenTelemetry shim; becomes a no‑op if otel API isn’t installed.

- workers/tasks.py
  - crawl_url Celery task (only registered if Celery is installed): fetch → optional render → parse → return normalized dict. Storage is intentionally left to the caller for idempotent, testable behavior.

- cli.py
  - urls: fetch and parse a list of URLs (robots‑aware) and log titles.
  - run: read a source entry from YAML and crawl its base_urls with parsing and robots checks.


## 5. Observability

- Logging: JSON lines to stdout. Example entries include level, message, logger, and optional context.
- Metrics: import crawler.ops.metrics and call start_metrics_server(8000) in a long‑running process to expose /metrics.
- Tracing: wrap blocks with ops.tracing.span("name") when desired; becomes a no‑op without otel.

Example:

```python
from crawler.ops.metrics import start_metrics_server, crawled_pages_total
start_metrics_server(8000)
# ... later during crawl
crawled_pages_total.labels(source="example-news", country="MZ").inc()
```


## 6. Quality & Performance Notes

- Connection pooling and concurrency are tuned via MAX_CONCURRENCY.
- Backoff retries reduce flakiness on transient network errors.
- Politeness jitter reduces burstiness per host; further host‑aware rate limiting can be added.
- Optional dependencies are lazy: the scaffold runs with a small base dependency set. Features requiring heavier deps fail gracefully or are no‑ops.
- Writers are idempotent; callers should choose deterministic keys or overwrite semantics.


## 7. Running Tests

Run individual tests explicitly (works everywhere):

```
python -m unittest crawler/tests/test_dedup.py -v
python -m unittest crawler/tests/test_parse.py -v
```

Run discovery across the repository:

```
python -m unittest discover -v
```

Notes:
- Some tests will be skipped automatically if optional dependencies (e.g., pydantic, pyarrow, playwright) aren’t installed.
- You can run individual tests for specific modules as needed.


## 8. Next Steps (Roadmap)

- Add a simple scheduler (APScheduler) to trigger sources based on cron expressions.
- Implement raw storage writing from CLI/worker, including metadata tags and snapshots.
- Improve parsing with readability/BS fallback heuristics and language detection.
- Add integration tests using a mock HTTP server and local MinIO via docker-compose.
- Add Dockerfile and compose for local stack (MinIO, Redis, Prometheus, Grafana).


## 9. Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines on setting up your environment, running tests, and submitting pull requests.

## 10. License

This project is licensed under the MIT License. See the LICENSE file for details.

## 0. Use Cases (Why Volector)

Volector is suited for:
- News aggregation across multiple countries and languages: collect headlines/articles, normalize to a unified schema, and store daily Parquet datasets.
- Market and competitive intelligence: periodically crawl product pages, press releases, blogs; extract text for analysis and alerting.
- Compliance monitoring and archival: respect robots, snapshot raw HTML, and keep curated datasets in MinIO for audits.
- Price and availability tracking: fetch listings at intervals; store raw and parsed structured data for analytics.
- Research and academic datasets: build reproducible corpora of public webpages for NLP or social sciences.
- Public sector and NGO monitoring: monitor government portals, NGOs, and publications with country scoping.

For how to use Volector in different modes (CLI, programmatic, scheduled, workers), see USAGE.md. For configuring sources and catalogs, see CONFIG.md.


## Further Documentation
- Full docs index: docs/index.md
- Usage Guide: docs/USAGE.md
- Configuration Guide: docs/CONFIG.md
- Architecture: docs/ARCHITECTURE.md
- Operations: docs/operations.md
- Contributing: docs/CONTRIBUTING.md
