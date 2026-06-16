#!/usr/bin/env python3
"""Stage 2 of the pipeline: classify raw catchments.

Reads ``catchments_raw.csv`` and assigns, per catchment:

* ``climate_region`` from the primary county GEOID (pipeline.climate),
* ``population_density_sqmi`` / ``housing_unit_density_sqmi`` from counts and
  land area,
* ``urbanicity`` (+ short label) from population density, retaining County rows
  only for rural catchments and CBSA rows only for non-rural catchments.

Writes ``catchments_classified.csv``. Deterministic and offline.

Run directly:  ``python3 -m pipeline.classify``
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from . import climate, config, weather_stations

CLASSIFIED_FIELDS = [
    "climate_region",
    "urbanicity",
    "urbanicity_short",
    "catchment_type",
    "catchment_code",
    "catchment_label",
    "primary_county_geoid",
    "population",
    "housing_units",
    "land_area_sqmi",
    "population_density_sqmi",
    "housing_unit_density_sqmi",
    "centroid_lat",
    "centroid_lon",
]


def _classify_row(raw: dict, station_labels: dict[str, dict[str, str]] | None = None) -> dict:
    land_area = float(raw["land_area_sqmi"])
    if land_area <= 0:
        raise ValueError(f"Non-positive land area for {raw['catchment_code']}; cannot compute density.")
    population = int(float(raw["population"]))
    housing_units = int(float(raw["housing_units"]))
    pop_density = round(population / land_area, 1)
    housing_density = round(housing_units / land_area, 1)

    # Urbanicity comes from the catchment's aggregate density. ISD station labels
    # are station/tract observations, so their CBSA majority is useful for climate
    # coverage but is not a sound replacement for aggregate CBSA urbanicity.
    urbanicity = config.urbanicity_for_density(pop_density)
    code = str(raw["catchment_code"]).strip().zfill(5)
    raw_type = str(raw["catchment_type"]).strip()
    if station_labels and str(raw["catchment_type"]).strip() == "CBSA" and code in station_labels:
        climate_region = station_labels[code]["climate_region"]
    else:
        climate_region = climate.climate_for_county(raw["primary_county_geoid"])

    return {
        "climate_region": climate_region,
        "urbanicity": urbanicity,
        "urbanicity_short": config.URBANICITY_SHORT[urbanicity],
        "catchment_type": raw_type,
        "catchment_code": str(raw["catchment_code"]).strip(),
        "catchment_label": raw["catchment_label"],
        "primary_county_geoid": str(raw["primary_county_geoid"]).strip().zfill(5),
        "population": population,
        "housing_units": housing_units,
        "land_area_sqmi": land_area,
        "population_density_sqmi": pop_density,
        "housing_unit_density_sqmi": housing_density,
        "centroid_lat": float(raw["centroid_lat"]),
        "centroid_lon": float(raw["centroid_lon"]),
    }


def classify_rows(raw_rows: list[dict], station_labels: dict[str, dict[str, str]] | None = None) -> list[dict]:
    rows = [_classify_row(row, station_labels) for row in raw_rows]
    # County identifiers are valid rural catchments; CBSA identifiers are valid
    # non-rural catchments. Filter the alternate raw geography instead of
    # relabelling its type while retaining an incompatible identifier.
    return [row for row in rows if (row["catchment_type"] == "County") == (row["urbanicity"] == "rural")]


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Classify raw catchments by climate + urbanicity.")
    parser.add_argument("--in", dest="in_path", type=Path, default=config.RAW_CATCHMENTS)
    parser.add_argument("--out", type=Path, default=config.CLASSIFIED_CATCHMENTS)
    parser.add_argument(
        "--use-station-labels",
        action="store_true",
        help="Use the ISD file's per-CBSA climate labels as authoritative "
        "(real --source api run); aggregate density still determines urbanicity.",
    )
    args = parser.parse_args(argv)

    with args.in_path.open(newline="", encoding="utf-8") as handle:
        raw_rows = list(csv.DictReader(handle))
    station_labels = weather_stations.cbsa_label_map() if args.use_station_labels else None
    rows = classify_rows(raw_rows, station_labels)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLASSIFIED_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[classify] classified {len(rows)} catchments -> {args.out}")
    return args.out


if __name__ == "__main__":
    main()
