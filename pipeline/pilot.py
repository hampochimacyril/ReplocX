#!/usr/bin/env python3
"""Tract-level pilot pipeline (Session 2).

Replaces the direct county/CBSA live-data shortcut with the project's intended
**tract-level method**, run over a small set of pilot states that exercise
different climate and urbanicity conditions (Pennsylvania, Arizona, Minnesota).

Method
------
1. Read one row per **census tract** (population, housing units, land area,
   interior point).
2. Classify each tract's **urbanicity** from its own population density
   (``config.URBANICITY_DENSITY_BREAKS`` — a documented, reproducible rule).
3. Assign each tract to a **county** structurally (the first five GEOID digits)
   and each county to a **CBSA** via a documented Census delineation file.
4. Aggregate **rural tracts → county catchments** and **non-rural tracts → CBSA
   catchments**, summing population/housing/land and recomputing density.
5. Assign each catchment a **climate region** from its primary county
   (``pipeline.climate``), score within stratum, and pick a deterministic
   per-stratum top.

The pilot emits **partial, schema-compatible** analytical outputs — only the
strata the pilot states reach — and a ``pilot_report.json`` that reports row
counts, join losses, and unresolved classifications rather than silently
dropping them. It is deliberately written to a separate directory and is **not**
a complete national result.

Two sources share the contract (mirroring the rest of the pipeline):

* ``--source api``     – real U.S. Census tract data: ACS 5-year tract
  population/housing, the Census Gazetteer tract file (land area + interior
  point), and the OMB/Census CBSA delineation file. Raw downloads are cached
  under ``pipeline/cache/pilot/`` with SHA-256 checksums and source dates.
  Requires ``CENSUS_API_KEY`` and outbound network access.
* ``--source fixture`` – the committed recorded fixtures in
  ``pipeline/data/pilot/`` (real geography identifiers; representative,
  clearly-labelled tract attributes) so the method, validator, and tests run
  offline and deterministically.

Run::

    python3 -m pipeline.pilot --source fixture            # offline (CI/tests)
    CENSUS_API_KEY=... python3 -m pipeline.pilot --source api
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from . import climate, config, geometry, resstock_dictionary, weather_qc
from .build_catchments import (
    CANDIDATE_FIELDS,
    SITE_FIELDS,
    STRATUM_FIELDS,
    _code_int,
    _percentiles,
    _station_fields,
)

# Make the sibling backend package importable when run as a module.
if str(config.APP_ROOT) not in sys.path:
    sys.path.insert(0, str(config.APP_ROOT))

from backend.models import ScenarioConfig  # noqa: E402

# ---------------------------------------------------------------------------
# Pilot scope + analytical vintage
# ---------------------------------------------------------------------------
# Three states spanning distinct climate regions and the full urbanicity range.
PILOT_STATES = {
    "04": "Arizona (Hot-Dry & Mixed Dry)",
    "27": "Minnesota (Cold & Very Cold)",
    "42": "Pennsylvania (Mixed-Humid)",
}

# A single, internally consistent 2020-boundary vintage so tract boundaries,
# population years, and CBSA delineations are never mixed:
#   * ACS 2019–2023 5-year  -> tabulated on 2020 census-tract boundaries
#   * 2023 Census Gazetteer -> 2020 tract boundaries (land area + interior point)
#   * July 2023 CBSA delineation (2020 standards) -> assigns 2020 counties to CBSAs
VINTAGE = {
    "tract_boundaries": "2020 Census tracts (TIGER/Line, 2020 vintage)",
    "population_housing": "ACS 2019–2023 5-year",
    "land_area_interior_point": "2023 Census Gazetteer (tracts)",
    "cbsa_delineation": "Census/OMB delineation, July 2023 (2020 standards)",
    "note": (
        "All four inputs share the 2020 census-tract/county boundary system, so "
        "tract→county→CBSA joins require no boundary crosswalk. The schema's "
        "legacy *_2010 column names now carry ACS 2019–2023 values."
    ),
}

ACS_DATASET = os.environ.get("PILOT_ACS_DATASET", "2023/acs/acs5")
POP_VAR = "B01003_001E"  # total population
HOUSING_VAR = "B25001_001E"  # total housing units
GAZETTEER_TRACTS_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_tracts_national.zip"
)
CBSA_DELINEATION_URL = (
    "https://www2.census.gov/programs-surveys/metro-micro/geographies/"
    "reference-files/2023/delineation-files/list1_2023.xlsx"
)

DENSITY_SCREEN = ScenarioConfig().density_screen_percentile  # 0.60
MAX_STATION_DISTANCE = ScenarioConfig().max_station_distance_miles  # 250.0

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

REPORT_FILE = "pilot_report.json"


def _s(value: object) -> str:
    """Trim and stringify; never coerce identifiers to numbers."""

    return str(value).strip()


# ===========================================================================
# Tract input — offline recorded fixtures
# ===========================================================================


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def load_tracts_fixture(states: list[str], data_dir: Path = config.PILOT_DATA_DIR) -> list[dict]:
    tracts: list[dict] = []
    for state in states:
        path = data_dir / f"tracts_{state}.csv"
        if not path.exists():
            raise SystemExit(f"missing pilot tract fixture: {path} (run pipeline/data/pilot/_generate_fixtures.py)")
        for raw in _read_csv(path):
            tracts.append(_normalise_tract(raw))
    return tracts


def _normalise_tract(raw: dict) -> dict:
    geoid = _s(raw["tract_geoid"]).zfill(11)
    county = _s(raw.get("county_geoid") or geoid[:5]).zfill(5)
    land = float(raw["land_area_sqmi"])
    if land <= 0:
        raise ValueError(f"non-positive land area for tract {geoid}")
    return {
        "tract_geoid": geoid,
        "state_fips": county[:2],
        "county_geoid": county,
        "county_name": _s(raw.get("county_name", "")),
        "population": int(float(raw["population"])),
        "housing_units": int(float(raw["housing_units"])),
        "land_area_sqmi": land,
        "intpt_lat": float(raw["intpt_lat"]),
        "intpt_lon": float(raw["intpt_lon"]),
    }


def load_delineation_fixture(data_dir: Path = config.PILOT_DATA_DIR) -> dict[str, dict]:
    path = data_dir / "cbsa_delineation.csv"
    if not path.exists():
        raise SystemExit(f"missing pilot delineation fixture: {path}")
    table: dict[str, dict] = {}
    for raw in _read_csv(path):
        county = _s(raw["county_geoid"]).zfill(5)
        table[county] = {
            "cbsa_code": _s(raw["cbsa_code"]).zfill(5),
            "cbsa_name": _s(raw.get("cbsa_name", "")),
            "cbsa_type": _s(raw.get("cbsa_type", "")),
        }
    return table


# ===========================================================================
# Tract input — live Census API (cached, checksummed)
# ===========================================================================


def _require(module: str):
    try:
        return __import__(module)
    except ImportError as exc:  # pragma: no cover - only hit when deps missing
        raise SystemExit(
            f"--source api needs the '{module}' package. Install it with `pip install {module}` and retry."
        ) from exc


def _cache_download(session, url: str, filename: str, manifest: list[dict]) -> bytes:
    """Download ``url`` once into the pilot cache, recording a provenance entry.

    Returns the raw bytes. Re-uses an existing cached copy when present so reruns
    are network-light; always (re)records the checksum, size, and source date so
    provenance stays accurate.
    """

    config.PILOT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = config.PILOT_CACHE_DIR / filename
    if cached.exists():
        data = cached.read_bytes()
    else:
        resp = session.get(url, timeout=(20, 180))
        resp.raise_for_status()
        data = resp.content
        partial = cached.with_suffix(cached.suffix + ".part")
        partial.write_bytes(data)
        partial.replace(cached)
    manifest.append(
        {
            "url": url,
            "cached_file": str(cached.relative_to(config.APP_ROOT)),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "downloaded_at_utc": datetime.now(UTC).isoformat(),
        }
    )
    return data


def _retrying_session(requests):
    """Requests session with bounded retry/backoff for Census public-data hosts."""

    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _load_state_tract_payload(session, base: str, state: str, key: str, manifest: list[dict]) -> list[list[str]]:
    """Load and cache one state's ACS tract response without recording the key."""

    config.PILOT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dataset_slug = ACS_DATASET.replace("/", "_")
    cached = config.PILOT_CACHE_DIR / f"acs_{dataset_slug}_tracts_{state}.json"
    safe_url = f"{base}?get=NAME,{POP_VAR},{HOUSING_VAR}&for=tract:*" f"&in=state:{state}&in=county:*"
    if cached.exists():
        data = cached.read_bytes()
    else:
        params = [
            ("get", f"NAME,{POP_VAR},{HOUSING_VAR}"),
            ("for", "tract:*"),
            ("in", f"state:{state}"),
            ("in", "county:*"),
            ("key", key),
        ]
        response = session.get(base, params=params, timeout=(20, 120))
        response.raise_for_status()
        data = response.content
        partial = cached.with_suffix(".json.part")
        partial.write_bytes(data)
        partial.replace(cached)
    manifest.append(
        {
            "url": safe_url,
            "cached_file": str(cached.relative_to(config.APP_ROOT)),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "read_at_utc": datetime.now(UTC).isoformat(),
        }
    )
    return json.loads(data)


