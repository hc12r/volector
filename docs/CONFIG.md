# Volector Configuration Guide (sources.yaml)

This document explains how to configure Volector sources via the YAML catalog at `crawler/config/sources.yaml`.

Overview
- The CLI command `run` selects a source by name and country and crawls its `base_urls`.
- Each entry describes the country, language, rendering option, allow/deny path filters, schedule, and limits.

Location
- Default catalog path used by the CLI: `crawler/config/sources.yaml`.

Example
```yaml
sources:
  - name: example-news
    base_urls: ["https://example.com/news"]
    country: MZ
    language: pt
    render: false
    allow: ["/news/"]
    deny: ["/login", "/privacy"]
    schedule: "0 * * * *"   # hourly
    max_pages: 200
```

Fields
- name (string, required): Unique source identifier.
- base_urls (list[string], required): One or more entry URLs to fetch (currently treated as a flat list in the minimal CLI; breadth-first or link-following is out of scope in this scaffold).
- country (string, required): Country code (e.g., MZ, US).
- language (string, optional): Language code (e.g., pt, en).
- render (bool, optional): If true, indicates preference for JS rendering (worker/advanced flows use this; the minimal CLI always performs static fetch).
- allow (list[string], optional): Path prefixes to include (not enforced by the minimal CLI; useful for future spiders).
- deny (list[string], optional): Path prefixes to exclude (not enforced by the minimal CLI; useful for future spiders).
- schedule (string, optional): 5-field cron expression (minute hour day month day_of_week). Used by the APScheduler helper.
- max_pages (int, optional): Upper bound of `base_urls` to process in a single run.

Cron format
- `"0 * * * *"` → run at minute 0 of every hour
- `"30 2 * * *"` → run daily at 02:30
- `"*/15 * * * *"` → run every 15 minutes

Scheduling with APScheduler
- Use the helper in `crawler.ops.scheduler.start_scheduler(catalog_path, run_source)` to schedule all valid entries.
- Invalid cron expressions are skipped with a warning.

Environment and storage
- MINIO_* variables configure output destinations when `--write-raw` is used.
- The curated Parquet writer stores under:
  - `curated/{entity}/{country}/dt=YYYY-MM-DD/data.parquet`

Tips
- Start small: a few base URLs and a low `max_pages` to validate the pipeline.
- Respect robots.txt. Volector checks robots for each URL before fetching.
- Rendering: prefer static where possible; only enable JS rendering for pages that need it.

Validation
- The minimal scaffold does not perform strict schema validation on the catalog. Keep keys and types as shown above for compatibility.
