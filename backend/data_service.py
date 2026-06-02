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
from .scoring import evaluate


APP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_DIR = APP_ROOT.parents[1] / "location_selection" / "data" / "processed"
DEFAULT_RAW_DIR = APP_ROOT.parents[1] / "location_selection" / "data" / "raw"


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


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.7613
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


class DataService:
    def __init__(self, analysis_dir: Path | None = None, raw_dir: Path | None = None) -> None:
        self.analysis_dir = analysis_dir or Path(os.environ.get("RLE_ANALYSIS_DATA_DIR", DEFAULT_ANALYSIS_DIR))
        self.raw_dir = raw_dir or Path(os.environ.get("RLE_RAW_DATA_DIR", DEFAULT_RAW_DIR))
        self.candidates = _read_csv(self.analysis_dir / "candidate_scores.csv", {"catchment_code"})
        self.selected = _read_csv(self.analysis_dir / "selected_locations.csv", {"catchment_code"})
        self.site_list = _read_csv(self.analysis_dir / "resstock_site_list.csv", {"target_catchment_code"})
        self.stratum_status = _read_csv(self.analysis_dir / "stratum_status.csv")
        self.metadata = json.loads((self.analysis_dir / "selection_metadata.json").read_text(encoding="utf-8"))
        self.zip_crosswalk = _read_csv(
            APP_ROOT / "data" / "zip_crosswalk_demo.csv",
            {"zip_code", "zcta", "county_geoid", "cbsa_code"},
        )
        self.filter_map = {
            f"{row['target_catchment_type']}:{row['target_catchment_code']}": row for row in self.site_list
        }
        for row in self.candidates:
            mapping = self.filter_map.get(f"{row['catchment_type']}:{row['catchment_code']}", {})
            row["hourly_weather_qc_status"] = mapping.get("hourly_weather_qc_status", "PENDING")

    def attach_filter(self, row: dict[str, Any]) -> dict[str, Any]:
        item = dict(row)
        mapping = self.filter_map.get(item["location_uniqueness_key"], {})
        item.update(
            {
                "nrel_filter_field": mapping.get(
                    "nrel_filter_field",
                    "in.county" if item["catchment_type"] == "County" else "in.metropolitan_and_micropolitan_statistical_area",
                ),
                "nrel_filter_value": mapping.get("nrel_filter_value", ""),
                "nrel_value_verified": bool(mapping.get("nrel_value_verified", False)),
                "nrel_verification_status": "VERIFIED" if mapping.get("nrel_value_verified") else "REVIEW REQUIRED",
                "filter_scope_note": mapping.get(
                    "filter_scope_note",
                    "Exact ResStock enumeration mapping must be curated before simulation export.",
                ),
                "hourly_weather_qc_status": mapping.get("hourly_weather_qc_status", "PENDING"),
            }
        )
        return item

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        result = evaluate(self.candidates, ScenarioConfig.from_dict(payload))
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
        baseline_keys = {f"{row['catchment_type']}:{row['catchment_code']}" for row in self.selected}
        rows = []
        for source in self.candidates:
            row = dict(source)
            row["location_uniqueness_key"] = f"{row['catchment_type']}:{row['catchment_code']}"
            row["baseline_selected"] = row["location_uniqueness_key"] in baseline_keys and bool(row.get("selected"))
            if search and search not in f"{row['catchment_label']} {row['catchment_code']} {row['selected_station_name']}".lower():
                continue
            if climate and row["climate_region"] != climate:
                continue
            if urbanicity and row["urbanicity_short"] != urbanicity:
                continue
            if selected_only and not row["baseline_selected"]:
                continue
            rows.append(self.attach_filter(row))
        rows.sort(key=lambda row: (not row["baseline_selected"], row["climate_region"], row["urbanicity"], -(row.get("location_score") or 0)))
        return {"rows": rows[:limit], "total": len(rows), "returned": min(len(rows), limit)}

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
        is_rural = primary["urbanicity"] == "rural"
        catchment_type = "County" if is_rural else "CBSA"
        catchment_code = primary["county_geoid"] if is_rural else primary["cbsa_code"]
        stratum_rows = [
            row
            for row in self.candidates
            if row["climate_region"] == primary["climate_region"]
            and row["urbanicity"] == primary["urbanicity"]
        ]
        candidate = next(
            (
                row
                for row in stratum_rows
                if row["catchment_type"] == catchment_type
                and str(row["catchment_code"]).zfill(5) == str(catchment_code).zfill(5)
            ),
            None,
        )
        baseline = next(
            (
                row
                for row in self.selected
                if row["climate_region"] == primary["climate_region"]
                and row["urbanicity"] == primary["urbanicity"]
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
            stations.append(
                {
                    "station_name": name,
                    "station_number": str(row["selected_station_number"]).zfill(6),
                    "latitude": row["selected_station_lat"],
                    "longitude": row["selected_station_lon"],
                    "distance_from_zip_miles": _haversine(
                        float(primary["latitude"]),
                        float(primary["longitude"]),
                        float(row["selected_station_lat"]),
                        float(row["selected_station_lon"]),
                    ),
                    "weather_qc_status": "PENDING",
                }
            )
        stations.sort(key=lambda row: row["distance_from_zip_miles"])
        return {
            "zip_code": zip_code,
            "resolved": primary,
            "crosswalk_matches": matches,
            "candidate": candidate,
            "selected_representative": baseline,
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
            "source_directory": str(self.analysis_dir),
            "sources": self.metadata["sources"],
            "limitations": self.metadata["limitations"],
            "zip_crosswalk": {
                "mode": "Bundled demonstration subset",
                "source_version": "HUD-USPS ZIP crosswalk-compatible schema; demonstration records curated 2026-06-02",
                "limitation": "Replace the bundled subset with a documented quarterly HUD-USPS refresh before national ZIP-search use.",
            },
        }
