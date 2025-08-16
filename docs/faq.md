# FAQ

Q: Do I need all dependencies installed?
A: No. Volector is designed with optional dependencies and graceful fallbacks. Install only what you need. Some tests will be skipped when optional dependencies are not present.

Q: Rendering fails with Playwright errors
A: Ensure you have installed the browser: `python -m playwright install chromium`. If you prefer not to render, disable or rely on fallback fetching.

Q: How do I write outputs to MinIO?
A: Set MINIO_* env vars and use `--write-raw` in CLI run mode. For curated Parquet, use pipelines.article.write_curated_articles with s3fs/pyarrow installed.

Q: Where are the scheduled jobs configured?
A: In the YAML catalog (crawler/config/sources.yaml) using a 5-field cron expression. Use the scheduler helper to load and schedule entries.

Q: How do I contribute?
A: See the Development & Contributing chapter or docs/CONTRIBUTING.md.
