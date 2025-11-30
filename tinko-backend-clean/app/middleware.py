"""
Middleware for request tracking and logging.
"""
import uuid
from typing import Callable
from fastapi import Request, Response
from structlog.contextvars import bind_contextvars, clear_contextvars
from app.logging_config import get_logger
import time

logger = get_logger(__name__)


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """
    Add unique request_id to each request for tracing.
    Binds request_id to structlog context for all logs in this request.
    """
    # Generate or extract request ID
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    
    # Bind to structlog context (available in all logs during this request)
    clear_contextvars()
    bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )
    
    # Add to request state for access in route handlers
    request.state.request_id = request_id
    
    # Log incoming request
    logger.info(
        "request_started",
        method=request.method,
        path=str(request.url.path),
        client_host=request.client.host if request.client else None,
    )
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Log response
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id
        
        return response
    
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "request_failed",
            exc_info=exc,
            duration_ms=round(duration_ms, 2),
        )
        raise
    finally:
        # Clear context after request
        clear_contextvars()


async def user_context_middleware(request: Request, call_next: Callable) -> Response:
    """
    Add authenticated user context to logs.
    Must be added after authentication middleware.
    """
    response = await call_next(request)
    
    # If user is authenticated, add to log context
    if hasattr(request.state, 'user'):
        user = request.state.user
        bind_contextvars(
            user_id=user.id,
            org_id=user.org_id,
            user_role=user.role,
        )
    
    return response
