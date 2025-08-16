from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "gclid",
    "fbclid",
}


def canonical(url: str) -> str:
    parts = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in TRACKING_PARAMS]
    query = urlencode(sorted(q))
    path = parts.path.rstrip("/")
    netloc = parts.netloc.lower()
    return urlunsplit((parts.scheme, netloc, path, query, ""))


# For deterministic behavior across environments, use sha256 for content fingerprints.
# mmh3 may be installed, but tests expect a 64-character hex digest.

def content_hash(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
