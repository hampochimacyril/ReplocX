"""Managed-dependency FastAPI entry point for deployment environments."""

from __future__ import annotations

import csv
import io
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from . import exports
from .api import SECURITY_HEADERS, frontend_dir, normalize_api_path, openapi_schema
from .auth import AuthConfigurationError, AuthError, require_api_auth
from .observability import capture_exception, log_event
from .scenario_store import ScenarioNotFound, ScenarioStore
from .service import APP_VERSION, ServiceUnavailableError, get_service
from .service import health as service_health

FRONTEND = frontend_dir()
SCENARIOS = ScenarioStore.from_env()
app = FastAPI(
    title="ReplocX",
    description="Transparent representative-location selection for building-stock simulation.",
    version=APP_VERSION,
)


@app.middleware("http")
async def production_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    api_path = normalize_api_path(request.url.path)
    try:
        require_api_auth(api_path, request.headers)
        response = await call_next(request)
    except AuthConfigurationError as exc:
        response = JSONResponse(status_code=503, content={"error": str(exc)})
    except AuthError as exc:
        response = JSONResponse(status_code=401, content={"error": str(exc)})
    except Exception as exc:  # pragma: no cover - FastAPI boundary
        capture_exception(exc, method=request.method, path=request.url.path)
        raise

    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    log_event(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.perf_counter() - started_at) * 1000, 3),
    )
    return response


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"error": str(exc)})


class ScenarioPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = "1.0"
    name: str = "User-defined scenario"
    density_screen_percentile: float = 0.60
    weights: dict[str, float] | None = None
    unique_location_constraint: bool = True
    max_station_distance_miles: float = 250.0
    station_distance_penalty: float = 0.0
    require_weather_qc: bool = False
    overrides: list[dict[str, Any]] | None = None
    parent_id: str | None = None
    base_scenario_id: str | None = None

    def scenario_dict(self) -> dict[str, Any]:
        payload = self.model_dump(exclude_none=True)
        if self.weights is None:
            payload.pop("weights", None)
        return payload


@app.get("/api/health", include_in_schema=False)
@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return service_health()


@app.get("/api/openapi.json", include_in_schema=False)
@app.get("/api/v1/openapi.json", include_in_schema=False)
def versioned_openapi() -> dict[str, Any]:
    return openapi_schema()


@app.get("/api/docs", include_in_schema=False)
@app.get("/api/v1/docs", include_in_schema=False)
def api_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/api/dashboard", include_in_schema=False)
@app.get("/api/v1/dashboard")
def dashboard() -> dict[str, Any]:
    return get_service().dashboard()


@app.get("/api/provenance", include_in_schema=False)
@app.get("/api/v1/provenance")
def provenance() -> dict[str, Any]:
    return get_service().provenance()


@app.get("/api/geometry", include_in_schema=False)
@app.get("/api/v1/geometry")
def geometry() -> dict[str, Any]:
    return get_service().geometry()


@app.get("/api/candidates", include_in_schema=False)
@app.get("/api/v1/candidates")
def candidates(
    search: str = "",
    climate: str = "",
    urbanicity: str = "",
    selected_only: bool = False,
    limit: int = Query(250, ge=1, le=3000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return get_service().candidates_page(
        {
            "search": search,
            "climate": climate,
            "urbanicity": urbanicity,
            "selected_only": str(selected_only).lower(),
            "limit": str(limit),
            "offset": str(offset),
        }
    )


@app.get("/api/scenarios", include_in_schema=False)
@app.get("/api/v1/scenarios")
def saved_scenarios(limit: int = Query(50, ge=1, le=250)) -> dict[str, Any]:
    return SCENARIOS.list(limit)


@app.get("/api/scenarios/{scenario_id}", include_in_schema=False)
@app.get("/api/v1/scenarios/{scenario_id}")
def saved_scenario(scenario_id: str) -> dict[str, Any]:
    try:
        return SCENARIOS.get(scenario_id)
    except ScenarioNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/zip/{zip_code}", include_in_schema=False)
@app.get("/api/v1/zip/{zip_code}")
def zip_lookup(zip_code: str) -> dict[str, Any]:
    try:
        return get_service().zip_lookup(zip_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/scenarios/evaluate", include_in_schema=False)
@app.post("/api/v1/scenarios/evaluate")
def evaluate(payload: ScenarioPayload) -> dict[str, Any]:
    try:
        return get_service().evaluate(payload.scenario_dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/scenarios", include_in_schema=False)
@app.post("/api/v1/scenarios", status_code=201)
def save_scenario(payload: ScenarioPayload) -> dict[str, Any]:
    scenario_config = payload.scenario_dict()
    result = get_service().evaluate(scenario_config)
    save_config = dict(result["config"])
    for key in ("parent_id", "base_scenario_id"):
        if scenario_config.get(key):
            save_config[key] = scenario_config[key]
    return SCENARIOS.save(save_config, result)


@app.post("/api/exports/site-list.csv", include_in_schema=False)
@app.post("/api/v1/exports/site-list.csv")
def export_site_list(payload: ScenarioPayload) -> Response:
    result = evaluate(payload)
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
    return Response(buffer.getvalue(), media_type="text/csv")


@app.post("/api/exports/resstock-sampling.csv", include_in_schema=False)
@app.post("/api/v1/exports/resstock-sampling.csv")
def export_resstock_sampling(payload: ScenarioPayload) -> Response:
    """ResStock/ComStock downselect input (one parameter=option row per site)."""
    result = evaluate(payload)
    return Response(exports.resstock_sampling_csv(result["selected"]), media_type="text/csv")


@app.post("/api/exports/openstudio-manifest.json", include_in_schema=False)
@app.post("/api/v1/exports/openstudio-manifest.json")
def export_openstudio_manifest(payload: ScenarioPayload) -> dict[str, Any]:
    """OpenStudio/EnergyPlus-ready manifest pairing each site with its ISD station."""
    result = evaluate(payload)
    return exports.openstudio_manifest(result["selected"], get_service().provenance())


# Hashed Vite assets live under frontend/dist/assets. check_dir=False keeps the
# mount valid even before the React app is built (the source fallback has no
# assets/ dir yet).
app.mount("/assets", StaticFiles(directory=str(FRONTEND / "assets"), check_dir=False), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def static_app(path: str) -> Response:
    """Serve a built static file, or fall back to index.html for client routes
    (so a direct refresh of /catchments, /methodology, etc. resolves the SPA)."""
    if path == "api" or path.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": "API route not found."})
    candidate = (FRONTEND / path).resolve()
    if path and FRONTEND.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(FRONTEND / "index.html")
