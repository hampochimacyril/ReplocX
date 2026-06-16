"""Stdlib-only Python client for the ReplocX REST API."""

from __future__ import annotations

from .client import RLEClient, RLEClientError

# Preferred product-branded names. The RLE aliases remain for compatibility with
# existing scripts and the published environment-variable/API conventions.
ReplocXClient = RLEClient
ReplocXClientError = RLEClientError

__all__ = [
    "ReplocXClient",
    "ReplocXClientError",
    "RLEClient",
    "RLEClientError",
]
__version__ = "1.0.0"
