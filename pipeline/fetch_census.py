#!/usr/bin/env python3
"""Stage 1 of the pipeline: produce a raw catchments table.

Output (``pipeline/work/catchments_raw.csv``) has one row per candidate
catchment with the minimum facts later stages need, *before* any climate or
urbanicity labels are applied:

    catchment_type, catchment_code, catchment_label, primary_county_geoid,
    population, housing_units, land_area_sqmi, centroid_lat, centroid_lon

Two sources share this contract:

* ``--source api``  – real U.S. Census data. Population & housing come from the
  Census API (ACS 5-year by default); land area + interior point come from the
  free Census Gazetteer files, and CBSA fallback counties come from the OMB
  delineation workbook. Requires ``CENSUS_API_KEY`` and network access.
* ``--source fixture`` – a deterministic, clearly-labelled offline dataset that
  reproduces the structural invariants the app and tests require, so everything
  runs without network or a key.

Run directly:  ``python3 -m pipeline.fetch_census --source fixture``
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from . import climate, config

RAW_FIELDS = [
    "catchment_type",
    "catchment_code",
    "catchment_label",
    "primary_county_geoid",
    "population",
    "housing_units",
    "land_area_sqmi",
    "centroid_lat",
    "centroid_lon",
]

# ---------------------------------------------------------------------------
# Offline fixture source
# ---------------------------------------------------------------------------

TOTAL_CANDIDATES = 2959  # matches the bundled demo so the full test suite holds.

# Anchor county GEOID per climate region. Used so the fixture's synthetic
# catchments classify back to the intended climate via pipeline.climate, and so
# the data exercises the real classifier rather than carrying pre-baked labels.
CLIMATE_ANCHOR_COUNTY = {
    "Cold & Very Cold": "27053",  # Hennepin County, MN
    "Hot-Dry & Mixed Dry": "04013",  # Maricopa County, AZ
    "Hot-Humid": "22071",  # Orleans Parish, LA
    "Marine": "53033",  # King County, WA
    "Mixed-Humid": "42101",  # Philadelphia County, PA
}
CLIMATE_CENTROID = {
    "Cold & Very Cold": (44.0, -93.2),
    "Hot-Dry & Mixed Dry": (33.6, -112.0),
    "Hot-Humid": (30.2, -90.1),
    "Marine": (47.3, -122.4),
    "Mixed-Humid": (39.0, -77.5),
}
URBAN_OFFSET = {"HDU": (0.0, 0.0), "LDU": (0.6, 0.4), "Suburban": (-0.5, 0.7), "Rural": (1.1, -0.9)}
# Density band (people / sq mi) each urbanicity class must land inside so the
# classifier reproduces the intended stratum.
URBAN_BAND = {
    "HDU": (3200.0, 8500.0),
    "LDU": (1100.0, 2900.0),
    "Suburban": (250.0, 950.0),
    "Rural": (30.0, 190.0),
}
LAND_AREA = {"CBSA": 700.0, "County": 600.0}

# Real research anchors injected into the Mixed-Humid / higher-density-urban
# stratum so the documented Philadelphia override targets a real CBSA that sits
# at rank 2 behind a single higher-scoring metro.
MH_HDU = ("Mixed-Humid", "higher density urban")
WASHINGTON = {
    "code": "47900",
    "label": "Washington-Arlington-Alexandria, DC-VA-MD-WV (fixture)",
    "county": "11001",
    "density": 8500.0,
}
PHILADELPHIA = {
    "code": "37980",
    "label": "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD (fixture)",
    "county": "42101",
    "density": 8245.0,
}


def _stratum_counts() -> list[int]:
    base, remainder = divmod(TOTAL_CANDIDATES, len(config.STRATA))
    return [base + (1 if i < remainder else 0) for i in range(len(config.STRATA))]


def _centroid(climate_region: str, short: str, index: int) -> tuple[float, float]:
    lat0, lon0 = CLIMATE_CENTROID[climate_region]
    dlat, dlon = URBAN_OFFSET[short]
    jitter = ((index % 13) - 6) * 0.03
    return round(lat0 + dlat + jitter, 4), round(lon0 + dlon - jitter, 4)


def build_fixture_rows() -> list[dict]:
    counts = _stratum_counts()
    rows: list[dict] = []
    cbsa_counter = 90000  # synthetic CBSA codes, well clear of real (<=49999) codes.

    for (climate_region, urbanicity), count in zip(config.STRATA, counts, strict=True):
        short = config.URBANICITY_SHORT[urbanicity]
        ctype = config.catchment_type_for(urbanicity)
        anchor_county = CLIMATE_ANCHOR_COUNTY[climate_region]
        band_min, band_max = URBAN_BAND[short]
        land_area = LAND_AREA[ctype]
        stratum_rows: list[dict] = []

        for n in range(count):
            # One unambiguous winner (n == 0) above a filler band, mirroring the
            # demo so the deterministic allocator has a clear per-stratum top.
            v = 0.97 if n == 0 else 0.62 + ((n - 1) % 22) * 0.01
            density = round(band_min + v * (band_max - band_min), 1)
            population = int(round(density * land_area))
            housing_units = int(round(population * 0.42))
            if ctype == "County":
                code = f"{anchor_county[:2]}{(n + 1):03d}"  # synthetic county in the climate's state
                primary_county = code
            else:
                cbsa_counter += 1
                code = str(cbsa_counter)
                primary_county = anchor_county
            lat, lon = _centroid(climate_region, short, n)
            stratum_rows.append(
                {
                    "catchment_type": ctype,
                    "catchment_code": code,
                    "catchment_label": f"{climate_region} {short} catchment {n + 1} (fixture)",
                    "primary_county_geoid": primary_county,
                    "population": population,
                    "housing_units": housing_units,
                    "land_area_sqmi": land_area,
                    "centroid_lat": lat,
                    "centroid_lon": lon,
                }
            )

        # Inject the two real Mixed-Humid / HDU anchors as the two densest rows.
        if (climate_region, urbanicity) == MH_HDU:
            for slot, anchor in ((0, WASHINGTON), (1, PHILADELPHIA)):
                population = int(round(anchor["density"] * land_area))
                stratum_rows[slot].update(
                    {
                        "catchment_code": anchor["code"],
                        "catchment_label": anchor["label"],
                        "primary_county_geoid": anchor["county"],
                        "population": population,
                        "housing_units": int(round(population * 0.42)),
                        "land_area_sqmi": land_area,
                    }
                )

        rows.extend(stratum_rows)

    assert len(rows) == TOTAL_CANDIDATES, len(rows)
    return rows


# ---------------------------------------------------------------------------
# Live Census API source (runs on a machine with a key + network)
# ---------------------------------------------------------------------------

ACS_DATASET = os.environ.get("CENSUS_ACS_DATASET", "2021/acs/acs5")
POP_VAR = "B01003_001E"  # total population
HOUSING_VAR = "B25001_001E"  # total housing units


def _require(module: str):
    try:
        return __import__(module)
    except ImportError as exc:  # pragma: no cover - only hit when deps missing
        raise SystemExit(
            f"--source api needs the '{module}' package. Install it with " f"`pip install {module}` and retry."
        ) from exc


def _load_gazetteer(env_var: str, code_field: str) -> dict[str, dict[str, float]]:
    """Read a free Census Gazetteer file for land area + interior point.

    Download (one-time, free):
      counties -> https://www.census.gov/geographies/reference-files/...gazetteer
      Set ``CENSUS_GAZETTEER_COUNTY`` / ``CENSUS_GAZETTEER_CBSA`` to the paths.
    """

    path = os.environ.get(env_var)
    if not path:
        raise SystemExit(
            f"--source api needs {env_var} pointing at a Census Gazetteer file "
            "(free download) to supply land area for density."
        )
    table: dict[str, dict[str, float]] = {}
    with open(path, newline="", encoding="latin-1") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for raw in reader:
            row = {k.strip(): (v.strip() if v else "") for k, v in raw.items()}
            code = row.get(code_field) or row.get("GEOID") or row.get("CBSA")
            if not code:
                continue
            try:
                table[str(code).zfill(5)] = {
                    "land_area_sqmi": float(row.get("ALAND_SQMI") or 0.0),
                    "lat": float(row.get("INTPTLAT") or 0.0),
                    "lon": float(row.get("INTPTLONG") or row.get("INTPTLON") or 0.0),
                }
            except ValueError:
                continue
    return table


def _normalise_header(value: object) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def _load_cbsa_counties() -> dict[str, list[str]]:
    """Return ``CBSA code -> central member county GEOIDs``.

    The national CBSA Census API endpoint supplies CBSA-level totals, but the
    climate fallback needs a valid county GEOID. The OMB/Census delineation file
    gives county membership and marks central counties. The caller chooses the
    most populous central member using the ACS county response. Membership is
    restricted to the same 50-state + DC scope as the climate/station framework.
    """

    path_text = os.environ.get("RLE_CBSA_DELINEATION_FILE")
    if not path_text:
        raise SystemExit(
            "--source api needs RLE_CBSA_DELINEATION_FILE pointing at the OMB/Census "
            "county-to-CBSA delineation file so CBSA climate fallback uses real county GEOIDs."
        )
    path = Path(path_text)
    if not path.exists():
        raise SystemExit(f"RLE_CBSA_DELINEATION_FILE does not exist: {path}")

    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        openpyxl = _require("openpyxl")
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        rows = workbook.active.iter_rows(values_only=True)
    else:
        handle = path.open(newline="", encoding="utf-8-sig")
        reader = csv.reader(handle)
        rows = iter(reader)

    header: dict[str, int] | None = None
    choices: dict[str, list[tuple[int, str]]] = {}
    for values in rows:
        cells = [str(v or "").strip() for v in values]
        if header is None:
            normalised = {_normalise_header(c): i for i, c in enumerate(cells) if c}
            if "cbsa code" in normalised and (
                {"fips state code", "fips county code"}.issubset(normalised) or "county geoid" in normalised
            ):
                header = normalised
            continue
        try:
            cbsa_code = cells[header["cbsa code"]].zfill(5)
            if "county geoid" in header:
                county_geoid = cells[header["county geoid"]].zfill(5)
            else:
                county_geoid = cells[header["fips state code"]].zfill(2) + cells[header["fips county code"]].zfill(3)
        except (KeyError, IndexError):
            continue
        if county_geoid[:2] not in climate.STATE_FIPS_TO_POSTAL:
            continue
        centrality = ""
        if "central/outlying county" in header and header["central/outlying county"] < len(cells):
            centrality = cells[header["central/outlying county"]].lower()
        priority = 0 if centrality == "central" else 1
        choices.setdefault(cbsa_code, []).append((priority, county_geoid))

    if "handle" in locals():
        handle.close()

    if header is None:
        raise SystemExit(f"Could not find CBSA/county columns in RLE_CBSA_DELINEATION_FILE: {path}")
    if not choices:
        raise SystemExit(f"RLE_CBSA_DELINEATION_FILE contained no 50-state/DC CBSA memberships: {path}")
    result: dict[str, list[str]] = {}
    for cbsa, counties in choices.items():
        central = {county for priority, county in counties if priority == 0}
        result[cbsa] = sorted(central or {county for _, county in counties})
    return result


def fetch_api_rows() -> list[dict]:
    """Pull real county + CBSA population/housing and join free land areas.

    Counties become candidate catchments for the rural stratum; CBSAs cover the
    denser classes. Final county-vs-CBSA assignment is resolved downstream in
    ``classify`` from density, so both geographies are emitted here.
    """

    requests = _require("requests")
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("--source api needs a free CENSUS_API_KEY (api.census.gov/data/key_signup.html).")

    session = requests.Session()
    base = f"https://api.census.gov/data/{ACS_DATASET}"

    def query(geo_clause: str) -> list[list[str]]:
        url = f"{base}?get=NAME,{POP_VAR},{HOUSING_VAR}&for={geo_clause}&key={key}"
        resp = session.get(url, timeout=60)
        resp.raise_for_status()
        return resp.json()

    county_gaz = _load_gazetteer("CENSUS_GAZETTEER_COUNTY", "GEOID")
    cbsa_gaz = _load_gazetteer("CENSUS_GAZETTEER_CBSA", "CBSA")
    cbsa_counties = _load_cbsa_counties()

    rows: list[dict] = []
    county_population: dict[str, int] = {}

    # Counties (one row each) -> primary_county_geoid is itself.
    county_rows = query("county:*")
    header, *records = county_rows
    idx = {name: i for i, name in enumerate(header)}
    for rec in records:
        geoid = f"{rec[idx['state']]}{rec[idx['county']]}".zfill(5)
        if geoid[:2] not in climate.STATE_FIPS_TO_POSTAL:
            continue
        population = int(rec[idx[POP_VAR]] or 0)
        county_population[geoid] = population
        gaz = county_gaz.get(geoid)
        if not gaz or gaz["land_area_sqmi"] <= 0:
            continue
        rows.append(
            {
                "catchment_type": "County",
                "catchment_code": geoid,
                "catchment_label": rec[idx["NAME"]],
                "primary_county_geoid": geoid,
                "population": population,
                "housing_units": int(rec[idx[HOUSING_VAR]] or 0),
                "land_area_sqmi": gaz["land_area_sqmi"],
                "centroid_lat": gaz["lat"],
                "centroid_lon": gaz["lon"],
            }
        )

    # CBSAs (metro + micro). Primary county is approximated by the CBSA's own
    # interior point; a full HUD crosswalk join is Phase 2.
    cbsa_rows = query("metropolitan statistical area/micropolitan statistical area:*")
    header, *records = cbsa_rows
    idx = {name: i for i, name in enumerate(header)}
    code_key = "metropolitan statistical area/micropolitan statistical area"
    for rec in records:
        code = str(rec[idx[code_key]]).zfill(5)
        gaz = cbsa_gaz.get(code)
        member_counties = cbsa_counties.get(code)
        if not member_counties:
            continue
        primary_county = max(
            member_counties,
            key=lambda county: (county_population.get(county, -1), county),
        )
        if not gaz or gaz["land_area_sqmi"] <= 0:
            continue
        rows.append(
            {
                "catchment_type": "CBSA",
                "catchment_code": code,
                "catchment_label": rec[idx["NAME"]],
                "primary_county_geoid": primary_county,
                "population": int(rec[idx[POP_VAR]] or 0),
                "housing_units": int(rec[idx[HOUSING_VAR]] or 0),
                "land_area_sqmi": gaz["land_area_sqmi"],
                "centroid_lat": gaz["lat"],
                "centroid_lon": gaz["lon"],
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def write_rows(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Fetch raw catchments for the RLE pipeline.")
    parser.add_argument("--source", choices=["fixture", "api"], default="fixture")
    parser.add_argument("--out", type=Path, default=config.RAW_CATCHMENTS)
    args = parser.parse_args(argv)

    rows = fetch_api_rows() if args.source == "api" else build_fixture_rows()
    write_rows(rows, args.out)
    print(f"[fetch_census] source={args.source} wrote {len(rows)} raw catchments -> {args.out}")
    return args.out


if __name__ == "__main__":
    main()
