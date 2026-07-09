# Changelog

All notable changes to ReplocX are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project uses semantic versioning. The analytical *method version* (currently
2.0) is tracked separately in `selection_metadata.json` and is unchanged by
these releases.

## [Unreleased]

### Atlas N3 full 20-stratum pivot

- Added the versioned `atlas.strata/1.0` server response for the complete
  five-climate × four-urbanicity lattice, derived server-side from certified
  run-level outputs with A/C/B/D ordering and R9/f2v3 provenance.
- Added guided climate, urbanicity, 20-stratum, and representative-site review
  steps with URL/share state, labels, tooltips, filters, and screenshot
  evidence.
- Extended backend, frontend, disabled-mode, and Playwright coverage for all 20
  strata without changing sealed-passive D comparison semantics.

### ReplocX Research Atlas — private local release candidate
- Added a modular sibling context set, the **Research Atlas**, served by the same
  React app and `/api/v1` backend and reading the certified
  `replocx_tmy3_wallfix_4scen` **720-cell A/C/B/D** results tier read-only.
  Certified provenance requires R9 PASS and resolves figures and source tables
  from `f2v3_final` only.
- Added backend `AtlasService` + shared router with `GET /api/v1/results/*`
  (`overview`, `scenario-dictionary`, `scenario-summary`, `by-stratum`,
  `scenario-c`, `d-comparisons`, figure source/bundle, exports, cooling seasons,
  sensitivity, and provenance) and `GET /api/v1/equity/*` (`profiles`,
  `scenario-cross`), wired into both stdlib and FastAPI entry points.
- Gated the Atlas behind `RLE_ENABLE_ATLAS` (default **off**): when disabled the
  results/equity routes return 404 so the public location-selection demo never
  exposes the unpublished results. `/api/v1/health` now reports `atlas_enabled`.
- Added the guided Atlas story spine, p95/exposure-hour framing, A/C/B/D
  selectors, D-B/D-C/D-A contrasts, site drill-down, and Fig02 source parity.
  The global data badge now distinguishes the location-selection data mode from
  the certified private Atlas tier.
- Added a reproducible, sidecar-backed 20-catchment equity profile. All four
  layers are READY: CDC/ATSDR SVI (Proxy), ACS income/poverty (Direct), DOE LEAD
  energy burden (Proxy), and heat vulnerability (Modeled).
- Added the private VM/Compose/Caddy candidate with Basic auth plus an
  independently rotated app token, read-only analytical mounts, a public-image
  runtime allowlist, and local auth/certified-route/equity/leak release checks.
  Local W4 gates pass; live private deployment and owner sign-off remain pending.

### Redesigned interface — workflows complete (Session 8)
- Added the scenario workbench: composite-weight editing with sum validation and
  one-click normalization, density/distance/penalty/uniqueness/weather-QC controls,
  an overrides editor, a live preview of deltas vs. the baseline, apply, and
  versioned save/share with a saved-scenario browser and version history.
- Added the candidate ranking table (TanStack Table) with sorting, column
  visibility, pagination, comparison selection, and CSV export of the filtered
  ranking, sharing the global filter state with the map.
- Added the comparison view: quantified baseline-vs-scenario allocation deltas,
  a per-stratum representative diff with reasons, and a side-by-side candidate
  matrix.
- Expanded methodology with data lineage, a live validation-status table, source
  citations, and API/export documentation; added scenario-config JSON and map-PNG
  exports.
- Removed the legacy vanilla frontend (`frontend/legacy/`); `frontend_dir()` now
  resolves `dist` → source.

## [1.2.0] — 2026-06-05

### Productionization
- Added `/api/v1` aliases and a published OpenAPI schema while preserving legacy
  `/api` routes for existing clients and uptime checks.
- Added SQLite scenario persistence with saved scenario ids, version metadata,
  and list/read endpoints.
- Added optional bearer-token auth for private deployments, plus a private
  Render blueprint example that keeps the public demo profile separate.
- Added structured JSON-style request/error logging and optional Sentry capture
  via environment variables.
- Added Phase 4 CI hardening: ruff, black, mypy, coverage gate, pip-audit, and
  Dependabot configuration.

## [1.1.0] — 2026-06-02

### Self-contained run & CI
- **Bundled demonstration dataset.** `scripts/generate_demo_data.py` produces a
  deterministic synthetic dataset in `data/demo/`; `DataService` falls back to it
  when the private analytical outputs are absent and no `RLE_ANALYSIS_DATA_DIR`
  override is set. The app, regression suite, and Playwright flows now run on any
  clone with zero external inputs. Active mode is reported via `data_mode`
  (`/api/health`, methodology sources, and a UI indicator).
- **GitHub Actions CI** (`.github/workflows/ci.yml`): Python 3.11/3.12 backend
  tests, a graceful-degradation smoke test, frontend syntax check, and Playwright
  end-to-end tests on every push and pull request.

### Operation & robustness
- **Fault-tolerant startup.** Analytical inputs are now loaded lazily through a
  shared accessor (`backend/service.py`). A missing or unreadable analysis
  directory no longer crashes the process at import time; the server starts and
  returns a clear `503 Service Unavailable` with remediation guidance until the
  data is available. Recovery no longer requires a restart.
- **Richer health probe.** `GET /api/health` now reports `status`
  (`ok`/`degraded`), `data_ready`, app `version`, the resolved analysis
  directory, candidate/selected counts, and the analytical method version. The
  local runner prints readiness on startup.
- **Hardened error handling.** The dependency-free server mirrors GET-style error
  mapping on POST (400 for invalid input, 404 for unknown ZIPs, 503 when inputs
  are unavailable, 500 as a last resort) and the FastAPI app gains a matching
  exception handler. The refresh action degrades gracefully instead of blanking
  the workspace.
- **Security headers.** Both entry points send a strict same-origin
  `Content-Security-Policy` plus `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Cross-Origin-Opener-Policy`, and `Permissions-Policy`.

### Method (additive, descriptive only — selection logic unchanged)
- `evaluate()` now reports `coverage_efficiency` (share of the unconstrained
  per-stratum composite score retained after distinct-coverage rules),
  `min`/`median` selected score, `mean`/`max` selected station distance, and
  `mean_unconstrained_rank`. These diagnostics do not influence which catchments
  are selected. Surfaced in the Allocation comparison view.

### UI / UX & accessibility
- Sortable ranking columns are keyboard-operable (`Tab` + `Enter`/`Space`),
  expose `aria-sort`, and show an active-sort caret.
- Mobile navigation gains a dismissable backdrop, `Escape`-to-close, and
  `aria-expanded` state; the active section is marked `aria-current="page"`.
- Visible keyboard focus styling, `prefers-reduced-motion` support, higher
  small-text contrast, per-page document titles, a favicon/theme color, and a
  print stylesheet that produces a clean methodology handout.
- The Scenario builder blocks evaluation until score weights total 100% and
  offers a one-click **Normalize to 100%** control, replacing the previous
  silent failed request.

## [1.0.0]
- Initial ReplocX release: overview dashboard, ZIP explorer,
  scenario builder, candidate ranking, allocation comparison, methodology
  appendix; deterministic scoring and min-cost distinct-location allocation;
  read-only ingestion with SHA-256 manifest; dependency-free and FastAPI entry
  points; Python regression suite and Playwright critical-flow tests.
