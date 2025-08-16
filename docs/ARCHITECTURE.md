# Volector Architecture

This chapter summarizes the main modules and their responsibilities so you can quickly understand and extend Volector.

Core modules
- fetch.py: Async HTTP client based on httpx with retries (backoff), connection pooling, redirect following, optional proxy, and politeness jitter.
- robots.py: robots.txt allowance check with an LRU-cached RobotFileParser per host; fail-open on read errors.
- render.py: Optional Playwright-based HTML rendering with graceful HTTP fetch fallback; raises RenderNotAvailable when disabled.
- parse.py: Lightweight HTML parsing (title + visible text) with an optional upgrade to readability + BeautifulSoup if installed.
- dedup.py: URL canonicalization (tracking query removal, host lowercase, sorted query) and sha256 content hashing.
- storage.py: MinIO/S3 writers for gzipped raw HTML and Parquet via s3fs/pyarrow; lazy imports with clear errors when deps missing.

Models & pipelines
- models/schemas.py: Pydantic models for CrawlJob, PageRaw, and Article.
- pipelines/article.py: Converts HTML to Article and writes curated Parquet partitioned by entity/country/date.

Operations & observability
- ops/logging.py: Structured JSON logging to stdout; includes optional context (job_id, source, country).
- ops/metrics.py: Prometheus counters with no-op fallbacks and an optional HTTP exporter.
- ops/tracing.py: OpenTelemetry shim that becomes a no-op when otel isn’t installed.
- ops/scheduler.py: Optional APScheduler helper to schedule runs from the YAML catalog.

CLI & workers
- cli.py: Entry point with two modes:
  - urls: crawl arbitrary URLs (robots-aware), parse, and log results.
  - run: read a source from the YAML catalog; crawl base_urls; optional raw writes; metrics support.
- workers/tasks.py: Minimal Celery task to fetch → optionally render → parse and return normalized dict; storage is kept outside for idempotency.

Testing strategy
- Unit tests cover fetching (with mocks), parsing, robots allowance, storage wrappers, metrics, tracing, scheduler behavior, CLI usage, models, and pipeline routines. Optional dependencies are handled with skips and no-ops to keep the suite portable.
