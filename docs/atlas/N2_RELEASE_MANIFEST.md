# N2 clean Atlas release manifest

**Prepared:** 2026-07-08

**Worktree:** `/Users/cch322/Developer-atlas-release`

**Branch:** `codex/atlas-release-candidate`

**Base:** `origin/main` at `c0fb5cb05f981fe7886261d2c5c2f5be30fa741d`

## Release decision

This worktree is the review candidate for the selected D1 clean release
series. It preserves current `origin/main`, restores the reviewed ReplocX
React/API/pipeline foundation required by Atlas, and layers W0-W4 Atlas work on
top. It is intentionally uncommitted and unpushed pending owner approval.

The source worktree remains at `/Users/cch322/Developer` on
`feature/research-atlas`. N2 did not reset, unstage, commit, rebase, or rewrite
that worktree.

## Source inventory

The preserved source worktree has 621 status entries:

- 592 staged paths;
- 36 unstaged paths;
- 27 untracked files;
- 528 staged `replocx_paper_workspace` files;
- 14 staged `x_growth_automation` files;
- 22 staged `data` files, including the legacy bundled Atlas scaffold;
- reviewed Atlas work spread across backend, frontend, tests, scripts, docs,
  container configuration, and three planning records.

Files can appear in both staged and unstaged counts, so those counts do not sum
to the status-entry count.

## Included release paths

The candidate contains 204 changed paths relative to `origin/main` after this
manifest is added. These path groups are the complete intended release scope:

### Release configuration and public-safe runtime

