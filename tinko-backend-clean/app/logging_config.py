"""
Structured logging configuration using structlog.
"""
import structlog
import logging
import sys
from typing import Any, Dict

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)


def add_app_context(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """Add application context to log entries."""
    event_dict['app'] = 'stealth-recovery'
    event_dict['environment'] = 'development'  # Override via env var in production
    return event_dict


def configure_logging():
    """Configure structlog with processors."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            add_app_context,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Initialize logging
configure_logging()


def get_logger(name: str = __name__):
    """Get a structured logger instance."""
    return structlog.get_logger(name)
