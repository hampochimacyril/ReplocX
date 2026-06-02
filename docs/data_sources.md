# Data Sources

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

## Limitations

- The boundary-consistent baseline uses 2010 tract definitions and counts.
- A current ACS sensitivity run requires a documented tract-boundary crosswalk.
- The station workbook does not contain hourly weather completeness metrics.
- Candidate rows outside the curated baseline ResStock handoff remain marked
  `REVIEW REQUIRED` until their exact enumeration values are verified.

