# Session Handoff

## Session N6 — B1 owner-assisted private deployment preflight

- Date: July 9, 2026.
- Branch/worktree: `codex/atlas-release-candidate` at
  `/private/tmp/Developer-atlas-release`.
- Runtime release commit prepared for deployment:
  `a13157dddb618352d4897df096238c676b7b0513`
  (`atlas(n4-n5): verify parity and container boundary`).
- Owner approval granted in-chat to execute and download what is needed for
  N6. This approval covers local/external command execution and required
  downloads, but no concrete live host, DNS name, firewall/VPN policy, secret
  manager path, or backup owner was discoverable in the workspace or shell
  environment.

### Preflight executed

- Confirmed the clean release worktree is ahead of `origin/main` by nine
  commits with no uncommitted changes before the N6 documentation update.
- Confirmed Docker is available at `/usr/local/bin/docker`.
- Confirmed the configured Git remote is
  `https://github.com/hampochimacyril/Location-representation-explorer.git`.
  `git ls-remote origin HEAD` resolved to `c0fb5cb`; the unauthenticated public
  GitHub API returned `404`, so the repository is not publicly discoverable
  through that endpoint.
- Environment-name scan found only `GH_PAGER` and `SSH_AUTH_SOCK` among
  deployment/cloud-related names. No `RLE_*`, cloud-provider, deploy-host, DNS,
  or secret-manager variables were present.
- Re-ran the W4/N3/N5 release smoke with explicit certified data and figure
  roots. Result: **PASS**. Evidence included the Basic-auth proxy block,
  app-token block, authorized 200 responses, 720 cells, A/C/B/D, R9 PASS,
  `f2v3_final`, full 20-stratum route checks, equity READY with 4/4 layers and
  20 records, public-disabled 404 regressions, and Docker build-context/runtime
  allowlist checks.
- `git diff --check`: **PASS**.
- `python3 -m unittest tests.test_atlas`: **26 passed, 2 skipped**.

### Gate state

N6 live deployment is **not complete**. The release candidate is prepared, local
preflight is green, and command/download approval is recorded, but there is no
actual provisionable target. The following owner/infrastructure values remain
required before any live deployment command can be run:

- approved VM/host or provider account;
- private DNS name;
- access-control owner and reviewer list;
- secret-manager source/path for Basic auth and `RLE_PRIVATE_AUTH_TOKEN`;
- allowed VPN/IP ranges or network policy;
- retention/backup owner and scenario database policy;
- exact host mount paths for `/analysis`, `/atlas`, and `/atlas-figures`;
- explicit confirmation that this GitHub remote/branch is the intended private
  release repository.

Stop honored: no live host was provisioned, no production DNS was created, no
production secret was generated or stored, and no reviewer URL exists yet.

## Session N5 — B1/C1 real container boundary

- Date: July 9, 2026.
- Branch/worktree: `codex/atlas-release-candidate` at
  `/private/tmp/Developer-atlas-release`.
- Starting point: N3 commit `f8a417c` plus the already executed N4 chart
  parity corrections. No push, pull request, public DNS, production
  credential, or live deployment.
- Goal: prove the committed Caddy plus app boundary using actual containers,
  scan the actual saved image/rootfs layers, exercise the two-layer auth
  matrix, and verify all analytical mounts are read-only.

### Runtime preparation

- Installed Docker Desktop 4.81.0 from Docker's official Apple-silicon
  distribution after the original machine had no container runtime.
- The DMG checksum verified. macOS code-signing and Gatekeeper checks passed
  outside the restricted sandbox: valid on disk, designated requirement
  satisfied, and accepted as a Notarized Developer ID from Docker Inc
  (`9BNSXJN65R`).
- Measured runtime: Docker Engine 29.6.1, Linux/arm64; Compose plugin present.
- The earlier signature-invalid Podman payload was not installed or executed.

### Real-build defects found and fixed

N5 did not rubber-stamp the first image:

1. Root-only `node_modules/` and `dist/` ignore rules admitted 463 MB of host
   frontend dependencies and stale compiled assets into the build context.
   Nested rules reduced the effective context to approximately 8 KB and left
   exactly five current production assets.
2. `backend/atlas_service.py` baked the owner's absolute canonical OneDrive
   paths into public runtime code. Defaults are now the container-safe
   `/atlas` and `/atlas-figures`; environment overrides remain authoritative.
3. Nested host Python bytecode entered the image and preserved the removed
   path. Nested `__pycache__`/`*.py[cod]` exclusions now prevent that.

Regression assertions cover the container-safe defaults, nested ignore rules,
and absence of `/Users/` in the runtime Atlas service source.

### Actual image/layer evidence

- Public image:
  `sha256:f821629698b257642a6fa5fc3380f7e5c243725bbe322ca59661bf0de42d0c7a`,
  59,253,207 bytes, Linux/arm64.
- Compose image:
  `sha256:9b8482a6cffd84a2923f0c5307280f6ac0e2f81d146a012a2c1941d4035ccb41`.
- Both images had the same 13 root filesystem diff IDs.
- Corrected merged rootfs: 30 app files, five frontend assets, zero host
  bytecode, zero provenance/checksum sidecars, zero canonical f2v3 asset
  basename collisions, and zero owner-path or disposable-secret hits.
- All 13 saved compressed layers were scanned; zero private-path or
  disposable-secret hits.
- Saved image SHA-256:
  `8701ac748331aca2e2ba81be792e70ca7ad3614351966954c52d76b7b7461b24`.
- Exported rootfs SHA-256:
  `5dc6e07751c5d302a522a3a21a922212f7473fe43f9b71dda5750599e6c6495f`.

The certified tier and f2v3 labels remain intentional code-level contract
identifiers. No certified row, asset, sidecar, secret, or owner-specific host
path is baked into the image.

### Actual Caddy/Compose evidence

- Started the committed `docker-compose.atlas-private.example.yml` and
  `deploy/atlas-private/Caddyfile` with disposable credentials, the actual
  selection analysis root, and the certified Atlas data/figure roots.
- Only Caddy published `443:443`. The app exposed `8787` only to the internal
  network and had an empty host port-binding map.
- Auth matrix:
  - frontend without Basic auth: 401;
  - certified API without Basic auth: 401;
  - certified API with Basic auth only: 401 from the app token gate;
  - certified API with Basic auth plus app token: 200;
  - frontend with Basic auth: 200.
- Effective mounts:
  `/analysis`, `/atlas`, and `/atlas-figures` were read-only binds; `/state`
  was the only writable named volume.
- Explicit write probes against all three analytical mounts failed with
  `Read-only file system`.

### Certified audit through the proxy

- Overview: 720 cells, A/C/B/D, `atlas.w1/1.0`.
- N3 stratum route: 20 metadata records, 80 scenario rows, nine certified
  cells per stratum/scenario, R9 PASS, `f2v3_final`.
- Equity: 20 profiles, 4/4 READY, zero `REVIEW REQUIRED`.
- Exports: four views, 19 figure bundles, and the four-row annual
  scenario-summary export with read-only source metadata.
- Logs: 20 app lines and 29 proxy lines; zero secret, owner-path, canonical
  asset-name, or certified-row hits.
- Named volumes held no canonical data, figures, sidecars, or app token.

### Verification and cleanup

- Targeted backend Atlas/contract suite: **33 passed**.
- Frontend typecheck: passed.
- Targeted Atlas frontend suite: **9 passed**.
- `scripts/check_atlas_release.py` with explicit certified roots: **PASS**.
- The stack was stopped with `docker compose down -v`. All N5 containers,
  networks, named volumes, and the port-443 binding were removed. The verified
  image remains local for review.
- Durable evidence:
  `docs/atlas/N5_CONTAINER_BOUNDARY_AUDIT_2026-07-09.md`.

### Gate and exact next starting point

N5 gate: **PASS**. Actual image layers are clean; the actual Caddy/app stack
passes unauthenticated, Basic-only, and Basic-plus-app-token cases; all
analytical write probes fail; and certified route/export/equity results match
the local candidate.

Start N6 only after the owner supplies the approved host/platform, private DNS
name, reviewer/access owner, production secret source, network/VPN policy,
retention/backup owner, exact private repository/branch, and budget approval.

Stop honored: no public DNS, production credential, push, pull request, or live
deployment. Temporary containers, networks, volumes, credentials, and local
test certificates were removed.

## Session N3 — A2 full 20-stratum Atlas pivot

- Date: July 8, 2026.
- Branch: `codex/atlas-release-candidate`.
- Worktree: `/private/tmp/Developer-atlas-release` (moved from the N2
  `/Users/cch322/Developer-atlas-release` path into the session's writable
  sandbox).
- Starting point: owner-approved N2 series at `fa66b47`, seven local commits
  ahead of `origin/main`; no push or pull request.
- Goal: make the landing and comparison flow cover all five climate regions ×
  four urbanicity groups while retaining A/C/B/D, D semantics, R9/f2v3
  provenance, and the public-disable boundary.

### N2 approval boundary resolved

The owner explicitly approved `docs/atlas/N2_RELEASE_MANIFEST.md` and its
seven-commit series before N3 work began. The commits are:

1. `d58c993` — application foundation.
2. `337c48a` — W0 contracts.
3. `bf1e0dd` — W1 certified results API.
4. `9e97a42` — W2 guided Atlas UI.
5. `d6e2dc1` — W3 exports/provenance/equity builder.
6. `763a2af` — W4 private container boundary.
7. `fa66b47` — N2 manifest and verification.

No commit was pushed and no pull request was opened.

