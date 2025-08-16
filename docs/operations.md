# Observability & Operations

Logging
- Structured JSON logs via crawler.ops.logging.configure_logging().
- Include optional context fields (job_id, source, country) by using logging extra in your calls if needed.

Metrics
- Use Prometheus counters in crawler.ops.metrics.
- Start the exporter when running a long-lived service:

```python
from crawler.ops.metrics import start_metrics_server, crawled_pages_total
start_metrics_server(8000)
```

Tracing
- Use the lightweight shim in crawler.ops.tracing:

```python
from crawler.ops.tracing import span
with span("parse-article"):
    # your code here
    pass
```

Run reports & alerts (future work)
- Emit per-run manifest (counts, bytes written) to MinIO.
- Provide Prometheus alerts and example Grafana dashboards.

Operational tips
- Respect robots.txt and be polite (jitter, reasonable concurrency).
- Prefer static fetching; use rendering selectively.
- Keep optional deps minimal in dev; enable them in CI or prod layers as needed.
