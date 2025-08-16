import unittest
from unittest.mock import patch

from crawler.core import robots as robots_mod


class TestRobots(unittest.TestCase):
    def test_allowed_true_from_can_fetch(self):
        class Dummy:
            def can_fetch(self, agent, url):
                return True
        with patch.object(robots_mod, "robots_for", return_value=Dummy()):
            self.assertTrue(robots_mod.allowed("https://example.com/x", agent="bot"))

    def test_allowed_false_from_can_fetch(self):
        class Dummy:
            def can_fetch(self, agent, url):
                return False
        with patch.object(robots_mod, "robots_for", return_value=Dummy()):
            self.assertFalse(robots_mod.allowed("https://example.com/x", agent="bot"))

    def test_allowed_on_exception_is_true(self):
        class Dummy:
            def can_fetch(self, agent, url):
                raise RuntimeError("boom")
        with patch.object(robots_mod, "robots_for", return_value=Dummy()):
            self.assertTrue(robots_mod.allowed("https://example.com/x", agent="bot"))


if __name__ == "__main__":
    unittest.main()