### What changed

- Added the stable `atlas.strata/1.0` response for
  `/api/v1/results/by-stratum?dimension=stratum`.
- The backend reads the certified annual or seasonal
  `run_level_metrics` CSV and groups server-side by `climate_region`,
  `urbanicity`, and `hvac_scenario`. It returns:
  - 20 stable stratum metadata records;
  - 80 metric rows per tier;
  - nine certified cells in every real-data stratum/scenario bucket;
  - scenario order `A`, `C`, `B`, `D`;
  - source CSV/sidecar plus R9 `PASS`, `f2v3_final`, and read-only provenance.
- Extended fixture and backend tests across every one of the 20 combinations
  for both annual and seasonal tiers.
- Reworked the landing pivot into a guided
  `climate → urbanicity → 20 strata → representative site` path. The full
  lattice is the default; climate and urbanicity filters only filter
  server-returned rows.
- Added friendly labels/tooltips, per-stratum site links, a reviewer breadcrumb
  on site detail, and a return link to the exact shared pivot state.
- Made tier, scenario, dimension, climate, urbanicity, stratum, metric, and
  threshold URL-backed; Atlas section navigation retains the query state.
- Extended the results surface to chart/filter the combined strata and report
  contract/source metadata. D comparison code and semantics were not changed.
- Updated the W0 contract record and added
  `docs/atlas/N3_20_STRATUM_CONTRACT.md`.

### Screenshot evidence

Visually inspected under `docs/atlas/screenshots/2026-07-08-n3/`:

- `atlas-n3-20-strata.png`;
- `atlas-n3-urbanicity-pivot.png`;
- `atlas-n3-site-drill.png`;
- `atlas-n3-results-strata.png`.

These show the complete 20-row lattice, the urbanicity step, stratum-to-site
drill-down, and the 20-stratum results view.

### Verification (local, July 8, 2026)

- Targeted backend:
  `.venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v`:
  **33 passed**.
- Targeted frontend Atlas unit suite: **9 passed**; TypeScript typecheck passed.
- Frontend lint/build: **0 errors / 3 pre-existing fast-refresh warnings**;
  production build passed.
- Enabled canonical Atlas Playwright: **1 passed, 1 expected disabled-mode
  skip**. It exercised all 20 strata, site drill, urbanicity pivot, combined
  results, A/C/B/D, D contrasts, equity, and exports.
- Disabled public-demo Playwright: **1 passed, 1 expected enabled-mode skip**;
  `/api/v1/results/by-stratum?dimension=stratum` returned **404**.
- `.venv/bin/python scripts/check_atlas_release.py`: **PASS** after extending
  the audit to both annual/seasonal 20-stratum routes (20 metadata records, 80
  A/C/B/D rows, R9 PASS, `f2v3_final`) and the disabled-route 404 check.
- `scripts/verify_all.sh`: **all checks passed**.
  - fixture build/validation passed;
  - bundled and regenerated-output backend suites: **121 tests each**;
  - ruff, black, mypy, API/security contract, and runtime dependency audit
    passed;
  - coverage: **72%**;
  - frontend: typecheck/build passed, lint 0 errors/3 existing warnings, and
    **52 tests passed**;
  - frontend production audit retained one known moderate ECharts advisory,
    below the configured high-severity failure gate;
  - full public-disabled Playwright: **13 passed, 1 expected skip**.
- `git diff --check`: passed before the final handoff update.

### Gate and exact next starting point

N3 gate: **PASS**. All 20 strata are directly visible/reachable; scenario order
is A/C/B/D; the D-B/D-C/D-A implementation is unchanged; the public deployment
still blocks the new private API; and four screenshots prove the reviewer path.

Start N4 from this branch by enumerating every f2v3 registry figure and mapping
each intended interactive twin (or documented non-applicable entry) in the
parity manifest. Do not deploy or change infrastructure.

Stop honored: no deployment or infrastructure changes; no push or pull request.

## Session N2 — Clean, reviewable Atlas release branch

- Date: July 8, 2026
- Source branch/worktree: `feature/research-atlas` at
  `/Users/cch322/Developer`.
- Candidate branch/worktree: `codex/atlas-release-candidate` at
  `/Users/cch322/Developer-atlas-release`.
- Base: fetched `origin/main` at
  `c0fb5cb05f981fe7886261d2c5c2f5be30fa741d`.
- Goal: reconcile the six `origin/main` commits and extract the reviewed
  ReplocX/Atlas release without changing the source mixed index or copying
  private canonical assets into Git.

### Source inventory and preservation

The source worktree began and ended N2 with 621 status entries: 592 staged
paths, 36 unstaged paths, and 27 untracked files. The staged set includes 528
`replocx_paper_workspace` files and 14 `x_growth_automation` files. N2 did not
reset, unstage, commit, rebase, or otherwise rewrite it.

### What changed in the clean worktree

- Fetched `origin` and created `codex/atlas-release-candidate` directly from
  current `origin/main`.
- Restored the reviewed React/API/pipeline foundation required by Atlas, then
  transferred W0 contracts, W1 results APIs, W2 UI/browser coverage, W3/W3.5
  equity/export/provenance work, and W4 private-boundary records.
- Excluded `data/atlas`, `pipeline/out`, canonical f2v3 assets and sidecars,
  secrets, the paper workspace/font cache, X-growth automation, and unrelated
  mixed-index presentation/generated files.
- Changed `.gitignore`, CI, and `scripts/verify_all.sh` so real
  `pipeline/out` data remains external and verification validates regenerated
  fixture outputs instead of requiring a committed national dataset.
- Added the complete review scope, exclusions, reconciliation notes, evidence,
  and seven-commit proposal in `docs/atlas/N2_RELEASE_MANIFEST.md`.

### Verification (clean worktree, July 8, 2026)

- Branch base check: `HEAD == merge-base == origin/main` at `c0fb5cb`; ahead
  0, behind 0 before commits.
- `scripts/verify_all.sh`: **all checks passed**.
  - fixture pipeline and validation passed;
  - bundled-demo suite: 120 tests with 4 expected output-fixture skips;
  - regenerated-output suite: 120 tests with no skips;
  - ruff, black, mypy, API/security contract, and backend dependency audit
    passed;
  - coverage: 72%;
  - frontend: typecheck/build passed, lint 0 errors/3 existing warnings, 50
    tests passed;
  - the configured high-severity npm audit gate passed; one known moderate
    ECharts advisory remains;
  - full public-disabled Playwright matrix: 13 passed, 1 expected skip.
- `.venv/bin/python scripts/check_atlas_release.py`: **PASS** against the
  external canonical roots.
  - 720 cells, A/C/B/D, R9 PASS, `f2v3_final`;
  - equity READY with 4/4 layers and 20 records;
  - auth and public-disable gates passed;
  - 43 public runtime files checked against 79 canonical names with zero
    collisions.
- Enabled private-Atlas Playwright: **1 passed, 1 expected skip**.
- `git diff --check`: **PASS**. N2 made the synthetic demo generator emit LF
  line endings and the focused demo/scoring/project regression rerun passed
  16/16.
- Forbidden-path and secret scans returned no release-candidate match.

### Gate and exact next starting point

N2 gate: **PASS, pending owner approval of the manifest and proposed commit
series**. The clean candidate has the current-main base, no unrelated paper,
font-cache, or X-growth files, no private canonical result/figure assets, and a
passing full verification matrix.

Stop honored: no staging for commit, commit, push, pull request, infrastructure
change, or deployment was performed. Review
`docs/atlas/N2_RELEASE_MANIFEST.md`; after explicit approval, create the logical
commit series. Then begin N3's full 20-stratum pivot on the clean branch.

## Session 17 / N1 — W4 local release-candidate closeout

- Date: July 8, 2026
- Branch: `feature/research-atlas`.
- Goal: make the W4 record truthful, record the selected release path, remove
  the ambiguous certified-Atlas `DEMO` presentation, and rerun every local N1
  gate without committing, rebasing, pushing, creating infrastructure, or
  deploying.
- Working tree note: the repository remains intentionally mixed and broadly
  dirty. This session touched only N1 release records, the global data-mode
  badge and focused tests, Atlas browser evidence, and this handoff. It did not
  reset, unstage, or revert unrelated user work.

### Owner decision recorded

The selected path is `A2 + B1 + C1 + D1`:

- A2: complete the full 20-stratum climate-by-urbanicity pivot and parity gates
  for every interactive figure before the first live release.
- B1: deploy on an approved organization-controlled VM using Docker Compose and
  Caddy.
- C1: retain two independent gates: browser-facing HTTP Basic auth plus the app
  token.
- D1: build a clean Atlas-only release series from updated `origin/main` in a
  separate worktree; do not publish the current mixed index.

### What changed

- Updated `docs/DEPLOYMENT_RECORD.md` to local W4 PASS / live pending and made
  the selected VM/Compose/Caddy path authoritative over the older Render
  alternative.
- Updated `CHANGELOG.md` from the superseded 540-cell A/B/C scaffold state to
  the certified 720-cell A/C/B/D tier, R9 PASS, `f2v3_final`, and the
  sidecar-backed 4/4 READY equity profile.
- Refreshed the prompt pack opening readiness note so W3.5B, Session 17, and
  `A2+B1+C1+D1` are authoritative. Historical W0-W4 prompt text remains as
  execution history.
- Updated `docs/atlas/W4_RELEASE_AUDIT.md` with measured local evidence and the
  remaining real-container/live-host gap.