def load_tracts_api(states: list[str], manifest: list[dict]) -> list[dict]:  # pragma: no cover - needs network
    requests = _require("requests")
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("--source api needs a free CENSUS_API_KEY (api.census.gov/data/key_signup.html).")
    session = _retrying_session(requests)

    # Land area + interior point from the Gazetteer tract file (one national zip).
    gaz_bytes = _cache_download(session, GAZETTEER_TRACTS_URL, "2023_Gaz_tracts_national.zip", manifest)
    gaz = _parse_gazetteer_tracts(gaz_bytes)

    base = f"https://api.census.gov/data/{ACS_DATASET}"
    tracts: list[dict] = []
    missing_area: list[str] = []
    for state in states:
        header, *records = _load_state_tract_payload(session, base, state, key, manifest)
        idx = {name: i for i, name in enumerate(header)}
        for rec in records:
            geoid = f"{rec[idx['state']]}{rec[idx['county']]}{rec[idx['tract']]}".zfill(11)
            area = gaz.get(geoid)
            if not area or area["land_area_sqmi"] <= 0:
                missing_area.append(geoid)
                continue
            tracts.append(
                _normalise_tract(
                    {
                        "tract_geoid": geoid,
                        "county_geoid": geoid[:5],
                        "county_name": rec[idx["NAME"]],
                        "population": int(rec[idx[POP_VAR]] or 0),
                        "housing_units": int(rec[idx[HOUSING_VAR]] or 0),
                        "land_area_sqmi": area["land_area_sqmi"],
                        "intpt_lat": area["lat"],
                        "intpt_lon": area["lon"],
                    }
                )
            )
    if missing_area:
        manifest.append({"gazetteer_tracts_without_land_area": len(missing_area)})
    return tracts


