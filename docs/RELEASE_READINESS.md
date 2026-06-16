# Release Readiness — ReplocX v1.2 (Session 9)

_Audit date: 2026-06-08. Branch: `feature/location-representation-explorer`.
Scope: release-candidate quality, security, performance, and release audit._

## Go / No-Go

**Status: GO for the public demo — pending two confirmations that can only run
outside this audit sandbox (GitHub CI and a macOS `scripts/verify_all.sh` run).**

Every gate that can execute in the audit environment is green, and the one
material defect found during the audit was fixed and covered by a new regression
test. The remaining items (Playwright browser e2e, Docker build/smoke) are wired
into CI and the local verifier but could not be executed in this sandbox because
it has no browser engine and no Docker daemon, and the GitHub release-asset
download endpoint is proxy-blocked. They must go green on GitHub Actions before
the Session 10 deployment.

This is a deliberate **conditional GO**: do not deploy until the GitHub `e2e`
and `docker` jobs pass on this branch.

## What ran, and the evidence

The audit could not use the committed `.venv` (a macOS symlink that does not
resolve on the Linux audit host) and could not download a CPython 3.12 build
(GitHub release assets are proxy-blocked). The Python gates therefore ran on the
host's CPython 3.10 with a single `datetime.UTC` compatibility shim (a `.pth`
import line in the throwaway venv only — **no product code was modified for
this**). `datetime.UTC` is the *only* 3.11+ runtime feature in the codebase
(6 call sites; no `tomllib`/`StrEnum`/`TaskGroup`/etc.), so behavior under the
shim is identical to CI's real 3.11/3.12. Node 22 / npm 10 ran natively.

### Backend, pipeline, and quality gates — all green

| Gate | Command | Result |
| --- | --- | --- |
| Fixture pipeline + invariants | `pipeline.run --source fixture --out <tmp>` | PASS — 2959 candidates, 20 selected, `validate` OK |
| Validate committed **national** outputs | `pipeline.validate --dir pipeline/out` | PASS — schema + invariants hold (20 distinct strata, county/CBSA rules, weights) |
| Unit tests (bundled demo) | `unittest discover -s tests` | **86 / 86 OK** |
| Unit tests (fixture pipeline outputs) | `RLE_ANALYSIS_DATA_DIR=<fixture> unittest` | **86 / 86 OK** |
| Ruff | `ruff check …` | PASS |
| Black | `black --check …` | PASS (43 files) |
| Mypy (api/auth/observability/scenario_store/client) | `mypy …` | PASS (no issues, 6 files) |
| Coverage | `coverage run … && coverage report` | **66%** total (gate ≥ 50) |
| pip-audit (runtime deps) | `pip_audit -r backend/requirements.txt` | **0 known vulnerabilities** |
| API + security + degraded contract | `scripts/check_release_contract.py` | PASS (9 checks) |

### Frontend gates — all green

| Gate | Command | Result |
| --- | --- | --- |
| Clean install | `npm ci` | PASS (334 packages, from committed lockfile) |
| Type check | `tsc -b` | PASS (clean) |
| Lint | `eslint .` | PASS — 0 errors, 3 accepted `react-refresh/only-export-components` warnings (provider+hook files, same category accepted since Session 7) |
| Unit tests | `vitest run` | **35 / 35 pass** (8 files) |
| Production build | `vite build` | PASS in ~6s |
| Dependency audit (production) | `npm audit --omit=dev` | **0 vulnerabilities** |

Production bundle (gzip in parentheses): `index` 169.66 kB (45.88), `vendor`
206.70 kB (65.77), `echarts` 463.80 kB (157.12), `maplibre` 801.64 kB (217.60),
CSS 90.87 kB (14.55). Total `dist` ≈ 1.7 MB (~500 kB gzipped). The map and chart
engines dominate and are code-split into their own cacheable chunks.

### API, security, auth, and degraded mode — verified live

The new `scripts/check_release_contract.py` boots the stdlib server and asserts:

- `/api/health` → 200, `status: ok`, `data_ready: true`, and **`data_mode:
  demo`** by default (the public-safe default; production only via an explicit
  `RLE_ANALYSIS_DATA_DIR`, since `DEFAULT_ANALYSIS_DIR` points outside the repo).