- Changed `DataModeBadge` so an Atlas-enabled environment displays two explicit
  lines: `SELECTION DEMO` (or production) and `ATLAS CERTIFIED`. Public
  Atlas-disabled mode retains the ordinary selection-data `DEMO` badge.
- Added focused unit and Playwright assertions for the two-tier badge.
- Recaptured and visually inspected:
  - `docs/atlas/screenshots/2026-07-08/atlas-enabled-desktop-overview.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-enabled-tablet-results.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-enabled-mobile-d-contrasts.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-w4-equity-ready.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-w4-exports-provenance.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-disabled-public-demo.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-w4-contact-sheet.png`

### Verification (local, July 8, 2026)

- Focused badge test: 4/4 passed. Frontend typecheck and production build
  passed.
- Targeted Atlas Playwright, enabled mode: **1 passed, 1 skipped**. It verifies
  the `SELECTION DEMO` / `ATLAS CERTIFIED` distinction, A/C/B/D story spine,
  Fig02 source rendering, threshold controls, D contrasts, equity READY, and
  exports/provenance while recapturing desktop/tablet/mobile screenshots.
- Targeted Atlas Playwright, disabled mode: **1 passed, 1 skipped**. The public
  deployment continues to show the Atlas-disabled panel.
- `scripts/check_atlas_release.py`: **PASS**.
  - proxy blocks unauthenticated Atlas frontend/results/equity;
  - Basic auth alone is insufficient for APIs; Basic plus app token returns 200;
  - certified evidence is 720 cells, A/C/B/D, R9 PASS, `f2v3_final`;
  - equity is READY with 4/4 layers and 20 records;
  - public Atlas routes return 404/disabled;
  - public runtime scan covered 117 files against 79 canonical asset/table
    names with zero collisions.
- `scripts/verify_all.sh`: **all checks passed**.
  - fixture pipeline and committed national validation passed;
  - backend suites: **120 passed** with bundled demo data and **120 passed**
    with fixture pipeline outputs;
  - ruff, black, mypy, release contract, and backend dependency audit passed;
  - coverage: **72%**;
  - frontend: typecheck and build passed, lint had 0 errors/3 existing warnings,
    and **50 tests passed**;
  - frontend production audit retained one known moderate ECharts advisory,
    below the configured high-severity failure gate;
  - full Playwright suite: **13 passed, 1 expected skip**.
- `git diff --check`: pass.
- Current release-note grep has no stale 540-cell, A/B/C-only, or all-equity
  `REVIEW REQUIRED` claim. Remaining legacy terms occur only in migration
  instructions or historical records.

### Remaining boundary and exact next starting point

- W4 is a fully documented **local release candidate PASS**. It is not a live
  private release and has no owner sign-off.
- Docker is not installed in this environment. The committed Compose/Caddy
  boundary and a built image still require a real container/image-layer test on
  the approved VM or an equivalent Docker-capable host before live sign-off.
- Start Session N2 exactly as defined in
  `ATLAS_POST_W4_SESSION_PLAN_2026-07-08.md`: preserve this worktree unchanged,
  fetch `origin`, create a clean `codex/` worktree/branch from updated
  `origin/main`, transfer only reviewed Atlas release files in logical groups,
  run the complete matrix, and produce the manifest/proposed commit series.
- Stop honored: no commit, rebase, push, infrastructure creation, or live
  deployment was performed.

## Session W3.5B — Research Atlas full certified equity profile

- Date: July 8, 2026
- Branch: `feature/research-atlas`.
- Start condition: The prior W3.5 entry had ACS income/poverty certified
  READY while SVI, DOE LEAD, and heat-vulnerability remained
  `REVIEW REQUIRED`. The user granted approval to acquire official sources,
  build the catchment crosswalk, regenerate the canonical equity profile, and
  rerun Atlas gates.
- Working tree note: the repo was already broadly dirty with prior Atlas and
  generated changes. This session added
  `scripts/build_atlas_equity_profile.py`, updated this append-only handoff,
  and wrote certified external artifacts under the canonical OneDrive data
  root. No unrelated repo changes were reverted.

### What changed

- Downloaded and verified official source files, then materialized certified
  raw/crosswalk/provenance artifacts under:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/equity_sources/`
- Added the reproducible builder:
  `scripts/build_atlas_equity_profile.py`
  The script reads official source files and the existing ACS certified
  profile fields only; it does not use scaffold/demo equity values.
- Regenerated:
  - `equity_profile.csv`: 20 rows, 39 columns,
    SHA-256 `911b04d576323df1f5a39958871390aff2f82b6843641687a23bd298b69ea43c`
  - `equity_profile.csv.prov.json`: sidecar SHA-256
    `ba3a62be116b0d331901f0bb193af2aecd303bf59d3a00931243c13f0b3c5c98`
  - `equity_sources/crosswalks/catchment_equity_crosswalk.csv`: 22,770 rows,
    SHA-256 `e2301d3bc58e8bff40052468eb3b96a05d595dfe7ac4efba9500923cd5472942`
  - `equity_sources/crosswalks/catchment_equity_crosswalk.csv.prov.json`:
    SHA-256 `7edf86b3cfcb4920135785a4f11b3c932201ad6c84a92d3faabb1f7ff1282780`
  - `equity_sources/raw/source_manifest.json`: SHA-256
    `8d5d77d1c4586ca52155cdce44591f672de5c76257185a8aedc3af1d23700369`
- Official source inputs recorded in the manifest:
  - CDC/ATSDR SVI 2022 U.S. tract CSV:
    `https://svi.cdc.gov/Documents/Data/2022/csv/states/SVI_2022_US.csv`,
    SHA-256 `58df3dca3d4194879ffbd4b5e753eae48676ef691da1fa669f5fc40c3f79bc6a`.
  - Census 2023 CBSA-to-county delineation workbook:
    `https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx`,
    SHA-256 `952c4b1e78acbb54e6ec9412434b7602fedacbf021736351a63c181bdb753629`.
  - Census 2020 ZCTA-to-county relationship file:
    `https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt`,
    SHA-256 `3ed41278d637dc249e0323306f68be8a6c234e3090f4de88ef328dee71aeaaaf`.
  - CDC/ATSDR Heat & Health Index 2024 data zip:
    `https://www.atsdr.cdc.gov/place-health/media/files/2024/08/HHI_Data.zip`,
    SHA-256 `5a5d37be873a741f2096c93a6793688496b063f3dd1ad45c25cf4d420767e4f1`.
  - DOE LEAD Tool 2022 Update, OEDI dataset
    `https://data.openei.org/submissions/6219`, DOI
    `https://doi.org/10.25984/2504170`; dictionary URL
    `https://data.openei.org/files/6219/Data%20Dictionary%202022.xlsx`,
    SHA-256 `8bedcb64e1356eaa981c63f9332988a623d92fade5a163f6c8063917f1ac5f23`.
    The 20 required state archives are recorded in
    `equity_sources/raw/lead/lead_state_zip_manifest.csv`, SHA-256
    `863785533bfaddb1da5c78c46b653ced49f6e50af60b768c139bb64e09f36379`.
    States: AZ, CA, DC, DE, FL, IL, IN, LA, MD, ME, MI, NJ, NY, PA, SC,
    TN, TX, VA, WA, WV.
  - Existing ACS Census Reporter payload from W3.5:
    `https://api.censusreporter.org/`, ACS 2024 5-year (2020-2024), tables
    `B19013` and `B17001`, SHA-256
    `8e537e8b433eba3a9daf983ca2146daf1ed30abc13dab481c8917b936cd5eac6`.

### Rollup and uncertainty method

- ACS income/poverty: direct CBSA/county geographies from Census Reporter;
  median-income MOE, poverty-universe MOE, and poverty-count MOE retained;
  derived poverty-rate MOE was not recomputed.
- SVI: CDC/ATSDR 2022 tract `RPL_THEMES` percentile, population-weighted by
  `E_TOTPOP`; tract-to-county via GEOID prefix; CBSA county membership from
  Census 2023 list1.
- DOE LEAD: official 2022 AMI county CSV rows extracted from state archives;
  catchment energy burden equals summed energy expenditures divided by summed
  household income, expressed as percent. CBSA values are county-rollup
  proxies.
- Heat vulnerability: CDC/ATSDR HHI 2024 `OVERALL_RANK` at ZCTA level,
  weighted by HHI population and Census 2020 ZCTA/county land-area allocation,
  then rolled to selected catchments. This is marked `Modeled` because ZCTAs
  approximate ZIP geography and the catchment rollup is modeled.

### Layer statuses

- `cdc_svi`: `READY`, badge `Proxy`.
- `acs_income_poverty`: `READY`, badge `Direct`.
- `doe_lead_energy_burden`: `READY`, badge `Proxy`.
- `heat_vulnerability`: `READY`, badge `Modeled`.
- Sidecar layer status summary reports all four layers READY, 20 source
  records, and `sha_match: true`.

### Verification (local, July 8, 2026)

- Builder:
  `.venv/bin/python scripts/build_atlas_equity_profile.py`: pass.
  Measured output: 20 profile rows, 22,770 crosswalk rows, 20 LEAD state
  archives, profile SHA-256
  `911b04d576323df1f5a39958871390aff2f82b6843641687a23bd298b69ea43c`.
- Canonical CSV/sidecar completeness probe:
  all value fields populated for all 20 rows.
  - `svi_percentile`: min `0.300773`, max `0.642083`
  - `acs_median_hh_income`: min `55406`, max `126684`
  - `acs_poverty_rate`: min `0.076536`, max `0.226619`
  - `doe_lead_energy_burden_pct`: min `1.213551`, max `3.69465`
  - `heat_vuln_index`: min `0.269658`, max `0.928028`
