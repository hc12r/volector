import unittest
from datetime import datetime

try:
    from pydantic import ValidationError  # type: ignore
    P_HAS = True
except Exception:  # pragma: no cover - if pydantic missing, skip tests
    ValidationError = Exception  # type: ignore
    P_HAS = False

try:
    from crawler.models.schemas import Article, CrawlJob, PageRaw  # type: ignore
    SCHEMAS = True
except Exception:  # pragma: no cover
    SCHEMAS = False
    Article = CrawlJob = PageRaw = object  # type: ignore


@unittest.skipIf(not P_HAS or not SCHEMAS, "pydantic/models not available")
class TestModels(unittest.TestCase):
    def test_article_construction(self):
        a = Article(
            url="https://example.com/x",
            title="t",
            text="body",
            authors=[],
            published_at=None,
            country="MZ",
            language="pt",
            source="s",
            content_hash="abcd",
        )
        self.assertEqual(a.country, "MZ")
        self.assertEqual(a.title, "t")

    def test_invalid_url_raises(self):
        with self.assertRaises(ValidationError):
            Article(
                url="not_a_url",
                title=None,
                text=None,
                authors=[],
                published_at=None,
                country="MZ",
                language=None,
                source="s",
                content_hash="x",
            )

    def test_crawljob_defaults(self):
        cj = CrawlJob(job_id="1", source="s", country="MZ", dt=datetime.utcnow())
        self.assertEqual(cj.max_pages, 1000)
        self.assertEqual(cj.render, False)

    def test_pageraw(self):
        pr = PageRaw(
            url="https://example.com",
            fetched_at=datetime.utcnow(),
            status=200,
            headers={"a":"b"},
            content_hash="h",
            storage_key="raw/k"
        )
        self.assertEqual(pr.status, 200)


if __name__ == "__main__":
    unittest.main()