def _parse_gazetteer_tracts(raw: bytes) -> dict[str, dict]:  # pragma: no cover - needs network
    """Parse the (tab-delimited) Census Gazetteer tract file from its zip."""

    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith((".txt", ".csv")))
        text = zf.read(name).decode("latin-1")
    table: dict[str, dict] = {}
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    for row in reader:
        clean = {k.strip(): (v.strip() if v else "") for k, v in row.items()}
        geoid = (clean.get("GEOID") or "").zfill(11)
        if not geoid:
            continue
        try:
            table[geoid] = {
                "land_area_sqmi": float(clean.get("ALAND_SQMI") or 0.0),
                "lat": float(clean.get("INTPTLAT") or 0.0),
                "lon": float(clean.get("INTPTLONG") or clean.get("INTPTLON") or 0.0),
            }
        except ValueError:
            continue
    return table


def load_delineation_api(manifest: list[dict]) -> dict[str, dict]:  # pragma: no cover - needs network
    """County→CBSA from the Census delineation file (xlsx), or a CSV override."""

    override = os.environ.get("RLE_CBSA_DELINEATION_FILE")
    if override:
        override_path = Path(override)
        if override_path.name == "cbsa_delineation.csv":
            return load_delineation_fixture(override_path.parent)
        if override_path.suffix.lower() == ".csv":
            return _parse_delineation_csv(override_path)
        openpyxl = _require("openpyxl")
        workbook = openpyxl.load_workbook(override_path, read_only=True, data_only=True)
        return _parse_delineation_workbook(workbook)
    requests = _require("requests")
    openpyxl = _require("openpyxl")
    session = _retrying_session(requests)
    raw = _cache_download(session, CBSA_DELINEATION_URL, "list1_2023.xlsx", manifest)
    workbook = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    return _parse_delineation_workbook(workbook)