- Required Atlas API smoke against canonical roots:
  `RLE_ENABLE_ATLAS=1`, canonical data root, and canonical f2v3 figure root:
  - `/api/equity/profiles`: `profiles_status READY`, 20 profiles; layer
    statuses `cdc_svi READY`, `acs_income_poverty READY`,
    `doe_lead_energy_burden READY`, `heat_vulnerability READY`.
  - `/api/equity/scenario-cross?scenario=D&dimension=climate`: 5 rows;
    preferred vulnerability layer `cdc_svi READY`.
  - `/api/results/export-view?view=equity-profiles`: view `equity-profiles`,
    20 rows, provenance sidecar present.
  - `/api/results/provenance`: `equity_verification.status READY`,
    `verified_layer_count 4`; `equity-profiles` export status `READY` and
    sidecar present.
- Targeted Atlas contract tests:
  `.venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v`:
  **30 passed**.
- Static/format gates for the new builder:
  `.venv/bin/python -m black --check scripts/build_atlas_equity_profile.py`:
  pass.
  `.venv/bin/python -m ruff check scripts/build_atlas_equity_profile.py`:
  pass.
  `.venv/bin/python -m mypy scripts/build_atlas_equity_profile.py`: pass.
- `git diff --check`: pass.
- One read-only escalated provenance-shape probe was rejected by the approval
  reviewer due the session usage limit; the same read-only check was rerun
  without elevation and succeeded. No verification gate remains blocked.

### Exact next starting point

- W4 can proceed with all four equity layers READY in the private canonical
  data root.
- Treat `equity_profile.csv`, `equity_profile.csv.prov.json`,
  `equity_sources/raw/source_manifest.json`, and
  `equity_sources/crosswalks/catchment_equity_crosswalk.csv.prov.json` as the
  source of truth for W4 release notes and smoke tests.
- Public demo gating remains unchanged: real Atlas results and equity data stay
  private behind `RLE_ENABLE_ATLAS`.

## Session W3.5 — Research Atlas partial certified equity profile

- Date: July 8, 2026
- Branch: `feature/research-atlas`.
- Start condition: Sessions 13-16 accepted as source of truth. Current branch
  confirmed as `feature/research-atlas`; the worktree was already dirty with
  prior Atlas/generated changes, so this session touched only the certified
  external equity artifact, thin FastAPI Atlas export wrappers, Atlas route
  coverage, and this append-only handoff entry.

### What changed

- Materialized a sidecar-backed equity profile at the certified Atlas data root:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/equity_profile.csv`
- Wrote the required provenance sidecar beside it:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/equity_profile.csv.prov.json`
- The profile contains 20 representative catchment rows and 39 columns.
- Source inputs:
  - `pipeline/out/selected_locations.csv` for the 20 selected catchment
    identifiers, labels, climate regions, and urbanicity groups.
  - Census Reporter API payload for ACS table `B19013` median household income
    and `B17001` poverty status. The API resolved to release
    `acs2024_5yr`, `ACS 2024 5-year`, years `2020-2024`.
- Geography join method:
  - CBSA catchments map directly to Census Reporter geoid
    `31000US{catchment_code}`.
  - County catchments map directly to Census Reporter geoid
    `05000US{catchment_code}`.
  - No tract-to-catchment ACS aggregation or spatial interpolation was
    performed.
- ACS calculations and uncertainty handling:
  - `acs_median_hh_income` = `B19013001` estimate.
  - `acs_poverty_rate` = `B17001002 / B17001001`.
  - Median-income MOE, poverty-universe MOE, and below-poverty-count MOE are
    retained. A derived poverty-rate MOE was not computed.
- Layer statuses:
  - `acs_income_poverty`: `READY`, badge `Direct`, source/vintage and join
    uncertainty populated for all 20 catchments.
  - `cdc_svi`: `REVIEW REQUIRED`; no verified SVI source file or
    tract/county-to-catchment rollup was available.
  - `doe_lead_energy_burden`: `REVIEW REQUIRED`; no verified DOE LEAD source
    file or catchment geography join was available.
  - `heat_vulnerability`: `REVIEW REQUIRED`; no certified source/model and
    catchment rollup were available.
- No values from checked-in scaffold `data/atlas/equity_profile.csv` were used.
- While verifying the requested `/api/v1/results/export-view` smoke surface, a
  W4-facing parity gap was found: `backend/atlas_routes.py` and `backend.server`
  already supported `/api/results/exports`, `/api/results/export-view`, and
  `/api/results/figure-bundle`, but `backend/fastapi_app.py` did not expose the
  matching managed-FastAPI wrappers. Added those thin wrappers and route
  assertions in `tests/test_atlas.py`.

### Verification (local, July 8, 2026)

- File/sidecar gate:
  `python3 - <<'PY' ...` over the canonical root:
  `equity_profile.csv` exists, sidecar exists, 20 rows, 39 fields,
  CSV SHA-256 matches sidecar `verified_sha256`, `sha_match: true`.
  CSV SHA-256:
  `a6a90510b62eedd9efface3adbdc648d7fb83bb2a0229f91fc1f75dd3644dae6`.
- Canonical equity API smoke:
  `RLE_ENABLE_ATLAS=1 .venv/bin/python - <<'PY' ...`:
  - `/api/equity/profiles`: 20 catchments, `catchment_profile_status: READY`,
    source CSV and sidecar resolve to the canonical equity files.
  - Layer statuses:
    `cdc_svi=REVIEW REQUIRED`, `acs_income_poverty=READY`,
    `doe_lead_energy_burden=REVIEW REQUIRED`,
    `heat_vulnerability=REVIEW REQUIRED`.
  - `/api/equity/scenario-cross?scenario=D&dimension=climate`: 5 climate rows;
    vulnerability layer `acs_income_poverty`, status `READY`.
  - `/api/results/export-view?view=equity-profiles`: `csv_export.status:
    READY`, 20 rows, source CSV is the canonical equity profile.
  - `/api/results/provenance`: `equity_verification.status: READY`,
    `verified_layer_count: 1`, `source_record_count: 20`, join method reports
    the direct Census Reporter ACS geography mapping.
- Managed FastAPI wrapper smoke:
  `RLE_ENABLE_ATLAS=1 .venv/bin/python - <<'PY' ...` against
  `backend.fastapi_app` functions:
  profiles 20 rows; layer statuses
  `cdc_svi=REVIEW REQUIRED`, `acs_income_poverty=READY`,
  `doe_lead_energy_burden=REVIEW REQUIRED`,
  `heat_vulnerability=REVIEW REQUIRED`; scenario-cross 5 rows with
  vulnerability layer `acs_income_poverty READY`; equity export `READY` with 20
  rows; provenance `READY` with one verified layer.
- Targeted Atlas contract tests:
  `.venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v`:
  **30 passed**.
- Static/format gates on touched Python files:
  `.venv/bin/python -m black --check backend/fastapi_app.py tests/test_atlas.py`:
  pass.
  `.venv/bin/python -m ruff check backend/fastapi_app.py tests/test_atlas.py`:
  pass.
  `.venv/bin/python -m mypy backend/fastapi_app.py tests/test_atlas.py`: pass.
- `git diff --check`: pass.

### Exact next starting point

- W4 can proceed with an honest partial equity state: ACS income/poverty is
  certified READY; SVI, DOE LEAD, and heat-vulnerability remain explicitly
  `REVIEW REQUIRED`.
- If the owner wants all equity layers READY before private release, the next
  session must supply verified SVI, DOE LEAD, and/or heat-vulnerability source
  files plus documented catchment crosswalk/rollup sidecars. Do not infer or
  backfill those layers from scaffold/demo values.

## Session 16 — W3 Research Atlas equity overlays, exports, provenance

- Date: July 8, 2026
- Branch: `feature/research-atlas`.
- Start condition: W2 accepted as green from Session 15. Current branch check
  before edits confirmed `feature/research-atlas`; local comparison to
  `origin/main` remains 25 ahead / 6 behind. As in W1/W2, this was treated as
  current enough for Atlas work but still needs reconciliation before
  publication.
- Working tree was already dirty with prior Atlas work and unrelated generated
  files. This session touched only Atlas backend/frontend/test files plus this
  handoff.

### What changed

- Extended `backend/atlas_service.py` W3 contracts:
  - `/api/equity/profiles` now emits layer records with source/vintage,
    proxy/direct/modeled badge, geography level, join-uncertainty note, ready
    vs `REVIEW REQUIRED` status, and exact missing-source path when no verified
    equity profile exists.
  - `/api/equity/scenario-cross` supports A/C/B/D, rejects invalid scenario
    codes, and includes a D-minus-selected scenario overheating-exposure
    contrast for the selected dimension. It remains descriptive and makes no
    causal claims.
  - Added `/api/results/exports`, `/api/results/export-view`, and
    `/api/results/figure-bundle` for per-view CSV descriptors, figure source
    CSVs, PNG/PDF/SVG f2v3 asset links, citation text, and provenance sidecar
    links.
  - Provenance now includes certified tier id, canonical data root, R9 report,
    f2v3 gate report, f2v3 registry/caption metadata, equity source notes, and
    export view descriptors.
- Updated shared Atlas dispatch in `backend/atlas_routes.py`.
- Updated frontend API/types/hooks and the Atlas Equity, Exports, Provenance
  views to render layer badges, source/vintage chips, join uncertainty,
  per-view export CSV status, f2v3 asset paths, citations, R9/f2v3 gate status,
  and equity source notes.
