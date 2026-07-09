# W4 Research Atlas release audit

Updated: 2026-07-09
Branch: `codex/atlas-release-candidate`

## Release state

- Certified results tier: `replocx_tmy3_wallfix_4scen`
- Certified cells: 720
- Scenario order: A, C, B, D
- R9 gate: PASS
- Figure registry/assets: `f2v3_final` only
- Interactive parity: PASS — all four intended f2v3 twins (Fig02 and
  Fig05–Fig07) pass; the other 15 registry figures have explicit
  not-applicable rationales
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
canonical f2v3 assets, host dependencies/build outputs, Python bytecode, and
owner-specific host paths are excluded from the public build context and
runtime image.

## Release-series state

N2 created the isolated `codex/atlas-release-candidate` worktree from current
`origin/main` and transferred only the reviewed Atlas release series. N3 added
the complete 20-stratum pivot. N4 parity and N5 container-boundary changes are
being reviewed in this clean worktree; the original mixed
`feature/research-atlas` index remains untouched.

## Local verification evidence

Measured on July 8–9, 2026:

- `scripts/check_atlas_release.py`: PASS. Basic and app-token gates behaved as
  designed; certified routes reported 720 cells, A/C/B/D, R9 PASS,
  `f2v3_final`, 4/4 READY equity layers, and 20 catchment records. The runtime
  scan checked 117 public-image files against 79 canonical figure/table names
  with zero collisions.
- `scripts/verify_all.sh`: all checks passed. Both backend modes ran 120 tests;
  coverage was 72%; backend dependency audit found no known vulnerabilities;
  frontend ran 50 tests, typecheck/lint/build passed, and the full disabled-mode
  browser suite ran 13 passed with one expected Atlas-enabled skip.
- Full f2v3 parity: Fig02 and Fig05–Fig07 checked 61 plotted values with
  `max|diff| = 0` at absolute tolerance `1e-12`; all 15 omitted twins have
  explicit rationales.
- Targeted Atlas Playwright: enabled mode 1 passed/1 skipped; disabled mode
  1 passed/1 skipped. The refreshed desktop, tablet, mobile, equity, exports,
  disabled-state, and contact-sheet screenshots were visually inspected.
- Known non-blocking audit output: frontend production audit reports one
  moderate ECharts advisory below the configured high-severity failure
  threshold. A breaking ECharts 6.1 upgrade is separate work.
- N5 real-container boundary: PASS on Docker Desktop 4.81.0 / Engine 29.6.1.
  The actual 13-layer image scan found zero canonical asset basenames,
  sidecars, secrets, owner host paths, or host bytecode. The actual
  Caddy/Compose stack passed unauthenticated, Basic-only, and
  Basic-plus-app-token cases; all analytical mounts rejected writes; the
  certified route/equity/export audit passed; and all temporary runtime
  resources were removed. See
  `docs/atlas/N5_CONTAINER_BOUNDARY_AUDIT_2026-07-09.md`.

## Final artifact checklist

- [x] A/C/B/D descriptive labels and p95/exposure framing
- [x] overheating/high-humidity terminology includes threshold notes
- [x] figure registry, captions, downloads, and provenance resolve to f2v3
- [x] every intended interactive f2v3 twin passes source-value, ordering,
  filtering, label, fixture-hash, and provenance-hash parity checks
- [x] actual public image/rootfs layers contain no canonical assets, sidecars,
  secrets, owner host paths, or host bytecode
- [x] actual Caddy + app containers pass the two-layer auth matrix
- [x] actual analytical bind mounts reject writes
- [x] sidecar-backed equity state is READY in API/UI/export/provenance contracts
- [x] desktop/tablet/mobile W2 screenshots retained
- [x] final W4 screenshots and contact sheet:
  `docs/atlas/screenshots/2026-07-08/atlas-w4-equity-ready.png`,
  `atlas-w4-exports-provenance.png`, and `atlas-w4-contact-sheet.png`
- [x] screenshots distinguish `SELECTION DEMO` from `ATLAS CERTIFIED`
- [ ] live private host URL and owner sign-off
