import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

import logging
import crawler.ops.scheduler as sched


class TestScheduler(unittest.IsolatedAsyncioTestCase):
    def test_returns_none_when_apscheduler_missing(self):
        # Patch logging to avoid KeyError when using 'message' in extra
        orig_make = logging.Logger.makeRecord
        def safe_make(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
            if extra and "message" in extra:
                extra = dict(extra)
                extra.pop("message", None)
            return orig_make(self, name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        with patch.object(logging.Logger, "makeRecord", safe_make):
            with patch.object(sched, "AsyncIOScheduler", None):
                s = sched.start_scheduler(Path("/does/not/matter.yaml"), AsyncMock())
                self.assertIsNone(s)

    async def test_adds_jobs_with_dummy_scheduler(self):
        # Prepare dummy catalog
        dummy_catalog = {
            "sources": [
                {"name": "src1", "country": "MZ", "schedule": "0 * * * *", "max_pages": 5},
                {"name": "bad", "country": "MZ", "schedule": "invalid"},
            ]
        }

        class DummyScheduler:
            def __init__(self):
                self.jobs = []
                self.started = False
            def add_job(self, func, trigger, minute, hour, day, month, day_of_week, id, replace_existing):
                self.jobs.append({"id": id, "trigger": trigger, "minute": minute})
            def start(self):
                self.started = True

        orig_make = logging.Logger.makeRecord
        def safe_make(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
            if extra and "message" in extra:
                extra = dict(extra)
                extra.pop("message", None)
            return orig_make(self, name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        with patch.object(logging.Logger, "makeRecord", safe_make):
            with patch.object(sched, "AsyncIOScheduler", DummyScheduler):
                with patch.object(sched, "_load_catalog", return_value=dummy_catalog):
                    async def run_source_coro(source, country, max_pages, **kwargs):
                        return None
                    sch = sched.start_scheduler(Path("/x"), run_source_coro)
                    self.assertIsInstance(sch, DummyScheduler)
                    self.assertTrue(sch.started)
                    # Only one valid job should be scheduled
                    self.assertEqual(len(sch.jobs), 1)
                    self.assertEqual(sch.jobs[0]["id"], "src1:MZ")


if __name__ == "__main__":
    asyncio.run(unittest.main())