def _parse_delineation_workbook(workbook) -> dict[str, dict]:
    """Parse an openpyxl Census/OMB delineation workbook."""

    ws = workbook.active
    rows = ws.iter_rows(values_only=True)
    header = None
    table: dict[str, dict] = {}
    for values in rows:
        cells = [("" if v is None else str(v).strip()) for v in values]
        if header is None:
            if any("CBSA Code" == c for c in cells):
                header = {c: i for i, c in enumerate(cells)}
            continue
        try:
            state = cells[header["FIPS State Code"]].zfill(2)
            county = cells[header["FIPS County Code"]].zfill(3)
        except (KeyError, IndexError):
            continue
        if not state.isdigit() or not county.isdigit():
            continue
        table[f"{state}{county}"] = {
            "cbsa_code": cells[header["CBSA Code"]].zfill(5),
            "cbsa_name": cells[header.get("CBSA Title", header["CBSA Code"])],
            "cbsa_type": cells[header.get("Metropolitan/Micropolitan Statistical Area", header["CBSA Code"])],
        }
    return table


def _parse_delineation_csv(path: Path) -> dict[str, dict]:  # pragma: no cover - exercised via override
    table: dict[str, dict] = {}
    for raw in _read_csv(path):
        county = _s(raw["county_geoid"]).zfill(5)
        table[county] = {
            "cbsa_code": _s(raw["cbsa_code"]).zfill(5),
            "cbsa_name": _s(raw.get("cbsa_name", "")),
            "cbsa_type": _s(raw.get("cbsa_type", "")),
        }
    return table


# ===========================================================================
# Tract → county/CBSA classification + aggregation
# ===========================================================================


def _weighted_centroid(tracts: list[dict]) -> tuple[float, float]:
    total = sum(t["population"] for t in tracts)
    if total <= 0:
        lat = sum(t["intpt_lat"] for t in tracts) / len(tracts)
        lon = sum(t["intpt_lon"] for t in tracts) / len(tracts)
        return round(lat, 5), round(lon, 5)
    lat = sum(t["intpt_lat"] * t["population"] for t in tracts) / total
    lon = sum(t["intpt_lon"] * t["population"] for t in tracts) / total
    return round(lat, 5), round(lon, 5)


def _aggregate_catchment(catchment_type: str, code: str, tracts: list[dict], primary_county: str) -> dict:
    population = sum(t["population"] for t in tracts)
    housing = sum(t["housing_units"] for t in tracts)
    land = sum(t["land_area_sqmi"] for t in tracts)
    pop_density = round(population / land, 1)
    housing_density = round(housing / land, 1)
    lat, lon = _weighted_centroid(tracts)
    climate_region = climate.climate_for_county(primary_county)
    return {
        "catchment_type": catchment_type,
        "catchment_code": code,
        "primary_county_geoid": primary_county,
        "climate_region": climate_region,
        "population": population,
        "housing_units": housing,
        "land_area_sqmi": round(land, 4),
        "population_density_sqmi": pop_density,
        "housing_unit_density_sqmi": housing_density,
        "centroid_lat": lat,
        "centroid_lon": lon,
        "tract_count": len(tracts),
    }


