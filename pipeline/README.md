# `pipeline/` — national data pipeline (Phase 1 + Phase 2)

Regenerates the analytical CSVs the app reads (`candidate_scores.csv`,
`selected_locations.csv`, `resstock_site_list.csv`, `stratum_status.csv`,
`selection_metadata.json`) plus the Phase 2 artifacts (`zip_crosswalk.csv`,
`station_weather_qc.csv`, `selected_geometry.json`) from **free, public data** —
removing the dependency on hand-supplied "private" outputs.

```
fixture: fetch_census -> classify -> build_catchments -> fetch_hud_crosswalk -> validate
api:     tract Census + CBSA delineation -> aggregate -> build_catchments -> fetch_hud_crosswalk -> validate
                                                        ^          ^   ^
                                                        |          |   └─ geometry (TIGER polygons, Phase 2)
                                   weather_stations (ISD master) ─┘
                                       weather_qc (ISD hourly completeness, Phase 2) ─┘
```

| Stage | Module | Does |
|---|---|---|
| 1 | `fetch_census.py` / `pilot.py` | Fixture mode replays a deterministic raw catchments table. Live national mode uses the tract-derived path in `pilot.py`: ACS tracts + Gazetteer tract area + OMB delineation. |
| 2 | `classify.py` / tract aggregation | Fixture mode classifies raw catchments. Live national mode classifies each tract by density, aggregates rural tracts to counties and non-rural tracts to CBSAs, and assigns climate from the primary county. |
| 3 | `build_catchments.py` | Assigns each catchment its nearest real NOAA ISD-2023 station (`weather_stations.py`); computes densities, within-stratum percentiles, and the baseline `location_score`; derives the canonical 20-location selection by calling the app's own `backend.scoring`; runs `weather_qc` + `geometry`; writes the five schema-matching files plus `station_weather_qc.csv` and `selected_geometry.json`. |
| 3a | `weather_qc.py` *(Phase 2)* | Per-station hourly temperature+humidity completeness. A station-year is `COMPLETE` at **≥90 % of 8,760 hours**, else `INCOMPLETE` — replacing the old `PENDING`. `--source api` reads NOAA ISD global-hourly; `--source fixture` assigns deterministic coverage. |
| 3b | `geometry.py` *(Phase 2)* | Simplified catchment polygons as GeoJSON for the map. `--source api` pulls + decimates Census TIGER/Line cartographic boundaries; `--source fixture` emits deterministic synthetic polygons. Rendered front-end-side as dependency-free SVG `<path>` (not TopoJSON). |
| 3c | `fetch_hud_crosswalk.py` *(Phase 2)* | ZIP→ZCTA/county/CBSA crosswalk with allocation ratios. `--source api` pulls the live HUD-USPS quarterly crosswalk (needs `HUD_API_TOKEN`); `--source fixture` replays the curated demonstration records. `--refresh` re-pulls a quarter. |
| 4 | `validate.py` | Checks column schemas and structural invariants (20 strata, 20 distinct catchments, County/CBSA filter rules, every stratum eligible, weights sum to 1.0) **plus** the Phase 2 artifacts when present (QC schema/threshold consistency, crosswalk schema, 20 closed-ring polygons matching the selection). |

`weather_stations.py` loads `data/ish2023_stations.csv` — the project's 2,007
continental-U.S. ISD-2023 stations, each tagged with a Köppen-derived climate
region, a LEAD tract urbanicity class, and its CBSA — and provides nearest-station
lookup plus the per-CBSA climate labels used in `--source api`.

## Run it

Offline (no network, no key — what CI and the test suite use):

```bash
python3 -m pipeline.run --source fixture
RLE_ANALYSIS_DATA_DIR=pipeline/out python3 -m unittest   # 30 tests pass, data_mode: production
```

Real national run (on a machine with outbound network):

```bash
export CENSUS_API_KEY=...            # free: api.census.gov/data/key_signup.html
export RLE_CBSA_DELINEATION_FILE=...  # OMB/Census county-to-CBSA workbook
export HUD_API_TOKEN=...             # free: huduser.gov/portal/dataset/uspszip-api.html (Phase 2 crosswalk)
python3 -m pipeline.run --source api
```

The app picks up the result automatically when `RLE_ANALYSIS_DATA_DIR` points at
`pipeline/out`; the bundled `data/demo/` dataset stays the default so a fresh
clone always loads.

## Tract-level pilot (Session 2)

`pipeline/pilot.py` is a separate, genuinely **tract-derived** pilot over three
states that span distinct climate and urbanicity conditions — **Pennsylvania**
(Mixed-Humid), **Arizona** (Hot-Dry & Mixed Dry), and **Minnesota** (Cold & Very
Cold). It replaces the direct county/CBSA live-data shortcut for these states:

