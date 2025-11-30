from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from app.config.flags import flag
from .util import safe_http_post, safe_s3_put

try:
    import structlog  # type: ignore
    logger = structlog.get_logger(__name__)
except Exception:  # pragma: no cover
    import logging
    logger = logging.getLogger(__name__)


def emit(event_type: str, payload: Dict[str, Any]) -> None:
    """Emit an analytics record to configured sinks if enabled.

    Never raises; controlled by FEATURE_ANALYTICS_SINK and per-sink flags.
    """
    if not flag("FEATURE_ANALYTICS_SINK"):
        return
    record = {
        "ts": int(time.time()),
        "event_type": event_type,
        "payload": payload,
    }
    try:
        if flag("FEATURE_CLICKHOUSE_SINK"):
            safe_http_post(
                os.getenv("CLICKHOUSE_URL"),
                os.getenv("CLICKHOUSE_DATABASE"),
                os.getenv("CLICKHOUSE_TABLE", "tinko_events"),
                record,
            )
        if flag("FEATURE_S3_SINK"):
            safe_s3_put(os.getenv("S3_BUCKET_NAME"), f"analytics/{record['ts']}-{event_type}.json", json.dumps(record).encode("utf-8"))
    except Exception as e:  # pragma: no cover
        # Guard rail: never throw
        logger.warning("analytics_emit_failed", error=str(e))
