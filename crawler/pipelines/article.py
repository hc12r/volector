from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from ..core.parse import parse_article
from ..core.dedup import content_hash
from ..models.schemas import Article
from ..core.storage import S3Config, write_parquet


def to_article(url: str, html: str, *, country: str, language: Optional[str], source: str) -> Article:
    parsed = parse_article(html)
    h = content_hash((parsed.get("title") or "") + "\n" + (parsed.get("text") or ""))
    return Article(
        url=url,  # type: ignore[arg-type]
        title=parsed.get("title"),
        text=parsed.get("text"),
        authors=[],
        published_at=None,
        country=country,
        language=language,
        source=source,
        content_hash=h,
    )


def write_curated_articles(records: list[Article], *, country: str, dt: datetime, entity: str = "articles") -> None:
    """Optionally write curated records to MinIO as Parquet.

    This function depends on optional pyarrow/s3fs; if not installed, it will
    raise a RuntimeError from storage layer. Callers should handle it.
    """
    # Convert to serializable dictionaries
    rows: list[Dict[str, object]] = [r.model_dump() for r in records]
    path = f"{S3Config().bucket}/curated/{entity}/{country}/dt={dt:%Y-%m-%d}/data.parquet"
    write_parquet(path, rows)
