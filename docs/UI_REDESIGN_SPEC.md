# ReplocX UI Redesign Specification

Session 5 deliverable and the contract for Sessions 6–8. It is grounded in the observed
domain patterns documented in `docs/UI_BENCHMARK.md`, not generic dashboard trends. The
companion artifact is the interactive prototype at `prototype/redesign_prototype.html`.

The goal: replace the functional-but-generic vanilla v1.2 UI with a **credible scientific
instrument** — map-dominant, geographically explicit, fast to scan, and careful about
uncertainty. The next session must be able to implement from this document without
inventing layout decisions ad hoc.

---

## 1. Primary users and their top jobs

| User | Context | Top jobs (what they come to do) |
|------|---------|---------------------------------|
| **Building-stock / heat-health researcher** (primary) | Selecting representative U.S. locations for national simulations | 1) Confirm the 20 strata are covered by credible representatives. 2) Inspect any catchment's score components, weather QC, and ResStock verification. 3) Adjust the scenario (weights, density screen, station-distance, weather-QC requirement, uniqueness, PA preference) and see what reassigns. 4) Export a defensible site list + OpenStudio/ResStock handoff. 5) Cite provenance and limitations. |
| **Simulation engineer / collaborator** | Consumes the selection for an OpenStudio/ResStock run | 1) Pull the current site list and OpenStudio manifest. 2) Verify each location's ResStock enumeration status and weather completeness. 3) Reproduce the exact scenario from saved JSON. |
| **Reviewer / committee / stakeholder** | Evaluating methodological credibility | 1) Understand the method, vintage, and boundary rules. 2) See where data is uncertain (crosswalk one-to-many, ZIP≠ZCTA, weather QC, REVIEW REQUIRED codes). 3) Compare baseline vs an edited scenario. |
| **ZIP-curious analyst** | Has a specific place in mind | 1) Type a ZIP/place and learn its catchment, stratum representative, score, and nearby stations, with crosswalk caveats. |

Design priority order: **researcher first**, engineer and reviewer second, ZIP-curious
analyst served by the same surfaces.

---

## 2. Information architecture

The application is **one workspace, not a deck of pages**. A compact left navigation rail
switches the *primary working context*; the map, filter panel, and details drawer persist
across contexts where meaningful.

### 2.1 Primary contexts (nav rail)

1. **Map workspace** (default landing) — the map-first analysis surface. Map + persistent
   filter/scenario panel + stratum coverage matrix + selection details drawer + coordinated
   charts.
2. **Catchments** (ranking/table) — the full candidate ranking as a dense table, sharing
   the same filter state as the map; selection here highlights on the map.
3. **Compare** — baseline allocation vs active scenario, side-by-side with quantified
   deltas and a synchronized map (the "swipe"/diff view).
4. **Scenario** — the scenario workbench (weights, density screen, station/weather/
   uniqueness/PA controls), with live preview and save/version/share.
5. **Methodology & data** — method, vintage, boundary rules, source citations, crosswalk
   and ZIP/ZCTA limitations, weather-QC definition, ResStock verification, API/export docs.

A persistent **top bar** holds: product mark, the global **type-aware search** (ZIP /
catchment name or code / station), the **data-mode badge** (`DEMO` vs `PRODUCTION`), the
active-scenario chip (name + dirty/saved state), and global actions (export menu, refresh,
help).

### 2.2 Capability → home mapping (no capability is orphaned)

This table satisfies the Session 5 gate that *every existing product capability has a
defined home in the new IA*. Left column = today's v1.2 capability (and its API).

