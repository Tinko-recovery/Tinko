from __future__ import annotations

import json
import os
from typing import Any, Optional

try:
    import structlog  # type: ignore
    logger = structlog.get_logger(__name__)
except Exception:  # pragma: no cover
    import logging
    logger = logging.getLogger(__name__)


def safe_http_post(url: Optional[str], database: Optional[str], table: Optional[str], record: dict) -> None:
    """Attempt to write a record to ClickHouse via HTTP; never raise.

    Expects the ClickHouse server URL (e.g., http://localhost:8123) and will
    perform an INSERT into database.table using JSONEachRow format.
    """
    if not url or not database or not table:
        logger.warning("analytics_http_disabled", reason="missing_url_or_db_or_table")
        return
    try:
        import httpx  # type: ignore
        query = f"INSERT INTO {database}.{table} FORMAT JSONEachRow"
        data = json.dumps(record).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        # Support optional basic auth via env (CLICKHOUSE_USER/PASSWORD)
        auth = None
        user = os.getenv("CLICKHOUSE_USER")
        pwd = os.getenv("CLICKHOUSE_PASSWORD")
        if user:
            auth = (user, pwd or "")
        with httpx.Client(timeout=3.0) as client:
            client.post(f"{url}/?query={query}", content=data, headers=headers, auth=auth)
    except Exception as e:  # pragma: no cover
        logger.warning("analytics_http_post_failed", error=str(e))


def safe_s3_put(bucket: Optional[str], key: str, body: bytes) -> None:
    """Attempt to write a blob to S3; never raise. Uses boto3 if available."""
    if not bucket:
        logger.warning("analytics_s3_disabled", reason="missing_bucket")
        return
    try:
        import boto3  # type: ignore
        region = os.getenv("S3_REGION") or os.getenv("AWS_DEFAULT_REGION")
        kwargs: dict[str, Any] = {"Bucket": bucket, "Key": key, "Body": body}
        if region:
            s3 = boto3.client("s3", region_name=region)
        else:
            s3 = boto3.client("s3")
        s3.put_object(**kwargs)
    except Exception as e:  # pragma: no cover
        logger.warning("analytics_s3_put_failed", error=str(e))
