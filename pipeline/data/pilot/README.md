# Tract-level pilot fixtures (recorded, offline)

These files are the offline (`--source fixture`) inputs for the tract-level pilot
(`pipeline/pilot.py`), covering three states that span distinct climate and
urbanicity conditions: Pennsylvania (Mixed-Humid), Arizona (Hot-Dry & Mixed Dry),
and Minnesota (Cold & Very Cold).

| File | Rows are | Columns |
| --- | --- | --- |
| `tracts_42.csv`, `tracts_04.csv`, `tracts_27.csv` | one census tract each | `tract_geoid, state_fips, county_geoid, county_name, population, housing_units, land_area_sqmi, intpt_lat, intpt_lon` |
| `cbsa_delineation.csv` | one county→CBSA membership | `county_geoid, county_name, cbsa_code, cbsa_name, cbsa_type` |

## What is real vs. representative

- **Real:** every geography identifier — state/county FIPS, 11-digit tract GEOID
  structure, and the CBSA codes and county→CBSA memberships, which match the
  July 2023 Census/OMB delineation (2020 standards). Counties absent from
  `cbsa_delineation.csv` are Non-core (no CBSA), which is correct for the rural
  counties included here.
- **Representative (not measured):** the per-tract `population`, `housing_units`,
  and `land_area_sqmi`. They are clearly-labelled structural stand-ins, tuned so
  the tract→county→CBSA method reaches a useful spread of climate × urbanicity
  strata and exercises the join-loss reporting. They are **not** measured ACS or
  Gazetteer values. Run `pipeline.pilot --source api` on a networked machine for
  measured values.

This mirrors the project's existing `--source fixture` stance: a deterministic,
reproducible structural stand-in, not a research result.

## Regenerate

The fixtures are produced deterministically (identical bytes every run) by:

```bash
python3 pipeline/data/pilot/_generate_fixtures.py
```

See `docs/methodology.md` and `docs/data_sources.md` for the analytical vintage
and source citations.