| Current capability (v1.2) | Backing API | New home |
|---------------------------|-------------|----------|
| Overview: 20-strata confirmation, distinct catchments, verified ResStock, weather-QC status, score distribution, research-priority (PA) override | `GET /api/dashboard` | **Map workspace** — stratum coverage matrix + KPI strip (compact, not ornamental) + coordinated score distribution chart; PA override lives in the Scenario panel. |
| Map context / selected catchment polygons | `GET /api/geometry` | **Map workspace** — dominant map canvas with selected + candidate layers, stations, station-distance links. |
| ZIP Code Explorer: ZCTA/county/CBSA/climate/urbanicity, uncertainty notes, catchment, score components, stratum representative, nearby stations | dashboard + geometry (+ crosswalk) | **Map workspace search + details drawer** — ZIP/place inspection opens the details drawer with a dedicated ZIP/ZCTA section separated from catchment/station sections. |
| Scenario Builder: density screen, weights, uniqueness rule, max station distance, station-distance penalty, weather-QC requirement, PA preference; live preview; mapping cautions; changed assignments | `POST /api/scenarios/evaluate`, `POST /api/scenarios`, `GET /api/scenarios` | **Scenario** context (workbench drawer) with live preview; changed assignments also visualize in **Compare**. |
| Candidate Ranking: filter (catchment/station/climate/urbanicity/selected/verified), sort, select up to 2, CSV export | `GET /api/candidates` | **Catchments** table (TanStack Table) sharing the global filter state; comparison selection feeds **Compare**. |
| Allocation Comparison: coverage diffs, score diffs, substitutions, map, reasons | evaluate vs baseline | **Compare** context. |
| Methodology & Sources: boundary rules, crosswalk limits, ResStock fields, source versions, weather QC | `GET /api/provenance` | **Methodology & data** context, **plus** in-context provenance badges throughout. |
| Exports: site-list CSV, ResStock-sampling CSV, OpenStudio manifest JSON, scenario JSON, ranking CSV, map/image | `GET /api/exports/*` + client | Global **Export menu** (top bar) + contextual export buttons (table → ranking CSV; scenario → scenario JSON; map → image). |
| Data mode / health / degraded state | `GET /api/health` | **Data-mode badge** (top bar) + global empty/error/degraded states. |
| OpenAPI / API docs | `GET /api/openapi.json`, `/api/docs` | Linked from **Methodology & data**. |

---

## 3. Desktop layout (map-dominant)

