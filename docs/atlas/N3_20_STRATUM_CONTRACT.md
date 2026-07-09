# N3 complete climate × urbanicity stratum contract

**Contract:** `atlas.strata/1.0`
**Endpoint:** `/api/v1/results/by-stratum?tier={annual|seasonal}&dimension=stratum`

## Stable lattice

The response covers five certified climate regions in source order:

1. Cold & Very Cold
2. Hot-Dry & Mixed Dry
3. Hot-Humid
4. Marine
5. Mixed-Humid

Each is crossed with `HDU`, `LDU`, `Rural`, and `Suburban`, producing exactly
20 strata. Every stratum contains scenario rows in canonical `A`, `C`, `B`,
`D` order. Stable IDs use
`{climate-slug}__{urbanicity-lowercase}`, for example
`hot-humid__suburban`.

## Response guarantees

- `stratum_count` is `20`.
- `group_column` is `stratum_id`.
- `group_columns` is `["climate_region", "urbanicity"]`.
- `strata` contains navigation metadata: stable ID, display label, climate,
  urbanicity, representative simulation location label, and per-scenario cell
  counts.
- `rows` contains 80 grouped metric records: one for every
  stratum × scenario combination.
- `scenario_order` is `["A", "C", "B", "D"]`.
- `certified_provenance` retains tier
  `replocx_tmy3_wallfix_4scen`, R9 `PASS`, `f2v3_final`, and read-only status.
- `source_csv` and `provenance_sidecar` identify the certified run-level table
  used by the server.

## Aggregation boundary

The server groups the certified annual or seasonal `run_level_metrics` rows by
`climate_region`, `urbanicity`, and `hvac_scenario`, then computes arithmetic
means for the same metric fields exposed by the existing certified
single-dimension aggregate tables. In the certified tier, every bucket contains
nine cells.

The frontend performs no analytical aggregation. It only chooses a server
dimension, filters already-returned rows for review, formats values, and links
the selected stratum to its representative site.

## Reviewer path and URL state

The landing flow is:

`climate → urbanicity → 20-stratum lattice → representative site`

The URL preserves `tier`, `scenario`, `dimension`, `climate`, `urbanicity`,
`stratum`, `metric`, and `threshold` where applicable. Links between Atlas
sections retain that query state, so a reviewer can share or revisit the same
slice without recomputation.

## Screenshot evidence

- `screenshots/2026-07-08-n3/atlas-n3-20-strata.png`: complete landing lattice
  with A/C/B/D columns and representative-site links.
- `screenshots/2026-07-08-n3/atlas-n3-urbanicity-pivot.png`: guided
  urbanicity-level step.
- `screenshots/2026-07-08-n3/atlas-n3-site-drill.png`: selected stratum to
  representative-site detail and drawer.
- `screenshots/2026-07-08-n3/atlas-n3-results-strata.png`: results surface
  using the 20-stratum contract.
