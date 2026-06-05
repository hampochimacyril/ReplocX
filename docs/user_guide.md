# User Guide

## Overview Dashboard

Use the overview to confirm the 20 target strata, distinct represented catchments,
verified ResStock values, weather-QC status, map context, score distribution, and
research-priority override.

## ZIP Code Explorer

Enter a five-digit ZIP code. The app preserves leading zeros and shows the resolved
ZCTA, county, CBSA, climate region, urbanicity context, uncertainty notes, analytical
catchment, score components, selected stratum representative, and nearby weather
stations.

The bundled crosswalk is a demonstration subset. Try `19104`, `02108`, `10001`,
`33130`, `90012`, `95501`, or rural `98290`.

## Scenario Builder

Adjust the density screen, weights, unique-location rule, maximum station distance,
station-distance penalty, weather-QC requirement, and an optional research-priority
override (off by default). The
live preview reports represented catchments, eligible candidates, combined score,
mapping cautions, and changed assignments.

Export scenario JSON to retain the exact configuration. Export site-list CSV for a
simulation handoff review.

## Candidate Ranking

Filter by catchment, station, climate region, urbanicity, selected status, or verified
status. Sort table columns by clicking headings. Select up to two rows for side-by-side
comparison. Export the filtered ranking table as CSV.

## Allocation Comparison

Compare independent top-ranked selections against the active scenario. The page shows
coverage differences, score differences, substitutions, a map, and reasons for every
changed assignment.

## Methodology and Sources

Use the final page as an academic methods appendix. It documents boundary rules,
crosswalk limitations, ResStock fields, source versions, and the separate hourly
weather-completeness QC requirement.

