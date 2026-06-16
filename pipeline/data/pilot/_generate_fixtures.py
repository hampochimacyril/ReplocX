#!/usr/bin/env python3
"""Generate the recorded offline fixtures for the tract-level pilot.

The tract-level pilot (``pipeline/pilot.py``) has two sources, mirroring the
rest of the pipeline:

* ``--source api``     – real U.S. Census tract data (ACS 5-year + Gazetteer +
  the OMB/Census CBSA delineation file). Requires outbound network access.
* ``--source fixture`` – the committed recorded fixtures this script writes, so
  the pilot, its validator, and the test suite run anywhere without network.

Honesty note (matches the rest of the project's ``--source fixture`` stance)
---------------------------------------------------------------------------
These fixtures use **real geography identifiers** – real state FIPS, county
FIPS, and CBSA codes, and the real county→CBSA memberships from the July 2023
Census delineation – but the per-tract **population, housing, and land area are
representative structural stand-ins, not measured ACS/Gazetteer values**. They
exist so the tract→county→CBSA *method* (classification, join, aggregation,
missing-join reporting, deterministic selection) can be exercised and tested
offline. Run ``pipeline.pilot --source api`` on a networked machine to produce
measured outputs. The fixtures are tuned so the three pilot states reach a
useful spread of climate × urbanicity strata.

Regenerate (deterministic — identical bytes every run)::

    python3 pipeline/data/pilot/_generate_fixtures.py
"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

HOUSING_RATIO = 0.42  # housing units per person, consistent with the rest of the pipeline

# Per-county fixture specification. Each county lists one or more tract "bands";
# each band is (tract_count, population_density_per_sqmi, land_area_sqmi_each).
# Bands let a single county carry both non-rural tracts (which roll up to its
# CBSA) and rural tracts (which roll up to the county itself). Centroids are the
# real approximate county interior points (public facts); tract interior points
# are derived from them with a small deterministic per-tract offset.
#
# Density bands follow pipeline.config.URBANICITY_DENSITY_BREAKS:
#   >= 3000 higher density urban · >= 1000 lower density urban
#   >= 200 suburban/small town  · else rural
COUNTY_SPECS = {
    # ----- Pennsylvania (Mixed-Humid) -------------------------------------
    "42": [
        # Philadelphia CBSA 37980 → tuned to aggregate into higher-density urban.
        ("42101", "Philadelphia County, PA", 39.9526, -75.1652, [(18, 11000.0, 0.45)]),
        ("42091", "Montgomery County, PA", 40.2105, -75.3705, [(8, 2200.0, 2.0), (2, 120.0, 6.0)]),
        ("42017", "Bucks County, PA", 40.3360, -75.1057, [(6, 1400.0, 3.0), (3, 90.0, 8.0)]),
        # Pittsburgh CBSA 38300 → aggregates into lower-density urban.
        ("42003", "Allegheny County, PA", 40.4686, -79.9842, [(12, 2400.0, 1.5)]),
        ("42007", "Beaver County, PA", 40.6824, -80.3493, [(5, 500.0, 4.0), (2, 80.0, 7.0)]),
        # Non-core (no CBSA) rural counties. The lone non-rural tract in Cameron
        # exercises the missing-join report (a non-rural tract with no CBSA).
        ("42023", "Cameron County, PA", 41.4346, -78.2008, [(3, 30.0, 50.0), (1, 1200.0, 2.0)]),
        ("42053", "Forest County, PA", 41.5106, -79.2363, [(3, 25.0, 60.0)]),
    ],
    # ----- Arizona (Hot-Dry & Mixed Dry) ----------------------------------
    "04": [
        # Phoenix CBSA 38060 → aggregates into higher-density urban.
        ("04013", "Maricopa County, AZ", 33.3490, -112.4915, [(20, 5500.0, 1.0)]),
        ("04021", "Pinal County, AZ", 32.9046, -111.3447, [(3, 350.0, 5.0), (3, 40.0, 30.0)]),
        # Tucson CBSA 46060 → suburban/small town.
        ("04019", "Pima County, AZ", 32.0972, -111.7890, [(8, 650.0, 3.0)]),
        # Non-core rural counties; Apache carries one non-rural tract (join loss).
        ("04012", "La Paz County, AZ", 33.7296, -113.9847, [(3, 15.0, 80.0)]),
        ("04001", "Apache County, AZ", 35.3960, -109.4889, [(3, 12.0, 100.0), (1, 1500.0, 1.5)]),
    ],
    # ----- Minnesota (Cold & Very Cold) -----------------------------------
    "27": [
        # Minneapolis-St. Paul CBSA 33460 → lower-density urban.
        ("27053", "Hennepin County, MN", 45.0001, -93.4669, [(14, 2300.0, 1.6)]),
        ("27123", "Ramsey County, MN", 45.0169, -93.0972, [(8, 2700.0, 1.2)]),
        # Duluth CBSA 20260 → suburban/small town.
        ("27137", "St. Louis County, MN", 47.5897, -92.4604, [(5, 300.0, 8.0), (2, 20.0, 200.0)]),
        # Non-core rural counties.
        ("27031", "Cook County, MN", 47.8628, -90.4990, [(3, 8.0, 150.0)]),
        ("27077", "Lake of the Woods County, MN", 48.7717, -94.9038, [(3, 6.0, 250.0)]),
    ],
}

# Real county → CBSA delineation (July 2023 Census delineation, 2020 standards).
# Only positive memberships are recorded; any county absent from this table is
# treated as Non-core (no CBSA) by the pilot, which is correct for the rural
# counties above. cbsa_type is Metropolitan/Micropolitan per the delineation.
DELINEATION = [
    ("42101", "Philadelphia County, PA", "37980", "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", "Metropolitan"),
    ("42091", "Montgomery County, PA", "37980", "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", "Metropolitan"),
    ("42017", "Bucks County, PA", "37980", "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", "Metropolitan"),
    ("42003", "Allegheny County, PA", "38300", "Pittsburgh, PA", "Metropolitan"),
    ("42007", "Beaver County, PA", "38300", "Pittsburgh, PA", "Metropolitan"),
    ("04013", "Maricopa County, AZ", "38060", "Phoenix-Mesa-Chandler, AZ", "Metropolitan"),
    ("04021", "Pinal County, AZ", "38060", "Phoenix-Mesa-Chandler, AZ", "Metropolitan"),
    ("04019", "Pima County, AZ", "46060", "Tucson, AZ", "Metropolitan"),
    ("27053", "Hennepin County, MN", "33460", "Minneapolis-St. Paul-Bloomington, MN-WI", "Metropolitan"),
    ("27123", "Ramsey County, MN", "33460", "Minneapolis-St. Paul-Bloomington, MN-WI", "Metropolitan"),
    ("27137", "St. Louis County, MN", "20260", "Duluth, MN-WI", "Metropolitan"),
]

TRACT_FIELDS = [
    "tract_geoid",
    "state_fips",
    "county_geoid",
    "county_name",
    "population",
    "housing_units",
    "land_area_sqmi",
    "intpt_lat",
    "intpt_lon",
]
DELINEATION_FIELDS = ["county_geoid", "county_name", "cbsa_code", "cbsa_name", "cbsa_type"]


def _tract_rows_for_state(state_fips: str) -> list[dict]:
    rows: list[dict] = []
    for county_geoid, county_name, lat, lon, bands in COUNTY_SPECS[state_fips]:
        tract_index = 0
        for band_idx, (count, density, land_each) in enumerate(bands):
            for _ in range(count):
                tract_index += 1
                # 6-digit tract sequence; band offset keeps codes unique + stable.
                tract_suffix = f"{(band_idx + 1) * 100 + tract_index:06d}"
                population = int(round(density * land_each))
                housing_units = int(round(population * HOUSING_RATIO))
                # Deterministic interior-point offset so nearest-station lookup
                # gets a plausible, stable point inside the county neighborhood.
                d = ((tract_index % 9) - 4) * 0.012
                rows.append(
                    {
                        "tract_geoid": f"{county_geoid}{tract_suffix}",
                        "state_fips": state_fips,
                        "county_geoid": county_geoid,
                        "county_name": county_name,
                        "population": population,
                        "housing_units": housing_units,
                        "land_area_sqmi": round(land_each, 4),
                        "intpt_lat": round(lat + d, 5),
                        "intpt_lon": round(lon - d, 5),
                    }
                )
    return rows


def write_fixtures(out_dir: Path = HERE) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for state_fips in sorted(COUNTY_SPECS):
        path = out_dir / f"tracts_{state_fips}.csv"
        rows = _tract_rows_for_state(state_fips)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=TRACT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        written.append(path)

    delineation_path = out_dir / "cbsa_delineation.csv"
    with delineation_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(DELINEATION_FIELDS)
        writer.writerows(DELINEATION)
    written.append(delineation_path)
    return written


if __name__ == "__main__":
    paths = write_fixtures()
    for p in paths:
        with p.open(encoding="utf-8") as handle:
            n = sum(1 for _ in handle) - 1
        print(f"[pilot-fixtures] wrote {n:4d} rows -> {p.relative_to(HERE.parents[2])}")
