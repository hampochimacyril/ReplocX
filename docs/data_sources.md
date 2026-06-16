# ReplocX Data Sources

## Existing Analytical Outputs

The explorer consumes regenerated outputs from
`04_Analysis/location_selection/data/processed/` as read-only inputs. Run:

```bash
python3 scripts/refresh_data.py
```

to fingerprint the current files after the upstream analytical pipeline is regenerated.

## Baseline Source Versions

| Source | Role | Version or file |
| --- | --- | --- |
| ISH contiguous-US station workbook | Candidate weather-station pool and climate-region assignment | `ISH2023_USAcontUSclimateurbanicitycbsa.xlsx` |
| LEAD tract classification | Four-category target-community urbanicity classification | [Mendeley dataset version 1](https://data.mendeley.com/datasets/332sc27css/1) |
| Census Tract Gazetteer | 2010 population, housing units, land area, and internal points | [Census Gazetteer archive](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/Gaz_tracts_national.zip) |
| Historical CBSA delineation | Boundary-consistent county composition and CBSA labels | [December 2009 delineation](https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2009/historical-delineation-files/list1.txt) |
| NREL ResStock enumeration dictionary | Exact simulation filter verification | `data/raw/nrel_resstock_2025/enumeration_dictionary.tsv` |

## Tract-Level Pilot Sources and Vintage (Session 2)

The tract-level pilot (`pipeline/pilot.py`, states PA/AZ/MN) and the live
national `pipeline.run --source api` path are built on a single, internally
consistent **2020-boundary** vintage. These are the authoritative live sources
their `--source api` paths use (verified June 2026):

| Source | Role | Version / URL |
| --- | --- | --- |
| Census ACS 5-year (tract) | Tract population (`B01003_001E`) and housing units (`B25001_001E`) | ACS 2019–2023 5-year, `api.census.gov/data/2023/acs/acs5` |
| Census Gazetteer (tracts) | Tract land area (`ALAND_SQMI`) and interior point (`INTPTLAT`/`INTPTLONG`) | [2023 Gazetteer tracts](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_tracts_national.zip) |
| Census/OMB CBSA delineation | County → CBSA membership (metro/micro) | [July 2023 delineation `list1_2023.xlsx`](https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx) |
| NOAA ISD 2023 stations | Nearest-station assignment per catchment | `pipeline/data/ish2023_stations.csv` |
| DOE Building America / IECC | Climate-region assignment from primary county | `pipeline/climate.py` |

Vintage reconciliation: this 2020 stack is **intentionally different** from the
boundary-consistent **2010** baseline above (2010 Gazetteer tracts + December 2009
historical delineation + LEAD tract urbanicity). The tract-derived live paths
never mix the two — all four inputs share the 2020 census-tract/county boundary
system, so tract→county→CBSA joins need no crosswalk. Urbanicity uses the
reproducible density-band classification (`pipeline/config.URBANICITY_DENSITY_BREAKS`);
substituting the LEAD tract classification (the 2010-baseline source) is a
documented future option that would require matching the LEAD vintage.

Offline fixtures live in `pipeline/data/pilot/` (`tracts_<state>.csv` and
`cbsa_delineation.csv`). They carry **real** geography identifiers (state/county
FIPS, CBSA codes, and the real July-2023 county→CBSA memberships) with
**representative, clearly-labelled** tract attributes — not measured ACS/Gazetteer
values. Run `--source api` on a networked machine for measured values; raw
downloads cache under `pipeline/cache/pilot/` with SHA-256 checksums and source
dates.

The live tract pilot and national run were executed on June 7, 2026. State ACS
responses and the national Gazetteer archive are cached with SHA-256 records
under `pipeline/cache/pilot/`; the national manifest is in
`pipeline/out/national_report.json`.

## ZIP Crosswalk

`data/zip_crosswalk_demo.csv` contains a small, curated demonstration subset with a
HUD-USPS-compatible schema. It is deliberately labeled as a subset in the user
interface. Before national ZIP search:

1. obtain a documented quarterly HUD-USPS ZIP-to-geography crosswalk
2. preserve ZIP, ZCTA, county, and CBSA identifiers as strings
3. retain one-to-many records and allocation ratios
4. record the source date and refresh procedure
5. test leading-zero ZIPs such as `02108`

ZIP delivery areas and Census ZCTAs are related but not interchangeable.

## Live Ancillary Data (Session 3)

The real `--source api` ancillary paths are implemented, provenance-stamped, and
unit-tested offline against recorded real-schema fixtures
(`tests/fixtures/ancillary/`). Run them with [docs/LIVE_DATA_RUNBOOK.md](LIVE_DATA_RUNBOOK.md).

- **HUD-USPS ZIP crosswalk** (`pipeline/fetch_hud_crosswalk.py`): ZIP-COUNTY rows
  are retained **one-to-many** with residential allocation ratios; each ZIP's
  primary CBSA comes from ZIP-CBSA. HUD supplies no ZCTA, so **ZCTA is never set
  equal to the ZIP** — it is populated only from a `RLE_ZIP_ZCTA_FILE` relationship
  file, else left blank with an explicit note. A `zip_crosswalk_provenance.json`
  sidecar records quarter, row/ZIP counts, one-to-many count, and ZCTA status.
- **TIGER/Line geometry** (`pipeline/geometry.py`): Douglas–Peucker simplification
  (topology-safe for independently rendered features) under a per-ring vertex cap;
  full **MultiPolygon** support (islands/detached parts kept); **Alaska**
  antimeridian normalisation; per-feature **geometry validation** recorded in the
  feature properties and the collection metadata.
- **NOAA ISD weather QC** (`pipeline/weather_qc.py`): temperature + dew-point
  hourly completeness vs the year's expected hours, **leap-year aware** (8,784 vs
  8,760), with a downloadable per-station **error report**
  (`station_weather_qc_errors.csv`).
