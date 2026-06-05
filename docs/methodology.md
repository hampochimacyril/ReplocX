# Methodology

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

## Research-Priority Overrides

No override is applied by default: every stratum keeps its top-ranked candidate. When a
research priority requires a specific catchment, a user can add a visible override for one
stratum (climate region + urbanicity + catchment code) in the Scenario builder. Any
override is labeled, editable, removable, reported with its score difference versus the
unconstrained top, and preserved in exported scenario JSON.

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

Do not substitute `in.city` for rural cases. That would discard the intended
rural-tract scope.

## Pre-Simulation Weather QC

Hourly temperature and humidity completeness, distance, elevation, and coastal context
must be reviewed before simulation. The current station workbook does not contain
hourly completeness metrics, so readiness remains explicitly pending.

