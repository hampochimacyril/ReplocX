"""Managed-dependency FastAPI entry point for deployment environments."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from .data_service import APP_ROOT, DataService


FRONTEND = APP_ROOT / "frontend"
SERVICE = DataService()
app = FastAPI(
    title="Representative Location Explorer",
    description="Transparent representative-location selection for building-stock simulation.",
    version="1.0.0",
)


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

    def scenario_dict(self) -> dict[str, Any]:
        payload = self.model_dump(exclude_none=True)
        if self.weights is None:
            payload.pop("weights", None)
        return payload


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Representative Location Explorer"}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    return SERVICE.dashboard()


@app.get("/api/provenance")
def provenance() -> dict[str, Any]:
    return SERVICE.provenance()


@app.get("/api/candidates")
def candidates(
    search: str = "",
    climate: str = "",
    urbanicity: str = "",
    selected_only: bool = False,
    limit: int = Query(250, ge=1, le=3000),
) -> dict[str, Any]:
    return SERVICE.candidates_page(
        {
            "search": search,
            "climate": climate,
            "urbanicity": urbanicity,
            "selected_only": str(selected_only).lower(),
            "limit": str(limit),
        }
    )


@app.get("/api/zip/{zip_code}")
def zip_lookup(zip_code: str) -> dict[str, Any]:
    try:
        return SERVICE.zip_lookup(zip_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/scenarios/evaluate")
def evaluate(payload: ScenarioPayload) -> dict[str, Any]:
    try:
        return SERVICE.evaluate(payload.scenario_dict())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/exports/site-list.csv")
def export_site_list(payload: ScenarioPayload) -> Response:
    result = evaluate(payload)
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
    return Response(buffer.getvalue(), media_type="text/csv")


app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def static_app(path: str) -> FileResponse:
    candidate = (FRONTEND / path).resolve()
    if path and FRONTEND.resolve() in candidate.parents and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(FRONTEND / "index.html")