- `.dockerignore`
- `.env.example`
- `.github/workflows/ci.yml`
- `.gitignore`
- `CHANGELOG.md`
- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.atlas-private.example.yml`
- `package.json`
- `package-lock.json`
- `playwright.config.ts`
- `pyproject.toml`
- `render.yaml`
- `render.private.example.yaml`
- `requirements-dev.txt`
- `deploy/atlas-private/Caddyfile`

### Reviewed application and analytical foundation

- `backend/*.py`
- `backend/requirements.txt`
- `clients/python/**`
- `data/demo/**`
- `data/zip_crosswalk_demo.csv`
- `pipeline/*.py`
- `pipeline/README.md`
- `pipeline/data/ish2023_stations.csv`
- `pipeline/data/pilot/**`
- `pipeline/data/resstock_enumerations.csv`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/eslint.config.js`
- `frontend/vite.config.ts`
- `frontend/tsconfig*.json`
- `frontend/.gitignore`
- `frontend/src/**`

The obsolete static frontend and superseded browser test are intentionally
deleted:

- `frontend/app.js`
- `frontend/styles.css`
- `tests/e2e/explorer.spec.ts`

### Atlas contracts, service, UI, equity, and tests

- `backend/atlas_routes.py`
- `backend/atlas_service.py`
- `frontend/src/routes/atlas/**`
- `tests/test_atlas.py`
- `tests/test_atlas_contract.py`
- `tests/fixtures/atlas/w0/w0_contract_bundle.golden.json`
- `tests/e2e/atlas.spec.ts`
- `scripts/build_atlas_equity_profile.py`
- `scripts/check_atlas_release.py`
- `docs/atlas/W0_acceptance_criteria.md`
- `docs/atlas/W0_data_contract.md`
- `docs/atlas/W0_scaffold_audit.md`
- `docs/atlas/W4_RELEASE_AUDIT.md`
- `docs/atlas/schemas/w0_contract_bundle.schema.json`
- `docs/atlas/screenshots/2026-07-08/**`

### Supporting regression, verification, and release records

- `tests/*.py`
- `tests/fixtures/ancillary/**`
- `tests/e2e/shell.spec.ts`
- `tests/e2e/workflows.spec.ts`
- `scripts/bootstrap_dev.sh`
- `scripts/check_release_contract.py`
- `scripts/generate_demo_data.py`
- `scripts/refresh_data.py`
- `scripts/run_dev.py`
- `scripts/verify_all.sh`
- `docs/DEPLOYMENT_RECORD.md`
- `docs/OPERATIONS_RUNBOOK.md`
- `docs/SESSION_HANDOFF.md`
- `docs/deployment_options.md`
- `docs/privacy_and_repository_rules.md`
- `ATLAS_CODEX_PROMPT_PACK_2026-07-07.md`
- `ATLAS_EXECUTION_PLAN_OPTIMIZED_2026-07-07.md`
- `ATLAS_POST_W4_SESSION_PLAN_2026-07-08.md`

## Explicit exclusions

The following are absent from the candidate worktree and release diff:

- `data/atlas/`;
- `pipeline/out/`;
- canonical `replocx_tmy3_wallfix_4scen` CSVs and provenance sidecars;
- canonical `f2v3_final` CSV/PNG/PDF/SVG assets;
- `.env` files, production tokens, Basic-auth hashes, and private keys;
- `replocx_paper_workspace/`;
- font caches;
- `x_growth_automation/`;
- `ReplocX_Overview.pptx`;
- unrelated marketing/media changes from the mixed feature index.

The committed W0 golden JSON and ancillary pipeline fixtures are schema/test
fixtures, not copies of the certified private result tier. W4 screenshots are
review evidence and are excluded from the public Docker build context.

## Reconciliation with `origin/main`

The branch starts exactly at current `origin/main`; `HEAD`, merge-base, and
`origin/main` all resolve to `c0fb5cb`. Main's six reconciled commits remain in
history. Main-only README, portfolio, outreach, social, CLAUDE, roadmap, and
marketing/media changes were not overwritten.

The latest optional research-override behavior from `origin/main` remains
covered by `test_implicit_default_override_is_removed_when_dataset_reclassifies_target`.
The React replacement makes the old static-frontend Playwright correction
inapplicable; equivalent ZIP/catchment behavior is covered by
`tests/e2e/shell.spec.ts`.

## Verification evidence

- `scripts/verify_all.sh`: **PASS**.
  - fixture pipeline and fixture validation: PASS;
  - bundled-demo backend suite: 120 tests, 4 expected output-fixture skips;
  - regenerated-output backend suite: 120 tests, no skips;
  - ruff, black, mypy, API/security contract, and runtime dependency audit:
    PASS;
  - coverage: 72%;
  - frontend: 50 tests, typecheck/build PASS, lint 0 errors/3 existing
    warnings;
  - production dependency gate: PASS, with one known moderate ECharts advisory
    below the configured high-severity threshold;
  - Playwright public-disabled matrix: 13 passed, 1 expected enabled-mode skip.
- `.venv/bin/python scripts/check_atlas_release.py`: **PASS**.
  - 720 cells, A/C/B/D, R9 PASS, `f2v3_final`;
  - equity READY, 4/4 layers, 20 records;
  - unauthenticated and Basic-only API requests blocked;
  - public Atlas routes disabled;
  - 43 runtime files checked against 79 canonical asset/table names, zero
    collisions.
- Enabled Atlas Playwright: **1 passed, 1 expected disabled-mode skip**.
- `git diff --check`: **PASS** after making the synthetic demo generator emit
  stable LF line endings; focused demo/scoring/project regressions: 16 passed.
- Forbidden-path scan: no paper workspace, X-growth, `data/atlas`,
  `pipeline/out`, canonical asset file, provenance-sidecar, or secret match.
- The source worktree still reports 621 status entries, 592 staged paths, 36
  unstaged paths, and 27 untracked files after extraction and verification.

## Proposed commit series

No commits have been created. After owner approval, build this series with
focused staging and, where integration files span phases, hunk-level staging:

1. `release: restore verified ReplocX application foundation on current main`
   - React/API/pipeline foundation, demo fixtures, client, toolchain, and
     non-Atlas regression coverage.
2. `atlas(w0): freeze certified four-scenario contracts`
   - W0 schema, contract docs, golden/negative contract tests.
3. `atlas(w1): add read-only certified results API`
   - Atlas service/routes, A/C/B/D results, R9/f2v3 gates, backend integration
     and API tests.
4. `atlas(w2): add guided research UI and browser coverage`
   - Atlas routes/components, data-mode distinction, responsive UI tests and
     screenshots.
5. `atlas(w3): add exports, provenance, and certified equity builder`
   - export/figure bundles, equity APIs and builder, sidecar validation, related
     tests and handoff evidence.
6. `atlas(w4): add private auth and container boundary`
   - Caddy/Compose, public-safe Docker allowlist, release checker, deployment
     and operations records.
7. `release(n2): record clean-branch manifest and verification`
   - external-only data rules, fixture-only CI/full verification adjustment,
     stable synthetic-demo line endings, this manifest, and the N2 handoff.

## Approval boundary

Owner review should confirm this manifest and commit sequence before any staging
for commit, commit creation, push, or pull request. N3 begins only after that
approval.
