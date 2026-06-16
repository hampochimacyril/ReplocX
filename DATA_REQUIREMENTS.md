# Data ReplocX requires — and free sources for all of it

Short version: **no paid or proprietary data is needed.** The files currently called
"private" are just *your own computed analytical outputs*. Everything needed to regenerate
them nationally is **free** from U.S. government and NREL/DOE sources.

## 1. The "private" files = your computed outputs (not secret, not paid)
The app reads these from `location_selection/data/processed/` (your upstream PhD pipeline):

| File | What it is |
|---|---|
| `candidate_scores.csv` | Every candidate catchment: climate region, urbanicity, geography codes (county/CBSA), 2010/2020 population & housing counts and densities, the three percentiles, `location_score`, selected weather station + distance, centroid lat/lon. (~2,959 rows nationally.) |
| `selected_locations.csv` | The 20 chosen catchments. |
| `resstock_site_list.csv` | The ResStock filter field/value per selected location + verification + weather-QC status. |
| `stratum_status.csv` | Per-stratum status/counts. |
| `selection_metadata.json` | Method version, boundary system, sources, limitations. |

These are "private" only because they are your results and are not committed to the public
repo. The app can either (a) read your real outputs, or (b) **recompute them from free
public data** (recommended — removes the dependency entirely).

## 2. Free public source data to regenerate everything
All free; all U.S. government or NREL/DOE. (Verify exact current URLs at build time.)

| Need | Free source |
|---|---|
| Tract population & housing (counts, density) | **U.S. Census** — 2020 Decennial + ACS via the Census API / data.census.gov |
| Geographies (tracts, counties, CBSAs, places) + polygons for maps | **Census TIGER/Line** shapefiles; **TIGERweb** |
| CBSA (metro/micro) delineations | **OMB / Census** delineation files |
| Climate-region classification | **IECC / DOE Building America** climate zones (PNNL/NREL) |
| Urbanicity (urban/rural / density classes) | **Census** urban–rural classification (or density-based scheme) |
| ZIP → ZCTA/county/CBSA crosswalk (with allocation ratios) | **HUD–USPS ZIP Crosswalk** (huduser.gov), updated quarterly |
| Weather stations + hourly temp/humidity completeness (QC) | **NOAA Integrated Surface Database (ISD)**; **NREL NSRDB / TMY3** |
| Exact ResStock filter enumerations (`in.county`, `in.metropolitan_and_micropolitan_statistical_area`) | **NREL ResStock/ComStock** public data dictionary / OEDI |

## 3. What this means for finishing the project
- The whole thing can be completed with **free resources** — Census, HUD, NOAA, NREL/DOE.
- A sponsor is **not required for data**; it would mainly buy time, compute for large
  downloads, and (separately) academic peer review of the method.
- The cleanest production path is to build a small **`pipeline/`** that downloads these
  free sources and regenerates `candidate_scores.csv` & friends, so the app stops needing
  any hand-supplied "private" file.

## 4. The only things a sponsor / you (not data) are needed for
- **Domain peer review** of the methodology for publication defensibility.
- **Funding/time** if the national downloads/compute become heavy, or for a paid private
  host (the current free Render demo is enough for the public demo).
- **Data-use citation/attribution** housekeeping (the sources above are open; just cite them).