Target reference width 1440px; designed fluid from 1024px up.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ TOP BAR  ReplocX │ ⌕ search (ZIP / catchment / station)   │ [PRODUCTION] scenario:Baseline·saved │ Export ▾  ⟳  ? │
├──┬───────────────────────────────────────────────────────────────┬───────────┤
│  │ FILTER / SCENARIO PANEL (persistent, ~320px, collapsible)      │           │
│N │  Climate ▾  Urbanicity ▾  Selected ▾  Verification ▾           │  DETAILS  │
│A │  Weather QC ▾   Score [▭▭▭▭▭—] range   Station dist [—▭▭] mi    │  DRAWER   │
│V │  ── Scenario ───────────────────────────────                   │  (opens   │
│  │  Weights: HU .45 / Dens .35 / Pop .20  (Σ=1.00)                 │  on map   │
│R │  Density screen ▾   Max station dist [__] mi                    │  or table │
│A │  ☑ Unique   ☑ Require weather QC   ☐ Prefer PA                  │  select)  │
│I │  [ Preview ]  [ Save ▾ ]                                        │           │
│L │                                                                │  ZIP/ZCTA │
│  │                  ┌──────────────────────────────┐              │  Catchment│
│  │                  │                              │              │  Station  │
│  │   M A P          │      DOMINANT MAP CANVAS     │              │  ResStock │
│  │  (primary)       │  selected polygons · cands · │              │  Score    │
│  │                  │  stations · distance links   │              │  Quality  │
│  │   legend ◣       │                              │              │  Provenance│
│  │   layers ▤       └──────────────────────────────┘              │           │
│  │                                                                │           │
│  ├───────────────────────────────────────────────────────────────┤           │
│  │ COVERAGE MATRIX 5×4   │  SCORE DIST ▮▮▮▯  │  STATION-DIST ▮▮▯   │           │
└──┴───────────────────────────────────────────────────────────────┴───────────┘
```

- **Navigation rail (left, ~56px):** icon-only with tooltips; the five primary contexts +
  methodology. Lucide icons only. Active state is a left accent bar + filled icon, not a
  pill.
- **Filter/scenario panel (left-inner, ~320px, collapsible):** persistent across Map,
  Catchments, and Compare. Filters on top; scenario controls below a divider. Slider-driven
  ranges (score, station distance) per the LEAD pattern. State is URL-encoded and
  shareable.
- **Map canvas (center, dominant):** fills remaining space. Floating, low-elevation
  controls: zoom, basemap switch, layer toggles, legend, zoom-to-selection, attribution
  (required). One thematic layer at a time; candidates/stations/links are toggleable
  overlays.
- **Coordinated bottom strip:** the 5×4 stratum coverage matrix + score distribution +
  station-distance distribution. All filter with the map and table; clicking a matrix cell
  selects that stratum's representative.
- **Details drawer (right, ~360px, overlay):** opens on selection (map feature, table row,
  search result, or matrix cell). Clearly separated sections — **ZIP/ZCTA**, **Catchment**,
  **Weather station**, **ResStock filter**, **Score components**, **Data quality**,
  **Provenance** — so geographic types are never conflated. Closes back to full map.

Context differences:
- **Catchments** replaces the map+matrix center with the full ranking table (map can dock
  to a right split or collapse to a toggle); filter panel persists.
- **Compare** shows two synchronized panels (baseline vs scenario) with a map diff and a
  deltas table.
- **Scenario** focuses the scenario workbench (can expand the left panel to a center
  workbench) with live preview metrics.
- **Methodology & data** is a readable single-column document context (full width, no map).

---

## 4. Mobile / tablet adaptation

- **Tablet (≥768px):** nav rail persists; filter/scenario panel becomes a collapsible
  left sheet (closed by default, toggled by a "Filters" button); map stays dominant;
  details drawer becomes a bottom sheet.
- **Mobile (<768px):** nav rail becomes a bottom tab bar (Map / Catchments / Compare /
  Scenario / More). The default view is the **map** with a compact filter button and a
  search field pinned to the top. Filters and scenario open as full-height bottom sheets.
  Selection opens a bottom sheet that expands to full screen; sections stack in the
  Place-Explorer column-reflow style. The coverage matrix scrolls horizontally or stacks
  to a 4-row list. Tables switch to a stacked card/row list with the key columns.
- Touch targets ≥44×44px. No hover-only affordances; every hover has a tap/focus
  equivalent.

---

## 5. Visual system (design tokens)

The aesthetic is **restrained analytical**: square/low-radius surfaces, hairline borders,
minimal elevation, dense but readable type, semantic color used sparingly and never as the
only signal.

### 5.1 Color (semantic, light theme primary; dark theme defined)

| Token | Light | Role |
|-------|-------|------|
| `--bg` | `#FFFFFF` | App background |
| `--surface` | `#F7F8FA` | Panels, rails |
| `--surface-2` | `#EEF1F4` | Nested/inset surfaces |
| `--border` | `#D7DCE2` | Hairline borders (1px) |
| `--border-strong` | `#B4BCC6` | Dividers, table outlines |
| `--text` | `#11161C` | Primary text |
| `--text-muted` | `#5B6470` | Secondary text, labels |
| `--accent` | `#1F6FEB` | Interactive/selection accent (single accent, not navy/teal monochrome) |
| `--accent-weak` | `#E3ECFD` | Selected-row / active tints |
| **Status** | | |
| `--ok` | `#1F8A53` | Verified / COMPLETE / pass |
| `--warn` | `#B5740B` | REVIEW REQUIRED / INCOMPLETE / caution |
| `--danger` | `#C0392B` | Errors / failed invariant |
| `--info` | `#2563A8` | Neutral informational |
| **Map sequential (score / density)** | colorblind-safe sequential (e.g., viridis-like), 5–6 stops, paired with labels + legend — **never color alone** |
| **Map categorical (5 climate regions)** | 5 distinct colorblind-safe hues, each also patterned/labeled in legend |

Dark theme: invert `--bg`→`#0E1116`, `--surface`→`#161B22`, text→`#E6EAF0`, keep accent and
status hues at adjusted luminance; all pairs must still meet contrast (§5.6).

### 5.2 Typography

- **UI / data:** Inter (or system `ui-sans-serif`) — used for app chrome and tables.
- **Numeric / tabular:** use `font-variant-numeric: tabular-nums` for all metric columns so
  digits align.
- **Reading (Methodology):** the same sans at a comfortable measure (~70ch).
- Scale (px / line-height): caption 12/16, body-sm 13/18, body 14/20, subtitle 16/22,
  h3 18/24, h2 22/28, h1 26/32. **No oversized hero headings.** Max heading on any working
  screen is h2; h1 reserved for the methodology document title.