- **ResStock/ComStock enumeration** (`pipeline/resstock_dictionary.py`): parses the
  public NREL `data_dictionary.tsv` and `enumeration_dictionary.tsv` directly
  (plus legacy CSV/JSON) via `RESSTOCK_ENUMERATION_FILE`, removing the hand-curated
  reformat. Current NREL releases enumerate geography labels rather than FIPS/CBSA
  codes, so the pipeline resolves each analytical code/name pair to the exact
  NREL label before verification. Absent labels stay `REVIEW REQUIRED`; the
  loaded dictionary's SHA-256 is recorded in provenance.

### June 7, 2026 live execution

- HUD-USPS Q1 2025: 54,242 ZIP-county rows, 39,299 distinct ZIPs, and 11,303
  one-to-many ZIPs; ZCTA values came from the supplied ZIP-to-ZCTA relationship.
- NREL ResStock 2025 AMY2018 release 1 enumeration dictionary:
  SHA-256 `a60a0d216a309945f4451bca006d1490e8442fb1de7e7729842697a982677f7a`;
  20 of 20 national filter values verified.
- NOAA ISD 2023: 19 of 20 selected station-years met the 90% completeness bar;
  one was `INCOMPLETE`, none were `PENDING`, and no fetch/parse errors remained.
- TIGERweb: 20 of 20 selected catchments returned real geometry with zero fetch
  errors and zero geometry-validation issues.
- National ACS tract run: 84,080 tracts, 4,019 candidates, 20 resolved strata,
  and 20 distinct selections.

## Limitations

- The boundary-consistent baseline uses 2010 tract definitions and counts.
- A current ACS sensitivity run requires a documented tract-boundary crosswalk.
- Hourly weather completeness is now computed per station-year by the weather-QC stage
  (`station_weather_qc.csv`, `COMPLETE`/`INCOMPLETE` at a 90% threshold). The real
  `--source api` path requires the NOAA ISD global-hourly record; fixture coverage is
  synthetic and labeled as such.
- The live national aggregation reports 918 non-rural tracts in non-core
  counties as join losses rather than silently assigning them to a CBSA.
- The prior dissertation output files are not stored in this repository, so a
  row-for-row numerical comparison was not possible here. The documented
  analytical differences are the ACS 2019-2023 vintage, 2020 tract boundaries,
  July 2023 CBSA delineation, density-band urbanicity, and current scoring.
