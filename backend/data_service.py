"""Read-only ingestion layer for analytical outputs and ZIP crosswalk context."""

from __future__ import annotations

import csv
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .models import ScenarioConfig
from .scoring import data_compatible_default_config, evaluate


def _external_data_root(app_root: Path) -> Path:
    """Return the sibling-project root without assuming a deep host path."""

    return app_root.parents[1] if len(app_root.parents) > 1 else app_root.parent


APP_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_DATA_ROOT = _external_data_root(APP_ROOT)
DEFAULT_ANALYSIS_DIR = EXTERNAL_DATA_ROOT / "location_selection" / "data" / "processed"
DEFAULT_RAW_DIR = EXTERNAL_DATA_ROOT / "location_selection" / "data" / "raw"
DEMO_ANALYSIS_DIR = APP_ROOT / "data" / "demo"


def _resolve_analysis_dir() -> tuple[Path, str]:
    """Pick the analysis directory and report which mode is active.

    Precedence: an explicit ``RLE_ANALYSIS_DATA_DIR`` override (used verbatim, so
    a misconfigured path fails loudly) -> the real processed outputs if present
    -> the bundled synthetic demonstration dataset, so a fresh clone, CI runner,
    or reviewer always has something to load.
    """

    override = os.environ.get("RLE_ANALYSIS_DATA_DIR")
    if override:
        return Path(override), "production"
    if (DEFAULT_ANALYSIS_DIR / "candidate_scores.csv").exists():
        return DEFAULT_ANALYSIS_DIR, "production"
    return DEMO_ANALYSIS_DIR, "demo"


def _convert(value: str) -> Any:
    text = value.strip()
    if text == "":
        return ""
    if text in {"True", "False"}:
        return text == "True"
    try:
        if any(char in text for char in ".eE"):
            return float(text)
        return int(text)
    except ValueError:
        return text


def _read_csv(path: Path, code_fields: set[str] | None = None) -> list[dict[str, Any]]:
    code_fields = code_fields or set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = []
        for source in csv.DictReader(handle):
            row = {}
            for key, value in source.items():
                row[key] = value.strip().zfill(5) if key in code_fields and value.strip() else _convert(value)
            rows.append(row)
        return rows


def _as_float(value: Any) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text != "" else None
    except (TypeError, ValueError):
        return None


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.7613
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


