import unittest

from crawler.core.parse import parse_article


class TestParse(unittest.TestCase):
    def test_parse_article_basic(self):
        html = """
        <html><head><title>Example Title</title></head>
        <body><h1>Hello</h1><p>World!</p></body></html>
        """
        result = parse_article(html)
        self.assertEqual(result["title"], "Example Title")
        self.assertIn("Hello", result["text"])  # basic text concat
        self.assertIn("World", result["text"])  # basic text concat


if __name__ == "__main__":
    unittest.main()
