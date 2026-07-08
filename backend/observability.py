"""Free-tier observability hooks: structured logs and optional Sentry capture."""

from __future__ import annotations

import json
import logging
import os
import time
import traceback
from typing import Any

LOGGER = logging.getLogger("replocx")
_CONFIGURED = False
_SENTRY_READY = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = os.environ.get("RLE_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, level, logging.INFO), format="%(message)s")
    _CONFIGURED = True


def _json_default(value: object) -> str:
    return str(value)


def log_event(event: str, **fields: Any) -> None:
    configure_logging()
    payload = {
        "event": event,
        "service": "replocx",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **fields,
    }
    LOGGER.info(json.dumps(payload, sort_keys=True, default=_json_default))


def capture_exception(exc: BaseException, **context: Any) -> None:
    log_event(
        "exception",
        error_type=type(exc).__name__,
        error=str(exc),
        traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        **context,
    )
    _capture_sentry(exc, context)


def _capture_sentry(exc: BaseException, context: dict[str, Any]) -> None:
    dsn = os.environ.get("RLE_SENTRY_DSN", "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk  # type: ignore
    except ImportError:
        log_event("sentry_unavailable", reason="sentry_sdk is not installed")
        return

    global _SENTRY_READY
    if not _SENTRY_READY:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=float(os.environ.get("RLE_SENTRY_TRACES_SAMPLE_RATE", "0")))
        _SENTRY_READY = True
    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(exc)
