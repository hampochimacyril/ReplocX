#!/usr/bin/env python3
"""Stage 3 of the pipeline: build catchment scores and emit the app's CSVs.

Reads ``catchments_classified.csv`` and writes the five analytical files the
application consumes, matching the existing schema exactly:

    candidate_scores.csv, selected_locations.csv, resstock_site_list.csv,
    stratum_status.csv, selection_metadata.json

Within-stratum percentiles feed the baseline composite ``location_score``. The
canonical 20-location selection is derived by calling the application's own
``backend.scoring`` with the default scenario, so the emitted selection and the
ResStock site list can never drift from what the app computes at request time.

Run directly:  ``python3 -m pipeline.build_catchments``
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from bisect import bisect_right
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from . import config, geometry, resstock_dictionary, weather_qc, weather_stations

# Make the sibling backend package importable when run as a module.
if str(config.APP_ROOT) not in sys.path:
    sys.path.insert(0, str(config.APP_ROOT))

from backend.models import DEFAULT_OVERRIDE, ScenarioConfig  # noqa: E402
from backend.scoring import data_compatible_default_config, evaluate  # noqa: E402

CANDIDATE_FIELDS = [
    "climate_region",
    "urbanicity",
    "urbanicity_short",
    "catchment_type",
    "catchment_code",
    "catchment_label",
    "population_2010",
    "housing_units_2010",
    "population_density_sqmi",
    "housing_unit_density_sqmi",
    "housing_unit_coverage_percentile",
    "population_density_percentile",
    "population_coverage_percentile",
    "location_score",
    "selection_rank",
    "selected",
    "station_distance_miles",
    "selected_station_name",
    "selected_station_number",
    "selected_station_lat",
    "selected_station_lon",
    "centroid_lat",
    "centroid_lon",
]
SITE_FIELDS = [
    "target_catchment_type",
    "target_catchment_code",
    "catchment_label",
    "nrel_filter_field",
    "nrel_filter_value",
    "nrel_value_verified",
    "filter_scope_note",
    "hourly_weather_qc_status",
]
STRATUM_FIELDS = ["climate_region", "urbanicity", "status", "eligible_candidate_count"]

DENSITY_SCREEN = ScenarioConfig().density_screen_percentile  # 0.60
MAX_STATION_DISTANCE = ScenarioConfig().max_station_distance_miles  # 250.0


def _percentiles(values: list[float]) -> list[float]:
    """Empirical percentile (fraction of values <= each value), max = 1.0."""

    ordered = sorted(values)
    n = len(ordered)
    return [round(bisect_right(ordered, value) / n, 6) for value in values]


def _station_fields(row: dict) -> dict:
    """Assign the nearest real NOAA ISD-2023 station to a catchment centroid."""

    station, distance = weather_stations.nearest_station(row["centroid_lat"], row["centroid_lon"])
    return {
        "station_distance_miles": distance,
        "selected_station_name": station.name,
        "selected_station_number": str(station.number),
        "selected_station_lat": round(station.lat, 4),
        "selected_station_lon": round(station.lon, 4),
    }


def build_candidate_rows(classified: list[dict]) -> list[dict]:
    by_stratum: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in classified:
        by_stratum[(row["climate_region"], row["urbanicity"])].append(row)

    candidates: list[dict] = []
    for stratum in config.STRATA:
        subset = by_stratum.get(stratum, [])
        if not subset:
            raise ValueError(f"No catchments classified into stratum {stratum[0]} / {stratum[1]}.")
        housing = [float(r["housing_units"]) for r in subset]
        population = [float(r["population"]) for r in subset]
        density = [float(r["population_density_sqmi"]) for r in subset]
        huc = _percentiles(housing)
        pcp = _percentiles(population)
        pdp = _percentiles(density)

        scored = []
        for i, src in enumerate(subset):
            location_score = round(
                config.SCORE_WEIGHTS["housing_unit_coverage_percentile"] * huc[i]
                + config.SCORE_WEIGHTS["population_density_percentile"] * pdp[i]
                + config.SCORE_WEIGHTS["population_coverage_percentile"] * pcp[i],
                6,
            )
            row = {
                "climate_region": src["climate_region"],
                "urbanicity": src["urbanicity"],
                "urbanicity_short": src["urbanicity_short"],
                "catchment_type": src["catchment_type"],
                "catchment_code": str(src["catchment_code"]).zfill(5),
                "catchment_label": src["catchment_label"],
                "population_2010": int(float(src["population"])),
                "housing_units_2010": int(float(src["housing_units"])),
                "population_density_sqmi": float(src["population_density_sqmi"]),
                "housing_unit_density_sqmi": float(src["housing_unit_density_sqmi"]),
                "housing_unit_coverage_percentile": huc[i],
                "population_density_percentile": pdp[i],
                "population_coverage_percentile": pcp[i],
                "location_score": location_score,
                "selection_rank": None,
                "selected": False,
                "centroid_lat": float(src["centroid_lat"]),
                "centroid_lon": float(src["centroid_lon"]),
            }
            row.update(_station_fields(row))
            scored.append(row)

        scored.sort(key=lambda r: (-r["location_score"], _code_int(r["catchment_code"])))
        for rank, row in enumerate(scored, start=1):
            row["selection_rank"] = rank
        candidates.extend(scored)
    return candidates


def _code_int(code: str) -> int:
    try:
        return int(code)
    except ValueError:
        return 10**9


def canonical_selection(candidates: list[dict]) -> list[dict]:
    """The 20 winners under the default scenario, via the app's own scoring."""

    config = data_compatible_default_config(candidates)
    result = evaluate([dict(row) for row in candidates], config)
    return result["selected"]


