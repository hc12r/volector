from __future__ import annotations

# Optional Prometheus counters. Provide no-op fallbacks when the dependency is missing
try:
    from prometheus_client import Counter, start_http_server  # type: ignore
except Exception:  # pragma: no cover
    class _NoopCounter:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            return None

        def observe(self, *args, **kwargs):
            return None

    def Counter(*args, **kwargs):  # type: ignore
        return _NoopCounter()

    def start_http_server(port: int):  # type: ignore
        # No-op if prometheus_client is not installed
        return None


def start_metrics_server(port: int = 8000) -> None:
    """Start Prometheus metrics HTTP server if available.

    If prometheus_client is not installed, this function is a no-op.
    """
    try:
        start_http_server(port)  # type: ignore
    except Exception:
        # Silently ignore to avoid breaking runtime in minimal environments
        pass


crawled_pages_total = Counter("crawled_pages_total", "Total pages successfully crawled", ["source", "country"])
fetch_errors_total = Counter("fetch_errors_total", "Total fetch errors", ["source", "country"]) 
bytes_written_total = Counter("bytes_written_total", "Total bytes written to storage", ["layer", "source", "country"]) 