- Expanded `tests/test_atlas.py` and `frontend/src/routes/atlas/atlas.test.tsx`
  for W3 contracts and UI rendering.

### Equity verification result

- Canonical data root reached:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen`
- Canonical figure root reached:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final`
- Certified Atlas data root contains only `annual/`, `seasonal/`, `metadata/`,
  and `audit/`. No sidecar-backed SVI/ACS/DOE LEAD/catchment equity profile was
  present.
- Exact missing verified join file:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/equity_profile.csv`
- Canonical W3 smoke status:
  - Scenario order: `('A', 'C', 'B', 'D')`
  - Equity profile status: `REVIEW REQUIRED`
  - Equity layers: `cdc_svi`, `acs_income_poverty`,
    `doe_lead_energy_burden`, and `heat_vulnerability` all
    `REVIEW REQUIRED`
  - Scenario D cross rows: 5 climate rows; vulnerability layer status
    `REVIEW REQUIRED`
  - Export statuses: results `READY`, D comparisons `READY`, equity
    `REVIEW REQUIRED`
  - Fig02 bundle: PNG/PDF/SVG assets all resolved under `f2v3_final`
  - f2v3 gate report status: `PASS`; that gate JSON has no `.prov.json`
    sidecar in the canonical folder, so provenance reports its sidecar as
    `null` while still requiring sidecars for certified CSVs and figure assets.

### Source/vintage notes now exposed

- CDC/ATSDR SVI: documented as SVI 2022 census-tract percentile fields
  (`RPL_THEMES` / `RPL_THEME1-4`), but not marked ready because no verified
  tract-to-catchment crosswalk/profile exists locally.
- ACS income/poverty: documented as ACS 2019-2023 5-year estimates with MOE
  handling required when supplied, but not marked ready because no verified
  catchment aggregation/profile exists locally.
- DOE LEAD energy burden: source/vintage and catchment geography join are not
  verified in this checkout, so the layer remains `REVIEW REQUIRED`.
- Heat-health vulnerability: modeled proxy source and catchment rollup are not
  verified, so the layer remains `REVIEW REQUIRED`.

### Verification (local, July 8, 2026)

- `.venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v`:
  **30 passed**.
- Full backend discovery:
  `.venv/bin/python -m unittest discover -s tests -v` ran in the sandbox and
  failed only at `test_phase3.PythonClientEndToEndTests.setUpClass` because the
  sandbox blocks binding `127.0.0.1` (`PermissionError: [Errno 1] Operation not
  permitted`). The required escalated rerun was requested, but the environment
  rejected it due a usage-limit review, so a full backend green rerun remains
  unverified this session.
- Backend static/format gates on touched backend/test files:
  `black --check`, `ruff check`, and
  `mypy backend/atlas_service.py tests/test_atlas.py`: all passed.
- Frontend TypeScript:
  `/Users/cch322/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node frontend/node_modules/typescript/bin/tsc -b frontend`:
  pass.
- Frontend unit tests:
  `/Users/cch322/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/vitest/vitest.mjs run`
  from `frontend/`: **49 passed** in 11 files. Existing React Router
  future-flag warnings and the pre-existing `act(...)` warning remain warnings.
- Frontend production build:
  `/Users/cch322/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/vite/bin/vite.js build`
  from `frontend/`: pass. Latest built assets include
  `index-Chk6AVZ3.css`, `index-BGjNtHSZ.js`, `vendor-BNz3Y5EQ.js`,
  `echarts-6n07c7J1.js`, and `maplibre-DgYawZTD.js`.
- Canonical W3 export smoke:
  `RLE_ENABLE_ATLAS=1 .venv/bin/python -c ...`: pass for one results view,
  one D comparison, one equity view, and one Fig02 asset bundle; measured values
  listed above.
- Guardrail greps:
  - Served Atlas paths:
    `rg -n "f2v2_final|f1v2|F1v2" backend/atlas_service.py backend/atlas_routes.py frontend/src/lib/api.ts frontend/src/lib/types.ts frontend/src/routes/atlas tests/e2e/atlas.spec.ts`
    returned no matches.
  - Served Atlas paths:
    `rg -n '\("A",\s*"B",\s*"C"\)|\["A",\s*"B",\s*"C"\]|540-cell|540 cells|replocx_tmy3/' ...`
    returned no matches.
  - Canonical terminology grep for `heat hours` / `humidity hours` returned no
    matches.
  - `git diff --check`: pass.

### Exact next starting point

- If the owner accepts W3 with no verified equity join available, start W4 from
  the current W3 contracts and private-boundary/leak tests.
- If W3 needs ready equity overlays before W4, first materialize a sidecar-backed
  `equity_profile.csv` under the certified data root (or set
  `RLE_ATLAS_DATA_DIR` to a read-only certified copy containing it). Required
  fields are values plus source/vintage, proxy badge, and join-uncertainty notes
  for each layer; otherwise the API will correctly keep the layer
  `REVIEW REQUIRED`.

## Session 15 — W2 Research Atlas frontend/story spine

- Date: July 8, 2026
- Branch: `feature/research-atlas`.
- Start condition: W1 accepted as green from Session 14. Current branch is still
  local-only/no upstream in this checkout; no attempt was made to reconcile the
  six divergent `origin/main` commits during W2.
- Canonical roots were reachable before edits:
  - Data:
    `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen`
  - Figures:
    `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final`

### What changed

- Upgraded Atlas frontend routing into the W2 story spine: Introduction, How
  locations were selected, Results A/C/B/D, Sealed-passive D contrasts, Equity
  context, Methods, and Exports/provenance.
- Migrated UI state, selectors, legends, route targets, and chart colors to the
  A/C/B/D scenario contract with the canonical palette and dictionary-driven
  descriptive labels. Scenario C renders as `AC 2-8pm + NV other hours`; D
  renders as `No AC or NV`.
- Added pivot-first landing behavior using the W1 `by-stratum` endpoint for the
  default climate-stratum x scenario overview, plus MapLibre drill-down to
  `/atlas/sites/<site_id>?scenario=<A|C|B|D>&tier=<annual|seasonal>&metric=<endpoint>`.
- Reworked metric UX so p95 and exposure-hour metrics lead. Mean operative
  temperature views render a paired extreme metric, and threshold selectors echo
  the threshold in chart subtitles and export/provenance metadata.
- Added the sealed-passive D panel opening on D-B, with D-C and D-A tabs. Raw D
  values remain behind an `Explore raw D values` affordance.
- Integrated f2v3 registry source tables through a new read-only backend
  `figure-source` endpoint and frontend query hook. Interactive twins read
  registry `source_csv` rows; Fig19 is shown only under Methods/supplementary,
  not the main results grid.
- Added Atlas e2e coverage for enabled private mode and disabled public-demo
  mode. Stable QA screenshots were saved to:
  - `docs/atlas/screenshots/2026-07-08/atlas-enabled-desktop-overview.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-enabled-tablet-results.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-enabled-mobile-d-contrasts.png`
  - `docs/atlas/screenshots/2026-07-08/atlas-disabled-public-demo.png`

### Verification (local, July 8, 2026)

- `.venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v`:
  **25 passed**.
- Frontend TypeScript:
  `/Users/cch322/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node frontend/node_modules/typescript/bin/tsc -b frontend`:
  pass.
- Frontend unit tests:
  `/Users/cch322/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/vitest/vitest.mjs run`
  from `frontend/`: **46 passed** in 11 files. Existing React Router future-flag
  warnings and one pre-existing `act(...)` warning remain warnings only.
- Frontend production build:
  `/Users/cch322/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node node_modules/vite/bin/vite.js build`
  from `frontend/`: pass. Latest built assets include
  `index-Chk6AVZ3.css`, `index-DkBtzA9N.js`, `vendor-BNz3Y5EQ.js`,
  `echarts-6n07c7J1.js`, and `maplibre-DgYawZTD.js`.
- Playwright Atlas e2e, enabled private mode:
  `RLE_ENABLE_ATLAS=1 ... node_modules/@playwright/test/cli.js test tests/e2e/atlas.spec.ts --project desktop-chromium`:
  **1 passed, 1 skipped**. This run verifies A/C/B/D labels, Fig02 chart
  rendering, Results threshold UI, D-B/D-C/D-A tabs, and desktop/tablet/mobile
  screenshots. Escalation was required because the sandbox blocks local server
  binding.
- Playwright Atlas e2e, disabled public-demo mode:
  `... node_modules/@playwright/test/cli.js test tests/e2e/atlas.spec.ts --project desktop-chromium`:
  **1 passed, 1 skipped**. Escalation was required for the same local-bind reason.
- Formatting/static backend gates on touched backend/test files:
  `black --check`, `ruff check`, and `mypy backend/atlas_service.py tests/test_atlas.py`
  all passed.
- Parity gate: `frontend/src/routes/atlas/atlas.test.tsx` computes Fig02 ECharts
  source values against the f2v3 registry `source_csv`; measured `max|diff| = 0`.
- Guardrail greps:
  - `rg -n '\bheat hours\b|\bhumidity hours\b' frontend/src/routes/atlas frontend/src/lib frontend/src/App.tsx`
    returned no matches.
  - `rg -n '(f2v2_final|f1v2|F1v2|\["A",\s*"B",\s*"C"\]|\("A",\s*"B",\s*"C"\))' ...`
    over Atlas frontend, served Atlas backend wrappers, and Atlas e2e returned no
    matches.
- Visual QA: desktop, tablet, and mobile screenshots were inspected. No
  label/chart overlap was observed; the mobile D screenshot scrolls to the D-B
  chart so chart labels are visible above the fixed bottom nav.

### Notes and exact next starting point

- W2 consumes W1 API payloads in the routed UI: health/provenance,
  scenario-dictionary, overview, scenario-summary, by-stratum, D comparisons,
  figure-source, dashboard, and geometry. Unit tests use fixture mocks only as
  test doubles.
- The W2 landing does not locally recompute the unavailable 20
  climate-by-urbanicity stratum aggregate. It uses the W1 `by-stratum` climate
  pivot as the default overview and keeps drill-down on the existing site map.
  If the next session needs the full 20-stratum national pivot, add a certified
  W1/W3 API endpoint rather than aggregating canonical CSVs in the browser.
- W3 was not started. Next session should begin from the remaining API/content
  gap above, then broaden parity beyond Fig02 if every interactive f2v3 twin is
  expected to have a formal max-diff gate.

## Session 14 — W1 Research Atlas backend migration

- Date: July 8, 2026
- Branch: `feature/research-atlas`.
- Branch/currentness check before edits: local branch has no upstream and
  `git merge-base --is-ancestor origin/main HEAD` returned nonzero. `origin/main`
  has six divergent selection/marketing commits; none touch
  `backend/atlas_service.py`, `backend/atlas_routes.py`, or Atlas tests. Current
  enough for W1 backend API work, but reconcile before publication.
- W0 status: unblocked and green per Session 13 handoff. Certified canonical
  roots were reachable before edits.

### What changed

- Rebuilt `backend/atlas_service.py` as a read-only canonical tier reader for
  `replocx_tmy3_wallfix_4scen`, defaulting to the recorded OneDrive canonical
  data root when `RLE_ATLAS_DATA_DIR` is unset and resolving f2v3 figures from
  the recorded figure root or a fixture `figures/f2v3_final` folder.
- The service now discovers certified CSVs by canonical filename stems, requires
  `.prov.json` sidecars, validates the R9 audit report, rejects the legacy
  bundled Atlas scaffold, loads the scenario dictionary from canonical metadata,
  and validates scenario order as `A`, `C`, `B`, `D`.
- Upgraded endpoint payloads for scenario dictionary, overview,
  scenario-summary, by-stratum, D comparisons, differential, figures, Scenario C
  intervention, provenance, and equity placeholders. Cooling-seasons and
  sensitivity now report certified-unavailable when no four-scenario sidecar is
  present, rather than reading legacy files.
- Expanded `tests/test_atlas.py` with an explicit canonical-style fixture tree
  generated in temp dirs. Tests cover disabled-by-default gating, legacy failure,
  `/api` and `/api/v1` route mounting, A/C/B/D annual and seasonal summaries,
  every by-stratum dimension, D-B/D-C/D-A story comparisons, R9/f2v3 provenance,
  public selection routes with Atlas disabled, and three-scenario fixture
  rejection.
- Updated `frontend/src/lib/types.ts` to match the richer Atlas payloads and fix
  the overview `scenario_summary` shape.

### Canonical smoke

- Data root:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen`
- Figure root:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final`
- `RLE_ENABLE_ATLAS=1` canonical smoke result:
  scenario order `['A', 'C', 'B', 'D']`; annual summary row count `4`;
  seasonal by-stratum scenario order `['A', 'C', 'B', 'D']`; provenance
  `replocx_tmy3_wallfix_4scen / 720 / PASS / f2v3_final`; D story order
  `['D-B', 'D-C', 'D-A']`.

### Verification (local, July 8, 2026)

- `.venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v`:
  **24 passed**. Includes negative tests for missing-D and A/B/C-only contract
  failures.
- `.venv/bin/python -m unittest discover -s tests -v`: initial sandbox run
  failed only because `test_phase3.PythonClientEndToEndTests` could not bind
  `127.0.0.1` (`PermissionError: [Errno 1] Operation not permitted`). Escalated
  rerun: **112 passed**.
- `.venv/bin/python -m coverage run -m unittest discover -s tests`: **112
  passed** under escalation for the same local-bind reason.
- `.venv/bin/python -m coverage report`: **71% total coverage**.
- `.venv/bin/python -m black --check backend/atlas_service.py tests/test_atlas.py`:
  pass.
- `.venv/bin/python -m ruff check backend/atlas_service.py tests/test_atlas.py`:
  pass.
- `.venv/bin/python -m mypy backend/atlas_service.py tests/test_atlas.py`: pass.
- Frontend typecheck, using bundled Node because `npm` is not on PATH:
  `/Users/cch322/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node frontend/node_modules/.bin/tsc -b frontend`:
  pass.
- `.venv/bin/python -m pip_audit -r backend/requirements.txt`: sandbox run
  failed while creating/upgrading pip-audit's temporary environment; escalated
  rerun: **No known vulnerabilities found**.
- Served-path grep proof:
  `rg -n '\("A",\s*"B",\s*"C"\)|\["A",\s*"B",\s*"C"\]|540-cell|540 cells|f2v2_final|f1v2|F1v2|replocx_tmy3/' backend/atlas_service.py backend/atlas_routes.py backend/fastapi_app.py backend/server.py frontend/src/lib/api.ts frontend/src/lib/types.ts frontend/src/routes/atlas/atlas.ts`
  returned no matches (exit 1/no output).

### Not run

- Full `scripts/verify_all.sh` and Playwright visual/e2e were not run in this W1
  session. W1 stop condition is backend API contract stability; no W2 UI work or
  browser screenshot QA was started. The touched TypeScript contract file did
  pass `tsc -b`.

### Next exact starting point

- Start W2 only after accepting this W1 API contract. The next session should
  wire the Atlas UI/story spine to these stable payloads, especially the
  D-comparison panel, metric/threshold notes, f2v3 figure registry rows, and the
  certified-unavailable cooling/sensitivity states.
- Before publication, reconcile `feature/research-atlas` with `origin/main` and
  keep the large unrelated pre-existing generated/scaffold additions out of any
  Atlas-only commit.

## Session 13 — W0 Research Atlas contract freeze (no W1)

- Date: July 8, 2026
- Branch: `feature/research-atlas`; current `HEAD` is not proven to be an
  ancestor of `origin/main` in this local checkout, so rebase/merge status should
  be checked before publication.
- Scope: W0 only for the ReplocX Research Atlas migration. Audited the legacy
  3-scenario scaffold, froze the certified 4-scenario contract, installed schema
  and fixture gates, and updated minimal backend/frontend constants so stale
  540-cell or f2v2/f1v2 assumptions fail closed. Did not start W1 data staging
  or the production reader.

### Certified source of truth

- Canonical data: `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen`
- Canonical figures: `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final`
- Smoke counts: annual scenario summary 5 lines, seasonal scenario summary
  5 lines, f2v3 registry 20 lines. Scenario order is `A`, `C`, `B`, `D`;
  certified cell count is 720.

### W0 artifacts

- Added `docs/atlas/W0_scaffold_audit.md`,
  `docs/atlas/W0_acceptance_criteria.md`, and
  `docs/atlas/W0_data_contract.md`.
- Added strict contract schema
  `docs/atlas/schemas/w0_contract_bundle.schema.json`.
- Added tiny real-derived golden fixture
  `tests/fixtures/atlas/w0/w0_contract_bundle.golden.json`.
- Added negative/positive contract tests in `tests/test_atlas_contract.py`.
- Updated Atlas service/routes, FastAPI wrappers, frontend Atlas constants/types,
  Atlas copy, and deployment notes to recognize only the certified
  `replocx_tmy3_wallfix_4scen`/f2v3/A-C-B-D contract. Enabling Atlas against
  the bundled legacy `data/atlas/replocx_tmy3` scaffold now fails loudly.

### Verification (local, July 8, 2026)

- `python -m json.tool` passed for the W0 schema and fixture.
- `.venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v`:
  **13 passed**.
- `.venv/bin/python -m black --check ...`: pass for touched backend/test files.
- `.venv/bin/python -m ruff check ...`: pass for touched backend/test files.
- Frontend Atlas typecheck and Vitest target passed using the repo/bundled Node
  runtime: `tsc -b` clean; Atlas Vitest target **passed**.
- Full `scripts/verify_all.sh` with local escalated permissions: **All checks
  passed**. Measured gates included fixture pipeline pass, committed national
  validation pass, backend unit suites **101 passed** in both bundled-demo and
  fixture-output modes, ruff/black/mypy/coverage 68%, pip-audit 0 backend
  vulnerabilities, API/security/degraded contract pass, frontend typecheck/lint/
  unit/build pass, Playwright **12 passed**. Frontend audit still reports the
  existing moderate `echarts <6.1.0` advisory; the script passes because the
  configured audit level is high.
- Targeted stale-contract grep over served Atlas code, fixtures, and W0 contract
  found only the intentional forbidden-path rule for `f2v2_final`/`f1v2`.

### Notes for the next session

- Start W1 from the W0 contract artifacts, not from the legacy scaffold. The next
  real task is to stage/read the certified 720-cell app-ready data domain and
  implement the W1 API behavior against `replocx_tmy3_wallfix_4scen`.
- The worktree contains substantial pre-existing unrelated generated/scaffold
  changes, including `data/atlas/replocx_tmy3`, `replocx_paper_workspace/`, and
  `x_growth_automation/`. Do not revert or stage them accidentally when preparing
  the W0 change set.
- A manual `RLE_ANALYSIS_DATA_DIR=pipeline/out unittest discover` against the
  committed national output still fails 4 demo-fixture-coupled assertions; this
  is the same known distinction documented in earlier handoffs. The supported
  `verify_all.sh` fixture-output leg is green.

## Session 12 — Phase 4: ReplocX Research Atlas scaffold (branch, no deploy)

- Date: July 3, 2026
- Branch: `feature/research-atlas` (off `feature/location-representation-explorer`)
- Scope: Phase 4 of the PhD completion plan — scaffold the private Research Atlas
  as modular sibling contexts on the existing ReplocX chassis, reading the
  certified ReplocX **TMY3 (Session 7, 540-cell)** results and a 20-catchment
  equity frame. No deploy; branch + local verify only.

### What shipped

- **Data domain** `data/atlas/` — compact certified CSVs copied from
  `_CANONICAL/10_DATA/replocx_tmy3` (annual/seasonal scenario + stratum
  summaries, Scenario C decomposition, cooling seasons, sensitivity), an
  `equity_profile.csv` for the 20 catchments (cooling-season fields populated;
  SVI/ACS/LEAD/heat-vuln blank + `REVIEW REQUIRED`), and `atlas_metadata.json`
  with per-file SHA-256 checksums, scenario semantics, and the tier wall.
- **Backend** — `backend/atlas_service.py` (lazy, flag-gated `AtlasService`) and
  `backend/atlas_routes.py` (shared dispatch), wired into `server.py` and
  `fastapi_app.py` as `/api/v1/results/*` and `/api/v1/equity/*`. Gated by
  `RLE_ENABLE_ATLAS` (default off → 404). `/api/v1/health` reports
  `atlas_enabled`. New `tests/test_atlas.py` (14 tests).
- **Frontend** — `frontend/src/routes/atlas/*`: an `AtlasShell` (sub-nav + tier +
  scenario selector + availability gating) with ten contexts, a `Research Atlas`
  nav-rail entry, api-client `api.atlas.*`, query hooks, and Atlas styles.
  ECharts read the same certified data as the paper figures.

### Verification (local, July 3, 2026)

- Backend: full suite **102 passed / 1 skipped** under a `datetime.UTC` shim on
  `PYTHONPATH` (behaviour identical to CI 3.11/3.12); ruff + black + mypy clean on
  the Atlas modules; live FastAPI check — enabled routes 200, disabled 404,
  public `/dashboard` unaffected.
- Frontend: `tsc -b` clean, `vite build` OK, `vitest run` **44 passed** (11
  files, +2 Atlas), ESLint 0 errors.

### Not done (intentionally, per plan)

- No deploy and not pushed; the Atlas stays unpublished until the paper is out.
- Proxy equity layers (SVI/ACS/LEAD/heat-vuln) not ingested — badged `REVIEW
  REQUIRED`. Phase 3 figure regeneration and Phase 5 reproducibility capsule are
  separate phases.

## Session

- Completed: Session 11 — Prepare the private production deployment and close the
  project (local production verification + operations/deployment docs; the live
  external deploy is owner-gated and pending sign-off).
- Date: June 8, 2026
- Branch: `feature/location-representation-explorer`
- Next: Owner-executed private deploy on a paid Render instance + sign-off, then
  tag `v1.2.0-production`. No further code session is required.

## Session 11 — Complete (private production prepared; live deploy owner-gated)

Scope chosen with the user: deploy target **Render private service**;
**prepare-and-document** (full local production-mode verification + all closeout
docs + a ready-to-execute deploy plan; the owner runs the live external deploy
since cloud credentials and sign-off are not available in this sandbox); and
**include the open Session 10 closeout items**.

### Local production-mode verification (June 8, 2026)

Sandbox Python is 3.10, so `datetime.UTC` (3.11+) was supplied via a
`sitecustomize` shim on `PYTHONPATH` — behavior identical to the CI 3.11/3.12
runtime (same approach used in the Session 9 audit).

- `pipeline.validate --dir pipeline/out`: **OK** (run twice, identical) — 20
  `RESOLVED` strata, 20 distinct catchments, 4 rural→County / 16 non-rural→CBSA,
  geometry 20/20 valid (19 Polygon + 1 MultiPolygon, 0 null), weather QC 19/20
  `COMPLETE` (NY Port Authority `INCOMPLETE` at 85.6%, no `PENDING`), ZIP
  crosswalk 39,299 distinct ZIPs (HUD-USPS Q1 2025), ResStock 20/20
  enumeration-verified, score weights sum to 1.0.
- Production app (`RLE_ANALYSIS_DATA_DIR=pipeline/out`, `RLE_REQUIRE_AUTH=1`,
  token set): `/api/v1/health` → `data_mode: production`, `candidate_count: 4019`,
  `selected_count: 20`, `auth.required/configured: true`. Protected route **401**
  without token / **200** with token; `/api/v1/openapi.json` public 200.
- Scenario persistence: `POST /api/v1/scenarios` → 201, read back at version 1,
  row written to the SQLite store. Exports (POST, auth-required): site-list (20),
  openstudio-manifest (`rle.openstudio_manifest/1.0`, 20), resstock-sampling
  (20); all **401** without token. Structured JSON request logs confirmed.

Full evidence table: `docs/DEPLOYMENT_RECORD.md` §3.

### Infrastructure (confirmed June 8, 2026 from Render docs)

Persistent disks require a **paid** instance (free filesystem is ephemeral, so
saved scenarios would be lost on deploy/restart); disks are encrypted with
automatic daily snapshots retained ≥ 7 days; free web services spin down after
15 min idle, paid do not. The prior `render.private.example.yaml` was corrected
accordingly: **Docker runtime** (so the React frontend actually builds), **paid
plan**, **persistent disk** at `/var/data`, branch
`feature/location-representation-explorer`, auth on, autoDeploy off, and
`RLE_ANALYSIS_DATA_DIR=/app/pipeline/out` (national data ships in the private
image since `pipeline/out/` is committed to the private repo).

### Session 10 closeout (done this session)

README now records the verified demo URL + date, an uptime-monitor note within
free-tier terms (≤ every ~5 min on `/api/v1/health`; free tier cold-starts after
idle), and release-tag instructions (`v1.2.0-demo`, `v1.2.0-production`). Tags
are pushed by the owner on the host (cannot push from this sandbox).

### Post-deploy fix — private-instance browser auth prompt

A free-tier test deploy of the national dataset went live at
`https://replocx-private-test.onrender.com` (`data_mode: production`, 4019
candidates, auth required, 401-without/200-with verified by curl). But the
browser UI showed "Something went wrong / Authentication required for this
private API route." with **no token prompt**: the React API client
(`frontend/src/lib/api.ts`) never attached an `Authorization` header and had no
token-entry UI. The "browser prompts for the token" behavior described in the
README existed only in the removed vanilla frontend, never in the React
redesign.

Fix (new commit, separate from the Session 11 docs commit `e1f03d1`):

- Added `frontend/src/lib/auth.ts`: in-memory bearer-token store
  (`getAuthToken`/`setAuthToken`/`authHeaders`) + `promptForToken` that prompts
  once, dedupes concurrent 401s, and never persists the token (reload
  re-prompts).
- `frontend/src/lib/api.ts` and `frontend/src/lib/exports.ts`: attach
  `authHeaders()` and retry once after prompting on a 401.
- README auth note corrected to describe the implemented prompt/retry behavior.
- Tests: `frontend/src/lib/auth.test.ts` (4) + `frontend/src/lib/api.test.ts`
  (3). Frontend suite 35 → 42, all green; `tsc -b` clean; ESLint 0 errors (3
  pre-existing accepted warnings); `vite build` OK.

This change must be committed and the private service **redeployed** for the
browser prompt to appear (the live test instance is still running the old
bundle).

### Changed files (Session 11)

- Added: `docs/OPERATIONS_RUNBOOK.md`, `docs/DEPLOYMENT_RECORD.md`.
- Modified: `render.private.example.yaml`, `docs/completion_checklist.md`,
  `README.md`, `docs/SESSION_HANDOFF.md`, `NEXT_SESSION_PROMPT.md`.
- Post-deploy auth fix (separate commit): added `frontend/src/lib/auth.ts`,
  `frontend/src/lib/auth.test.ts`, `frontend/src/lib/api.test.ts`; modified
  `frontend/src/lib/api.ts`, `frontend/src/lib/exports.ts`, `README.md`,
  `docs/SESSION_HANDOFF.md`.

### Commit/push — REQUIRED on the macOS host (cannot run in this sandbox)

Same fuse-mount limitation as Sessions 9–10: `.git/index.lock` cannot be removed
here and git refuses to write the index, so commit/push must run on macOS. The
three files git lists as "modified" but with **no content delta**
(`NEXT_SESSION_PROMPT.md`, `docs/SESSION_HANDOFF.md`, `tests/test_phase4.py`)
are index-mtime artifacts; `git diff HEAD` on them is empty.

```bash
cd ~/Developer
rm -f .git/index.lock
git add docs/OPERATIONS_RUNBOOK.md docs/DEPLOYMENT_RECORD.md \
        render.private.example.yaml docs/completion_checklist.md \
        README.md docs/SESSION_HANDOFF.md NEXT_SESSION_PROMPT.md
git commit -m "Session 11: private production prep — verification, ops runbook, deployment record, closeout"
git push origin feature/location-representation-explorer
# Then, after the owner-executed private deploy + sign-off:
#   git tag -a v1.2.0-production -m "ReplocX private production (national dataset)"
#   git push origin v1.2.0-production
```

---

## Session 10 — Complete (public demo deployed and verified)

Deployed and verified the public, demo-only instance on Render
(<https://replocx.onrender.com>). Two focused commits landed after the
Session 9 audit work:

- `ac18568` — Port the unknown-`/api` guard into `backend/fastapi_app.py` (the
  Render/Docker entry point, `uvicorn backend.fastapi_app:app`). Unknown
  `GET /api/...` paths now return `404 {"error": "API route not found."}`
  instead of the SPA `index.html`; non-API deep links still resolve to the SPA.
  Regression coverage added in `tests/test_phase4.py`.
- `e87fc4b` — Guard that test behind `importlib.util.find_spec("fastapi")` and
  import fastapi inside the test. The dependency-free `backend` CI job (Python
  3.11 + 3.12, stdlib `backend.server` path, no third-party installs) was
  failing collection on a module-level `from fastapi.responses import ...`
  (`ModuleNotFoundError: fastapi`). The test now skips where fastapi is absent
  and runs in the `quality`/`e2e`/`docker` jobs and locally where it is present.

### Local gates

- unittest, bundled demo: 88/88. Fixture-output override: 88/88.
- Bare Python 3.11, no third-party deps (mirrors the `backend` CI job):
  `py_compile` OK; suite `OK (skipped=1)` — module collects, the FastAPI
  routing test skips.
- `pipeline.run --source fixture` + `validate`; `pipeline.validate --dir
  pipeline/out`: OK. ruff, black, mypy (CI scope): pass.
  `scripts/check_release_contract.py`: PASS. ASGI `TestClient` against
  `backend.fastapi_app`: unknown `/api` → JSON 404, deep links → SPA.

### CI and push

Both commits pushed to `feature/location-representation-explorer`; GitHub CI is
green (backend 3.11/3.12, frontend, quality, e2e, docker).

### Live smoke verification — <https://replocx.onrender.com> (June 8, 2026)

Driven through Chrome against the deployed Render service:

- `/api/v1/health`: `status: ok`, `data_mode: demo`, `data_ready: true`,
  `analysis_directory: /app/data/demo`, `candidate_count: 2959`,
  `selected_count: 20`, auth not required. This is the synthetic demo dataset,
  not the 4019-candidate national set — no private data is published.
- `/api/v1/does-not-exist`: HTTP 404, JSON `{"error": "API route not found."}`
  (the deployed Session 10 fix).
- `/scenario` SPA deep link: 200, full React workbench renders against live demo
  data (2,959 eligible candidates, 20/20 distinct catchments, Philadelphia
  override); `/api/v1/dashboard`, `/provenance`, `/health` and all map/chart
  assets return 200.
- Security headers present live on `/` and `/api/...`: `content-security-policy`,
  `x-content-type-options: nosniff`, `x-frame-options`.

### Remaining Session 10 closeout (not yet done)

- Tag the public-demo release and add the verified URL + date to `README.md`.
- Configure an approved uptime monitor for `/api/v1/health` within Render
  free-tier terms. Note: the free tier spins down on idle, so the first request
  cold-starts (~30 s was observed during verification).

## Session 9 — Complete (with one external blocker: see "Commit/push")

Treated as the release-candidate audit. Every gate that can run in the audit
environment is green; the one material defect found was fixed with a regression
test. Full evidence, performance numbers, residual risks, and the go/no-go are in
**`docs/RELEASE_READINESS.md`** (status: **GO for the public demo pending the
GitHub `e2e` + `docker` jobs**).

### Gates run and results

- Python (host CPython 3.10 + a `datetime.UTC` `.pth` shim in a throwaway venv;
  `datetime.UTC` is the only 3.11+ feature, 6 sites — behavior identical to CI):
  - `unittest` bundled demo: **86/86**. Fixture-output override
    (`RLE_ANALYSIS_DATA_DIR=<fixture>`): **86/86**.
  - `pipeline.run --source fixture` + `validate`: OK. `pipeline.validate --dir
    pipeline/out` (committed national data): OK.
  - ruff: pass. black: pass (43 files). mypy (CI scope): pass.
    coverage: **66%** (gate ≥ 50). pip-audit: **0 vulnerabilities**.
  - New `scripts/check_release_contract.py`: PASS (health/data-mode, `/api/v1`
    alias, OpenAPI 3.1.0, CSP + hardening headers, unknown-route 404, SPA deep
    link, scenario versioning, auth 401/200, degraded-mode 503).
- Frontend (Node 22, clean `npm ci` of 334 pkgs in a sandbox-local copy):
  - `tsc -b`: clean. ESLint: 0 errors, 3 accepted react-refresh warnings.
    Vitest: **35/35**. `vite build`: OK. `npm audit --omit=dev`: **0**.
  - Bundle (gz): index 169.66 (45.88), vendor 206.70 (65.77), echarts 463.80
    (157.12), maplibre 801.64 (217.60), css 90.87 (14.55); dist ≈ 1.7 MB.
- Performance: startup → first health 0.22 s (demo) / 0.82 s (national); all API
  responses < 200 ms; `/api/candidates` is server-paginated (constant payload at
  2959 vs 4019 candidates); `/api/geometry` ships only the 20 selected polygons.

### Defect fixed during the audit

Unknown `GET /api/...` paths returned the SPA `index.html` (200) instead of a
JSON 404 (POST already returned 404). Fixed in `backend/server.py` (unknown API
GET → `404 {"error": "Route not found."}`; non-API deep links still serve the
SPA). New regression test `tests/test_phase3.py::test_unknown_api_route_returns_json_404`
(suite 85 → 86).

### Why the production-override suite "failed" 4 tests — and why that is correct

Running `RLE_ANALYSIS_DATA_DIR=pipeline/out unittest` against the **committed
national** data (4019 candidates) diverges in 4 dataset-coupled assertions
(candidate_count 2959 vs 4019; ZIP 98290 → CBSA not County; ResStock option is
the real MSA enumeration string, not a 5-digit code; the Philadelphia override is
legitimately auto-removed when national classification differs). These are demo/
fixture-format assertions; the supported flow (CLAUDE.md, CI, and
`verify_all.sh`) runs the override gate against a **fixture-regenerated**
`pipeline/out` (2959), where it is 86/86. The committed national data is instead
validated by `pipeline.validate` (now a gate). The tests were **not** weakened.

### Local/CI alignment

- `scripts/verify_all.sh`: added national-output validation and the release
  contract check (alongside the existing matrix).
- `.github/workflows/ci.yml`: backend job gained the fixture-pipeline +
  outputs-mode regression, national-output validation, and the release contract
  check; frontend job gained a production `npm audit`; new **`docker` job** builds
  the multi-stage image and smoke-tests the container.

## Unresolved issues / not run in this environment

- **Playwright e2e (desktop + mobile-viewport) and Docker build/smoke**: not
  runnable in the audit sandbox (no browser engine; GitHub release download
  blocked; no Docker daemon). Both are wired into CI and `verify_all.sh` and must
  be confirmed green on GitHub before Session 10.
- **npm dev-chain advisories**: 4 moderate + 1 "critical" in esbuild/vite/vitest;
  **0** in the production bundle. The critical is the Vitest UI-server file-read
  (only with `vitest --ui`). Fix is a breaking `vite@8`/`vitest` bump — schedule
  separately; not a deploy blocker.
- **a11y/visual automation is partial**: evidence screenshots only, no `axe` pass,
  no `toHaveScreenshot` diffing, no separate mobile project. Deferred (see
  `docs/RELEASE_READINESS.md`) to avoid landing unverifiable scaffolding.

## Commit/push — REQUIRED on the macOS host (could not run in the audit sandbox)

The audit ran against a fuse mount that forbids `unlink`/`rename`. Git cannot
manage `.git/index.lock`, and a stale zero-byte lock left by the harness's own
`git status` is present and cannot be removed here, so `git add`/`commit`/`push`
all fail in-sandbox. Complete the end-of-session contract on macOS:

```bash
cd ~/Developer
rm -f .git/index.lock        # clear the stale lock
rm -f __t1 .git/__t2         # audit scratch files the mount would not let me delete
git add backend/server.py tests/test_phase3.py scripts/verify_all.sh \
        scripts/check_release_contract.py .github/workflows/ci.yml \
        docs/RELEASE_READINESS.md docs/SESSION_HANDOFF.md
git commit -m "Session 9: release-candidate audit, /api 404 fix, contract gate, CI/verify alignment"
git push origin feature/location-representation-explorer
# Then confirm GitHub CI (esp. the e2e and docker jobs) is green, and run
# scripts/verify_all.sh locally for the full Playwright + Docker matrix.
```

## Changed files (Session 9)

- Added: `scripts/check_release_contract.py`, `docs/RELEASE_READINESS.md`.
- Modified: `backend/server.py` (unknown-API-GET 404), `tests/test_phase3.py`
  (regression test + imports), `scripts/verify_all.sh` (national validate +
  contract gate), `.github/workflows/ci.yml` (backend gates + npm audit + docker
  job), `docs/SESSION_HANDOFF.md`.
- Audit scratch to delete on host: `__t1`, `.git/__t2` (created by mount probes;
  unremovable here).

## Next Session

Session 11 — deploy the real national dataset to an owner-approved **private**
environment (authentication, persistent scenario storage, backups, monitoring),
verify `data_mode: production` and all production invariants, and produce the
operations runbook, deployment record, and final completion checklist. Never
expose the national dataset through the public demo service. Optionally first
finish the Session 10 closeout items above (release tag, README URL/date, uptime
monitor).
