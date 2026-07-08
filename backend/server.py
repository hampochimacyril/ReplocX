#!/usr/bin/env python3
"""Dependency-free local server for ReplocX."""

from __future__ import annotations

import argparse
import csv
import io
import json
import mimetypes
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from . import exports
from .api import SECURITY_HEADERS, frontend_dir, is_api_path, normalize_api_path, openapi_schema
from .atlas_routes import handle_atlas, is_atlas_path
from .atlas_service import AtlasUnavailableError
from .auth import AuthConfigurationError, AuthError, require_api_auth
from .observability import capture_exception, log_event
from .scenario_store import ScenarioNotFound, ScenarioStore
from .service import ServiceUnavailableError, get_service, health

FRONTEND = frontend_dir()
SCENARIOS = ScenarioStore.from_env()


class Handler(BaseHTTPRequestHandler):
    server_version = "ReplocX/1.2"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        started_at = getattr(self, "_started_at", time.perf_counter())
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for header, value in SECURITY_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        log_event(
            "http_request",
            method=self.command,
            path=self.path,
            status=status,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
        )

    def _json(self, status: int, payload: object) -> None:
        self._send(status, json.dumps(payload, indent=2).encode("utf-8"), "application/json; charset=utf-8")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def _authorize(self, path: str) -> bool:
        try:
            require_api_auth(path, self.headers)
            return True
        except AuthConfigurationError as exc:
            self._json(503, {"error": str(exc)})
            return False
        except AuthError as exc:
            self._json(401, {"error": str(exc)})
            return False

    def do_HEAD(self) -> None:  # noqa: N802 - http.server naming
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802 - http.server naming
        self._started_at = time.perf_counter()
        route = urlparse(self.path)
        api_path = normalize_api_path(route.path)
        if not self._authorize(api_path):
            return
        try:
            if api_path == "/api/health":
                return self._json(200, health())
            if api_path == "/api/openapi.json":
                return self._json(200, openapi_schema())
            if api_path == "/api/docs":
                return self._json(
                    200,
                    {
                        "openapi": "/api/v1/openapi.json",
                        "swagger_ui": "FastAPI deployments expose interactive Swagger UI at /docs.",
                    },
                )
            if api_path == "/api/dashboard":
                return self._json(200, get_service().dashboard())
            if api_path == "/api/provenance":
                return self._json(200, get_service().provenance())
            if api_path == "/api/geometry":
                return self._json(200, get_service().geometry())
            if api_path == "/api/candidates":
                filters = {key: values[0] for key, values in parse_qs(route.query).items()}
                return self._json(200, get_service().candidates_page(filters))
            if api_path == "/api/scenarios":
                filters = {key: values[0] for key, values in parse_qs(route.query).items()}
                return self._json(200, SCENARIOS.list(int(filters.get("limit", 50))))
            if api_path.startswith("/api/scenarios/"):
                return self._json(200, SCENARIOS.get(unquote(api_path.rsplit("/", 1)[-1])))
            if api_path.startswith("/api/zip/"):
                return self._json(200, get_service().zip_lookup(unquote(api_path.rsplit("/", 1)[-1])))
            if is_atlas_path(api_path):
                params = {key: values[0] for key, values in parse_qs(route.query).items()}
                return self._json(200, handle_atlas(api_path, params))
            if is_api_path(api_path):
                # Unknown API route: return a JSON 404 instead of falling through
                # to the SPA index.html (matches the POST contract on line below).
                return self._json(404, {"error": "Route not found."})
            return self._static(route.path)
        except ScenarioNotFound as exc:
            self._json(404, {"error": str(exc)})
        except AtlasUnavailableError as exc:
            # Feature disabled / data absent: 404 so the public demo never hints
            # at the unpublished private results.
            self._json(404, {"error": str(exc)})
        except ServiceUnavailableError as exc:
            self._json(503, {"error": str(exc)})
        except LookupError as exc:
            self._json(404, {"error": str(exc)})
        except (ValueError, FileNotFoundError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - last-resort HTTP boundary
            capture_exception(exc, method=self.command, path=self.path)
            self._json(500, {"error": f"Unexpected server error: {exc}"})

    def do_POST(self) -> None:  # noqa: N802 - http.server naming
        self._started_at = time.perf_counter()
        route = urlparse(self.path)
        api_path = normalize_api_path(route.path)
        if not self._authorize(api_path):
            return
        try:
            if api_path == "/api/scenarios/evaluate":
                return self._json(200, get_service().evaluate(self._body()))
            if api_path == "/api/scenarios":
                payload = self._body()
                result = get_service().evaluate(payload)
                save_config = dict(result["config"])
                for key in ("parent_id", "base_scenario_id"):
                    if payload.get(key):
                        save_config[key] = payload[key]
                return self._json(201, SCENARIOS.save(save_config, result))
            if api_path == "/api/exports/site-list.csv":
                result = get_service().evaluate(self._body())
                fields = [
                    "climate_region",
                    "urbanicity_short",
                    "catchment_type",
                    "catchment_code",
                    "catchment_label",
                    "scenario_rank",
                    "scenario_score",
                    "scenario_note",
                    "selected_station_name",
                    "station_distance_miles",
                    "nrel_filter_field",
                    "nrel_filter_value",
                    "nrel_verification_status",
                    "hourly_weather_qc_status",
                ]
                buffer = io.StringIO()
                writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(result["selected"])
                return self._send(200, buffer.getvalue().encode("utf-8"), "text/csv; charset=utf-8")
            if api_path == "/api/exports/resstock-sampling.csv":
                result = get_service().evaluate(self._body())
                csv_text = exports.resstock_sampling_csv(result["selected"])
                return self._send(200, csv_text.encode("utf-8"), "text/csv; charset=utf-8")
            if api_path == "/api/exports/openstudio-manifest.json":
                service = get_service()
                result = service.evaluate(self._body())
                manifest = exports.openstudio_manifest(result["selected"], service.provenance())
                return self._json(200, manifest)
            self._json(404, {"error": "Route not found."})
        except ServiceUnavailableError as exc:
            self._json(503, {"error": str(exc)})
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - last-resort HTTP boundary
            capture_exception(exc, method=self.command, path=self.path)
            self._json(500, {"error": f"Unexpected server error: {exc}"})

    def _static(self, route: str) -> None:
        relative = route.strip("/") or "index.html"
        path = (FRONTEND / relative).resolve()
        if FRONTEND.resolve() not in path.parents and path != FRONTEND.resolve():
            return self._json(403, {"error": "Invalid path."})
        if not path.exists() or not path.is_file():
            path = FRONTEND / "index.html"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._send(200, path.read_bytes(), f"{content_type}; charset=utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8787, type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    probe = health()
    print(f"ReplocX {probe['version']}: http://{args.host}:{args.port}", flush=True)
    if probe["data_ready"]:
        print(
            f"  Analytical inputs loaded: {probe['candidate_count']} candidates " f"from {probe['analysis_directory']}",
            flush=True,
        )
    else:
        print(
            "  WARNING: analytical inputs not loaded yet; the UI will show a clear "
            "message and /api/v1/health reports 'degraded' until the data directory is available.",
            flush=True,
        )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
