import unittest

from crawler.ops.tracing import get_tracer, span, _NoopTracer


class TestTracing(unittest.TestCase):
    def test_get_tracer_returns_tracer(self):
        t = get_tracer()
        # When opentelemetry is missing, we get a _NoopTracer
        self.assertTrue(hasattr(t, "start_as_current_span"))

    def test_span_context_manager(self):
        with span("x") as s:
            # Should enter and exit without issues
            self.assertIsNotNone(s)


if __name__ == "__main__":
    unittest.main()
