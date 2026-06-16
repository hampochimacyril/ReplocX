# Live Data Runbook — Sessions 3 & 4 (networked machine)

This runbook executes the parts of **Session 3 (real ancillary-data integration)**
and **Session 4 (national production run)** that require outbound network access
to public federal data hosts. The code for every step is implemented and
**unit-tested offline against recorded real-schema fixtures**; this document is
how you run it for real and audit the result.

> Why a separate runbook: the Cowork sandbox these sessions were prepared in can
> only reach `github.com`. `census.gov`, `huduser.gov`, `ncei.noaa.gov`, and the
> NREL/OEDI S3 lake are blocked there, so the live downloads and the national run
> must happen on a machine with network access. No analytical data is fabricated;
> fixtures stay clearly labeled synthetic.

## 0. Prerequisites

```bash
# Python 3.11 or 3.12 (the pipeline uses datetime.UTC, which is 3.11+).
scripts/bootstrap_dev.sh                 # creates .venv, installs deps + Playwright
.venv/bin/python -m pip install requests openpyxl   # needed only for --source api
```

Free credentials (both no-cost):

| Variable | Get it from |
| --- | --- |
| `CENSUS_API_KEY` | https://api.census.gov/data/key_signup.html |
| `HUD_API_TOKEN`  | https://www.huduser.gov/portal/dataset/uspszip-api.html |

Load locally saved credentials without printing them:

```bash
set -a
. ./.env.live       # local, chmod 600, gitignored
set +a
```

Verified-current public sources (checked June 2026):

| Source | URL |
| --- | --- |
| HUD-USPS ZIP crosswalk API | `https://www.huduser.gov/hudapi/public/usps` (type 2 = ZIP-COUNTY, type 3 = ZIP-CBSA; quarterly) |
| Census TIGERweb (county/CBSA polygons) | `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb` |
| NOAA ISD global-hourly | `https://www.ncei.noaa.gov/data/global-hourly/access/<year>/<11-digit-id>.csv` |
| NREL ResStock dictionaries (2025 AMY2018 release 1) | OEDI lake `.../2025/resstock_amy2018_release_1/data_dictionary.tsv` and `enumeration_dictionary.tsv` |

Additional inputs:

| Variable | Purpose |
| --- | --- |
| `RLE_ZIP_ZCTA_FILE` | A ZIP→ZCTA relationship CSV (cols: `zip`,`zcta`). HUD does **not** supply ZCTA, so without this ZCTA stays blank — it is **never** equated to the ZIP. |
| `RLE_CBSA_DELINEATION_FILE` | **Required for the national API run.** OMB/Census county→CBSA delineation (xlsx or CSV), used to assign each CBSA a valid central-county climate fallback. |
| `RESSTOCK_ENUMERATION_FILE` | A real ResStock dictionary artifact (see above) so filter values are verified, not assumed. |
| `RLE_WEATHER_QC_YEAR` | Simulation year for weather QC (default 2023). Leap years are handled (8,784 vs 8,760 hours). |
| `RLE_ISD_HISTORY_FILE` | Optional cached NOAA `isd-history.csv`; otherwise it is downloaded and cached automatically to resolve USAF→WBAN IDs. |

---

## 1. Session 3 — live ancillary data

Run each ancillary fetcher with `--source api` and inspect its provenance.

### 1a. HUD-USPS ZIP crosswalk (one-to-many, real ZCTA)

```bash
export HUD_API_TOKEN=...
export RLE_ZIP_ZCTA_FILE=/path/to/zip_to_zcta.csv     # optional but recommended
.venv/bin/python -m pipeline.fetch_hud_crosswalk --source api --quarter 1 --year 2025 \
    --out pipeline/out/zip_crosswalk.csv
```

Check `pipeline/out/zip_crosswalk_provenance.json`:
- `one_to_many_zip_count > 0` (split ZIPs retained, each with its `allocation_ratio`);
- `zcta_resolved` reflects whether `RLE_ZIP_ZCTA_FILE` was supplied;
- spot-check that **no** row has `zcta == zip_code` unless the relationship file says so.
- the analytical scope is the 50 states plus DC; territory rows returned by HUD
  are explicitly excluded because the project climate/station framework is CONUS-based.

### 1b. NOAA ISD weather QC (leap-year aware + error report)

```bash
.venv/bin/python -m pipeline.weather_qc --source api --year 2023 \
    --out pipeline/out/station_weather_qc.csv
```

- `expected_hours` is 8,760 (8,784 in a leap year);
- every selected station is `COMPLETE`/`INCOMPLETE` — **no `PENDING`**;
- `pipeline/out/station_weather_qc_errors.csv` lists any per-station fetch/parse failures with the exact URL (the downloadable error report).
- station-year CSVs cache under `pipeline/cache/weather/<year>/`; interrupted
  files retain a `.part` suffix and resume with HTTP Range on rerun.

### 1c. TIGER/Line geometry (MultiPolygon, Alaska, validation)

Geometry is emitted as part of the build (1d) or standalone:

```bash
.venv/bin/python -m pipeline.geometry --in pipeline/out/selected_locations.csv \
    --source api --out pipeline/out/selected_geometry.json
```

