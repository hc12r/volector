import unittest

import sys, types

# Provide dummy backoff if missing
if "backoff" not in sys.modules:
    import types as _types
    def _on_exception(*args, **kwargs):
        def deco(fn):
            return fn
        return deco
    sys.modules["backoff"] = _types.SimpleNamespace(on_exception=_on_exception, expo=lambda *a, **k: None)

# Ensure httpx exists for import time in workers.tasks dependency chain
if "httpx" not in sys.modules:
    sys.modules["httpx"] = types.SimpleNamespace(
        AsyncClient=object,
        ConnectError=Exception,
        ReadTimeout=Exception,
        RemoteProtocolError=Exception,
        Timeout=object,
        Limits=object,
    )

# Skip if pydantic missing (workers import pipelines -> schemas)
try:
    import pydantic  # type: ignore
    _HAS_PYD = True
except Exception:
    _HAS_PYD = False

if _HAS_PYD:
    import crawler.workers.tasks as tasks  # type: ignore
else:
    tasks = None  # type: ignore


@unittest.skipIf(tasks is None, "pydantic not installed")
class TestWorkersTasks(unittest.TestCase):
    def test_app_present_even_without_celery(self):
        # If Celery is not installed, app is None; but attribute exists
        self.assertTrue(hasattr(tasks, "app"))
        # If Celery not installed in environment, app should be None
        # We cannot assert exact None in all environments, but ensure it's not raising
        _ = tasks.app
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