class DataService:
    def __init__(self, analysis_dir: Path | None = None, raw_dir: Path | None = None) -> None:
        if analysis_dir is not None:
            self.analysis_dir = analysis_dir
            self.data_mode = "demo" if analysis_dir == DEMO_ANALYSIS_DIR else "production"
        else:
            self.analysis_dir, self.data_mode = _resolve_analysis_dir()
        self.raw_dir = raw_dir or Path(os.environ.get("RLE_RAW_DATA_DIR", DEFAULT_RAW_DIR))
        self.candidates = _read_csv(self.analysis_dir / "candidate_scores.csv", {"catchment_code"})
        self.selected = _read_csv(self.analysis_dir / "selected_locations.csv", {"catchment_code"})
        self.site_list = _read_csv(self.analysis_dir / "resstock_site_list.csv", {"target_catchment_code"})
        self.stratum_status = _read_csv(self.analysis_dir / "stratum_status.csv")
        self.metadata = json.loads((self.analysis_dir / "selection_metadata.json").read_text(encoding="utf-8"))

        # Phase 2 ZIP crosswalk precedence: explicit RLE_ZIP_CROSSWALK override ->
        # a national crosswalk emitted next to the analytical outputs -> the
        # bundled demonstration subset (so a fresh clone / demo still resolves).
        crosswalk_override = os.environ.get("RLE_ZIP_CROSSWALK")
        analysis_crosswalk = self.analysis_dir / "zip_crosswalk.csv"
        if crosswalk_override:
            self.zip_crosswalk_path = Path(crosswalk_override)
            self.zip_crosswalk_mode = "Configured HUD-USPS crosswalk"
        elif analysis_crosswalk.exists():
            self.zip_crosswalk_path = analysis_crosswalk
            self.zip_crosswalk_mode = "HUD-USPS crosswalk (pipeline output)"
        else:
            self.zip_crosswalk_path = APP_ROOT / "data" / "zip_crosswalk_demo.csv"
            self.zip_crosswalk_mode = "Bundled demonstration subset"
        self.zip_crosswalk = _read_csv(
            self.zip_crosswalk_path,
            {"zip_code", "zcta", "county_geoid", "cbsa_code"},
        )

        # Phase 2 per-station hourly weather QC, if the pipeline emitted it.
        self.station_qc = self._load_station_qc(self.analysis_dir / "station_weather_qc.csv")

        self.filter_map = {
            f"{row['target_catchment_type']}:{row['target_catchment_code']}": row for row in self.site_list
        }
        for row in self.candidates:
            row["hourly_weather_qc_status"] = self.weather_qc_status(row)

    @staticmethod
    def _load_station_qc(path: Path) -> dict[str, str]:
        if not path.exists():
            return {}
        return {
            str(row["station_number"]).strip(): str(row["hourly_weather_qc_status"]).strip() for row in _read_csv(path)
        }

    def weather_qc_status(self, row: dict[str, Any]) -> str:
        """Per-station weather QC for a candidate: station map first, then the
        selected-site mapping, then PENDING when no QC has been computed."""

        station = str(row.get("selected_station_number", "")).strip()
        if station and station in self.station_qc:
            return self.station_qc[station]
        mapping = (
            self.filter_map.get(f"{row.get('catchment_type')}:{row.get('catchment_code')}", {})
            if hasattr(self, "filter_map")
            else {}
        )
        return mapping.get("hourly_weather_qc_status", "PENDING")

    def geometry(self) -> dict[str, Any]:
        """Selected-catchment polygons (GeoJSON) for the map, or an empty set."""

        path = self.analysis_dir / "selected_geometry.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"type": "FeatureCollection", "features": []}

    def attach_filter(self, row: dict[str, Any]) -> dict[str, Any]:
        item = dict(row)
        item["location_uniqueness_key"] = (
            item.get("location_uniqueness_key") or f"{item['catchment_type']}:{item['catchment_code']}"
        )
        mapping = self.filter_map.get(item["location_uniqueness_key"], {})
        item.update(
            {
                "nrel_filter_field": mapping.get(
                    "nrel_filter_field",
                    (
                        "in.county"
                        if item["catchment_type"] == "County"
                        else "in.metropolitan_and_micropolitan_statistical_area"
                    ),
                ),
                "nrel_filter_value": mapping.get("nrel_filter_value", ""),
                "nrel_value_verified": bool(mapping.get("nrel_value_verified", False)),
                "nrel_verification_status": "VERIFIED" if mapping.get("nrel_value_verified") else "REVIEW REQUIRED",
                "filter_scope_note": mapping.get(
                    "filter_scope_note",
                    "Exact ResStock enumeration mapping must be curated before simulation export.",
                ),
                "hourly_weather_qc_status": self.weather_qc_status(item),
            }
        )
        return item

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        config = ScenarioConfig.from_dict(payload)
        if payload is None or "overrides" not in payload:
            config = data_compatible_default_config(self.candidates, config)
        result = evaluate(self.candidates, config)
        for key in ["independent", "distinct", "selected"]:
            result[key] = [self.attach_filter(row) for row in result[key]]
        return result

    def dashboard(self) -> dict[str, Any]:
        result = self.evaluate()
        selected = result["selected"]
        scores = [float(row["scenario_score"]) for row in selected]
        score_bins = [0] * 5
        for score in scores:
            score_bins[min(int(score * 5), 4)] += 1
        return {
            "scenario": result,
            "kpis": {
                "target_strata": len(selected),
                "distinct_locations": len({row["location_uniqueness_key"] for row in selected}),
                "candidate_count": len(self.candidates),
                "verified_filter_count": sum(row["nrel_value_verified"] for row in selected),
                "weather_qc_complete_count": sum(row["hourly_weather_qc_status"] == "COMPLETE" for row in selected),
            },
            "climate_distribution": dict(Counter(row["climate_region"] for row in selected)),
            "urbanicity_distribution": dict(Counter(row["urbanicity_short"] for row in selected)),
            "score_distribution": [
                {"label": f"{start / 5:.1f}-{(start + 1) / 5:.1f}", "count": count}
                for start, count in enumerate(score_bins)
            ],
            "provenance": self.provenance(),
        }

    def candidates_page(self, filters: dict[str, str]) -> dict[str, Any]:
        search = filters.get("search", "").lower().strip()
        climate = filters.get("climate", "").strip()
        urbanicity = filters.get("urbanicity", "").strip()
        selected_only = filters.get("selected_only", "") == "true"
        limit = min(max(int(filters.get("limit", 250)), 1), 3000)
        offset = max(int(filters.get("offset", 0)), 0)
        baseline_keys = {f"{row['catchment_type']}:{row['catchment_code']}" for row in self.selected}
        rows = []
        for source in self.candidates:
            row = dict(source)
            row["location_uniqueness_key"] = f"{row['catchment_type']}:{row['catchment_code']}"
            row["baseline_selected"] = row["location_uniqueness_key"] in baseline_keys and bool(row.get("selected"))
            if (
                search
                and search
                not in (
                    f"{row['catchment_label']} {row['catchment_code']} "
                    f"{row['selected_station_name']} {row['selected_station_number']}"
                ).lower()
            ):
                continue
            if climate and row["climate_region"] != climate:
                continue
            if urbanicity and row["urbanicity_short"] != urbanicity:
                continue
            if selected_only and not row["baseline_selected"]:
                continue
            rows.append(self.attach_filter(row))
        rows.sort(
            key=lambda row: (
                not row["baseline_selected"],
                row["climate_region"],
                row["urbanicity"],
                -(row.get("location_score") or 0),
            )
        )
        page = rows[offset : offset + limit]
        next_offset = offset + len(page)
        return {
            "rows": page,
            "total": len(rows),
            "returned": len(page),
            "limit": limit,
            "offset": offset,
            "has_more": next_offset < len(rows),
            "next_offset": next_offset if next_offset < len(rows) else None,
        }

    def zip_lookup(self, zip_code: str) -> dict[str, Any]:
        if len(zip_code) != 5 or not zip_code.isdigit():
            raise ValueError("Enter a five-digit ZIP code. Leading zeros are preserved.")
        matches = [row for row in self.zip_crosswalk if str(row["zip_code"]).zfill(5) == zip_code]
        if not matches:
            raise LookupError(
                "ZIP code is not present in the bundled demonstration crosswalk. "
                "Load a documented HUD-USPS ZIP crosswalk refresh for national coverage."
            )
        primary = max(matches, key=lambda row: float(row["allocation_ratio"]))
        zip_lat = _as_float(primary.get("latitude"))
        zip_lon = _as_float(primary.get("longitude"))
        crosswalk_urbanicity = str(primary.get("urbanicity", "")).strip()
        if crosswalk_urbanicity:
            is_rural = crosswalk_urbanicity == "rural"
            catchment_type = "County" if is_rural else "CBSA"
            catchment_code = primary["county_geoid"] if is_rural else primary["cbsa_code"]
            candidate = next(
                (
                    row
                    for row in self.candidates
                    if row["catchment_type"] == catchment_type
                    and str(row["catchment_code"]).zfill(5) == str(catchment_code).zfill(5)
                ),
                None,
            )
        else:
            # HUD supplies geography relationships, not this project's
            # urbanicity class. Resolve the live row against the analytical
            # catchments instead of treating a blank class as non-rural.
            candidate = next(
                (
                    row
                    for row in self.candidates
                    if (
                        row["catchment_type"] == "CBSA"
                        and primary.get("cbsa_code")
                        and str(row["catchment_code"]).zfill(5) == str(primary["cbsa_code"]).zfill(5)
                    )
                    or (
                        row["catchment_type"] == "County"
                        and str(row["catchment_code"]).zfill(5) == str(primary["county_geoid"]).zfill(5)
                    )
                ),
                None,
            )
            if candidate:
                primary = dict(primary)
                primary["climate_region"] = candidate["climate_region"]
                primary["urbanicity"] = candidate["urbanicity"]
                primary["urbanicity_short"] = candidate["urbanicity_short"]
                catchment_type = candidate["catchment_type"]
                catchment_code = candidate["catchment_code"]
            else:
                catchment_type = "CBSA" if primary.get("cbsa_code") else "County"
                catchment_code = primary["cbsa_code"] if catchment_type == "CBSA" else primary["county_geoid"]
            is_rural = catchment_type == "County"
        stratum_rows = [
            row
            for row in self.candidates
            if row["climate_region"] == primary["climate_region"] and row["urbanicity"] == primary["urbanicity"]
        ]
        baseline = next(
            (
                row
                for row in self.selected
                if row["climate_region"] == primary["climate_region"] and row["urbanicity"] == primary["urbanicity"]
            ),
            None,
        )
        seen = set()
        stations = []
        for row in stratum_rows:
            name = row["selected_station_name"]
            if name in seen:
                continue
            seen.add(name)
            distance = (
                _haversine(zip_lat, zip_lon, float(row["selected_station_lat"]), float(row["selected_station_lon"]))
                if zip_lat is not None and zip_lon is not None
                else None
            )
            stations.append(
                {
                    "station_name": name,
                    "station_number": str(row["selected_station_number"]).zfill(6),
                    "latitude": row["selected_station_lat"],
                    "longitude": row["selected_station_lon"],
                    "distance_from_zip_miles": distance,
                    "weather_qc_status": self.station_qc.get(str(row["selected_station_number"]).strip(), "PENDING"),
                }
            )
        stations.sort(key=lambda row: (row["distance_from_zip_miles"] is None, row["distance_from_zip_miles"] or 0.0))
        return {
            "zip_code": zip_code,
            "resolved": primary,
            "crosswalk_matches": matches,
            "candidate": self.attach_filter(candidate) if candidate else None,
            "selected_representative": self.attach_filter(baseline) if baseline else None,
            "nearby_weather_stations": stations[:5],
            "simulation_filter_geography": {
                "boundary_type": catchment_type,
                "boundary_code": str(catchment_code).zfill(5),
                "explanation": (
                    "Rural tracts are filtered with the county catchment; the ZIP is only a search entry point."
                    if is_rural
                    else "HDU, LDU, and suburban tracts are filtered within the CBSA catchment; the ZIP is only a search entry point."
                ),
            },
        }

    def provenance(self) -> dict[str, Any]:
        return {
            "analysis_name": self.metadata["analysis_name"],
            "method_version": self.metadata["method_version"],
            "boundary_system": self.metadata["boundary_system"],
            "data_mode": self.data_mode,
            "source_directory": str(self.analysis_dir),
            "sources": self.metadata["sources"],
            "limitations": self.metadata["limitations"],
            "zip_crosswalk": {
                "mode": self.zip_crosswalk_mode,
                "record_count": len(self.zip_crosswalk),
                "source_version": "HUD-USPS ZIP crosswalk schema (zip -> zcta/county/cbsa with allocation ratios)",
                "limitation": (
                    "Bundled demonstration subset: replace with a documented quarterly HUD-USPS "
                    "refresh (pipeline/fetch_hud_crosswalk.py --source api) before national ZIP search."
                    if self.zip_crosswalk_mode == "Bundled demonstration subset"
                    else "Quarterly HUD-USPS crosswalk loaded. HUD does not supply ZCTA; ZIP and ZCTA are kept "
                    "distinct and ZCTA is populated only from a ZIP→ZCTA relationship file (never equated to the ZIP)."
                ),
            },
            "weather_qc": {
                "threshold": ">= 90% of the year's hourly temperature + humidity observations (8,760; 8,784 leap year)",
                "stations_scored": len(self.station_qc),
                "status": "computed" if self.station_qc else "not computed (PENDING)",
            },
        }
