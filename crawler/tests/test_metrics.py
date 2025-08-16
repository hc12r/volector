import unittest
from unittest.mock import patch

from crawler.ops import metrics as metrics_mod


class TestMetrics(unittest.TestCase):
    def test_counters_have_labels(self):
        c = metrics_mod.crawled_pages_total.labels(source="s", country="MZ")
        # Should return a counter-like object where inc can be called
        self.assertTrue(hasattr(c, "inc"))
        c.inc()

    def test_start_metrics_server_no_throw_when_missing(self):
        with patch.object(metrics_mod, "start_http_server", side_effect=RuntimeError("x"), create=True):
            metrics_mod.start_metrics_server(8123)  # must not raise


if __name__ == "__main__":
    unittest.main()
