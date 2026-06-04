#!/usr/bin/env python3
"""Dependency-free local server for the Representative Location Explorer."""

from __future__ import annotations

import argparse
import csv
import io
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .data_service import APP_ROOT
from .service import ServiceUnavailableError, get_service, health


FRONTEND = APP_ROOT / "frontend"

# Same-origin only: the UI loads a local ES module and stylesheet, sets inline
# style attributes, and renders inline SVG. No external origins, no inline
# <script>, no eval. This policy is deliberately strict while remaining
# compatible with that surface.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
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


class Handler(BaseHTTPRequestHandler):
    server_version = "RLE/1.1"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for header, value in SECURITY_HEADERS.items():
            self.send_header(header, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: object) -> None:
        self._send(status, json.dumps(payload, indent=2).encode("utf-8"), "application/json; charset=utf-8")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_HEAD(self) -> None:  # noqa: N802 - http.server naming
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802 - http.server naming
        route = urlparse(self.path)
        try:
            if route.path == "/api/health":
                return self._json(200, health())
            if route.path == "/api/dashboard":
                return self._json(200, get_service().dashboard())
            if route.path == "/api/provenance":
                return self._json(200, get_service().provenance())
            if route.path == "/api/candidates":
                filters = {key: values[0] for key, values in parse_qs(route.query).items()}
                return self._json(200, get_service().candidates_page(filters))
            if route.path.startswith("/api/zip/"):
                return self._json(200, get_service().zip_lookup(unquote(route.path.rsplit("/", 1)[-1])))
            return self._static(route.path)
        except ServiceUnavailableError as exc:
            self._json(503, {"error": str(exc)})
        except LookupError as exc:
            self._json(404, {"error": str(exc)})
        except (ValueError, FileNotFoundError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - last-resort HTTP boundary
            self._json(500, {"error": f"Unexpected server error: {exc}"})

    def do_POST(self) -> None:  # noqa: N802 - http.server naming
        route = urlparse(self.path)
        try:
            if route.path == "/api/scenarios/evaluate":
                return self._json(200, get_service().evaluate(self._body()))
            if route.path == "/api/exports/site-list.csv":
                result = get_service().evaluate(self._body())
                fields = [
                    "climate_region", "urbanicity_short", "catchment_type", "catchment_code",
                    "catchment_label", "scenario_rank", "scenario_score", "scenario_note",
                    "selected_station_name", "station_distance_miles", "nrel_filter_field",
                    "nrel_filter_value", "nrel_verification_status", "hourly_weather_qc_status",
                ]
                buffer = io.StringIO()
                writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(result["selected"])
                return self._send(200, buffer.getvalue().encode("utf-8"), "text/csv; charset=utf-8")
            self._json(404, {"error": "Route not found."})
        except ServiceUnavailableError as exc:
            self._json(503, {"error": str(exc)})
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - last-resort HTTP boundary
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
    print(f"Representative Location Explorer {probe['version']}: http://{args.host}:{args.port}", flush=True)
    if probe["data_ready"]:
        print(f"  Analytical inputs loaded: {probe['candidate_count']} candidates "
              f"from {probe['analysis_directory']}", flush=True)
    else:
        print("  WARNING: analytical inputs not loaded yet; the UI will show a clear "
              "message and /api/health reports 'degraded' until the data directory is available.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

