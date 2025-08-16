import gzip
import io
import unittest
from unittest.mock import MagicMock, patch

import crawler.core.storage as storage


class TestStorage(unittest.TestCase):
    def test_put_gz_raises_when_boto_missing(self):
        with patch.object(storage, "boto3", None):
            with self.assertRaises(RuntimeError):
                storage.put_gz("x", b"data")

    def test_write_parquet_raises_when_deps_missing(self):
        with patch.object(storage, "s3fs", None), patch.object(storage, "pa", None):
            with self.assertRaises(RuntimeError):
                storage.write_parquet("bucket/path", [{"a": 1}])

    def test_put_gz_calls_s3_with_gzip(self):
        # Mock boto3 client to capture params
        mock_client = MagicMock()
        mock_client.put_object = MagicMock()
        with patch.object(storage, "_client", return_value=mock_client):
            storage.put_gz("k", b"hello world", metadata={"x":"y"})
        args, kwargs = mock_client.put_object.call_args
        self.assertEqual(kwargs["ContentEncoding"], "gzip")
        # ensure body is gzipped
        buf = io.BytesIO(kwargs["Body"])
        with gzip.GzipFile(fileobj=buf, mode="rb") as f:
            out = f.read()
        self.assertEqual(out, b"hello world")


if __name__ == "__main__":
    unittest.main()
