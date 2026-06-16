# UI Benchmark — Leading Geospatial / Building-Stock / Climate Tools

Session 5 deliverable. This document benchmarks six established public tools whose
domain (geographic energy / building-stock / climate / resilience analysis) overlaps
ReplocX, then distills patterns the redesign should adopt and anti-patterns it should
avoid. The companion specification is `docs/UI_REDESIGN_SPEC.md`.

## Method and confidence

- Compiled **2026-06-07** from each tool's official product pages, user guides, and
  documentation (links per row). This is a documentation- and screenshot-based review,
  not an automated UI crawl: several of these are heavy JavaScript map apps that do not
  render meaningfully through plain HTTP fetch, so behavioral claims are taken from
  vendor documentation and help material rather than live DOM inspection.
- Where a dimension is not documented publicly, it is marked _not documented_ rather
  than guessed. Treat low-confidence cells as "verify during Session 6/7 implementation"
  rather than settled fact.
- Goal per the Session 5 acceptance gate: tie the redesign to **observed domain
  patterns**, not generic dashboard trends, and ensure **every existing ReplocX
  capability has a home** in the new information architecture.

## Tools reviewed

| # | Tool | Owner | Primary purpose | Entry URL |
|---|------|-------|-----------------|-----------|
| A | ResStock Data Viewer | NREL | Explore residential building-stock characteristics + energy results | https://resstock.nrel.gov/ |
| B | SLOPE Data Viewer | DOE / NREL | Jurisdiction-resolved energy potential & projections for planning | https://maps.nrel.gov/slope/data-viewer |
| C | LEAD Tool | DOE / NREL | Low-income energy affordability/burden by geography | https://www.energy.gov/cmei/scep/low-income-energy-affordability-data-lead-tool |
| D | FEMA RAPT | FEMA (Esri/ArcGIS) | Combine resilience indicators + infrastructure + hazards on a map | https://www.fema.gov/emergency-managers/practitioners/resilience-analysis-and-planning-tool |
| E | Climate Explorer | NOAA / U.S. Climate Resilience Toolkit | County climate observations + projections, maps + graphs | https://toolkit.climate.gov/tool/climate-explorer |
| F | Data Commons Place Explorer | Google | Place-first statistical profiles with peer comparison & ranking | https://datacommons.org/place |

## Comparison matrix

### Information architecture

| Tool | First screen | Structure |
|------|--------------|-----------|
| A ResStock | Results/data-viewer entry, not a marketing wall | Pick geography (state) → filter housing segments → view stock + energy results. |
| B SLOPE | Map data viewer is the product | Layer-led: choose a data layer (consumption, generation, ResStock savings, etc.) then a geography level (state/county/city). |
| C LEAD | Map + criteria-filter workspace | Geography selector (state→county→tract→tribal/city) + criteria filters drive a choropleth and charts. |
| D RAPT | Full-screen ArcGIS map | Layer groups behind top "blue icon" buttons (Infrastructure, Hazards, Community Resilience Indicators…). Map is the entire app. |
| E Climate Explorer | Map + graph, county-centric | Search/select a county → switch among map and chart views with time/threshold controls. |
| F Place Explorer | Search box → place profile | Place-first: one place yields an auto-assembled, sectioned scrollytelling of charts with peer comparisons + rankings. |

**Lesson:** every comparable tool makes the *analysis surface* (map or place profile) the
first screen. None opens on a marketing page or a grid of ornamental KPI cards. The
strongest map tools (B, D) treat the map as the whole app with controls layered over it.

### Map behavior

| Tool | Notes |
|------|-------|
| A | Geographic results presented by state/region; segment filtering rather than free-pan GIS. |
| B | Full interactive map; one thematic layer at a time; legend tied to the active layer; state/county/city resolution. |
| C | Interactive choropleth heat-map; range sliders recolor the map live; multi-geography (tract→state, tribal). |
| D | Mature GIS: 100+ layers, basemap switching (navigation/satellite/streets/topo/terrain), feature pop-ups, layer grouping. Reference standard for map depth. |
| E | Map with a draggable **swipe line** comparing historical vs projected, or two emission scenarios, side-by-side on one map. |
| F | Map is secondary; small choropleths embedded inside the place profile rather than a dominant canvas. |

**Lesson:** adopt RAPT/SLOPE map discipline — one primary thematic layer at a time, a
legend bound to that layer, toggleable secondary layers (candidates, stations,
station-distance links), basemap choice, and feature pop-ups/selection. Climate
Explorer's swipe is a strong model for ReplocX scenario-vs-baseline comparison on the map.

### Place / geography search

| Tool | Notes |
|------|-------|
| A | Geography chosen from controls (state-led), not free-text first. |
| B | Geography level selection within the viewer. |
| C | Hierarchical geography selection (state → county → tract, plus tribal/city). |
| D | ArcGIS search/zoom to place; selection via map. |
| E | County search/selection is the entry action. |
| F | **Strongest:** prominent free-text search accepting city, ZIP, county, state, or country — the front door to everything. |

