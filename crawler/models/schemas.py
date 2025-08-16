from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, HttpUrl


class CrawlJob(BaseModel):
    job_id: str
    source: str
    country: str
    dt: datetime
    max_pages: int = 1000
    render: bool = False
    filters: Dict[str, str] = {}


class PageRaw(BaseModel):
    url: HttpUrl
    fetched_at: datetime
    status: int
    headers: Dict[str, str]
    content_hash: str
    storage_key: str  # s3 path


class Article(BaseModel):
    url: HttpUrl
    title: Optional[str]
    text: Optional[str]
    authors: List[str] = []
    published_at: Optional[datetime]
    country: str
    language: Optional[str]
    source: str
    content_hash: str