def aggregate(tracts: list[dict], delineation: dict[str, dict]) -> dict:
    """Aggregate rural tracts → county catchments, non-rural tracts → CBSA.

    Returns a dict with the built ``catchments`` plus a ``report`` describing
    join losses and unresolved classifications (never silently dropped).
    """

    county_tracts: dict[str, list[dict]] = defaultdict(list)
    cbsa_tracts: dict[str, list[dict]] = defaultdict(list)
    cbsa_county_pop: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tract_class_counts: dict[str, int] = defaultdict(int)
    join_losses: list[dict] = []

    for t in tracts:
        density = t["population"] / t["land_area_sqmi"]
        urbanicity = config.urbanicity_for_density(density)
        tract_class_counts[urbanicity] += 1
        if urbanicity == "rural":
            county_tracts[t["county_geoid"]].append(t)
            continue
        membership = delineation.get(t["county_geoid"])
        if membership is None:
            # Non-rural tract in a county with no CBSA: a real join loss. Report
            # it explicitly rather than folding it into the county silently.
            join_losses.append(
                {
                    "tract_geoid": t["tract_geoid"],
                    "county_geoid": t["county_geoid"],
                    "tract_urbanicity": urbanicity,
                    "reason": "non-rural tract in a county absent from the CBSA delineation (Non-core)",
                }
            )
            continue
        code = membership["cbsa_code"]
        cbsa_tracts[code].append(t)
        cbsa_county_pop[code][t["county_geoid"]] += t["population"]

    catchments: list[dict] = []

    # Rural → county catchments.
    for county_geoid in sorted(county_tracts):
        c = _aggregate_catchment("County", county_geoid, county_tracts[county_geoid], county_geoid)
        c["urbanicity"] = "rural"
        c["urbanicity_short"] = config.URBANICITY_SHORT["rural"]
        c["catchment_label"] = _county_label(county_tracts[county_geoid])
        catchments.append(c)

    # Non-rural → CBSA catchments (urbanicity from the CBSA's aggregate density).
    unresolved: list[dict] = []
    for code in sorted(cbsa_tracts):
        members = cbsa_tracts[code]
        primary_county = max(cbsa_county_pop[code].items(), key=lambda kv: (kv[1], kv[0]))[0]
        c = _aggregate_catchment("CBSA", code, members, primary_county)
        urbanicity = config.urbanicity_for_density(c["population_density_sqmi"])
        if urbanicity == "rural":
            unresolved.append(
                {
                    "cbsa_code": code,
                    "aggregate_density_sqmi": c["population_density_sqmi"],
                    "reason": "CBSA aggregate density classified rural; excluded from non-rural catchments",
                }
            )
            continue
        c["urbanicity"] = urbanicity
        c["urbanicity_short"] = config.URBANICITY_SHORT[urbanicity]
        c["catchment_label"] = _cbsa_label(members, delineation)
        catchments.append(c)

    catchments.sort(key=lambda r: (r["catchment_type"], _code_int(r["catchment_code"])))
    report = {
        "tract_count": len(tracts),
        "tract_urbanicity_counts": dict(sorted(tract_class_counts.items())),
        "county_catchment_count": sum(1 for c in catchments if c["catchment_type"] == "County"),
        "cbsa_catchment_count": sum(1 for c in catchments if c["catchment_type"] == "CBSA"),
        "join_loss_count": len(join_losses),
        "join_losses": join_losses,
        "unresolved_cbsa_count": len(unresolved),
        "unresolved_cbsa": unresolved,
    }
    return {"catchments": catchments, "report": report}


def _county_label(tracts: list[dict]) -> str:
    name = next((t["county_name"] for t in tracts if t.get("county_name")), "")
    return name or f"County {tracts[0]['county_geoid']}"


def _cbsa_label(tracts: list[dict], delineation: dict[str, dict]) -> str:
    for t in tracts:
        membership = delineation.get(t["county_geoid"])
        if membership and membership.get("cbsa_name"):
            return membership["cbsa_name"]
    return f"CBSA {delineation.get(tracts[0]['county_geoid'], {}).get('cbsa_code', '')}"


# ===========================================================================
# Candidate scoring + partial deterministic selection
# ===========================================================================


def build_candidate_rows(catchments: list[dict]) -> list[dict]:
    """Within-stratum percentiles + baseline score, over only present strata."""

    by_stratum: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for c in catchments:
        by_stratum[(c["climate_region"], c["urbanicity"])].append(c)

    candidates: list[dict] = []
    for stratum in sorted(by_stratum):
        subset = by_stratum[stratum]
        huc = _percentiles([float(r["housing_units"]) for r in subset])
        pcp = _percentiles([float(r["population"]) for r in subset])
        pdp = _percentiles([float(r["population_density_sqmi"]) for r in subset])
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
                "population_2010": int(src["population"]),
                "housing_units_2010": int(src["housing_units"]),
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


