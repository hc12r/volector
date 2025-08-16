from __future__ import annotations

# Minimal tracing shim. If OpenTelemetry is available, expose basic helpers.

from contextlib import contextmanager
from typing import Optional


try:
    from opentelemetry import trace  # type: ignore
    from opentelemetry.trace import Tracer  # type: ignore
except Exception:  # pragma: no cover
    trace = None  # type: ignore
    Tracer = None  # type: ignore


def get_tracer(name: str = "crawler"):
    if trace is None:  # pragma: no cover
        return _NoopTracer()
    return trace.get_tracer(name)


class _NoopSpan:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class _NoopTracer:
    def start_as_current_span(self, name: str):  # noqa: D401
        return _NoopSpan()


@contextmanager
def span(name: str):
    tracer = get_tracer()
    if isinstance(tracer, _NoopTracer):  # no-op
        with _NoopSpan() as s:
            yield s
    else:
        with tracer.start_as_current_span(name) as s:  # type: ignore
            yield s
