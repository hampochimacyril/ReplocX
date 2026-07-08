# W4 Research Atlas release audit

Date: 2026-07-08  
Branch: `feature/research-atlas`

## Release state

- Certified results tier: `replocx_tmy3_wallfix_4scen`
- Certified cells: 720
- Scenario order: A, C, B, D
- R9 gate: PASS
- Figure registry/assets: `f2v3_final` only
- Equity: READY — 4/4 layers, 20 sidecar-backed catchment records
- Public demo: Atlas disabled; no private Atlas mount
- Local release gates: PASS
- UI evidence: selection-data mode and certified Atlas tier are labeled
  separately
- Live deployment: not authorized until the unchecked owner/infrastructure
  items in `docs/deployment_options.md` are resolved

## Authentication boundary

The private candidate uses reverse-proxy HTTP Basic auth plus the existing app
token gate. The SPA sends its in-memory app token as `X-RLE-Auth`; Caddy/nginx
uses the ordinary `Authorization` header for Basic auth and translates the app
token to `Authorization: Bearer …` upstream. The app container is not published
directly.

Required smoke outcomes:

| Request | Expected |
| --- | --- |
| `/atlas` without Basic auth | 401 at proxy |
| `/api/v1/results/*` without Basic auth | 401 at proxy |
| `/api/v1/equity/*` without Basic auth | 401 at proxy |
| API with Basic auth but no app token | 401 at app |
| API with Basic auth plus valid app token | 200 |

## Public-image boundary

The runtime Docker stage uses an allowlist. It copies backend code, generated
synthetic demo data, the demo ZIP crosswalk, and compiled frontend assets only.
Private Atlas data, `pipeline/out`, test fixtures, provenance sidecars, docs,
and canonical f2v3 assets are excluded from both the public build context and
runtime image.

## Branch divergence

The local ref comparison on 2026-07-08 is 25 commits ahead and 6 commits behind
`origin/main`. The six `origin/main`-only commits are selection/marketing work;
their changed paths do not include the Atlas backend, Atlas frontend routes, or
Atlas tests. Because the worktree contains protected W0–W3 and unrelated dirty
state, W4 does not merge/rebase it implicitly. Reconcile in a clean worktree
before publication, rerun all W4 gates, and record the resulting commit.

## Local verification evidence

Measured on July 8, 2026:

- `scripts/check_atlas_release.py`: PASS. Basic and app-token gates behaved as
  designed; certified routes reported 720 cells, A/C/B/D, R9 PASS,
  `f2v3_final`, 4/4 READY equity layers, and 20 catchment records. The runtime
  scan checked 117 public-image files against 79 canonical figure/table names
  with zero collisions.
- `scripts/verify_all.sh`: all checks passed. Both backend modes ran 120 tests;
  coverage was 72%; backend dependency audit found no known vulnerabilities;
  frontend ran 50 tests, typecheck/lint/build passed, and the full disabled-mode
  browser suite ran 13 passed with one expected Atlas-enabled skip.
- Targeted Atlas Playwright: enabled mode 1 passed/1 skipped; disabled mode
  1 passed/1 skipped. The refreshed desktop, tablet, mobile, equity, exports,
  disabled-state, and contact-sheet screenshots were visually inspected.
- Known non-blocking audit output: frontend production audit reports one
  moderate ECharts advisory below the configured high-severity failure
  threshold. A breaking ECharts 6.1 upgrade is separate work.
- Docker is not installed in this environment, so the Compose/Caddy candidate
  and built image have not yet been exercised as real containers. That remains
  a pre-live-deployment gate.

## Final artifact checklist

- [x] A/C/B/D descriptive labels and p95/exposure framing
- [x] overheating/high-humidity terminology includes threshold notes
- [x] figure registry, captions, downloads, and provenance resolve to f2v3
- [x] sidecar-backed equity state is READY in API/UI/export/provenance contracts
- [x] desktop/tablet/mobile W2 screenshots retained
- [x] final W4 screenshots and contact sheet:
  `docs/atlas/screenshots/2026-07-08/atlas-w4-equity-ready.png`,
  `atlas-w4-exports-provenance.png`, and `atlas-w4-contact-sheet.png`
- [x] screenshots distinguish `SELECTION DEMO` from `ATLAS CERTIFIED`
- [ ] live private host URL and owner sign-off
