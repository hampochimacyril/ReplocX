#!/usr/bin/env python3
"""Release-candidate contract check for the ReplocX HTTP surface.

Exercises the stdlib server (``backend.server``) end to end without external
dependencies: health/data-mode, the OpenAPI document, the ``/api/v1`` alias,
strict same-origin security headers, the unknown-route 404 contract, optional
private-deployment auth, scenario persistence/versioning, and the graceful
degraded-mode contract when analytical inputs are missing.

Run directly (``python scripts/check_release_contract.py``); exits non-zero with
a readable message on the first broken guarantee so it can serve as a CI and
``scripts/verify_all.sh`` gate.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"  ok: {message}")


def _get(url: str, headers: dict[str, str] | None = None):
    request = urllib.request.Request(url, headers=headers or {})
    return urllib.request.urlopen(request, timeout=10)


def _post(url: str, body: dict[str, object], headers: dict[str, str] | None = None):
    data = json.dumps(body).encode("utf-8")
    merged = {"Content-Type": "application/json", **(headers or {})}
    request = urllib.request.Request(url, data=data, headers=merged, method="POST")
    return urllib.request.urlopen(request, timeout=10)


def main() -> int:
    # Bind scenario persistence to a throwaway database before importing the
    # server so the real private store is never touched.
    tmp = tempfile.TemporaryDirectory()
    os.environ["RLE_SCENARIO_DB"] = str(Path(tmp.name) / "scenarios.sqlite3")

    from backend.api import SECURITY_HEADERS
    from backend.server import Handler

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"

    try:
        print("[1] health + data mode")
        with _get(f"{base}/api/health") as resp:
            _check(resp.status == 200, "/api/health returns 200")
            health = json.load(resp)
        _check(health.get("status") == "ok", "health status is ok")
        _check(health.get("data_ready") is True, "health reports data_ready")
        _check(health.get("data_mode") == "demo", "default data_mode is demo (public-safe)")

        print("[2] /api/v1 alias")
        with _get(f"{base}/api/v1/health") as resp:
            _check(resp.status == 200, "/api/v1/health alias returns 200")

        print("[3] OpenAPI document")
        with _get(f"{base}/api/openapi.json") as resp:
            schema = json.load(resp)
        _check(str(schema.get("openapi", "")).startswith("3."), "OpenAPI version is 3.x")
        _check(len(schema.get("paths", {})) > 0, "OpenAPI declares paths")

        print("[4] security headers")
        with _get(f"{base}/api/dashboard") as resp:
            for header in ("Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options"):
                _check(resp.headers.get(header) == SECURITY_HEADERS[header], f"{header} present and strict")

        print("[5] unknown API route -> JSON 404 (not the SPA shell)")
        try:
            _get(f"{base}/api/v1/does-not-exist")
            raise SystemExit("FAIL: unknown API route did not return 404")
        except urllib.error.HTTPError as exc:
            _check(exc.code == 404, "unknown API route returns 404")
            payload = json.loads(exc.read().decode("utf-8"))
            _check("error" in payload, "404 body is JSON with an error message")

        print("[6] SPA deep link still served")
        with _get(f"{base}/scenario") as resp:
            _check(resp.status == 200, "/scenario serves the SPA shell")
            _check("text/html" in resp.headers.get("Content-Type", ""), "SPA deep link is text/html")

        print("[7] scenario persistence + versioning")
        with _post(f"{base}/api/scenarios", {"name": "contract", "density_screen_percentile": 0.7}) as resp:
            first = json.load(resp)
        _check(first.get("version") == 1, "first save is version 1")
        with _post(
            f"{base}/api/scenarios",
            {"name": "contract", "parent_id": first["id"], "density_screen_percentile": 0.8},
        ) as resp:
            second = json.load(resp)
        _check(second.get("version") == 2, "child save increments to version 2")
        _check(second.get("parent_id") == first["id"], "child records parent lineage")
        with _get(f"{base}/api/scenarios") as resp:
            listing = json.load(resp)
        _check(int(listing.get("returned", 0)) >= 2, "saved scenarios are listed")

        print("[8] private-deployment auth rejects unauthenticated calls")
        os.environ["RLE_PRIVATE_AUTH_TOKEN"] = "contract-token"
        try:
            try:
                _get(f"{base}/api/dashboard")
                raise SystemExit("FAIL: protected route allowed an unauthenticated request")
            except urllib.error.HTTPError as exc:
                _check(exc.code == 401, "no token -> 401")
            with _get(f"{base}/api/dashboard", headers={"Authorization": "Bearer contract-token"}) as resp:
                _check(resp.status == 200, "valid Bearer token -> 200")
            with _get(f"{base}/api/health") as resp:
                _check(resp.status == 200, "health stays public under auth")
        finally:
            os.environ.pop("RLE_PRIVATE_AUTH_TOKEN", None)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        tmp.cleanup()

    print("[9] graceful degraded mode (missing analytical inputs)")
    snippet = (
        "from backend import service\n"
        "h = service.health()\n"
        "assert h['status'] == 'degraded' and h['data_ready'] is False, h\n"
        "try:\n"
        "    service.get_service()\n"
        "    raise SystemExit('expected ServiceUnavailableError')\n"
        "except service.ServiceUnavailableError:\n"
        "    print('  ok: degraded-mode contract holds')\n"
    )
    env = dict(os.environ, RLE_ANALYSIS_DATA_DIR="/nonexistent/release-contract")
    result = subprocess.run([sys.executable, "-c", snippet], cwd=str(ROOT), env=env)
    if result.returncode != 0:
        raise SystemExit("FAIL: degraded-mode contract did not hold")

    print("\nRelease contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
