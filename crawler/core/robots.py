from __future__ import annotations

from functools import lru_cache
from urllib import robotparser
from urllib.parse import urlparse

AGENT = "*"


@lru_cache(maxsize=1024)
def robots_for(netloc: str) -> robotparser.RobotFileParser:
    rp = robotparser.RobotFileParser()
    scheme = "https"
    rp.set_url(f"{scheme}://{netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        # Fail-open: if robots cannot be read, allow by default.
        pass
    return rp


def allowed(url: str, agent: str = AGENT) -> bool:
    netloc = urlparse(url).netloc
    rp = robots_for(netloc)
    try:
        return rp.can_fetch(agent, url)
    except Exception:
        return True