- `/api/v1/health` alias → 200; OpenAPI document is 3.1.0 with 12 paths.
- Strict same-origin **Content-Security-Policy** plus `X-Content-Type-Options:
  nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
  `Cross-Origin-Opener-Policy: same-origin`, and a locked-down `Permissions-Policy`.
- Scenario persistence + versioning over HTTP: save → version 1, child save with
  `parent_id` → version 2 with lineage, listed back (`returned ≥ 2`).
- Private-deployment auth: with `RLE_PRIVATE_AUTH_TOKEN` set, a protected route
  returns **401** without a token and **200** with a valid Bearer/`X-RLE-Auth`
  token, while `/api/health` stays public.
- Graceful degraded mode: with inputs missing, `health` reports `degraded` /
  `data_ready: false` and service routes return **503** with remediation text.

### Defect found and fixed during the audit

`GET` on an unknown `/api/...` path previously fell through to the SPA
`index.html` and returned **200**, while `POST` correctly returned a JSON
**404**. Fixed in `backend/server.py`: unknown API GETs now return
`404 {"error": "Route not found."}`, and non-API deep links (e.g. `/scenario`)
still serve the SPA shell so client-side routing survives a hard refresh. Added
`tests/test_phase3.py::test_unknown_api_route_returns_json_404` (suite 85 → 86).

## Performance profile

Measured against the stdlib server on both candidate universes.

| Surface | Demo (2959 candidates) | National (4019 candidates) |
| --- | --- | --- |
| Startup → first `/api/health` 200 | 0.22 s | 0.82 s |
| `GET /api/dashboard` | ~185 ms, 96 KB | ~150 ms, 106 KB |
| `GET /api/candidates` | ~11 ms, 330 KB | ~12 ms, 326 KB |
| `GET /api/geometry` | ~2 ms, 18 KB | ~4 ms, 86 KB |

No material bottleneck. The key scalability safeguard is already in place:
`/api/candidates` is **server-paginated** (`total`/`returned`/`limit`/`offset`/
`has_more`, 250-row default page), so payload and render cost are constant
whether the dataset has 2959 or 4019 candidates. `/api/geometry` ships only the
20 selected polygons. Map rendering of the candidate point layer (≤ ~4k points)
is well within MapLibre's comfortable range. All API responses are < 200 ms.

## Local/CI alignment

- `scripts/verify_all.sh` now also runs **national-output validation** and the
  **API + security + degraded-mode contract** check, alongside its existing
  fixture pipeline, demo + fixture-output regression suites, ruff/black/mypy/
  coverage/pip-audit, frontend typecheck/lint/test/build, `npm audit
  --omit=dev --audit-level=high`, and Playwright e2e.
- `.github/workflows/ci.yml` gained, in the backend job: the fixture
  pipeline + outputs-mode regression, national-output validation, and the
  release-contract check; in the frontend job: a production `npm audit`; and a
  new **`docker` job** that builds the multi-stage image and smoke-tests the
  running container (`/api/health` reports demo data; CSP header present).

## Residual risks and follow-ups

1. **Browser e2e / Docker not executed in this audit.** Playwright Chromium is
   not installable here (blocked GitHub download) and there is no Docker daemon.
   The `e2e` and `docker` CI jobs must be confirmed green on GitHub before
   deploying. Severity: medium (gating), mitigated by CI.
2. **Frontend dev-toolchain advisories.** `npm audit` (including dev) reports 5
   issues — 4 moderate + 1 "critical" — all in the **esbuild/vite/vitest** dev
   chain (the critical is the Vitest UI-server file-read, which only applies when
   running `vitest --ui`, never in CI or the shipped artifact). The production
   bundle has **0** vulnerabilities (`npm audit --omit=dev`). The only fix is a
   breaking `vite@8`/`vitest` major bump; recommend a scheduled, separately
   verified upgrade rather than a forced bump in the release window. Severity:
   low (not in the deployed artifact).
3. **Accessibility and visual-regression automation are partial.** The Playwright
   suite captures desktop and mobile (viewport-resized) evidence screenshots but
   has no separate mobile project, no `toHaveScreenshot` pixel diffing, and no
   automated `axe` pass. App-level a11y (keyboard, focus, reduced-motion, ARIA)
   was built in Sessions 6–7 and is partly asserted in unit tests. Recommend
   adding an axe check and a named mobile project as a follow-up (deferred here
   to avoid landing unverifiable test scaffolding during the audit). Severity:
   low.
4. **Python audited under shimmed 3.10.** CI remains the authority for the real
   3.11/3.12 matrix. Severity: negligible (single `datetime.UTC` delta).
5. **Commit/push must be done on the host.** The audit ran against a fuse mount
   that forbids `unlink`/`rename`, so git cannot manage `.git/index.lock` and a
   stale lock from the harness's own `git status` is present. Commit and push the
   Session 9 changes from macOS (see `docs/SESSION_HANDOFF.md`).

## Bottom line

All in-environment release gates pass; the one real defect was fixed with a
test; performance scales via existing pagination. Mark **GO for the public demo
once the GitHub `e2e` and `docker` jobs are green** on this branch and a full
`scripts/verify_all.sh` run passes on the macOS toolchain. Real national data
stays off the public demo (Session 11).
