# ReplocX Completion Checklist (Final)

Project closeout for the Sessions 0–11 completion and deployment plan
(`NEXT_SESSION_PROMPT.md`). Status as of June 8, 2026.

## Repository workflow

- Private repository: `https://github.com/hampochimacyril/Location-representation-explorer`
- Branch: `feature/location-representation-explorer`; draft PR #1.
- Commit scope: application source, documentation, tests, Docker/Render config,
  the committed reproducible `pipeline/out/` dataset, and private PR screenshots.
- Excluded from Git: credentials, local manifests (absolute paths), large raw
  downloads (`pipeline/cache/`, `pipeline/work/`), `.venv/`, `.tools/`,
  `node_modules/`, coverage, and Playwright artifacts.

## Sessions 0–11 status

| # | Session | Status |
| --- | --- | --- |
| 0 | Reproducible toolchain | ✅ `scripts/bootstrap_dev.sh`, `scripts/verify_all.sh` |
| 1 | Clean v1.2 baseline + docs reconciliation | ✅ |
| 2 | Real tract-level pilot (PA/AZ/MN) | ✅ |
| 3 | Real ancillary data (HUD, TIGER, NOAA ISD, ResStock) | ✅ (live path; runbook) |
| 4 | National production run + audit | ✅ `pipeline/out/` (4,019 candidates) |
| 5 | UI benchmark + redesign spec | ✅ `docs/UI_BENCHMARK.md`, `docs/UI_REDESIGN_SPEC.md` |
| 6 | React/TS/Vite frontend foundation | ✅ |
| 7 | Map-first analysis workspace | ✅ |
| 8 | Scenarios, ranking, comparison, provenance; legacy UI removed | ✅ |
| 9 | Release-candidate audit | ✅ `docs/RELEASE_READINESS.md` (GO) |
| 10 | Public demo deployed + verified | ✅ <https://replocx.onrender.com> (`data_mode: demo`) |
| 11 | Private production prepared + closeout docs | ✅ docs/verification; live deploy pending owner sign-off |

## Verified application behavior

- Starts locally with `python3 -m backend.server`; managed entry point
  `uvicorn backend.fastapi_app:app`.
- Overview dashboard renders all 20 strata; map, filters, coverage matrix,
  charts, and details stay synchronized (React workspace).
- ZIP search preserves leading-zero identifiers and explains
  ZIP/ZCTA/county/CBSA scope and uncertainty.
- Deterministic scoring (weights sum to 1.0); unique allocator selects one
  catchment per stratum; rural → County, non-rural → CBSA.
- Candidate ranking supports filtering, keyboard-operable sorting, comparison,
  and CSV export; exports include site-list, ResStock/ComStock sampling, and an
  OpenStudio manifest.
- Scenarios save, version, and share via SQLite.
- `/api/v1` is versioned with legacy `/api` aliases and an OpenAPI schema;
  private deployments require bearer-token auth without changing the public demo.
- Per-station hourly weather QC (`COMPLETE`/`INCOMPLETE`, 90% threshold) is
  computed and exported; no `PENDING` for processed stations.

## Production dataset verification (June 8, 2026)

`pipeline.validate --dir pipeline/out`: **OK**. Production-mode app + invariant
evidence is recorded in `docs/DEPLOYMENT_RECORD.md` §3 (20 strata, 20 distinct
catchments, 4/16 county/CBSA split, 20/20 valid geometry, 19/20 weather
`COMPLETE`, 39,299 ZIPs, 20/20 ResStock enumeration-verified, auth 401/200,
scenario persistence, exports).

## Automated checks

Reproducible toolchain via `scripts/bootstrap_dev.sh`; full local matrix via one
command:

```bash
scripts/bootstrap_dev.sh
scripts/verify_all.sh
```

`verify_all.sh` and CI (`.github/workflows/ci.yml`) run the same gates: backend
unittest in both data modes, fixture-pipeline + `pipeline/out` validation, the
release-contract check, ruff/black/mypy/coverage/pip-audit, frontend
typecheck/lint/Vitest/build + production `npm audit`, Playwright e2e, and the
Docker build + container smoke.

## Methodological peer-review tracking

The selection method derives from the dissertation analysis; the app implements
it deterministically and documents every deviation by data vintage in
`docs/methodology.md`.

| Item | Reviewer / owner | Status |
| --- | --- | --- |
| Strata definition (5 climate × 4 urbanicity) | _author_ | ✅ matches dissertation |
| Density-band urbanicity classification | **TO CONFIRM** (domain reviewer) | ⏳ documented; awaiting external review |
| Composite score weights (0.45 / 0.35 / 0.20) | _author_ | ✅ fixed and enforced |
| Tract → county / CBSA aggregation + join-loss reporting | **TO CONFIRM** | ⏳ 918 join losses documented, not hidden |
| Vintage choices (2020 tracts, ACS 2019–2023, Jul-2023 CBSA) | **TO CONFIRM** | ⏳ documented in `docs/methodology.md` |
| Weather-QC threshold (90% hourly completeness) | **TO CONFIRM** | ⏳ documented; 1 station `INCOMPLETE` |
| ResStock/ComStock enumeration verification | _author_ | ✅ 20/20 against real NREL dictionary |

Record reviewer names and dates here as external methodological review completes.
A row-for-row comparison with the prior dissertation outputs was not possible
(those files are not in this repo); the documented differences are vintage,
boundaries, delineation, classification, and scoring — not error.

## Final source attribution

Full citations, versions, quarters/releases, and SHA-256 fingerprints are in
`docs/data_sources.md` (and the in-app provenance + `selection_metadata.json`).
Primary sources for the national run:

- U.S. Census Bureau — ACS 2019–2023 5-year (tract population and housing units).
- U.S. Census Bureau — 2023 Gazetteer (tract land area and interior points).
- Census/OMB — July 2023 CBSA delineation (2020 standards).
- HUD-USPS ZIP crosswalk — Q1 2025 (ZIP-COUNTY and ZIP-CBSA, allocation ratios).
- NOAA Integrated Surface Database (ISD) — global-hourly, 2023.
- NREL ResStock 2025 AMY2018 release 1 enumeration dictionary
  (SHA-256 `a60a0d21…677f7a`).
- Census TIGER/Line — county/CBSA cartographic boundaries (2020 vintage).

## Deliverables produced this session (11)

- `docs/OPERATIONS_RUNBOOK.md` — day-2 operations, backups, recovery, incident
  response for the private instance.
- `docs/DEPLOYMENT_RECORD.md` — infrastructure decisions, verification evidence,
  ready-to-execute deploy plan, sign-off + release-tag section.
- `render.private.example.yaml` — corrected private blueprint (Docker runtime,
  paid plan, persistent disk, auth).
- This checklist; README closeout (verified demo URL + date, release tags).

## Remaining (owner-gated, outside this sandbox)

- Execute the private production deploy on a paid Render instance and run the
  live post-deploy smoke (`docs/OPERATIONS_RUNBOOK.md` §6).
- Confirm the §2 infrastructure owners/budget/secret-manager in
  `docs/DEPLOYMENT_RECORD.md`.
- Owner sign-off, then tag `v1.2.0-production`.
- Complete external methodological peer-review rows above.
- Optional research-data follow-ups: national HUD-USPS refresh cadence, broader
  weather-QC station set, and curated NREL enumerations for non-baseline
  scenario alternatives.
