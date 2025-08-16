from __future__ import annotations

import gzip
import io
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

# Lazy import to avoid hard dependency during basic tests
try:
    import boto3  # type: ignore
    import s3fs  # type: ignore
    import pandas as pd  # type: ignore
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore
except Exception:  # pragma: no cover
    boto3 = None
    s3fs = None
    pd = None
    pa = None
    pq = None


@dataclass(frozen=True)
class S3Config:
    endpoint_url: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    access_key: str = os.getenv("MINIO_ACCESS_KEY", "minio")
    secret_key: str = os.getenv("MINIO_SECRET_KEY", "minio123")
    bucket: str = os.getenv("MINIO_BUCKET", "crawler")
    region: str = os.getenv("MINIO_REGION", "us-east-1")
    force_path_style: bool = os.getenv("S3_FORCE_PATH_STYLE", "true").lower() == "true"


def _client():  # type: ignore
    if boto3 is None:
        raise RuntimeError("boto3 not available. Install dependencies to use storage features.")
    from boto3.session import Config as BotoConfig  # type: ignore

    cfg = S3Config()
    return boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
        config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path" if cfg.force_path_style else "auto"}),
        region_name=cfg.region,
    )


def put_gz(key: str, data: bytes, content_type: str = "text/html; charset=utf-8", metadata: Dict[str, str] | None = None) -> None:
    s3 = _client()
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(data)
    s3.put_object(
        Bucket=S3Config().bucket,
        Key=key,
        Body=buf.getvalue(),
        ContentEncoding="gzip",
        ContentType=content_type,
        Metadata=metadata or {},
    )


def write_parquet(path: str, records: List[Dict[str, Any]]) -> None:
    if s3fs is None or pa is None:
        raise RuntimeError("Parquet write dependencies not available (s3fs/pyarrow).")
    fs = s3fs.S3FileSystem(
        client_kwargs={"endpoint_url": S3Config().endpoint_url},
        key=S3Config().access_key,
        secret=S3Config().secret_key,
    )
    with fs.open(path, "wb") as f:
        import pandas as pd  # type: ignore  # ensure lazy import works even if global pd is None
        table = pa.Table.from_pydict({k: [row.get(k) for row in records] for k in {k for r in records for k in r.keys()}})
        pq.write_table(table, f, compression="zstd")
