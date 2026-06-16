"""Shared API versioning and schema helpers for both server entry points."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .data_service import APP_ROOT

API_VERSION = "v1"
API_BASE = f"/api/{API_VERSION}"
LEGACY_API_BASE = "/api"


def frontend_dir() -> Path:
    """Resolve the directory of built static assets to serve.

    Prefers the Vite production build (``frontend/dist``) and falls back to the
    frontend source directory, so the server always has a root document to serve
    even before the React app has been built. (The previous vanilla
    ``frontend/legacy`` fallback was removed in Session 8 once the React redesign
    replaced it.)
    """

    base = APP_ROOT / "frontend"
    for candidate in (base / "dist", base):
        if (candidate / "index.html").exists():
            return candidate
    return base


# Same-origin CSP. ``worker-src``/``img-src`` permit the blob URLs MapLibre GL JS
# uses for its render worker and tile/image canvases; both are locally derived,
# so no third-party origin is allowed and the strict same-origin posture holds.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; worker-src 'self' blob:; child-src 'self' blob:; "
    "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def normalize_api_path(path: str) -> str:
    """Map versioned API paths onto the legacy internal route table."""

    if path == API_BASE:
        return LEGACY_API_BASE
    if path.startswith(f"{API_BASE}/"):
        return f"{LEGACY_API_BASE}{path[len(API_BASE):]}"
    return path


def is_api_path(path: str) -> bool:
    return path == LEGACY_API_BASE or path.startswith(f"{LEGACY_API_BASE}/")


def is_public_api_path(path: str) -> bool:
    """API routes that stay public even when private auth is enabled."""

    return path in {"/api/health", "/api/openapi.json", "/api/docs"}


def openapi_schema() -> dict[str, Any]:
    """Lightweight OpenAPI document for the dependency-free stdlib server."""

    from .service import APP_VERSION

    error_response = {
        "description": "Error response",
        "content": {"application/json": {"schema": {"type": "object", "additionalProperties": True}}},
    }
    object_response = {
        "description": "JSON object response",
        "content": {"application/json": {"schema": {"type": "object", "additionalProperties": True}}},
    }
    scenario_payload = {
        "required": True,
        "content": {"application/json": {"schema": {"type": "object", "additionalProperties": True}}},
    }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "ReplocX API",
            "version": APP_VERSION,
            "description": "Versioned API for representative-location selection, scenario storage, and exports.",
        },
        "servers": [{"url": API_BASE}],
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
        "paths": {
            "/health": {"get": {"summary": "Readiness probe", "responses": {"200": object_response}}},
            "/dashboard": {
                "get": {
                    "summary": "Baseline dashboard data",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": object_response, "401": error_response, "503": error_response},
                }
            },
            "/provenance": {
                "get": {
                    "summary": "Source and method provenance",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": object_response, "401": error_response, "503": error_response},
                }
            },
            "/geometry": {
                "get": {
                    "summary": "Selected-catchment GeoJSON",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": object_response, "401": error_response, "503": error_response},
                }
            },
            "/candidates": {
                "get": {
                    "summary": "Filtered candidate ranking page",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {"name": "search", "in": "query", "schema": {"type": "string"}},
                        {"name": "climate", "in": "query", "schema": {"type": "string"}},
                        {"name": "urbanicity", "in": "query", "schema": {"type": "string"}},
                        {"name": "selected_only", "in": "query", "schema": {"type": "boolean"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 3000}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "minimum": 0}},
                    ],
                    "responses": {
                        "200": object_response,
                        "400": error_response,
                        "401": error_response,
                        "503": error_response,
                    },
                }
            },
            "/zip/{zip_code}": {
                "get": {
                    "summary": "Resolve a five-digit ZIP code to simulation context",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {
                            "name": "zip_code",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "pattern": "^[0-9]{5}$"},
                        }
                    ],
                    "responses": {
                        "200": object_response,
                        "400": error_response,
                        "401": error_response,
                        "404": error_response,
                        "503": error_response,
                    },
                }
            },
            "/scenarios": {
                "get": {
                    "summary": "List saved scenarios",
                    "security": [{"BearerAuth": []}],
                    "responses": {"200": object_response, "401": error_response},
                },
                "post": {
                    "summary": "Save a versioned scenario after evaluating it",
                    "security": [{"BearerAuth": []}],
                    "requestBody": scenario_payload,
                    "responses": {
                        "201": object_response,
                        "400": error_response,
                        "401": error_response,
                        "503": error_response,
                    },
                },
            },
            "/scenarios/{scenario_id}": {
                "get": {
                    "summary": "Read a saved scenario by share id",
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {"name": "scenario_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": object_response, "401": error_response, "404": error_response},
                }
            },
            "/scenarios/evaluate": {
                "post": {
                    "summary": "Evaluate a scenario configuration",
                    "security": [{"BearerAuth": []}],
                    "requestBody": scenario_payload,
                    "responses": {
                        "200": object_response,
                        "400": error_response,
                        "401": error_response,
                        "503": error_response,
                    },
                }
            },
            "/exports/site-list.csv": {
                "post": {
                    "summary": "Export selected sites as CSV",
                    "security": [{"BearerAuth": []}],
                    "requestBody": scenario_payload,
                    "responses": {
                        "200": {"description": "CSV site list"},
                        "400": error_response,
                        "401": error_response,
                        "503": error_response,
                    },
                }
            },
            "/exports/resstock-sampling.csv": {
                "post": {
                    "summary": "Export ResStock/ComStock sampling inputs as CSV",
                    "security": [{"BearerAuth": []}],
                    "requestBody": scenario_payload,
                    "responses": {
                        "200": {"description": "CSV sampling downselect"},
                        "400": error_response,
                        "401": error_response,
                        "503": error_response,
                    },
                }
            },
            "/exports/openstudio-manifest.json": {
                "post": {
                    "summary": "Export an OpenStudio/EnergyPlus manifest",
                    "security": [{"BearerAuth": []}],
                    "requestBody": scenario_payload,
                    "responses": {
                        "200": object_response,
                        "400": error_response,
                        "401": error_response,
                        "503": error_response,
                    },
                }
            },
        },
    }