- Weights: 400 body, 500 labels/emphasis, 600 headings. Avoid heavy black weights.

### 5.3 Spacing & grid

- 4px base unit; spacing scale 4/8/12/16/20/24/32/48.
- Panel padding 16; dense table row height 36 (comfortable 44 toggle).
- 8-column inner content grid within document contexts; map contexts are flex, not grid.

### 5.4 Borders, radius, elevation

- Radius: `--radius` 4px for inputs/buttons/cards; 0px option for table containers. **No
  large pill radii** except true toggle chips (filter values), which use 4px, not 999px.
- Borders: 1px hairline default; surfaces are delineated by borders, **not drop shadows**.
- Elevation: only floating map controls, drawers, sheets, menus, and toasts get a single
  soft shadow (`0 1px 2px rgba(16,22,28,.08), 0 2px 8px rgba(16,22,28,.06)`). Static panels
  use borders only.

### 5.5 Iconography

- **Lucide** icons exclusively (per stack). 16px in dense UI, 20px in the nav rail. No
  emoji, no text glyphs, no ad-hoc SVGs. Icons always paired with a text label or an
  accessible name.

### 5.6 Focus, motion, contrast

- Focus: 2px `--accent` outline with 2px offset, always visible on keyboard focus.
- Motion: 120–180ms ease for drawers/sheets; respect `prefers-reduced-motion` (disable
  non-essential transitions, no map fly animations).
- Contrast: text ≥ 4.5:1 (≥3:1 for ≥18px/bold); UI/graphic boundaries ≥ 3:1. Map encodings
  carry a non-color cue.

### 5.7 Required UI states (define for every surface)

- **Empty:** e.g., "No catchments match these filters" with a Reset action.
- **Loading:** skeletons for table/cards, a contained spinner for the map; never a blank
  flash.
- **Error:** inline, actionable (retry / contact), surfaced via toast for transient and
  panel for persistent; map errors keep controls usable.
- **Degraded / 503 (no data):** a clear banner with remediation (mirrors backend health
  guidance), not a crash.
- **Data-quality states:** verified (`--ok`), REVIEW REQUIRED (`--warn`), INCOMPLETE
  weather (`--warn`), crosswalk one-to-many / ZIP≠ZCTA uncertainty (info note), each with
  an icon + label + tooltip.

---

## 6. Anti-"vibe-coded" rules (explicit)

Do **not** ship any of the following:
- gradient backgrounds or gradient text;
- oversized hero headings on working screens;
- floating, shadowed "section cards" as the primary layout device;
- rounded-pill everything (999px radii), or rows of decorative pills;
- ornamental KPI cards with giant numbers and no context;
- single-hue navy/teal monochrome treatment;
- emoji or improvised glyph icons;
- animation as decoration.

Do ship: square/low-radius analytical surfaces delineated by hairline borders; dense but
readable tables with tabular numerals; a clear geographic hierarchy (region → urbanicity →
catchment → ZIP/station); visible provenance and data-quality; one restrained accent color.

---

## 7. Target screens and interaction flows

Each screen below has a corresponding panel in `prototype/redesign_prototype.html`.

### 7.1 Map workspace (default)
- On load: fetch `health` (data mode), `dashboard`, `geometry`. Map fits to selected
  catchments; coverage matrix and distributions render; filter/scenario panel shows current
  scenario.
- Flow — inspect a catchment: click polygon → details drawer opens with Catchment + Score
  components + Weather station + ResStock + Data quality + Provenance sections; map zooms to
  selection; matrix cell highlights.
- Flow — filter: adjust climate/urbanicity/score-range etc. → map, matrix, table, and
  distributions all update; URL updates.

### 7.2 ZIP / place inspection
- Flow: type `19104` (or place / station) in global search → typed results disambiguate
  ZIP vs catchment vs station → choose ZIP → details drawer opens to the **ZIP/ZCTA**
  section: resolved ZCTA (or explicit "no ZCTA mapping" note), county, CBSA, climate,
  urbanicity, crosswalk one-to-many caveat, then the assigned catchment, its score
  components, the stratum representative, and nearby stations. Map pans/highlights.

