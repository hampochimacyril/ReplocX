# Changelog

All notable changes to the Representative Location Explorer are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project uses semantic versioning. The analytical *method version* (currently
2.0) is tracked separately in `selection_metadata.json` and is unchanged by
these releases.

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
- Initial Representative Location Explorer: overview dashboard, ZIP explorer,
  scenario builder, candidate ranking, allocation comparison, methodology
  appendix; deterministic scoring and min-cost distinct-location allocation;
  read-only ingestion with SHA-256 manifest; dependency-free and FastAPI entry
  points; Python regression suite and Playwright critical-flow tests.