def build_outputs(classified: list[dict], source: str = "fixture") -> dict[str, object]:
    candidates = build_candidate_rows(classified)
    by_key = {f"{r['catchment_type']}:{r['catchment_code']}": r for r in candidates}

    winners = canonical_selection(candidates)
    winner_keys = []
    selected_rows = []
    for win in winners:
        key = f"{win['catchment_type']}:{str(win['catchment_code']).zfill(5)}"
        winner_keys.append(key)
        row = by_key[key]
        row["selected"] = True
        selected_rows.append(row)

    # Phase 2: hourly weather QC for the canonical selected sites. The complete
    # 2,007-station pool is intentionally not downloaded (roughly 14 GB/year).
    qc_errors: list[dict] = []
    qc_rows = weather_qc.compute_rows(
        [(int(r["selected_station_number"]), r["selected_station_name"]) for r in selected_rows],
        source,
        errors=qc_errors,
    )
    qc_status = weather_qc.status_map(qc_rows)

    # Phase 3 (task 8): verify each ResStock filter value against the public data
    # dictionary instead of asserting it. fixture/demo verify against the bundled
    # demonstration enumeration; --source api verifies against the real ResStock
    # dictionary (RESSTOCK_ENUMERATION_FILE), honestly emitting REVIEW REQUIRED for
    # any code not present.
    enumerations, dictionary_label, resstock_provenance = resstock_dictionary.load_enumerations_detailed(source)
    site_rows = []
    for row in selected_rows:
        is_rural = row["urbanicity"] == "rural"
        filter_field = resstock_dictionary.COUNTY_FIELD if is_rural else resstock_dictionary.CBSA_FIELD
        filter_value = resstock_dictionary.resolve_filter_value(
            filter_field,
            row["catchment_code"],
            row["catchment_label"],
            enumerations,
        )
        verified, note = resstock_dictionary.verify(filter_field, filter_value, enumerations, dictionary_label)
        site_rows.append(
            {
                "target_catchment_type": row["catchment_type"],
                "target_catchment_code": row["catchment_code"],
                "catchment_label": row["catchment_label"],
                "nrel_filter_field": filter_field,
                "nrel_filter_value": filter_value,
                "nrel_value_verified": verified,
                "filter_scope_note": note,
                "hourly_weather_qc_status": qc_status.get(str(row["selected_station_number"]), "PENDING"),
            }
        )

    stratum_rows = []
    eligible_by_stratum: dict[tuple[str, str], int] = defaultdict(int)
    for row in candidates:
        if (
            row["population_density_percentile"] >= DENSITY_SCREEN
            and row["station_distance_miles"] <= MAX_STATION_DISTANCE
        ):
            eligible_by_stratum[(row["climate_region"], row["urbanicity"])] += 1
    for climate_region, urbanicity in config.STRATA:
        count = eligible_by_stratum[(climate_region, urbanicity)]
        stratum_rows.append(
            {
                "climate_region": climate_region,
                "urbanicity": urbanicity,
                "status": "RESOLVED" if count else "UNRESOLVED",
                "eligible_candidate_count": count,
            }
        )

    return {
        "candidates": candidates,
        "selected": selected_rows,
        "site_list": site_rows,
        "stratum_status": stratum_rows,
        "station_weather_qc": qc_rows,
        "station_weather_qc_errors": qc_errors,
        "resstock_provenance": resstock_provenance,
        "baseline_config": data_compatible_default_config(candidates).to_dict(),
        "geometry": geometry.feature_collection(selected_rows, source),
    }


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(outputs: dict, out_dir: Path, source: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "candidate_scores.csv", CANDIDATE_FIELDS, outputs["candidates"])
    _write_csv(out_dir / "selected_locations.csv", CANDIDATE_FIELDS, outputs["selected"])
    _write_csv(out_dir / "resstock_site_list.csv", SITE_FIELDS, outputs["site_list"])
    _write_csv(out_dir / "stratum_status.csv", STRATUM_FIELDS, outputs["stratum_status"])
    _write_csv(out_dir / "station_weather_qc.csv", weather_qc.QC_FIELDS, outputs["station_weather_qc"])
    weather_qc.write_error_report(
        outputs.get("station_weather_qc_errors", []), out_dir / "station_weather_qc_errors.csv"
    )
    (out_dir / "selected_geometry.json").write_text(json.dumps(outputs["geometry"], indent=2), encoding="utf-8")

    is_fixture = source == "fixture"
    qc_rows = outputs["station_weather_qc"]
    qc_complete = sum(r["hourly_weather_qc_status"] == "COMPLETE" for r in qc_rows)
    site_rows = outputs["site_list"]
    site_verified = sum(bool(r["nrel_value_verified"]) for r in site_rows)
    metadata = {
        "analysis_name": (
            "Representative Location Selection (offline fixture)"
            if is_fixture
            else "Representative Location Selection (national pipeline)"
        ),
        "method_version": "2.0-pipeline",
        "boundary_system": "Census counties (rural) and CBSAs (non-rural)",
        "data_mode": "fixture" if is_fixture else "production",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "default_override": {
            "configured": {
                "climate_region": DEFAULT_OVERRIDE.climate_region,
                "urbanicity": DEFAULT_OVERRIDE.urbanicity,
                "catchment_code": DEFAULT_OVERRIDE.catchment_code,
            },
            "applied": bool(outputs.get("baseline_config", {}).get("overrides")),
        },
        "sources": (
            [
                {
                    "name": "U.S. Census Bureau — ACS 5-year (population & housing units)",
                    "role": "Catchment population and housing-unit counts.",
                    "file": "pipeline/fetch_census.py (--source api)",
                },
                {
                    "name": "U.S. Census Bureau — Gazetteer (land area, interior point)",
                    "role": "Land area for densities and map centroids.",
                    "file": "pipeline/fetch_census.py (--source api)",
                },
                {
                    "name": "NOAA Integrated Surface Database (ISH/ISD 2023)",
                    "role": (
                        "Weather-station assignment (nearest station per catchment) and "
                        "authoritative CBSA climate-region + urbanicity labels."
                    ),
                    "file": "pipeline/data/ish2023_stations.csv",
                },
                {
                    "name": "DOE Building America / IECC climate zones",
                    "role": "Climate-region fallback for geographies the ISD file does not cover.",
                    "file": "pipeline/climate.py",
                },
                {
                    "name": "HUD-USPS ZIP crosswalk",
                    "role": "ZIP -> ZCTA/county/CBSA resolution with allocation ratios for ZIP search.",
                    "file": "pipeline/fetch_hud_crosswalk.py (--source api)",
                },
                {
                    "name": "Census TIGER/Line cartographic boundaries",
                    "role": "County/CBSA polygons for the map (simplified GeoJSON).",
                    "file": "pipeline/geometry.py (--source api)",
                },
                {
                    "name": "NOAA ISD global-hourly",
                    "role": "Per-station hourly temperature/humidity completeness QC (>= 90% of 8,760 h).",
                    "file": "pipeline/weather_qc.py (--source api)",
                },
            ]
            if not is_fixture
            else [
                {
                    "name": "Offline structural fixture",
                    "role": (
                        "Deterministic stand-in generated by pipeline.fetch_census "
                        "(--source fixture) so the pipeline and tests run without "
                        "network or a Census API key. Not a research result."
                    ),
                    "file": "pipeline/fetch_census.py (--source fixture)",
                }
            ]
        ),
        "limitations": [
            (
                "Fixture counts are synthetic apart from real anchor geographies and "
                "the real ISD station assignment; regenerate with --source api for "
                "any analytical use."
                if is_fixture
                else "Climate/urbanicity use ISD-file CBSA labels where available, with "
                "the state/county map + density rule as fallback for uncovered areas."
            ),
            (
                f"Per-station hourly weather QC is computed (Phase 2): {qc_complete} of "
                f"{len(qc_rows)} assigned stations meet the >= 90% completeness bar. "
                "Fixture coverage is a deterministic stand-in; --source api reads NOAA ISD."
                if is_fixture
                else f"Per-station hourly weather QC (NOAA ISD): {qc_complete} of "
                f"{len(qc_rows)} assigned stations meet the >= 90% completeness bar."
            ),
            (
                "Catchment polygons are synthetic placeholders in the fixture; --source api "
                "emits simplified TIGER/Line boundaries."
                if is_fixture
                else "Catchment polygons are simplified Census TIGER/Line cartographic boundaries."
            ),
            (
                f"ResStock/ComStock filter values are enumeration-verified (Phase 3): "
                f"{site_verified} of {len(site_rows)} selected codes match the bundled "
                "demonstration data dictionary; the remainder are flagged REVIEW REQUIRED."
                if is_fixture
                else f"ResStock/ComStock filter values are enumeration-verified (Phase 3): "
                f"{site_verified} of {len(site_rows)} selected codes match the real ResStock "
                "data dictionary (RESSTOCK_ENUMERATION_FILE); any others are REVIEW REQUIRED."
            ),
        ],
        "provenance": {
            "ancillary_data_version": "3.0-ancillary",
            "resstock_dictionary": outputs.get("resstock_provenance", {}),
            "weather_qc": {
                "expected_hours_basis": "leap-aware (8,760 hours; 8,784 in a leap year)",
                "completeness_threshold": weather_qc.COMPLETE_THRESHOLD,
                "fetch_error_count": len(outputs.get("station_weather_qc_errors", [])),
                "error_report": "station_weather_qc_errors.csv",
            },
            "geometry": outputs["geometry"].get("metadata", {}),
            "zip_crosswalk": "see zip_crosswalk_provenance.json (written by fetch_hud_crosswalk)",
        },
    }
    (out_dir / "selection_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Build catchment scores and emit app CSVs.")
    parser.add_argument("--in", dest="in_path", type=Path, default=config.CLASSIFIED_CATCHMENTS)
    parser.add_argument("--out", type=Path, default=config.OUT_DIR)
    parser.add_argument(
        "--source",
        choices=["fixture", "api"],
        default="fixture",
        help="Provenance label written into selection_metadata.json.",
    )
    args = parser.parse_args(argv)

    with args.in_path.open(newline="", encoding="utf-8") as handle:
        classified = list(csv.DictReader(handle))
    outputs = build_outputs(classified, args.source)
    write_outputs(outputs, args.out, args.source)
    print(
        f"[build_catchments] {len(outputs['candidates'])} candidates, "
        f"{len(outputs['selected'])} selected -> {args.out}"
    )
    return args.out


if __name__ == "__main__":
    main()
