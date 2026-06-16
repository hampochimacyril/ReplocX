# ReplocX Methodology

## Target Strata

The baseline method selects one target catchment for each of 20 strata:

- Cold & Very Cold
- Hot-Dry & Mixed Dry
- Hot-Humid
- Marine
- Mixed-Humid

Each climate region is crossed with HDU, LDU, suburban / small-town, and rural
urbanicity categories.

## Catchments and Weather Stations

Target communities and weather stations are intentionally separate. A weather station
provides climate context. It does not redefine the building-stock or socioeconomic
geography.

- HDU, LDU, and suburban tracts are aggregated within a CBSA.
- Rural tracts are aggregated within a county.
- Stations remain separate points with explicit distances to catchment centroids.

## Density Screen and Score

Candidates at or above the configurable within-stratum population-density percentile
remain eligible. The baseline is the 60th percentile.

```text
score =
  0.45 × housing-unit coverage percentile
  + 0.35 × population-density percentile
  + 0.20 × population-coverage percentile
```

The scenario builder can add an explicit station-distance penalty without silently
changing the baseline formula.

## Allocation

The global allocator uses deterministic min-cost flow to maximize the sum of selected
scores while assigning one catchment to each stratum. When the unique-location rule is
enabled, each target catchment has capacity one. The interface reports substitutions
and score differences relative to independent within-stratum top candidates.

## Tract-Derived Pilot and National Run

`pipeline/pilot.py` implements the genuinely tract-derived method above for three
pilot states that span distinct climate regions and the full urbanicity range:
Pennsylvania (Mixed-Humid), Arizona (Hot-Dry & Mixed Dry), and Minnesota (Cold &
Very Cold). `pipeline.run --source api` applies the same method nationally,
replacing the earlier county/CBSA live-data shortcut. The steps are:

1. Read one row per **census tract** (population, housing units, land area,
   interior point).
2. Classify each tract's **urbanicity** from its own population density using the
   documented, reproducible breaks in `pipeline/config.URBANICITY_DENSITY_BREAKS`
   (≥3000 HDU, ≥1000 LDU, ≥200 suburban/small town, else rural). This is the
   reproducible classification permitted by the method; swapping in the LEAD
   tract classification is a documented future option (see `docs/data_sources.md`).
3. Join each tract to its **county** structurally (the first five GEOID digits)
   and each county to a **CBSA** via a documented Census delineation file.
4. Aggregate **non-rural tracts → CBSA catchments** and **rural tracts → county
   catchments**, summing population/housing/land and recomputing density and a
   population-weighted centroid. A CBSA's catchment urbanicity comes from its
   aggregate density.
5. Assign each catchment a **climate region** from its primary county, score it
   within stratum, and pick a deterministic per-stratum top.

### Analytical vintage (no mixing)

The pilot and live national run pin a single, internally consistent **2020
boundary** vintage so tract boundaries, population years, and CBSA delineations
are never mixed:

| Input | Vintage |
| --- | --- |
| Tract & county boundaries | 2020 Census (TIGER/Line, 2020 vintage) |
| Population & housing units | ACS 2019–2023 5-year |
| Tract land area & interior point | 2023 Census Gazetteer (tracts) |
| County → CBSA delineation | Census/OMB delineation, July 2023 (2020 standards) |

All four share the 2020 census-tract/county boundary system, so the
tract→county→CBSA joins require no boundary crosswalk. This vintage is
**intentionally distinct** from the dissertation's boundary-consistent 2010 tract
baseline (see `docs/data_sources.md`); the two are never combined in one run, and
the schema's legacy `*_2010` column names carry the ACS 2019–2023 values under the
tract-derived run.

### Partial result, reported join losses

The pilot is explicitly **partial**: three states reach only the strata they
contain (nine of the national twenty in the recorded fixture), and the output
metadata sets `is_partial_result: true`. It is written to a separate directory
(`pipeline/pilot_out/`), never the national `pipeline/out/`. A `pilot_report.json`
records tract counts, per-class tract counts, the county/CBSA catchment counts,
and — critically — every **join loss** (a non-rural tract whose county has no
CBSA) and **unresolved classification** (a CBSA whose aggregate density falls
rural), so nothing is silently discarded.

