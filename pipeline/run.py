#!/usr/bin/env python3
"""Run the full national data pipeline end to end.

    fixture: fetch_census  ->  classify
    api:     tract Census  ->  rural County / non-rural CBSA aggregation

    then:    build_catchments -> fetch_hud_crosswalk -> validate

Examples
--------
Offline (no network/key; what CI and the test suite use)::

    python3 -m pipeline.run --source fixture

Real national run (on a machine with a free Census API key + network)::

    export CENSUS_API_KEY=...            # api.census.gov/data/key_signup.html
    export RLE_CBSA_DELINEATION_FILE=...  # OMB/Census county-to-CBSA workbook
    python3 -m pipeline.run --source api

Then point the app at the result::

    RLE_ANALYSIS_DATA_DIR=pipeline/out python3 -m unittest
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from . import build_catchments, classify, climate, config, fetch_census, fetch_hud_crosswalk, pilot, validate


def _write_classified(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=classify.CLASSIFIED_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _prepare_live_tract_catchments() -> tuple[list[dict], list[dict], dict]:
    """Build national County/CBSA catchments from tract-level live inputs."""

    states = sorted(climate.STATE_FIPS_TO_POSTAL)
    manifest: list[dict] = []
    tracts = pilot.load_tracts_api(states, manifest)
    delineation = pilot.load_delineation_api(manifest)
    aggregation = pilot.aggregate(tracts, delineation)
    _write_classified(aggregation["catchments"], config.CLASSIFIED_CATCHMENTS)
    return aggregation["catchments"], manifest, aggregation["report"]


def _write_national_provenance(out_dir: Path, manifest: list[dict], report: dict) -> None:
    """Attach tract-method provenance to the national report and metadata."""

    national_report = {
        "source": "api",
        "method": "tract classification; rural tracts -> County, non-rural tracts -> CBSA",
        "vintage": pilot.VINTAGE,
        "download_manifest": manifest,
        "aggregation_report": report,
    }
    report_path = out_dir / "national_report.json"
    report_path.write_text(json.dumps(national_report, indent=2), encoding="utf-8")

    metadata_path = out_dir / "selection_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(
        {
            "analysis_name": "Representative Location Selection (national tract-derived pipeline)",
            "method_version": "3.0-national-tract",
            "boundary_system": (
                "2020 Census tracts aggregated as rural tracts -> counties and " "non-rural tracts -> CBSAs"
            ),
            "vintage": pilot.VINTAGE,
        }
    )
    metadata["sources"][:2] = [
        {
            "name": "U.S. Census Bureau - ACS 2019-2023 5-year (tract population and housing units)",
            "role": "Tract-level population and housing-unit counts.",
            "file": "pipeline/pilot.py (national --source api path)",
        },
        {
            "name": "U.S. Census Bureau - 2023 Gazetteer (tract land area and interior point)",
            "role": "Tract density and population-weighted catchment centroids.",
            "file": "pipeline/pilot.py (national --source api path)",
        },
        {
            "name": "Census/OMB - July 2023 CBSA delineation (2020 standards)",
            "role": "County-to-CBSA membership for non-rural tract aggregation.",
            "file": "RLE_CBSA_DELINEATION_FILE",
        },
    ]
    for source in metadata["sources"]:
        if source.get("file") == "pipeline/data/ish2023_stations.csv":
            source["role"] = "Nearest weather-station assignment per tract-derived catchment."
        elif source.get("file") == "pipeline/climate.py":
            source["role"] = "Climate-region assignment from each catchment's primary county."
    if metadata["limitations"]:
        metadata["limitations"][0] = (
            "Climate is assigned from each catchment's primary county; urbanicity is "
            "derived from tract density before rural-to-county and non-rural-to-CBSA aggregation."
        )
    metadata["limitations"].insert(
        0,
        (
            f"Tract aggregation reported {report['join_loss_count']} non-rural tract join loss(es) "
            f"and {report['unresolved_cbsa_count']} CBSA(s) with rural aggregate density; "
            "details are retained in national_report.json."
        ),
    )
    metadata.setdefault("provenance", {})["national_tract_pipeline"] = {
        "report": "national_report.json",
        "vintage": pilot.VINTAGE,
        "download_manifest": manifest,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the RLE national data pipeline.")
    parser.add_argument("--source", choices=["fixture", "api"], default="fixture")
    parser.add_argument("--out", default=config.OUT_DIR)
    args = parser.parse_args(argv)

    if args.source == "api":
        _, manifest, aggregation_report = _prepare_live_tract_catchments()
    else:
        fetch_census.main(["--source", args.source, "--out", str(config.RAW_CATCHMENTS)])
        classify.main(["--in", str(config.RAW_CATCHMENTS), "--out", str(config.CLASSIFIED_CATCHMENTS)])
    build_catchments.main(
        [
            "--in",
            str(config.CLASSIFIED_CATCHMENTS),
            "--out",
            str(args.out),
            "--source",
            args.source,
        ]
    )
    if args.source == "api":
        _write_national_provenance(Path(args.out), manifest, aggregation_report)
    # Phase 2: ZIP crosswalk alongside the analytical outputs (geometry + weather
    # QC are emitted inside build_catchments). The backend reads zip_crosswalk.csv
    # from this directory when present, with the bundled demo crosswalk as fallback.
    fetch_hud_crosswalk.main(
        [
            "--source",
            args.source,
            "--out",
            str(Path(args.out) / "zip_crosswalk.csv"),
        ]
    )
    code = validate.main(["--dir", str(args.out)])
    if code == 0:
        print(f"[run] pipeline complete ({args.source}). App-ready outputs in {args.out}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
