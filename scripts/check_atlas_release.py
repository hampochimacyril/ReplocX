#!/usr/bin/env python3
"""W4 private-auth, certified-tier, and public-image boundary smoke.

This check starts the stdlib app on an ephemeral loopback port and fronts it
with a tiny test-only Basic-auth proxy that mirrors the committed Caddy/nginx
header contract. It does not deploy or copy canonical data.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import atlas_service  # noqa: E402
from backend.atlas_service import reset_atlas_cache  # noqa: E402
from backend.server import Handler  # noqa: E402

APP_TOKEN = "w4-ephemeral-app-token"
BASIC_USER = "atlas-reviewer"
BASIC_PASSWORD = "w4-ephemeral-basic-password"
BASIC_AUTH = "Basic " + base64.b64encode(f"{BASIC_USER}:{BASIC_PASSWORD}".encode()).decode()
APP_HEADER = {"Authorization": f"Bearer {APP_TOKEN}"}
PROXY_HEADERS = {"Authorization": BASIC_AUTH, "X-RLE-Auth": APP_TOKEN}


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"  ok: {message}")


def _request(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes, dict[str, str]]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers)


def _json_get(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    status, body, _ = _request(url, headers)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL: expected JSON from {url}, got status {status}") from exc
    return status, payload


class QuietAppHandler(Handler):
    def log_message(self, _format: str, *args: object) -> None:
        return


class BasicAuthProxyHandler(BaseHTTPRequestHandler):
    upstream = ""

    def log_message(self, _format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.headers.get("Authorization") != BASIC_AUTH:
            body = b'{"error":"Basic authentication required."}'
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.send_header("WWW-Authenticate", 'Basic realm="ReplocX Research Atlas"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        app_token = self.headers.get("X-RLE-Auth", "")
        upstream_request = urllib.request.Request(
            f"{self.upstream}{self.path}",
            headers={
                "Accept": self.headers.get("Accept", "*/*"),
                "Authorization": f"Bearer {app_token}",
                "Host": "atlas-app",
                "X-Forwarded-Proto": "https",
            },
        )
        try:
            response = urllib.request.urlopen(upstream_request, timeout=30)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            body = response.read()
            self.send_response(response.status)
            self.send_header("Content-Type", response.headers.get("Content-Type", "application/octet-stream"))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


@contextmanager
def _server(handler: type[BaseHTTPRequestHandler]) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextmanager
def _environment(values: dict[str, str | None]) -> Iterator[None]:
    old = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        reset_atlas_cache()
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        reset_atlas_cache()


def _walk_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def _assert_current_payload(payload: dict[str, Any], route: str) -> None:
    tier = payload.get("tier_id")
    if tier is not None:
        _check(tier == atlas_service.CERTIFIED_TIER_ID, f"{route} uses the certified tier")
    order = payload.get("scenario_order")
    if order is not None:
        _check(order == list(atlas_service.EXPECTED_SCENARIO_ORDER), f"{route} uses A/C/B/D")
    strings = list(_walk_strings(payload))
    _check(not any("f2v2_final" in item for item in strings), f"{route} has no superseded f2v2 link")
    _check(not any("f1v2" in item.lower() for item in strings), f"{route} has no superseded f1v2 link")


def _private_smoke(data_dir: Path, figure_dir: Path) -> None:
    print("[1] private app + reverse-proxy authentication")
    env = {
        atlas_service.ENABLE_ENV: "1",
        atlas_service.DATA_DIR_ENV: str(data_dir),
        atlas_service.FIGURE_DIR_ENV: str(figure_dir),
        "RLE_REQUIRE_AUTH": "1",
        "RLE_PRIVATE_AUTH_TOKEN": APP_TOKEN,
    }
    with _environment(env), _server(QuietAppHandler) as app:
        BasicAuthProxyHandler.upstream = app
        with _server(BasicAuthProxyHandler) as proxy:
            for path in ("/atlas", "/api/v1/results/provenance", "/api/v1/equity/profiles"):
                status, _, _ = _request(f"{proxy}{path}")
                _check(status == 401, f"proxy blocks unauthenticated {path}")

            status, _ = _json_get(f"{app}/api/v1/results/provenance")
            _check(status == 401, "app blocks results without its token")
            status, _ = _json_get(f"{app}/api/v1/equity/profiles")
            _check(status == 401, "app blocks equity without its token")

            status, _ = _json_get(
                f"{proxy}/api/v1/results/provenance",
                {"Authorization": BASIC_AUTH},
            )
            _check(status == 401, "Basic auth alone is insufficient at the app gate")

            status, _, _ = _request(f"{proxy}/atlas", {"Authorization": BASIC_AUTH})
            _check(status == 200, "Basic-authenticated Atlas frontend route returns 200")
            status, provenance = _json_get(f"{proxy}/api/v1/results/provenance", PROXY_HEADERS)
            _check(status == 200, "Basic + app token returns 200 for results")
            status, equity = _json_get(f"{proxy}/api/v1/equity/profiles", PROXY_HEADERS)
            _check(status == 200, "Basic + app token returns 200 for equity")

            _check(provenance["tier_id"] == atlas_service.CERTIFIED_TIER_ID, "provenance tier is 4scen")
            _check(provenance["certified_cell_count"] == 720, "provenance certifies 720 cells")
            _check(provenance["r9_status"] == "PASS", "provenance reports R9 PASS")
            _check(provenance["figure_registry_tier"] == "f2v3_final", "provenance reports f2v3_final")
            _check(equity["catchment_profile_status"] == "READY", "equity profile is READY")
            _check(equity["layers"]["verified_layer_count"] == 4, "equity has 4 ready layers")
            _check(equity["layers"]["source_record_count"] == 20, "equity has 20 catchment records")
            _check(equity["missing_source_path"] is None, "equity has no missing source path")
            _check(Path(equity["source_csv"]) == data_dir / "equity_profile.csv", "equity source_csv is canonical")
            _check(
                Path(equity["provenance_sidecar"]) == Path(f"{data_dir / 'equity_profile.csv'}.prov.json"),
                "equity provenance sidecar is canonical",
            )

            print("[2] certified route/figure/export audit")
            routes = [
                "/api/v1/results/overview",
                "/api/v1/results/scenario-dictionary",
                "/api/v1/results/scenario-summary?tier=annual",
                "/api/v1/results/scenario-summary?tier=seasonal",
                "/api/v1/results/scenario-c?tier=annual",
                "/api/v1/results/d-comparisons?tier=annual",
                "/api/v1/results/differential?tier=annual",
                "/api/v1/results/figures",
                "/api/v1/results/figure-source?figure_id=Fig02",
                "/api/v1/results/figure-bundle?figure_id=Fig02",
                "/api/v1/results/exports",
                "/api/v1/results/export-view?view=scenario-summary&tier=annual",
                "/api/v1/results/export-view?view=d-comparisons&tier=annual",
                "/api/v1/results/export-view?view=equity-profiles",
                "/api/v1/results/cooling-seasons",
                "/api/v1/results/sensitivity",
                "/api/v1/results/provenance",
                "/api/v1/equity/profiles",
                "/api/v1/equity/scenario-cross?scenario=D&dimension=climate",
            ]
            routes.extend(
                f"/api/v1/results/by-stratum?tier={tier}&dimension={dimension}"
                for tier in ("annual", "seasonal")
                for dimension in ("climate", "urbanicity", "stratum", "building", "vintage")
            )
            for route in routes:
                status, payload = _json_get(f"{app}{route}", APP_HEADER)
                _check(status == 200, f"{route} returns 200")
                _assert_current_payload(payload, route)
                if "dimension=stratum" in route:
                    _check(payload["contract_version"] == "atlas.strata/1.0", f"{route} uses N3 contract")
                    _check(payload["stratum_count"] == 20, f"{route} exposes 20 strata")
                    _check(len(payload["rows"]) == 80, f"{route} exposes 80 A/C/B/D rows")
                    _check(
                        all(
                            row["n_cells"] == atlas_service.CERTIFIED_CELLS_PER_STRATUM_SCENARIO
                            for row in payload["rows"]
                        ),
                        f"{route} retains nine certified cells per stratum/scenario",
                    )
                    _check(
                        payload["certified_provenance"]["r9_status"] == "PASS",
                        f"{route} retains R9 provenance",
                    )
                    _check(
                        payload["certified_provenance"]["figure_registry_tier"] == "f2v3_final",
                        f"{route} retains f2v3 provenance",
                    )


def _public_smoke() -> None:
    print("[3] public-demo disabled/leak boundary")
    env = {
        atlas_service.ENABLE_ENV: "0",
        atlas_service.DATA_DIR_ENV: None,
        atlas_service.FIGURE_DIR_ENV: None,
        "RLE_REQUIRE_AUTH": None,
        "RLE_PRIVATE_AUTH_TOKEN": None,
    }
    with _environment(env), _server(QuietAppHandler) as app:
        status, health = _json_get(f"{app}/api/v1/health")
        _check(status == 200, "public health returns 200")
        _check(health["atlas_enabled"] is False, "public health reports Atlas disabled")
        for route in (
            "/api/v1/results/overview",
            "/api/v1/results/provenance",
            "/api/v1/results/by-stratum?dimension=stratum",
            "/api/v1/equity/profiles",
            "/api/v1/equity/scenario-cross",
        ):
            status, payload = _json_get(f"{app}{route}")
            _check(status == 404, f"public {route} returns 404")
            _check("not enabled" in str(payload.get("error", "")).lower(), f"{route} explains disabled state")


def _runtime_file_scan(figure_dir: Path) -> None:
    print("[4] public Docker build-context/runtime file scan")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    _check("COPY . /app" not in dockerfile, "runtime Docker stage has no broad COPY")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    for ignored in ("data/atlas/", "pipeline/out/", "tests/fixtures/atlas/", "docs/atlas/screenshots/"):
        _check(ignored in dockerignore, f"public build context excludes {ignored}")

    runtime_roots = (
        ROOT / "backend",
        ROOT / "data" / "demo",
        ROOT / "data" / "zip_crosswalk_demo.csv",
        ROOT / "frontend" / "dist",
    )
    runtime_files: list[Path] = []
    for root in runtime_roots:
        if root.is_file():
            runtime_files.append(root)
        elif root.is_dir():
            runtime_files.extend(path for path in root.rglob("*") if path.is_file())
    _check(bool(runtime_files), "runtime allowlist resolves to files")
    _check(not any(path.name.endswith(".prov.json") for path in runtime_files), "no provenance sidecar is baked")
    _check(
        not any("replocx_tmy3_wallfix_4scen" in str(path) for path in runtime_files),
        "no certified 4scen data path is baked",
    )
    _check(not any("f2v3_final" in str(path) for path in runtime_files), "no f2v3 asset path is baked")

    canonical_asset_names = {
        path.name
        for path in figure_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".png", ".pdf", ".svg"}
    }
    collisions = sorted(path.name for path in runtime_files if path.name in canonical_asset_names)
    _check(not collisions, f"no canonical f2v3 asset basenames are baked ({len(collisions)} collisions)")
    print(
        f"  evidence: scanned {len(runtime_files)} runtime files against "
        f"{len(canonical_asset_names)} canonical f2v3 asset/table names"
    )

    caddy = (ROOT / "deploy" / "atlas-private" / "Caddyfile").read_text(encoding="utf-8")
    _check("basic_auth" in caddy, "Caddy edge requires Basic auth")
    _check('Authorization "Bearer {http.request.header.X-RLE-Auth}"' in caddy, "Caddy translates app token")
    compose = (ROOT / "docker-compose.atlas-private.example.yml").read_text(encoding="utf-8")
    _check('RLE_ENABLE_ATLAS: "1"' in compose, "private profile enables Atlas")
    _check(compose.count(":ro") >= 4, "private profile uses read-only config/data/figure mounts")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=atlas_service.CANONICAL_DATA_ROOT)
    parser.add_argument("--figure-dir", type=Path, default=atlas_service.CANONICAL_FIGURE_ROOT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    data_dir = args.data_dir.expanduser()
    figure_dir = args.figure_dir.expanduser()
    _check(data_dir.is_dir(), f"certified data root is reachable: {data_dir}")
    _check(figure_dir.is_dir(), f"certified figure root is reachable: {figure_dir}")
    _check((data_dir / "equity_profile.csv").is_file(), "equity_profile.csv exists")
    _check(Path(f"{data_dir / 'equity_profile.csv'}.prov.json").is_file(), "equity sidecar exists")

    _private_smoke(data_dir, figure_dir)
    _public_smoke()
    _runtime_file_scan(figure_dir)
    print("\nW4 Atlas release boundary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