Two sources share one contract: `--source api` pulls real Census tract data (ACS
5-year + Gazetteer + delineation), caching raw downloads under
`pipeline/cache/pilot/` with SHA-256 checksums and source dates; `--source
fixture` replays committed recorded fixtures with real geography identifiers and
clearly-labelled representative tract attributes so the method and tests run
offline and deterministically.

## Philadelphia Research Priority

The configured baseline preference targets Philadelphia-Camden-Wilmington,
PA-NJ-DE-MD in the Mixed-Humid HDU stratum because the project team has stronger
local heat-health data coverage there. The preference is applied only when that
exact candidate belongs to that exact stratum and passes eligibility. In the live
ACS 2019-2023 tract-derived run, Philadelphia classifies as Mixed-Humid LDU, so
the default preference is visibly inactive rather than forcing the CBSA into HDU.
Researchers can still submit explicit overrides, which fail loudly when invalid.

## ZIP Search

A ZIP code is only an entry point. The ZIP explorer:

1. validates a five-digit string and preserves leading zeros
2. displays the linked ZCTA, county, CBSA, state, climate region, and urbanicity context
3. reports any crosswalk uncertainty and one-to-many records
4. explains whether the target simulation catchment is CBSA-based or county-based
5. keeps the weather-station point separate

ZIP, ZCTA, Census place, county, CBSA, and station locations are not interchangeable.

## ResStock Filter Rules

Use exact, enumeration-verified NREL values:

```text
Non-rural: in.metropolitan_and_micropolitan_statistical_area
Rural:     in.county
```

Current NREL releases enumerate human-readable values (for example,
`PA, Philadelphia County` and
`Philadelphia-Camden-Wilmington, PA-NJ-DE-MD MSA`), while this analysis retains
FIPS/CBSA codes as target identifiers. The handoff resolves each code and Census
label to the exact NREL release label, records both values, and verifies the
resolved label against the release enumeration dictionary.

Do not substitute `in.city` for rural cases. That would discard the intended
rural-tract scope.

## Pre-Simulation Weather QC

Each weather station assigned to a selected catchment is checked for hourly temperature
and humidity (dew-point) completeness for the simulation year. A station-year is
`COMPLETE` when at least 90% of the 8,760 hours carry both a temperature and a humidity
observation, and `INCOMPLETE` otherwise — the conventional completeness bar for
assembling a representative weather year. The QC stage (`pipeline/weather_qc.py`) writes
a per-station `station_weather_qc.csv` recording expected hours, present hours, coverage
fraction, and status, replacing the earlier `PENDING` placeholder. The scenario builder
can require weather-QC completeness as an eligibility filter.

Fixture runs emit deterministic synthetic coverage clearly labeled `source=fixture`; the
real `--source api` path reads NOAA Integrated Surface Database global-hourly files and
requires network access. Distance, elevation, and coastal context remain reported
separately for interpretation.

The expected hour count is **leap-year aware** — 8,784 hours in a leap year, 8,760
otherwise — so the 90% bar is applied as a fraction of the correct denominator. Live
runs also emit a downloadable per-station error report (`station_weather_qc_errors.csv`)
listing any station-year whose ISD file could not be fetched or parsed, with the URL.

## Ancillary Data Integration (Session 3)

The live ancillary paths follow the dual-source contract used elsewhere and are
provenance-stamped. The ZIP crosswalk retains one-to-many ZIP→county records with
allocation ratios and keeps ZIP and ZCTA distinct (ZCTA is populated only from a
supplied ZIP→ZCTA relationship file, never copied from the ZIP). Map geometry uses
Douglas–Peucker simplification with full MultiPolygon support and Alaska antimeridian
handling, and every feature is geometry-validated. ResStock/ComStock filter values are
verified against the real public NREL data/enumeration dictionaries; unverified values
or labels stay `REVIEW REQUIRED`. See [docs/data_sources.md](data_sources.md) and the
[live data runbook](LIVE_DATA_RUNBOOK.md) for sources, env vars, and acceptance checks.

## June 2026 Live Run

The June 7, 2026 production run processed 84,080 ACS tracts into 3,095 rural
county catchments and 924 non-rural CBSA catchments (4,019 candidates total).
It resolved all 20 strata and selected 20 distinct catchments. The aggregation
reported 918 non-rural tracts in counties outside a CBSA as explicit join losses
and zero CBSAs with unresolved rural aggregate density; details are retained in
`pipeline/out/national_report.json`.
