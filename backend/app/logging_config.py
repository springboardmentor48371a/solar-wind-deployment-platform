"""
Structured logging for the platform. Every log line is a single JSON
object — this is what "monitoring and logging setup" (PDF item 14) means
in practice for a project this size: not a full Prometheus/Sentry stack,
but logs that a log aggregator (or a grep/jq pipeline, or CloudWatch,
or Docker's own `json-file` driver) can actually parse and query.

Two things are wired up:
  1. `configure_logging()` — call once at startup. Formats every log
     record (uvicorn's own + ours) as one JSON line with a timestamp,
     level, logger name, and message.
  2. `RequestLoggingMiddleware` — logs one line per HTTP request with
     method, path, status code, latency, client IP, and the
     authenticated user id if the request carried a valid token. This is
     the audit-adjacent request log; app/routers/audit.py's AuditLog
     table remains the source of truth for "who did what" business
     events — this is the lower-level "what did the server do" log.
"""

import json
import logging
import time
import traceback
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Extra structured fields passed via logger.info(..., extra={...})
        for key in ("request_id", "method", "path", "status_code", "latency_ms", "user_id", "ip"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Keep uvicorn's own loggers flowing through the same JSON formatter
    # instead of its default colored text, so a single log stream (stdout,
    # in a Docker container) is uniformly parseable.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers = [handler]
        logging.getLogger(name).propagate = False


request_logger = logging.getLogger("swdip.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            latency_ms = round((time.monotonic() - start) * 1000, 2)
            request_logger.exception(
                "unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "latency_ms": latency_ms,
                    "ip": request.client.host if request.client else None,
                },
            )
            raise

        latency_ms = round((time.monotonic() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        request_logger.info(
            "request handled",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "ip": request.client.host if request.client else None,
            },
        )
        return response
