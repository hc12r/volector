import io
import json
import logging
import unittest
from unittest.mock import patch

from crawler.ops.logging import JsonFormatter, configure_logging


class TestLogging(unittest.TestCase):
    def test_json_formatter_basic(self):
        record = logging.LogRecord(
            name="test.logger", level=logging.INFO, pathname=__file__, lineno=10, msg="hello", args=(), exc_info=None
        )
        # attach extra context
        setattr(record, "job_id", "jid")
        setattr(record, "source", "src")
        setattr(record, "country", "MZ")
        s = JsonFormatter().format(record)
        obj = json.loads(s)
        self.assertEqual(obj["level"], "INFO")
        self.assertEqual(obj["message"], "hello")
        self.assertEqual(obj["logger"], "test.logger")
        self.assertEqual(obj["job_id"], "jid")
        self.assertEqual(obj["source"], "src")
        self.assertEqual(obj["country"], "MZ")

    def test_configure_logging_sets_handler(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        with patch("crawler.ops.logging.logging.StreamHandler", return_value=handler):
            configure_logging("INFO")
            logging.getLogger("x").info("msg")
            # ensure some JSON output happened
            out = stream.getvalue().strip()
            self.assertTrue(out.startswith("{"))
            data = json.loads(out)
            self.assertEqual(data["message"], "msg")


if __name__ == "__main__":
    unittest.main()