def select(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    """Deterministic per-stratum top among eligible candidates (partial).

    Eligibility mirrors the national density screen + station-distance bound. A
    stratum with no eligible candidate is reported UNRESOLVED with no selection,
    rather than forcing a pick.
    """

    by_stratum: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in candidates:
        by_stratum[(row["climate_region"], row["urbanicity"])].append(row)

    selected: list[dict] = []
    stratum_rows: list[dict] = []
    for stratum in sorted(by_stratum):
        subset = by_stratum[stratum]
        eligible = [
            r
            for r in subset
            if float(r["population_density_percentile"]) >= DENSITY_SCREEN
            and float(r["station_distance_miles"]) <= MAX_STATION_DISTANCE
        ]
        stratum_rows.append(
            {
                "climate_region": stratum[0],
                "urbanicity": stratum[1],
                "status": "RESOLVED" if eligible else "UNRESOLVED",
                "eligible_candidate_count": len(eligible),
            }
        )
        if not eligible:
            continue
        winner = sorted(eligible, key=lambda r: (-r["location_score"], _code_int(r["catchment_code"])))[0]
        winner["selected"] = True
        selected.append(winner)
    selected.sort(key=lambda r: (config.CLIMATE_ORDER.index(r["climate_region"]), r["catchment_code"]))
    return selected, stratum_rows


# ===========================================================================
# Output assembly
# ===========================================================================


def build_outputs(source: str, states: list[str] | None = None, data_dir: Path = config.PILOT_DATA_DIR) -> dict:
    states = sorted(states or PILOT_STATES)
    manifest: list[dict] = []
    if source == "api":  # pragma: no cover - needs network
        tracts = load_tracts_api(states, manifest)
        delineation = load_delineation_api(manifest)
    else:
        tracts = load_tracts_fixture(states, data_dir)
        delineation = load_delineation_fixture(data_dir)

    agg = aggregate(tracts, delineation)
    candidates = build_candidate_rows(agg["catchments"])
    selected, stratum_rows = select(candidates)

    qc_rows = weather_qc.compute_rows(
        [(int(r["selected_station_number"]), r["selected_station_name"]) for r in selected],
        source,
    )
    qc_status = weather_qc.status_map(qc_rows)

    enumerations, dictionary_label, resstock_provenance = resstock_dictionary.load_enumerations_detailed(source)
    site_rows = []
    for row in selected:
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

    report = dict(agg["report"])
    report.update(
        {
            "pilot_states": {s: PILOT_STATES[s] for s in states if s in PILOT_STATES},
            "candidate_count": len(candidates),
            "selected_count": len(selected),
            "strata_present": len(stratum_rows),
            "strata_resolved": sum(1 for r in stratum_rows if r["status"] == "RESOLVED"),
            "strata_unresolved": sum(1 for r in stratum_rows if r["status"] != "RESOLVED"),
            "national_strata_total": len(config.STRATA),
            "download_manifest": manifest,
            "source": source,
            "vintage": VINTAGE,
        }
    )

    return {
        "candidates": candidates,
        "selected": selected,
        "site_list": site_rows,
        "stratum_status": stratum_rows,
        "station_weather_qc": qc_rows,
        "resstock_provenance": resstock_provenance,
        "geometry": geometry.feature_collection(selected, source),
        "report": report,
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
    (out_dir / "selected_geometry.json").write_text(json.dumps(outputs["geometry"], indent=2), encoding="utf-8")
    (out_dir / REPORT_FILE).write_text(json.dumps(outputs["report"], indent=2), encoding="utf-8")

    report = outputs["report"]
    site_rows = outputs["site_list"]
    site_verified = sum(bool(r["nrel_value_verified"]) for r in site_rows)
    qc_rows = outputs["station_weather_qc"]
    qc_complete = sum(r["hourly_weather_qc_status"] == "COMPLETE" for r in qc_rows)
    is_fixture = source != "api"
    metadata = {
        "analysis_name": "Representative Location Selection — tract-level pilot (PA/AZ/MN)",
        "method_version": "2.1-pilot-tract",
        "boundary_system": "Tract-derived: rural tracts → county catchments, non-rural tracts → CBSA catchments",
        "data_mode": "pilot-fixture" if is_fixture else "pilot-api",
        "is_partial_result": True,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "vintage": VINTAGE,
        "pilot_states": report["pilot_states"],
        "strata_present": report["strata_present"],
        "national_strata_total": report["national_strata_total"],
        "sources": (
            [
                {
                    "name": "U.S. Census Bureau — ACS 2019–2023 5-year (tract population & housing units)",
                    "role": "Tract-level population and housing-unit counts.",
                    "file": "pipeline/pilot.py (--source api)",
                },
                {
                    "name": "U.S. Census Bureau — 2023 Gazetteer (tract land area + interior point)",
                    "role": "Tract land area for density and population-weighted centroids.",
                    "file": "pipeline/pilot.py (--source api)",
                },
                {
                    "name": "Census/OMB — Metro/Micro delineation file (July 2023, 2020 standards)",
                    "role": "County→CBSA membership for aggregating non-rural tracts.",
                    "file": "pipeline/pilot.py (--source api)",
                },
                {
                    "name": "NOAA Integrated Surface Database (ISH/ISD 2023)",
                    "role": "Nearest weather-station assignment per catchment.",
                    "file": "pipeline/data/ish2023_stations.csv",
                },
                {
                    "name": "DOE Building America / IECC climate zones",
                    "role": "Climate-region assignment from the primary county.",
                    "file": "pipeline/climate.py",
                },
            ]
            if not is_fixture
            else [
                {
                    "name": "Recorded tract-level pilot fixtures",
                    "role": (
                        "Real geography identifiers (state/county FIPS, CBSA codes, July-2023 "
                        "county→CBSA memberships) with representative, clearly-labelled tract "
                        "attributes so the tract→county→CBSA method runs offline. Not measured "
                        "ACS/Gazetteer values; run --source api for those."
                    ),
                    "file": "pipeline/data/pilot/*.csv",
                }
            ]
        ),
        "limitations": [
            (
                "PARTIAL RESULT: a 3-state pilot reaches "
                f"{report['strata_present']} of {report['national_strata_total']} national "
                "strata; it is not a complete national selection."
            ),
            (
                f"Join/classification reporting: {report['join_loss_count']} non-rural tract(s) "
                f"had no CBSA (Non-core) and {report['unresolved_cbsa_count']} CBSA(s) classified "
                "rural in aggregate; both are reported in pilot_report.json, not discarded."
            ),
            (
                "Tract attributes are representative structural stand-ins in --source fixture; "
                "regenerate with --source api for measured ACS/Gazetteer values."
                if is_fixture
                else "Tract attributes are measured ACS 2019–2023 / 2023 Gazetteer values."
            ),
            (
                f"ResStock/ComStock values are enumeration-verified: {site_verified} of "
                f"{len(site_rows)} selected codes matched the loaded data dictionary; the rest "
                "are flagged REVIEW REQUIRED (real county/CBSA codes need the real ResStock "
                "dictionary via RESSTOCK_ENUMERATION_FILE)."
            ),
            (
                f"Per-station hourly weather QC: {qc_complete} of {len(qc_rows)} assigned "
                "stations meet the ≥90% completeness bar "
                + ("(fixture stand-in coverage)." if is_fixture else "(NOAA ISD).")
            ),
        ],
        "provenance": {
            "resstock_dictionary": outputs.get("resstock_provenance", {}),
            "geometry": outputs["geometry"].get("metadata", {}),
            "weather_qc": {
                "expected_hours_basis": "leap-aware (8,760 hours; 8,784 in a leap year)",
                "completeness_threshold": weather_qc.COMPLETE_THRESHOLD,
            },
        },
    }
    (out_dir / "selection_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


# ===========================================================================
# Partial-result validation (the national validator enforces 20 strata; the
# pilot is intentionally partial, so it gets its own tolerant checks).
# ===========================================================================


def _columns(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return next(csv.reader(handle))


def validate_pilot(out_dir: Path) -> list[str]:
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
        REPORT_FILE,
    ]
    for name in required:
        check((out_dir / name).exists(), f"missing pilot output file: {name}")
    if errors:
        return errors

    check(_columns(out_dir / "candidate_scores.csv") == CANDIDATE_FIELDS, "candidate_scores.csv schema mismatch")
    check(_columns(out_dir / "selected_locations.csv") == CANDIDATE_FIELDS, "selected_locations.csv schema mismatch")
    check(_columns(out_dir / "resstock_site_list.csv") == SITE_FIELDS, "resstock_site_list.csv schema mismatch")
    check(_columns(out_dir / "stratum_status.csv") == STRATUM_FIELDS, "stratum_status.csv schema mismatch")

    candidates = _read_csv(out_dir / "candidate_scores.csv")
    selected = _read_csv(out_dir / "selected_locations.csv")
    site_list = _read_csv(out_dir / "resstock_site_list.csv")
    stratum_status = _read_csv(out_dir / "stratum_status.csv")

    check(bool(candidates), "pilot produced no candidate catchments")
    check(bool(selected), "pilot produced no selected catchments")

    # Partial-but-coherent invariants.
    valid_strata = set(config.STRATA)
    for r in candidates:
        check((r["climate_region"], r["urbanicity"]) in valid_strata, f"candidate in unknown stratum: {r}")
    # One selection per RESOLVED stratum; selections are distinct catchments.
    resolved = {(r["climate_region"], r["urbanicity"]) for r in stratum_status if r["status"] == "RESOLVED"}
    sel_strata = [(r["climate_region"], r["urbanicity"]) for r in selected]
    check(len(sel_strata) == len(set(sel_strata)), "more than one selection in a stratum")
    check(set(sel_strata) == resolved, "selected strata do not match the RESOLVED strata")
    keys = {f"{r['catchment_type']}:{str(r['catchment_code']).zfill(5)}" for r in selected}
    check(len(keys) == len(selected), "selected catchments are not distinct")

    # County/CBSA + rural rules.
    for r in selected:
        if r["urbanicity"] == "rural":
            check(r["catchment_type"] == "County", f"rural selection {r['catchment_code']} must be County")
        else:
            check(r["catchment_type"] == "CBSA", f"non-rural selection {r['catchment_code']} must be CBSA")
    for r in site_list:
        if r["target_catchment_type"] == "County":
            check(r["nrel_filter_field"] == resstock_dictionary.COUNTY_FIELD, "county must use in.county")
        else:
            check(r["nrel_filter_field"] == resstock_dictionary.CBSA_FIELD, "CBSA must use the CBSA filter field")

    check(abs(sum(config.SCORE_WEIGHTS.values()) - 1.0) < 1e-9, "score weights must sum to 1.0")

    try:
        meta = json.loads((out_dir / "selection_metadata.json").read_text(encoding="utf-8"))
        for fld in ("analysis_name", "method_version", "boundary_system", "sources", "limitations", "vintage"):
            check(fld in meta, f"selection_metadata.json missing '{fld}'")
        check(meta.get("is_partial_result") is True, "pilot metadata must mark is_partial_result true")
    except json.JSONDecodeError as exc:
        errors.append(f"selection_metadata.json invalid JSON: {exc}")

    return errors


# ===========================================================================
# Entry point
# ===========================================================================


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the tract-level pilot pipeline (PA/AZ/MN).")
    parser.add_argument("--source", choices=["fixture", "api"], default="fixture")
    parser.add_argument("--out", type=Path, default=config.PILOT_OUT_DIR)
    parser.add_argument(
        "--states",
        nargs="+",
        default=None,
        help="State FIPS to include (default: the three pilot states 04, 27, 42).",
    )
    args = parser.parse_args(argv)

    outputs = build_outputs(args.source, args.states)
    write_outputs(outputs, args.out, args.source)
    errors = validate_pilot(args.out)
    report = outputs["report"]
    print(
        f"[pilot] source={args.source} states={sorted(report['pilot_states'])}: "
        f"{report['tract_count']} tracts -> {report['candidate_count']} candidates, "
        f"{report['selected_count']} selected across {report['strata_resolved']} resolved strata "
        f"(of {report['national_strata_total']} national); "
        f"join_losses={report['join_loss_count']}, unresolved_cbsa={report['unresolved_cbsa_count']} -> {args.out}"
    )
    if errors:
        print(f"[pilot] VALIDATION FAILED ({len(errors)} issue(s)):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("[pilot] validation OK — partial schema + invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
