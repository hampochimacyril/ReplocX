#!/usr/bin/env python3
"""Stage 4 of the pipeline: validate emitted outputs against the app schema.

Checks the column schema and the structural invariants the application and its
regression suite rely on, so a bad pipeline run fails here rather than in the
running app. Exits non-zero on any failure.

Run directly:  ``python3 -m pipeline.validate --dir pipeline/out``
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from . import config
from .build_catchments import CANDIDATE_FIELDS, SITE_FIELDS, STRATUM_FIELDS
from .fetch_hud_crosswalk import CROSSWALK_FIELDS
from .weather_qc import COMPLETE_THRESHOLD, QC_FIELDS


def _read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _columns(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle))


def validate(out_dir: Path) -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    required = [
        "candidate_scores.csv",
        "selected_locations.csv",
        "resstock_site_list.csv",
        "stratum_status.csv",
        "selection_metadata.json",
    ]
    for name in required:
        check((out_dir / name).exists(), f"missing output file: {name}")
    if errors:
        return errors

    # Column schemas.
    check(
        _columns(out_dir / "candidate_scores.csv") == CANDIDATE_FIELDS,
        "candidate_scores.csv columns do not match the expected schema",
    )
    check(
        _columns(out_dir / "selected_locations.csv") == CANDIDATE_FIELDS,
        "selected_locations.csv columns do not match the expected schema",
    )
    check(
        _columns(out_dir / "resstock_site_list.csv") == SITE_FIELDS,
        "resstock_site_list.csv columns do not match the expected schema",
    )
    check(
        _columns(out_dir / "stratum_status.csv") == STRATUM_FIELDS,
        "stratum_status.csv columns do not match the expected schema",
    )

    candidates = _read(out_dir / "candidate_scores.csv")
    selected = _read(out_dir / "selected_locations.csv")
    site_list = _read(out_dir / "resstock_site_list.csv")
    stratum_status = _read(out_dir / "stratum_status.csv")

    # Selection invariants.
    check(len(selected) == 20, f"expected 20 selected locations, found {len(selected)}")
    strata = {(r["climate_region"], r["urbanicity"]) for r in selected}
    check(len(strata) == 20, f"expected 20 distinct strata, found {len(strata)}")
    keys = {f"{r['catchment_type']}:{str(r['catchment_code']).zfill(5)}" for r in selected}
    check(len(keys) == 20, f"expected 20 distinct catchments, found {len(keys)}")
    check(strata == set(config.STRATA), "selected strata do not equal the canonical 20")

    # Every stratum must retain at least one eligible candidate.
    eligible = {s: 0 for s in config.STRATA}
    for r in candidates:
        s = (r["climate_region"], r["urbanicity"])
        if s in eligible and float(r["population_density_percentile"]) >= 0.60:
            eligible[s] += 1
    empty = [s for s, n in eligible.items() if n == 0]
    check(not empty, f"strata with no eligible candidate: {empty}")

    # ResStock field rules + verification.
    for r in site_list:
        if r["target_catchment_type"] == "County":
            check(
                r["nrel_filter_field"] == "in.county",
                f"county catchment {r['target_catchment_code']} must use in.county",
            )
        else:
            check(
                r["nrel_filter_field"] == "in.metropolitan_and_micropolitan_statistical_area",
                f"CBSA catchment {r['target_catchment_code']} must use the CBSA filter field",
            )
        check(
            str(r["nrel_value_verified"]).strip() in {"True", "true", "1"},
            f"unverified ResStock value for {r['target_catchment_code']}",
        )
    rural_selected = [r for r in selected if r["urbanicity"] == "rural"]
    for r in rural_selected:
        check(r["catchment_type"] == "County", f"rural selection {r['catchment_code']} must be a County catchment")

    # Stratum status.
    check(len(stratum_status) == 20, f"expected 20 stratum-status rows, found {len(stratum_status)}")
    unresolved = [r for r in stratum_status if r["status"] != "RESOLVED"]
    check(not unresolved, f"unresolved strata: {[(r['climate_region'], r['urbanicity']) for r in unresolved]}")

    # Score weights still sum to 1.0.
    check(abs(sum(config.SCORE_WEIGHTS.values()) - 1.0) < 1e-9, "score weights must sum to 1.0")

    # --- Phase 2 artifacts (optional/additive; checked when present) ---------
    qc_path = out_dir / "station_weather_qc.csv"
    if qc_path.exists():
        check(_columns(qc_path) == QC_FIELDS, "station_weather_qc.csv columns do not match the expected schema")
        qc_rows = _read(qc_path)
        check(bool(qc_rows), "station_weather_qc.csv has no rows")
        for r in qc_rows:
            check(
                r["hourly_weather_qc_status"] in {"COMPLETE", "INCOMPLETE"},
                f"invalid weather QC status: {r['hourly_weather_qc_status']}",
            )
            coverage = float(r["coverage_fraction"])
            expected = "COMPLETE" if coverage >= COMPLETE_THRESHOLD else "INCOMPLETE"
            check(
                r["hourly_weather_qc_status"] == expected,
                f"weather QC status/threshold mismatch for station {r['station_number']}",
            )
        # Every selected catchment's site-list status must come from a known station.
        qc_numbers = {str(r["station_number"]) for r in qc_rows}
        sel_stations = {str(r["selected_station_number"]) for r in selected}
        missing = sel_stations - qc_numbers
        check(not missing, f"selected stations missing weather QC: {sorted(missing)}")

    crosswalk_path = out_dir / "zip_crosswalk.csv"
    if crosswalk_path.exists():
        check(
            _columns(crosswalk_path) == CROSSWALK_FIELDS, "zip_crosswalk.csv columns do not match the expected schema"
        )
        check(bool(_read(crosswalk_path)), "zip_crosswalk.csv has no rows")

    geometry_path = out_dir / "selected_geometry.json"
    if geometry_path.exists():
        try:
            geo = json.loads(geometry_path.read_text(encoding="utf-8"))
            check(geo.get("type") == "FeatureCollection", "selected_geometry.json must be a FeatureCollection")
            features = geo.get("features", [])
            check(len(features) == 20, f"expected 20 geometry features, found {len(features)}")
            geo_keys = {
                f"{f['properties']['catchment_type']}:{str(f['properties']['catchment_code']).zfill(5)}"
                for f in features
            }
            sel_keys = {f"{r['catchment_type']}:{str(r['catchment_code']).zfill(5)}" for r in selected}
            check(geo_keys == sel_keys, "geometry features do not match the selected catchments")
            for f in features:
                geom = f["geometry"]
                gtype = geom.get("type")
                check(gtype in ("Polygon", "MultiPolygon"), f"unsupported geometry type: {gtype}")
                # Polygon -> [rings]; MultiPolygon -> [[rings], ...]. Check the
                # outer ring of every polygon part is closed (live runs may emit
                # MultiPolygon for catchments with islands/detached parts).
                polygons = geom["coordinates"] if gtype == "MultiPolygon" else [geom["coordinates"]]
                for polygon in polygons:
                    ring = polygon[0]
                    check(ring[0] == ring[-1], "geometry polygon rings must be closed")
            geometry_meta = geo.get("metadata", {})
            check(
                geometry_meta.get("features_with_validation_issues", 0) == 0,
                "geometry metadata reports validation issues",
            )
            check(
                not geometry_meta.get("fetch_errors", []),
                f"geometry metadata reports fetch errors: {geometry_meta.get('fetch_errors', [])}",
            )
        except json.JSONDecodeError as exc:
            errors.append(f"selected_geometry.json is not valid JSON: {exc}")

    # Metadata.
    try:
        meta = json.loads((out_dir / "selection_metadata.json").read_text(encoding="utf-8"))
        for field in ("analysis_name", "method_version", "boundary_system", "sources", "limitations"):
            check(field in meta, f"selection_metadata.json missing '{field}'")
        dictionary = meta.get("provenance", {}).get("resstock_dictionary", {})
        check(dictionary.get("loaded") is True, "ResStock dictionary provenance is not loaded")
        check(
            len(str(dictionary.get("sha256", ""))) == 64,
            "ResStock dictionary provenance is missing a SHA-256",
        )
    except json.JSONDecodeError as exc:
        errors.append(f"selection_metadata.json is not valid JSON: {exc}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pipeline outputs against the app schema.")
    parser.add_argument("--dir", type=Path, default=config.OUT_DIR)
    args = parser.parse_args(argv)

    errors = validate(args.dir)
    if errors:
        print(f"[validate] FAILED ({len(errors)} issue(s)) for {args.dir}:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"[validate] OK — schema and invariants hold for {args.dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