**Lesson:** ReplocX must search **ZIP, catchment name/code, and weather station** without
conflating their geographic meanings (a current strength to preserve). Place Explorer's
single prominent search is the model; the result must disambiguate type (ZIP ≠ ZCTA ≠
county ≠ CBSA ≠ station).

### Persistent filters / scenarios

| Tool | Notes |
|------|-------|
| A | Persistent segment filters (vintage, heating fuel, wall type, etc.) that re-slice results. |
| B | Layer + scenario selection (e.g., future renewable-generation scenarios) persisted in the view; shareable via URL params. |
| C | Persistent **criteria filters** with range **sliders** (e.g., energy-burden range) recoloring the map. |
| D | Persistent layer on/off state and grouping; no scenario modeling. |
| E | Persistent timeframe / emissions-scenario / threshold controls. |
| F | Lightweight; comparison-place selection persists within a profile. |

**Lesson:** LEAD's slider-driven criteria filters and SLOPE's URL-encoded scenario state
are the right references for ReplocX's persistent stratum/scenario panel (climate,
urbanicity, selected status, verification, weather-QC, score range, station-distance, plus
weights/density screen). Encode scenario state in the URL so views are shareable and
reproducible.

### Comparison

| Tool | Notes |
|------|-------|
| A | Compare segments within a geography. |
| B | Compare scenarios/projections over time. |
| C | Compare across geographies and download comparative outputs. |
| D | Visual comparison by overlaying layers. |
| E | **Two-scenario side-by-side** via the map swipe; historical vs projected. |
| F | **Place-vs-peers** comparison and cross-place **rankings** are core. |

**Lesson:** combine Climate Explorer's side-by-side (baseline allocation vs edited
scenario) with Place Explorer's ranked comparison (candidate ranking + side-by-side
candidate/allocation deltas). Deltas should be quantified, not decorative.

### Charts / coordinated views

| Tool | Notes |
|------|-------|
| A | Stock + energy charts beside the segment filters. |
| B | Layer-specific charts/values per geography. |
| C | Custom charts + heat-maps generated from the same filter state. |
| D | Pop-up detail panels per feature; chart depth secondary to the map. |
| E | Map **and** time-series graphs as co-equal views of the same county/variable. |
| F | Dense, sectioned chart catalog auto-generated per place; the chart grid *is* the page. |

**Lesson:** charts must be **coordinated** with map + filters (score distribution,
station-distance distribution that filter with the map), echoing Climate Explorer's
map↔graph coupling — not a detached "charts page."

### Methodology / provenance

| Tool | Notes |
|------|-------|
| A | Documentation, FAQ, and dataset lineage published alongside the viewer. |
| B | About page documents sources, scenarios, and methodology. |
| C | ACS-based methodology and FAQ documented; vintage stated. |
| D | User guide details indicators, sources, and peer-reviewed basis of the CRCI. |
| E | Documents CMIP5 / LOCA downscaling provenance explicitly. |
| F | Each statistic is traceable to a source dataset (open-source graph). |

**Lesson:** ReplocX already exposes source versions, crosswalk uncertainty, weather-QC
status, and ResStock verification — a genuine differentiator. Make provenance **visible
in-context** (badges/notes on the data being viewed), not only on a separate methodology
page, in the spirit of Climate Explorer stating its downscaling method and Data Commons
making each stat traceable.

### Export

| Tool | Notes |
|------|-------|
| A | Underlying datasets downloadable (open-data lake). |
| B | Layer data exportable; deep-linkable views. |
| C | **Strong:** download customized heat-maps and charts plus data for any geography. |
| D | Layer/data export via the ArcGIS app. |
| E | Download button with selectable data format. |
| F | Data exportable; programmatic API access. |

**Lesson:** preserve and surface ReplocX's existing exports (site-list CSV,
ResStock-sampling CSV, OpenStudio manifest JSON, scenario JSON, ranking CSV, and
map/image) with explicit filenames and error states — already broader than several of
these tools.

### Responsive behavior

| Tool | Notes |
|------|-------|
| A | Desktop-oriented analytical viewer. |
| B | Desktop-first map app. |
| C | Desktop-first; usable on tablets. |
| D | ArcGIS viewer is desktop-first; dense controls degrade on small screens. |
| E | Reasonably adaptive maps/graphs. |
| F | **Best responsive behavior:** profile flows into a single scroll column on mobile. |

**Lesson:** these are overwhelmingly desktop-first; small-screen behavior is their common
weakness. ReplocX should explicitly design tablet/mobile adaptations (map collapses to a
secondary tab; filters become a sheet; profile/details stack), taking the Place Explorer
column-reflow as the model.

### Accessibility