### 7.3 Scenario editing (workbench)
- Flow: open **Scenario** → adjust weights (must sum to 1.00; live normalization helper +
  validation; block save if Σ≠1), density screen, max station distance, station-distance
  penalty, weather-QC requirement, uniqueness, PA preference → **Preview** calls
  `scenarios/evaluate` → live metrics (represented catchments, eligible candidates,
  combined score, mapping cautions, count of changed assignments) → **Save** (name +
  version) via `scenarios`; dirty/saved state shown in the top-bar scenario chip; **Share**
  copies the URL-encoded scenario. Export scenario JSON from here.

### 7.4 Candidate ranking (Catchments)
- Flow: dense TanStack table from `candidates`, sharing the global filter state. Sort any
  column; toggle column visibility; select up to N rows for comparison; **Export ranking
  CSV**. Row select highlights on the docked/collapsed map and can open the details drawer.

### 7.5 Compare (allocation)
- Flow: from ranking selection or a "Compare to baseline" action → two synchronized panels:
  baseline allocation vs active scenario, with a map diff (changed assignments emphasized),
  a deltas table (coverage Δ, score Δ, substitutions), and a per-change **reason** column.
  Deltas are quantified, never decorative.

### 7.6 Methodology & data
- Readable document context: method + vintage, boundary rules (rural→county /
  non-rural→CBSA), crosswalk limitations (one-to-many, ZIP≠ZCTA), weather-QC definition
  (leap-aware, 90% threshold), ResStock fields + verification status, source citations +
  versions + checksums, and links to OpenAPI/API docs and the export catalog. Provenance
  badges elsewhere deep-link here.

---

## 8. Frontend stack (small, audited)

Adopt the plan's preferred stack; deviations require a documented reason.

| Concern | Choice | Why |
|---------|--------|-----|
| Framework | **React 18 + TypeScript** | Mainstream, typed, testable. |
| Build/dev | **Vite** | Fast builds; multi-stage Docker friendly. |
| Map | **MapLibre GL JS** | Open-source vector maps, no token lock-in, GIS-grade; matches RAPT/SLOPE map depth without proprietary deps. |
| Charts | **Apache ECharts** | Dense, coordinated, accessible-capable charts (score/station-distance distributions, comparisons). |
| Table | **TanStack Table** | Headless, server-aware sorting/filtering/pagination/virtualization, column visibility. |
| Icons | **Lucide** | Consistent, license-clean icon set; no glyph improvisation. |
| State/router | React Router + lightweight store (URL-encoded filter/scenario state); TanStack Query for API caching | Shareable, reproducible views. |
| Styling | CSS variables (the §5 tokens) + minimal utility CSS or CSS Modules | No heavy CSS framework; tokens are the source of truth. |

Constraints carried from the project: preserve the `/api/v1` contract (Python backend owns
data, scoring, persistence, exports); strict same-origin CSP and hardening headers must
still pass; multi-stage Docker build (Node builds static assets, Python image serves them).
Run `npm audit` and keep the dependency set minimal and justified.

---

## 9. Visual acceptance criteria (screenshot-based)

Sessions 6–8 are accepted against screenshots at **desktop (1440×900)** and **mobile
(390×844)**; capture via Playwright.

Map workspace (desktop) must show:
1. Map occupying the dominant central area (≥55% of viewport width), not a card grid.
2. Persistent left filter/scenario panel and a thin icon nav rail.
3. The 5×4 coverage matrix + at least one coordinated distribution chart in the bottom
   strip.
4. A visible legend bound to the active layer, basemap/layer controls, and map attribution.
5. The data-mode badge (`DEMO`/`PRODUCTION`) and active-scenario chip in the top bar.
6. No gradient, no oversized hero heading, no floating ornamental KPI cards.

Details drawer must show distinctly labeled ZIP/ZCTA, Catchment, Weather station, ResStock,
Score components, Data quality, and Provenance sections (no conflation).

Mobile must show: map-first default, bottom tab bar, filters/selection as bottom sheets,
stacked sections, and no clipped/overlapping controls.

General: keyboard-only operation reaches all controls with visible focus; contrast passes
WCAG 2.1 AA; `prefers-reduced-motion` disables non-essential animation.

These criteria, plus the IA mapping in §2.2, are the definition of done for the redesign
build sessions.
