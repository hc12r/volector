from __future__ import annotations

"""
Optional APScheduler helper to schedule sources from the YAML catalog.
If APScheduler is not installed, functions become safe no-ops with logging.
"""

import logging
from pathlib import Path
from typing import Any, Dict


try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
except Exception:  # pragma: no cover
    AsyncIOScheduler = None  # type: ignore


def _load_catalog(catalog_path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load the catalog.") from e
    return (yaml.safe_load(catalog_path.read_text()) or {})


def start_scheduler(catalog_path: Path, run_source_coro):
    """Start a minimal cron scheduler using APScheduler.

    Parameters:
      - catalog_path: path to sources.yaml
      - run_source_coro: coroutine function with signature
          run_source(source: str, country: str, max_pages: int, **kwargs)

    If APScheduler is not installed, this logs a message and returns None.
    """
    log = logging.getLogger("crawler.scheduler")
    if AsyncIOScheduler is None:  # pragma: no cover
        log.error("apscheduler_missing", extra={"message": "Install apscheduler to use scheduler."})
        return None

    data = _load_catalog(catalog_path)
    sources = data.get("sources", [])
    scheduler = AsyncIOScheduler()

    for entry in sources:
        source = entry.get("name")
        country = entry.get("country")
        schedule = entry.get("schedule")  # cron string like "0 * * * *"
        max_pages = entry.get("max_pages", 50)
        if not (source and country and schedule):
            continue
        # Convert standard 5-field cron into APScheduler args
        try:
            minute, hour, day, month, day_of_week = schedule.split()
        except Exception:
            log.warning("invalid_cron", extra={"message": f"Skipping invalid cron for {source}:{country}: {schedule!r}"})
            continue

        async def job(_source=source, _country=country, _max=max_pages):
            try:
                await run_source_coro(_source, _country, _max)
            except Exception:
                log.error("scheduled_run_error", exc_info=True)

        scheduler.add_job(
            job,
            trigger="cron",
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=f"{source}:{country}",
            replace_existing=True,
        )
        log.info("scheduled", extra={"message": f"{source}:{country} -> {schedule}"})

    scheduler.start()
    log.info("scheduler_started", extra={"message": f"Loaded {len(sources)} entries"})
    return scheduler
