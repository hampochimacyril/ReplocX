#!/usr/bin/env python3
"""Generate a self-contained synthetic demonstration dataset.

ReplocX normally reads private analytical outputs
from ``04_Analysis/location_selection/data/processed``. That directory is not
distributed with the application, so a fresh clone (or CI runner, or reviewer)
has nothing to load. This script writes a deterministic, clearly-synthetic
dataset into ``data/demo/`` so the app and the full test suite run anywhere.

The demo is engineered to reproduce the structural invariants the regression
suite checks against real data:

* exactly 2,959 scored candidates,
* the 5 climate-region x 4 urbanicity strata (20 total), one distinct selection
  each,
* a Mixed-Humid / higher-density-urban stratum where CBSA 37980
  (Philadelphia-Camden-Wilmington) is the unconstrained rank-2 candidate, so the
  documented research-priority override produces a single transparent change,
* rural strata mapped to ``in.county`` and non-rural strata to
  ``in.metropolitan_and_micropolitan_statistical_area``, all enumeration-verified.

The numbers are illustrative only. They are NOT a research result and must never
be substituted for the real analytical outputs.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = APP_ROOT / "data" / "demo"

TOTAL_CANDIDATES = 2959

CLIMATE_ORDER = [
    "Cold & Very Cold",
    "Hot-Dry & Mixed Dry",
    "Hot-Humid",
    "Marine",
    "Mixed-Humid",
]
URBANICITY = [
    ("higher density urban", "HDU"),
    ("lower density urban", "LDU"),
    ("suburban/small town", "Suburban"),
    ("rural", "Rural"),
]
STRATA = [(c, u) for c in CLIMATE_ORDER for u in URBANICITY]

# Rough geographic centroids per climate region (decimal degrees).
CLIMATE_CENTROID = {
    "Cold & Very Cold": (44.0, -93.2),
    "Hot-Dry & Mixed Dry": (33.6, -112.0),
    "Hot-Humid": (30.2, -90.1),
    "Marine": (47.3, -122.4),
    "Mixed-Humid": (38.6, -80.6),
}
URBAN_OFFSET = {"HDU": (0.0, 0.0), "LDU": (0.6, 0.4), "Suburban": (-0.5, 0.7), "Rural": (1.1, -0.9)}

# The Mixed-Humid / HDU stratum is special: a higher-scoring "winner" plus the
# Philadelphia CBSA at rank 2, so the override changes exactly one assignment.
MH_HDU = ("Mixed-Humid", ("higher density urban", "HDU"))
PHILLY_CODE = "37980"
PHILLY_LABEL = "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD (demo)"
WINNER_CODE = "47900"
WINNER_LABEL = "Washington-Arlington-Alexandria, DC-VA-MD-WV (demo)"

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


def _stratum_counts() -> list[int]:
    base, remainder = divmod(TOTAL_CANDIDATES, len(STRATA))
    return [base + (1 if i < remainder else 0) for i in range(len(STRATA))]


def _make_row(climate, urb, code, label, value, index, *, selected=False):
    short = urb[1]
    is_rural = urb[0] == "rural"
    lat0, lon0 = CLIMATE_CENTROID[climate]
    dlat, dlon = URBAN_OFFSET[short]
    jitter = ((index % 13) - 6) * 0.03
    centroid_lat = round(lat0 + dlat + jitter, 4)
    centroid_lon = round(lon0 + dlon - jitter, 4)
    # Score equals `value` because the three percentile inputs are equal and the
    # baseline weights sum to 1.0 (0.45 + 0.35 + 0.20).
    score = round(value, 6)
    pop_density = round(400 + value * 9000, 1)
    return {
        "climate_region": climate,
        "urbanicity": urb[0],
        "urbanicity_short": short,
        "catchment_type": "County" if is_rural else "CBSA",
        "catchment_code": code,
        "catchment_label": label,
        "population_2010": int(20000 + value * 2_400_000),
        "housing_units_2010": int(9000 + value * 980_000),
        "population_density_sqmi": pop_density,
        "housing_unit_density_sqmi": round(pop_density * 0.42, 1),
        "housing_unit_coverage_percentile": round(value, 4),
        "population_density_percentile": round(value, 4),
        "population_coverage_percentile": round(value, 4),
        "location_score": score,
        "selection_rank": None,  # filled per stratum below
        "selected": selected,
        "station_distance_miles": round(18 + (index % 9) * 11.5, 1),
        "selected_station_name": f"{climate.split(' ')[0]} {short} Climate Station {index % 7 + 1} (demo)",
        "selected_station_number": str(720000 + index),
        "selected_station_lat": round(centroid_lat + 0.18, 4),
        "selected_station_lon": round(centroid_lon - 0.22, 4),
        "centroid_lat": centroid_lat,
        "centroid_lon": centroid_lon,
    }


def build() -> tuple[list[dict], list[dict], list[dict]]:
    counts = _stratum_counts()
    candidates: list[dict] = []
    by_stratum: dict[tuple, list[dict]] = {s: [] for s in STRATA}
    next_code = 10000

    for stratum, count in zip(STRATA, counts, strict=True):
        climate, urb = stratum
        for n in range(count):
            # Exactly one unambiguous winner per stratum (n == 0) sits above an
            # eligible-but-not-winning filler band, so the deterministic allocator
            # and the written baseline selection always agree (every selection is
            # then enumeration-verified in the site list).
            value = 0.90 if n == 0 else 0.62 + ((n - 1) % 22) * 0.01  # winner, else 0.62..0.83
            row = _make_row(
                climate, urb, str(next_code), f"{climate} {urb[1]} catchment {n + 1} (demo)", value, next_code
            )
            next_code += 1
            candidates.append(row)
            by_stratum[stratum].append(row)

    # Inject the Philadelphia narrative into Mixed-Humid / HDU without changing
    # the total count: repurpose the two highest filler slots.
    mh = by_stratum[MH_HDU]
    winner = mh[0]
    winner.update(
        {
            "catchment_code": WINNER_CODE,
            "catchment_label": WINNER_LABEL,
            "location_score": 0.952,
            "housing_unit_coverage_percentile": 0.952,
            "population_density_percentile": 0.952,
            "population_coverage_percentile": 0.952,
        }
    )
    philly = mh[1]
    philly.update(
        {
            "catchment_code": PHILLY_CODE,
            "catchment_label": PHILLY_LABEL,
            "location_score": 0.901,
            "housing_unit_coverage_percentile": 0.901,
            "population_density_percentile": 0.901,
            "population_coverage_percentile": 0.901,
        }
    )

    # Rank within each stratum and choose the baseline selection (override applied
    # for the Mixed-Humid HDU stratum: Philadelphia, not the unconstrained top).
    selected_rows: list[dict] = []
    for stratum, rows in by_stratum.items():
        rows.sort(key=lambda r: (-float(r["location_score"]), int(r["catchment_code"])))
        for rank, row in enumerate(rows, start=1):
            row["selection_rank"] = rank
            row["selected"] = False
        chosen = (
            next((r for r in rows if r["catchment_code"] == PHILLY_CODE), rows[0]) if stratum == MH_HDU else rows[0]
        )
        chosen["selected"] = True
        selected_rows.append(chosen)

    site_rows = [
        {
            "target_catchment_type": r["catchment_type"],
            "target_catchment_code": r["catchment_code"],
            "catchment_label": r["catchment_label"],
            "nrel_filter_field": (
                "in.county" if r["urbanicity"] == "rural" else "in.metropolitan_and_micropolitan_statistical_area"
            ),
            "nrel_filter_value": r["catchment_code"],
            "nrel_value_verified": True,
            "filter_scope_note": "Enumeration-verified demonstration mapping.",
            "hourly_weather_qc_status": "PENDING",
        }
        for r in selected_rows
    ]
    return candidates, selected_rows, site_rows


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    candidates, selected_rows, site_rows = build()
    assert len(candidates) == TOTAL_CANDIDATES, len(candidates)
    assert len(selected_rows) == len(STRATA) == 20

    _write_csv(DEMO_DIR / "candidate_scores.csv", CANDIDATE_FIELDS, candidates)
    _write_csv(DEMO_DIR / "selected_locations.csv", CANDIDATE_FIELDS, selected_rows)
    _write_csv(DEMO_DIR / "resstock_site_list.csv", SITE_FIELDS, site_rows)
    _write_csv(
        DEMO_DIR / "stratum_status.csv",
        ["climate_region", "urbanicity", "status", "eligible_candidate_count"],
        [
            {
                "climate_region": c,
                "urbanicity": u[0],
                "status": "RESOLVED",
                "eligible_candidate_count": sum(
                    1 for r in candidates if r["climate_region"] == c and r["urbanicity"] == u[0]
                ),
            }
            for c, u in STRATA
        ],
    )
    metadata = {
        "analysis_name": "Representative Location Selection (DEMONSTRATION DATA)",
        "method_version": "2.0",
        "boundary_system": "2010 Census tracts (demonstration)",
        "data_mode": "demo",
        "sources": [
            {
                "name": "Synthetic demonstration dataset",
                "role": "Generated by scripts/generate_demo_data.py for offline review and CI.",
                "file": "data/demo/",
            },
            {
                "name": "HUD-USPS ZIP crosswalk schema",
                "role": "Bundled demonstration subset for ZIP resolution.",
                "file": "data/zip_crosswalk_demo.csv",
            },
        ],
        "limitations": [
            "This dataset is synthetic and for demonstration only; it is not a research result.",
            "Replace with the real processed analytical outputs for any analytical use.",
        ],
    }
    (DEMO_DIR / "selection_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote demonstration dataset to {DEMO_DIR} ({len(candidates)} candidates, {len(selected_rows)} selected).")


if __name__ == "__main__":
    main()