| Tool | Notes |
|------|-------|
| A–E | Accessibility not prominently documented; choropleth-heavy tools risk color-only encoding and weak keyboard support — _verify, do not assume._ |
| F | Standard web semantics; text/table fallbacks for chart data aid screen readers. |

**Lesson:** treat a11y as a **differentiator**: WCAG 2.1 AA contrast, non-color-only map
encodings (patterns/labels/legends), full keyboard operation, visible focus, reduced
motion, screen-reader labels, and table fallbacks for every chart.

## Per-tool weaknesses to avoid

- **A ResStock Data Viewer:** geography entry is control-led rather than search-first;
  comparison across geographies is limited.
- **B SLOPE:** layer-first framing can bury "what's the answer for *my* place"; legend +
  units must stay obvious as layers change.
- **C LEAD:** powerful filters can overwhelm; criteria controls need clear grouping,
  labels, and reset.
- **D FEMA RAPT:** classic Esri viewer — heavy, dense, slow on large layer counts, and
  poor on small screens; layer discovery via icon groups has a learning curve.
- **E Climate Explorer:** narrow scope (climate variables only); limited multi-entity
  comparison beyond the two-scenario swipe.
- **F Data Commons Place Explorer:** map is an afterthought; weak for a workflow whose
  core object is a selected geographic catchment on a map.

## Synthesis — patterns ReplocX should adopt

1. **Analysis-first landing.** Open directly on the map workspace (RAPT/SLOPE), never a
   marketing page or ornamental KPI grid.
2. **Map-dominant, one thematic layer at a time**, with a legend bound to it and
   toggleable secondary layers, basemaps, and feature selection (RAPT depth).
3. **Prominent, type-aware search** as the front door (Place Explorer), disambiguating
   ZIP/ZCTA/county/CBSA/station.
4. **Persistent, slider-driven filter/scenario panel** with URL-encoded, shareable state
   (LEAD + SLOPE).
5. **Coordinated map ↔ charts ↔ table**, all reacting to the same filter state (Climate
   Explorer coupling).
6. **Side-by-side + ranked comparison** with quantified deltas (Climate Explorer swipe +
   Place Explorer rankings).
7. **In-context provenance and data-quality** badges (Climate Explorer's stated method;
   Data Commons traceability) — ReplocX's strongest differentiator.
8. **First-class export** with clear filenames/formats (LEAD), preserving ReplocX's
   broader export set.
9. **Deliberate responsive + accessibility design**, the shared weakness of this cohort,
   turned into a ReplocX advantage.

## Sources

- ResStock: [resstock.nrel.gov](https://resstock.nrel.gov/), [ResStock Data Visualization Tools (NREL/88924)](https://docs.nrel.gov/docs/fy24osti/88924.pdf), [ResStock Analysis Tool](https://www.nrel.gov/buildings/resstock), [End-Use Load Profiles open data](https://registry.opendata.aws/nrel-pds-building-stock/)
- SLOPE: [SLOPE Data Viewer](https://maps.nrel.gov/slope/data-viewer), [About SLOPE](https://maps.nrel.gov/slope/about), [SLOPE Platform (research hub)](https://research-hub.nrel.gov/en/publications/state-and-local-planning-for-energy-slope-platform), [SLOPE Platform (NREL/78801)](https://docs.nrel.gov/docs/fy21osti/78801.pdf)
- LEAD: [DOE LEAD Tool](https://www.energy.gov/cmei/scep/low-income-energy-affordability-data-lead-tool), [LEAD FAQ](https://www.energy.gov/scep/slsc/low-income-energy-affordability-data-lead-tool-frequently-asked-questions), [Census ACS data story: LEAD](https://www.census.gov/programs-surveys/acs/about/acs-data-stories/lead-tool.html)
- FEMA RAPT: [RAPT overview](https://www.fema.gov/emergency-managers/practitioners/resilience-analysis-and-planning-tool), [RAPT User Guide (May 2025)](https://www.fema.gov/sites/default/files/documents/fema_rapt-user-guide_2025.pdf), [RAPT web app](https://fema.maps.arcgis.com/apps/webappviewer/index.html?id=90c0c996a5e242a79345cdbc5f758fc6), [Esri on RAPT](https://www.esri.com/en-us/industries/blog/articles/femas-resilience-analysis-and-planning-tool-supports-all-phases-of-emergency-management)
- Climate Explorer: [Climate Explorer (toolkit.climate.gov)](https://toolkit.climate.gov/tool/climate-explorer), [Climate Explorer v3.0 announcement](https://toolkit.climate.gov/news/new-and-improved-%E2%80%94-climate-explorer-version-30-now-available), [NOAA story](https://www.noaa.gov/stories/climate-change-in-your-county-plan-with-new-tool)
- Data Commons: [Place Explorer](https://datacommons.org/place), [What is Data Commons](https://docs.datacommons.org/what_is.html), [Explore](https://datacommons.org/explore)