```
load tracts ─▶ classify tract urbanicity ─▶ join tract→county→CBSA (delineation)
            ─▶ aggregate rural→County / non-rural→CBSA ─▶ score ─▶ partial select
```

Each tract is classified by its own density, rural tracts roll up to **county**
catchments and non-rural tracts to **CBSA** catchments (via the documented Census
delineation), each catchment takes a climate region from its primary county, and a
deterministic per-stratum top is selected. Outputs are **schema-compatible but
partial** (only the strata the pilot states reach) and land in a separate
`pipeline/pilot_out/` — never the national `pipeline/out/`. A `pilot_report.json`
reports row counts, **join losses** (non-rural tracts with no CBSA) and
**unresolved** classifications instead of dropping them.

```bash
# Offline (recorded fixtures; what the tests use):
python3 -m pipeline.pilot --source fixture

# Real tract data (networked machine; caches raw downloads + checksums):
export CENSUS_API_KEY=...          # api.census.gov/data/key_signup.html
python3 -m pipeline.pilot --source api
```

Vintage is pinned to a single 2020-boundary stack (ACS 2019–2023 5-year · 2023
Gazetteer tracts · July-2023 CBSA delineation), intentionally distinct from the
2010 dissertation baseline and never mixed with it. The offline fixtures
(`pipeline/data/pilot/`) carry real geography identifiers with clearly-labelled
representative tract attributes; see `docs/methodology.md` and
`docs/data_sources.md`.

## Honesty notes / scope

- **`--source fixture` is not a research result.** It is a reproducible
  structural stand-in (synthetic counts apart from real anchor geographies,
  including Philadelphia CBSA 37980, plus the real ISD station assignment) that
  preserves every invariant the app and tests assert, so everything runs without
  network or a key. The fixture keeps its engineered climate/urbanicity so the
  documented override stays valid; file-label authority applies to `--source api`.
- **`--source api` produces a real national computation** from open data but
  still owes the methodological peer review the project tracks separately.
- **Resolved with the ISD-2023 file:** weather stations are now real (nearest
  ISD station per catchment), and CBSA climate comes from the file in
  `--source api`; aggregate density determines urbanicity.
- **Phase 2 — done:** per-selected-station *hourly completeness* QC is computed
  (`station_weather_qc.csv`; `COMPLETE` at ≥90 % of 8,760 h, else `INCOMPLETE` —
  no more `PENDING` for selected sites); the ZIP crosswalk is a documented artifact
  (`zip_crosswalk.csv`; HUD-USPS in `--source api`, curated replay in `fixture`);
  and the map draws real catchment polygons (`selected_geometry.json`; TIGER/Line
  in `--source api`, synthetic in `fixture`) as dependency-free SVG paths. In the
  offline fixture the QC coverage and polygons are deterministic stand-ins, not
  measured values.
- **Phase 3 — done:** ResStock/ComStock filter values are now
  *enumeration-verified* against a public data dictionary
  (`resstock_dictionary.py`): `--source api` checks the real ResStock
  enumeration (`RESSTOCK_ENUMERATION_FILE`) and honestly emits `REVIEW REQUIRED`
  for any code not present, while `--source fixture` verifies against the bundled
  demonstration enumeration (`data/resstock_enumerations.csv`). One-click export
  adapters (`backend/exports.py`) emit a ResStock/ComStock sampling downselect and
  an OpenStudio/EnergyPlus manifest from the selected sites, and a stdlib-only
  Python client (`clients/python/`) lets URBANopt/GeoPandas pipelines call the
  selection over the REST API.
- **Phase 4 — done:** production hooks are free-tier/stdlib-first. The API is
  formally versioned at `/api/v1` while legacy `/api` routes stay compatible;
  saved scenarios persist to SQLite (`RLE_SCENARIO_DB`) with share ids and
  version metadata; private deployments can require bearer-token auth
  (`RLE_PRIVATE_AUTH_TOKEN`) and use `render.private.example.yaml`; request/error
  logs are structured JSON with optional Sentry capture (`RLE_SENTRY_DSN`); CI
  now declares ruff/black/mypy/coverage/pip-audit gates plus Dependabot.
- **Still carried forward:** climate falls back to the state/county map where the
  ISD file has no coverage; the real ResStock dictionary must be supplied for a
  national `--source api` verification.

## Data sources (free / public)

U.S. Census ACS 5-year (population, housing units) · Census Gazetteer (land
area, interior point) · Census TIGER/Line cartographic boundaries (map polygons) ·
HUD-USPS ZIP crosswalk (ZIP→ZCTA/county/CBSA with allocation ratios) · NOAA
Integrated Surface Database (ISH/ISD 2023 stations + global-hourly completeness) ·
DOE Building America / IECC climate zones (fallback) · NREL ResStock spatial
enumerations / data dictionary, on the Open Energy Data Initiative — OEDI (Phase 3
ResStock value verification). Cite these in any downstream use.
