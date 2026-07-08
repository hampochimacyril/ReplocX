"""Shared provenance helpers for the live ancillary-data fetchers (Session 3).

Every real ``--source api`` download or dictionary load should leave behind an
auditable record: where it came from, when it was fetched, how big it was, and a
SHA-256 of the exact bytes used. These helpers keep that recording consistent
across :mod:`pipeline.fetch_hud_crosswalk`, :mod:`pipeline.geometry`,
:mod:`pipeline.weather_qc`, and :mod:`pipeline.resstock_dictionary` without each
module re-implementing it.

All helpers are pure-stdlib and offline-safe; they record metadata about bytes
the caller already has in hand, so they run identically under fixture and api
sources.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import config


def _repo_relative(path: Path) -> str:
    """Path relative to the repo root when possible (no machine-specific absolutes)."""

    try:
        return str(path.resolve().relative_to(config.APP_ROOT))
    except ValueError:
        return path.name


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string (second precision, ``Z`` style)."""

    return datetime.now(UTC).isoformat()


def sha256_bytes(data: bytes) -> str:
    """SHA-256 hex digest of ``data``."""

    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """SHA-256 hex digest of a file's contents (streamed)."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_record(url: str, data: bytes, *, cached_file: str | None = None) -> dict[str, Any]:
    """A provenance entry for one downloaded payload.

    Records the source URL, byte length, content SHA-256, and fetch timestamp so
    a reviewer can confirm a rerun used the same upstream bytes.
    """

    record: dict[str, Any] = {
        "url": url,
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "downloaded_at_utc": utc_now_iso(),
    }
    if cached_file is not None:
        record["cached_file"] = cached_file
    return record


def file_record(path: str | Path) -> dict[str, Any]:
    """A provenance entry for a local file used as an input (e.g. a dictionary)."""

    p = Path(path)
    return {
        "file": _repo_relative(p),
        "bytes": p.stat().st_size if p.exists() else 0,
        "sha256": sha256_file(p) if p.exists() else "",
        "read_at_utc": utc_now_iso(),
    }


def write_sidecar(path: str | Path, payload: dict[str, Any]) -> Path:
    """Write a provenance sidecar JSON next to an output, returning its path."""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return out