In the `FeatureCollection.metadata`: `features_with_validation_issues` should be 0
and `fetch_errors` empty. Islands are kept (MultiPolygon); Alaskan rings that
cross the antimeridian carry `antimeridian_adjusted: true`.

### 1d. ResStock enumeration (real dictionary)

```bash
export RESSTOCK_ENUMERATION_FILE=/path/to/data_dictionary.tsv   # or enumeration_dictionary.tsv
```

The parser reads the real NREL artifacts directly (no hand reformat). A repository
`options_lookup.tsv` containing human-readable geography labels is not sufficient
to verify the numeric county/CBSA filters emitted here. Codes not present become
`REVIEW REQUIRED` — never silently verified.

### Session 3 acceptance gate

- [x] Pilot ZIP resolution works beyond the bundled demo records.
- [x] Every selected pilot location has valid geometry or an explicit failure status.
- [x] Weather QC has no `PENDING` for processed pilot stations.
- [x] Enumeration verification is backed by the real dictionary (provenance records its SHA-256).

Pilot end-to-end with live inputs:

```bash
export CENSUS_API_KEY=...
.venv/bin/python -m pipeline.pilot --source api          # PA / AZ / MN tract pilot
```

---

## 2. Session 4 — national production run

```bash
export CENSUS_API_KEY=... HUD_API_TOKEN=...
export RESSTOCK_ENUMERATION_FILE=/path/to/data_dictionary.tsv
export RLE_ZIP_ZCTA_FILE=/path/to/zip_to_zcta.csv
export RLE_CBSA_DELINEATION_FILE=/path/to/delineation.xlsx
export RLE_WEATHER_QC_YEAR=2023

.venv/bin/python -m pipeline.run --source api            # full national pipeline
```

The live national path uses the tract-derived method: ACS tracts are classified
by density, rural tracts aggregate to counties, and non-rural tracts aggregate to
CBSAs via the OMB/Census delineation. Raw downloads cache under `pipeline/cache/`
(gitignored) with SHA-256 + source dates, so reruns are network-light. **Verify/
confirm** retry + resumable-download behavior on first live execution and add
backoff where a host rate-limits — that hardening is part of Session 4 and cannot
be exercised offline.

Outputs land in `pipeline/out/` plus the provenance sidecars
(`zip_crosswalk_provenance.json`, `station_weather_qc_errors.csv`, geometry
metadata, and the `provenance` block in `selection_metadata.json`).

### Validate

```bash
.venv/bin/python -m pipeline.validate --dir pipeline/out
```

Confirm the invariants: 20 resolved strata, deterministic selection, rural→County /
non-rural→CBSA, 20 distinct catchments, score weights sum to 1.0, geometry validity
(Polygon/MultiPolygon, closed rings), weather-QC coverage, ZIP coverage, and
ResStock enumeration status.

### Audit & document

- Compare national results against the prior dissertation outputs; explain material
  differences by **data vintage, boundary definitions, classification, or scoring** —
  do not force agreement (see `docs/methodology.md` → analytical vintage).
- Update `docs/methodology.md` and `docs/data_sources.md` with citations, source
  quarters/release versions, and known limitations.

### Run the app on the national outputs (production mode)

```bash
RLE_ANALYSIS_DATA_DIR=pipeline/out .venv/bin/python -m backend.server
curl -s localhost:8787/api/v1/health | .venv/bin/python -m json.tool   # expect data_mode: production
scripts/verify_all.sh
```

> Keep the national dataset private. Never publish it through the public demo
> service (see `docs/deployment_options.md`).

### Session 4 acceptance gate

- [x] The live national run completes from documented public inputs.
- [x] The app reports `data_mode: production` when pointed at the outputs.
- [x] Validation produces no unexplained failed invariant.
- [x] A reviewer can reproduce the run from this runbook + provenance sidecars.

---

## 3. June 7, 2026 execution record

The ancillary logic is covered by `tests/test_session3_ancillary.py` against
recorded real-schema fixtures in `tests/fixtures/ancillary/`:
one-to-many ZIP retention, the ZIP≠ZCTA guarantee, TIGER MultiPolygon/Alaska
handling + geometry validation, leap-year hour accounting + the error report, and
the three real ResStock dictionary formats. The full suite (84 tests in both demo
and pipeline-output modes), `ruff`, `black`, `mypy`, coverage, dependency audit,
frontend syntax, and four Playwright tests passed.

Live results:

- pilot: 6,712 tracts, 244 candidates, 10 selected; 10/10 NREL filters verified,
  9 weather `COMPLETE`, 1 `INCOMPLETE`, and zero TIGER errors;
- national: 84,080 tracts, 4,019 candidates, 20 resolved strata, 20 distinct
  selections, 20/20 NREL filters verified, 19 weather `COMPLETE`, 1
  `INCOMPLETE`, and zero TIGER errors;
- HUD Q1 2025: 54,242 rows covering 39,299 ZIPs, including 11,303 one-to-many
  ZIPs, with supplied ZIP-to-ZCTA resolution;
- app health: `data_mode: production`, `method_version: 3.0-national-tract`.
