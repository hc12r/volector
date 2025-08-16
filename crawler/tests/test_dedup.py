import unittest

from crawler.core.dedup import canonical, content_hash


class TestDedup(unittest.TestCase):
    def test_canonical_strips_tracking_and_lowercases_host(self):
        url = "https://Example.COM/Path/?utm_source=x&a=1&fbclid=zzz"
        c = canonical(url)
        self.assertTrue("utm_source" not in c)
        self.assertTrue("fbclid" not in c)
        self.assertTrue("example.com" in c)
        self.assertTrue(c.endswith("?a=1"))

    def test_content_hash_is_hex(self):
        h = content_hash("hello")
        int(h, 16)  # should not raise
        self.assertEqual(len(h), 64)  # sha256 fallback length


if __name__ == "__main__":
    unittest.main()
