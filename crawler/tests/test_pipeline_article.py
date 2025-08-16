import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Skip if pydantic missing (pipeline imports schemas)
try:
    import pydantic  # type: ignore
    _HAS_PYD = True
except Exception:
    _HAS_PYD = False

if _HAS_PYD:
    from crawler.pipelines.article import to_article, write_curated_articles
else:
    to_article = write_curated_articles = None  # type: ignore


@unittest.skipIf(not _HAS_PYD, "pydantic not installed")
class TestArticlePipeline(unittest.TestCase):
    def test_to_article_fields(self):
        html = """
        <html><head><title>A</title></head><body><p>B</p></body></html>
        """
        art = to_article("https://example.com/x", html, country="MZ", language="pt", source="src")
        self.assertEqual(art.country, "MZ")
        self.assertEqual(art.source, "src")
        self.assertTrue(art.content_hash)

    def test_write_curated_calls_storage_with_expected_path(self):
        records = [
            to_article("https://ex.com/1", "<html><title>T</title></html>", country="MZ", language=None, source="s")
        ]
        dt = datetime(2025, 8, 16)
        with patch("crawler.pipelines.article.S3Config") as Cfg, \
             patch("crawler.pipelines.article.write_parquet") as wp:
            Cfg.return_value.bucket = "bucket"
            write_curated_articles(records, country="MZ", dt=dt)
            wp.assert_called_once()
            path_arg = wp.call_args[0][0]
            self.assertEqual(path_arg, "bucket/curated/articles/MZ/dt=2025-08-16/data.parquet")


if __name__ == "__main__":
    unittest.main()
