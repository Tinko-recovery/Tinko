import os
from typing import Any, Dict, Optional
from app.logging_config import get_logger

_logger = get_logger(__name__)

class AnalyticsSink:
    """Optional analytics sink. When disabled, emit() is a no-op.

    Enable via env ANALYTICS_SINK_ENABLED=true. Destination is currently the app log
    with event metadata; can be extended to send to a webhook or analytics pipeline.
    """

    def __init__(self, enabled: bool = False, sink_url: Optional[str] = None) -> None:
        self.enabled = enabled
        self.sink_url = sink_url

    def emit(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return
        # For now, just log structured analytics events.
        try:
            _logger.info("analytics_event", extra={"event": event, "data": data or {}, "sink_url": self.sink_url})
        except Exception:
            # Never raise from analytics path
            pass


_sink: Optional[AnalyticsSink] = None

def get_sink() -> AnalyticsSink:
    global _sink
    if _sink is None:
        enabled = os.getenv("ANALYTICS_SINK_ENABLED", "false").lower() == "true"
        sink_url = os.getenv("ANALYTICS_SINK_URL")
        _sink = AnalyticsSink(enabled=enabled, sink_url=sink_url)
    return _sink
