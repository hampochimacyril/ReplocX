"""Lazy, fault-tolerant accessor for the shared :class:`DataService` instance.

Both entry points (the dependency-free ``server.py`` and the managed
``fastapi_app.py``) load the same read-only analytical inputs. Constructing the
service eagerly at import time means a missing or unreadable analysis directory
takes the whole process down before it can report a useful error. This module
defers construction until the first request and caches either the live service
or the failure, so the application starts cleanly and surfaces a clear
``503 Service Unavailable`` with remediation guidance instead of a stack trace.
"""

from __future__ import annotations

from typing import Any

from .data_service import DataService

__all__ = ["APP_VERSION", "ServiceUnavailableError", "get_service", "health"]

APP_VERSION = "1.1.0"


class ServiceUnavailableError(RuntimeError):
    """Raised when the read-only analytical inputs cannot be loaded."""


_service: DataService | None = None


def get_service() -> DataService:
    """Return the cached service, constructing it on first use.

    Re-attempts construction on each call until it succeeds, so the process can
    recover once a misconfigured analysis directory is corrected without a
    restart. Failures are normalised to :class:`ServiceUnavailableError` with
    actionable guidance.
    """

    global _service
    if _service is not None:
        return _service
    try:
        _service = DataService()
    except Exception as exc:  # noqa: BLE001 - surfaced to clients as HTTP 503
        raise ServiceUnavailableError(
            "Analytical inputs are not available. Confirm the read-only "
            "analysis directory exists and is readable (set RLE_ANALYSIS_DATA_DIR "
            f"to override the default location). Details: {exc}"
        ) from exc
    return _service


def health() -> dict[str, Any]:
    """Liveness/readiness probe describing whether inputs are loaded."""

    payload: dict[str, Any] = {
        "status": "ok",
        "service": "Representative Location Explorer",
        "version": APP_VERSION,
        "data_ready": False,
    }
    try:
        service = get_service()
    except ServiceUnavailableError as exc:
        payload["status"] = "degraded"
        payload["detail"] = str(exc)
        return payload
    payload["data_ready"] = True
    payload["data_mode"] = getattr(service, "data_mode", "production")
    payload["analysis_directory"] = str(service.analysis_dir)
    payload["candidate_count"] = len(service.candidates)
    payload["selected_count"] = len(service.selected)
    payload["method_version"] = service.metadata.get("method_version")
    return payload
