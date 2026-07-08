# ReplocX Research Atlas - Codex Prompt Pack

> **Post-W4 note (2026-07-08):** W0-W3, W3.5, and W3.5B have been executed,
> and the W4 implementation now passes local auth/leak and full-repository
> gates. It has not been released to a live private host. The opening W4 equity
> notes below predate W3.5B and are retained as execution history, not current
> state. The owner selected `A2+B1+C1+D1`: product-depth before release,
> approved VM/Compose/Caddy hosting, Basic auth plus app token, and a clean
> Atlas-only release series. Use `ATLAS_POST_W4_SESSION_PLAN_2026-07-08.md`
> for the reviewed status, owner decisions, and next-session sequence.

**Prepared from:** `ATLAS_BUILD_BRIEF_2026-07-07.md`,
`ATLAS_COMPLETION_PLAN_4SCEN_2026-07-07.md`, and
`ATLAS_EXECUTION_PLAN_OPTIMIZED_2026-07-07.md`.
**Completion pass:** 2026-07-08.
**W4 readiness update:** 2026-07-08, after W3.5B and Session 17 local closeout.
**Repo:** `/Users/cch322/Developer`
**Branch:** `feature/research-atlas`

This file is paste-ready. Use one session prompt at a time. Each session must end with
measured gates, a dated append-only entry in `docs/SESSION_HANDOFF.md`, and a clear stop
or handoff note.

---

## W4 Readiness Notes After W3.5B And Session 17

W0-W3, W3.5, W3.5B, and the W4 local release-candidate closeout have been
executed. Treat the newest entries in `docs/SESSION_HANDOFF.md` and
`ATLAS_POST_W4_SESSION_PLAN_2026-07-08.md` as the source of truth over the
historical prompts below.

Current state after Session 17:

- Backend Atlas results read the certified `replocx_tmy3_wallfix_4scen` four-scenario
  tier with scenario order `A`, `C`, `B`, `D`.
- f2v3 registry, Fig02 parity, D comparisons, exports, provenance, and disabled-public-demo
  behavior have been implemented and locally verified.
- Canonical data root reached:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen`
- Canonical figure root reached:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final`
- W3.5B produced a sidecar-backed 20-record equity profile with all four layers
  READY: CDC/ATSDR SVI, ACS income/poverty, DOE LEAD energy burden, and heat
  vulnerability.
- The VM/Compose/Caddy candidate uses Basic auth plus the app token, read-only
  mounts, and a public-safe runtime allowlist. Local W4 auth, certified-route,
  equity, disabled-public, leak, repository, and enabled/disabled Playwright
  gates pass. No live private deployment or owner sign-off has occurred.
- The owner selected `A2+B1+C1+D1`: complete the full 20-stratum pivot and all
  interactive parity gates before release; deploy on an approved
  VM/Compose/Caddy host; keep Basic auth plus app token; and build a clean
  Atlas-only release series from updated `origin/main`.
- The mixed branch remains 25 commits ahead and 6 behind `origin/main`. Session
  N2 must preserve this worktree and transfer only reviewed Atlas release files
  into a clean worktree before publication.

---

## Global Instructions For Every Session

Paste this block at the top of every W0-W4 prompt.

```text
You are implementing the ReplocX Research Atlas in /Users/cch322/Developer on branch feature/research-atlas.

Read first:
- CLAUDE.md
- ATLAS_EXECUTION_PLAN_OPTIMIZED_2026-07-07.md
- docs/SESSION_HANDOFF.md
- docs/deployment_options.md
- backend/atlas_service.py
- backend/atlas_routes.py
- frontend/src/routes/atlas/atlas.ts
- frontend/src/lib/api.ts
- frontend/src/lib/types.ts
- tests/test_atlas.py

Non-negotiable Atlas guardrails:
- This is a migration of an existing 3-scenario scaffold, not a greenfield build.
- Migrate from the legacy 540-cell replocx_tmy3 A/B/C tier to the certified 720-cell replocx_tmy3_wallfix_4scen A/C/B/D tier.
- Scenario order is A, C, B, D. Descriptive labels are primary; codes are detail/provenance only.
- Link only f2v3_final figures and registry records. Never link f2v2_final or any f1v2* folder.
- Read canonical CSVs read-only. Do not recompute certified results or figure values.
- Use "Overheating exposure hours" and "High-humidity exposure hours" with thresholds in notes/subtitles.
- Lead on p95/exposure-hour/degree-hour metrics; pair any mean with an extreme counterpart.
- Real results and equity data are private: RLE_ENABLE_ATLAS is off in public demo builds.
- Do not weaken ruff, black, mypy, coverage, pip-audit, TypeScript, Playwright, or existing route gates.

Before edits:
- Inspect the working tree and avoid reverting unrelated user or prior-session changes.
- Confirm the current branch and whether feature/research-atlas is current enough for this session.
- If canonical OneDrive data is cloud-only or stalls, fail loudly and document the exact missing path. Do not silently fall back to data/atlas/replocx_tmy3 as current.

End-of-session contract:
- Append a dated entry to docs/SESSION_HANDOFF.md with measured gate values.
- Run the session's verification commands. If a command cannot run, document why and what remains unverified.
- Summarize changed files, gate status, and the next session's exact starting point.
```

---

## W0 Prompt - Audit, Reconcile, Freeze Contract

```text
Use the global instructions above.

Session W0 goal:
Turn the legacy Atlas scaffold into a known quantity, locate/materialize the certified 720-cell four-scenario data and f2v3 registry, and freeze the results/equity API contract before feature work.

Required source targets:
- Certified data root: 04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/{annual,seasonal,metadata,audit}/
- Scenario dictionary: replocxTMY3wf4_metadata_scenario_dictionary_4scen_2026-07-07.csv
- Endpoint dictionary: replocxTMY3wf4_*endpoint_definitions*4scen_2026-07-07.csv
- Figure registry: 04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/replocxTMY3wf4_figure_registry_f2v3_2026-07-07.csv
- Captions/alt text: replocxTMY3wf4_fig_captions_alt_text_f2v3_2026-07-07.md

Work:
1. Produce docs/atlas/W0_scaffold_audit.md. Enumerate every hard-coded 3-scenario or 540-tier assumption in backend, frontend, tests, data metadata, docs, and route names. Include file paths and line numbers where useful.
2. Produce docs/atlas/W0_acceptance_criteria.md. Convert the official precedent patterns into gates:
   - OWID: chart data, metadata, ZIP/readme style downloads.
   - IPCC Atlas: FAIR, provenance, reproducible figures/data products.
   - NREL EULP: multiple access modes, aggregate download clarity, source/citation notes.
   - CDC/ATSDR SVI: percentile/proxy/vintage transparency and data-documentation links.
3. Resolve the canonical data path. Record the exact absolute path and a read-only access smoke test. If data is cloud-only, materialize only the needed canonical subtrees or document the blocker.
4. Define docs/atlas/W0_data_contract.md with endpoint-by-endpoint payload shapes:
   - /api/v1/results/scenario-dictionary
   - /api/v1/results/scenario-summary
   - /api/v1/results/by-stratum
   - /api/v1/results/differential or /api/v1/results/d-comparisons
   - /api/v1/results/figures
   - /api/v1/results/provenance
   - /api/v1/equity/profiles
   - /api/v1/equity/scenario-cross
5. Add JSON Schemas and small golden fixtures derived from the real tier. Fixtures must prove A/C/B/D, annual/seasonal, D-B/D-C/D-A comparisons, primary endpoint families, descriptive labels, provenance fields, and f2v3 registry resolution.
6. Update only the minimum backend/frontend type constants needed for contract tests to understand A/C/B/D. Do not build W1 API features yet.

Required negative tests:
- A results fixture missing D fails schema validation.
- A results fixture with only A/B/C fails schema validation.
- A figure registry fixture pointing to f2v2_final or f1v2* fails schema validation.
- A scenario dictionary out of A/C/B/D order fails schema validation.

Gate:
- Canonical data path recorded and load-smoke-tested.
- docs/atlas/W0_scaffold_audit.md, W0_acceptance_criteria.md, and W0_data_contract.md exist.
- Schema validation tests pass and negative tests fail for the intended reason.
- Grep proof recorded in handoff for current served paths: no ("A","B","C"), hard-coded *3 scenario count, f2v2_final, or f1v2* assumptions remain in the contract layer.
- Existing public selection app tests still pass.

Stop condition:
Do not proceed to W1 until W0 gate is green or the handoff names a single concrete blocker.
```

---

## W1 Prompt - Four-Scenario Results API

```text
Use the global instructions above.
Start only after W0 is green or explicitly unblocked.

Session W1 goal:
Migrate the existing Atlas backend from the legacy A/B/C 540-cell data domain to the certified A/C/B/D 720-cell results domain, preserving existing dispatch and public-demo gating.

Work:
1. Update backend/atlas_service.py so it serves the 4scen tier through RLE_ATLAS_DATA_DIR or the recorded read-only canonical path. The service must fail loudly if the certified metadata/sidecars are missing.
2. Replace SCENARIOS = ("A","B","C") with a scenario dictionary loaded from canonical metadata. Preserve stable fallback only for tests that explicitly use fixtures.
3. Add or upgrade endpoints:
   - scenario-dictionary
   - overview
   - scenario-summary
   - by-stratum for climate, urbanicity, building, vintage
   - D comparisons: D-B natural ventilation effect, D-C peak-window effect, D-A full-AC protection
   - cooling-seasons and sensitivity if still valid for 4scen
   - provenance
4. Reconcile /api/results/scenario-c. Keep a Scenario C intervention panel endpoint if the story needs it, but stop treating C as a special scenario in core loops.
5. Update backend/atlas_routes.py, backend/fastapi_app.py, backend/server.py, and client typings only as needed. Preserve /api/v1/results/* and /api/v1/equity/* mapping.
6. Update tests/test_atlas.py and any schema tests so every default results payload includes A/C/B/D and the primary endpoint families:
   - op_temp_mean_c
   - op_temp_p95_true_c
   - humidity_ratio_mean_kgkg
   - humidity_ratio_p95_true_kgkg
   - exposure-hour and degree-hour families where present

Required tests:
- Atlas disabled by default still returns 404/disabled for private results.
- /api/v1/results/scenario-summary returns A/C/B/D in canonical order.
- /api/v1/results/by-stratum returns A/C/B/D for annual and seasonal tiers.
- /api/v1/results/provenance reports replocx_tmy3_wallfix_4scen, 720 cells, R9 certification, and f2v3 figure registry where applicable.
- Three-scenario payloads fail contract tests.
- /api/v1 path mapping and normalized /api path dispatch both work where the repo already supports both.

Gate:
- Backend tests green.
- Contract tests reject 3-scenario payloads.
- Provenance points to the certified 720-cell 4scen tier.
- Grep proof: legacy 540-tier language is no longer on served Atlas paths except in archived audit notes or explicit migration docs.
- Public selection endpoints remain unaffected with RLE_ENABLE_ATLAS off.

Stop condition:
Do not start W2 UI work until all W1 API contracts are stable.
```

---

## W2 Prompt - Atlas UI And Story Spine

```text
Use the global instructions above.
Start only after W1 is green.

Session W2 goal:
Upgrade the existing Atlas frontend from a legacy A/B/C dashboard into the guided A/C/B/D Research Atlas, with pivot-first overview, map drill-down, sealed-passive D story panel, and f2v3 figure-chart parity.

Work:
1. Update frontend/src/lib/types.ts and frontend/src/routes/atlas/atlas.ts for Scenario = A | C | B | D and the canonical palette:
   - A #0072B2
   - C #009E73
   - B #E69F00
   - D #D55E00
2. Replace labels with descriptive labels from the scenario-dictionary endpoint. Scenario C reader label: "AC 2-8pm + NV other hours". Scenario D reader label: "No AC or NV" or the canonical metadata label.
3. Rework AtlasShell and routes into the story spine:
   - Introduction
   - How locations were selected
   - Results A/C/B/D
   - Sealed-passive D contrasts
   - Equity context
   - Methods/supplementary
   - Exports/provenance
4. Pivot-first landing: national stratum x scenario pivot is the default overview. MapLibre site map is the drill path, with site click -> drawer -> /atlas/sites/<site_id>?scenario=<A|C|B|D>&tier=<annual|seasonal>&metric=<endpoint>.
5. Metric UX: default to p95/exposure-hours. Any mean view must render the paired extreme metric beside it. Threshold selector must echo threshold in chart subtitle and export metadata.
6. Add D panel: open on D-B, D-C, and D-A contrasts. Keep raw D values behind an explore affordance.
7. Figure registry integration: embed only f2v3_final registry assets. F19 goes under Supplementary/Methods, never the main results grid.
8. Add a parity test: ECharts source values equal the f2v3 registry source_csv values for each interactive twin, reporting max absolute difference.

Required tests/QA:
- TypeScript build.
- Frontend unit tests.
- Playwright e2e for Atlas enabled and disabled modes.
- Desktop/tablet/mobile screenshots with no label/chart overlap.
- D appears in every relevant selector, chart, legend, and route.
- Text search shows no bare "heat hours" or "humidity hours" in UI copy; use canonical exposure-hours terminology.

Gate:
- UI tests and Playwright green.
- Parity gate reports max|diff| = 0 or documented floating tolerance near zero.
- No f2v2_final or f1v2* links in frontend or served figure registry.
- Screenshots/contact sheet saved or referenced in handoff.

Stop condition:
Do not start W3 until the UI consumes the W1 API contract without local mock-only assumptions.
```

---

## W3 Prompt - Equity, Exports, Provenance

```text
Use the global instructions above.
Start only after W2 is green.

Session W3 goal:
Verify and join equity proxies, extend equity views to all four scenarios including D, and ship data/figure exports with provenance.

Work:
1. Verify equity source data before building overlays:
   - CDC/ATSDR SVI source, vintage, geography level, and percentile fields.
   - ACS median income and poverty source, vintage, margin/uncertainty handling if available.
   - DOE LEAD energy burden source, vintage, and geography join.
   - Catchment join/crosswalk method for the 20 representative locations.
2. If a layer is not verified, keep it out of "ready" outputs or mark it REVIEW REQUIRED. Never silently backfill fake equity values.
3. Update /api/v1/equity/profiles:
   - source/vintage chip per layer
   - proxy/direct/modeled badge
   - join uncertainty note
   - catchment-level values for all verified layers
4. Update /api/v1/equity/scenario-cross:
   - supports A/C/B/D
   - includes D-related exposure x vulnerability contrast
   - stays descriptive and avoids causal claims
5. Exports:
   - per-view CSV
   - per-figure source CSV link
   - PNG/PDF/SVG f2v3 asset links
   - citation text
   - provenance sidecar link
6. Provenance page:
   - certified tier id
   - canonical data root
   - R9 gate report
   - f2v3 registry and captions
   - source/vintage notes for equity

Required tests:
- Equity endpoints include D and reject invalid scenario codes.
- Verified equity layers expose source/vintage/proxy badge/uncertainty.
- Unverified layers remain REVIEW REQUIRED.
- Exports resolve only f2v3_final assets and source_csv values.
- Provenance page renders all required fields.

Gate:
- Backend and frontend tests green.
- Export smoke tests pass for at least one results view, one D comparison, one equity view, and one figure asset bundle.
- Handoff records which equity sources are verified and which remain REVIEW REQUIRED.
```

---

## Optional W3.5 Prompt - Certify Equity Profile Before W4

Use this only if the owner wants equity overlays marked `READY` before private deployment.
Skip this and proceed to W4 if deploying with explicit `REVIEW REQUIRED` equity badges is acceptable.

```text
Use the global instructions above.

Session W3.5 goal:
Resolve the remaining W3 equity REVIEW REQUIRED state by producing or wiring a verified,
sidecar-backed catchment-level equity profile for the certified 4scen Atlas data root.

Start condition:
Session 16 says no verified equity profile exists at:
/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/equity_profile.csv

Important boundary:
Do not mark any equity layer READY unless values, source/vintage, proxy badge, join uncertainty,
and provenance sidecar are all present. Do not silently use checked-in scaffold data/atlas/equity_profile.csv
as certified.

Work:
1. Locate or create the certified catchment-level equity profile outside the app repo under the canonical
   data root, or point RLE_ATLAS_DATA_DIR at a read-only certified copy containing it.
2. Required CSV structure:
   - one row per representative catchment
   - catchment identifiers/labels and grouping fields compatible with W1/W3 API joins
   - CDC/ATSDR SVI percentile fields, source vintage, proxy badge, join uncertainty note
   - ACS median household income and poverty-rate fields, source vintage, MOE/uncertainty note, proxy badge
   - DOE LEAD energy-burden field, source vintage, geography join note, proxy badge
   - optional heat-vulnerability index only if source/model and catchment rollup are documented
   - catchment_join_method
3. Required sidecar:
   - equity_profile.csv.prov.json beside the CSV
   - tier id: replocx_tmy3_wallfix_4scen
   - generation timestamp
   - source input files/URLs/vintages
   - geography/crosswalk method
   - aggregation method
   - uncertainty/MOE handling
   - checksum for the CSV
4. Re-run Atlas equity smoke against the canonical data root:
   - /api/v1/equity/profiles
   - /api/v1/equity/scenario-cross?scenario=D&dimension=climate
   - /api/v1/results/export-view?view=equity-profiles
   - /api/v1/results/provenance
5. If only some layers can be certified, let the API report partial readiness:
   - READY only for complete layers
   - REVIEW REQUIRED for incomplete layers
   - release notes must name exactly which layers remain unresolved

Gate:
- equity_profile.csv and equity_profile.csv.prov.json exist in the certified data root or read-only certified copy.
- API reports READY for each truly complete layer and REVIEW REQUIRED for incomplete layers.
- Provenance exposes source/vintage, proxy badge, join uncertainty, source CSV, and sidecar.
- No equity layer uses fake values or scaffold-only data.
- docs/SESSION_HANDOFF.md records the exact sources, join method, layer statuses, and verification commands.
```

---

## W4 Prompt - Private Authenticated Deploy And Release Audit

```text
Use the global instructions above.
Start only after W3 is green. Sessions 13-16 in docs/SESSION_HANDOFF.md are the current source of truth.

Session W4 goal:
Prepare and verify a private authenticated deployment of the real Research Atlas while proving the public demo cannot serve or leak the private tier.

Owner decision already made:
- Use reverse-proxy basic auth in front of the private host plus the existing bearer-token gate in the app. Do not add a new identity system unless the owner explicitly changes this decision.

W4 preflight:
1. Read docs/SESSION_HANDOFF.md Sessions 13-16, especially Session 16.
2. Inspect git status. The working tree is expected to be dirty from W0-W3. Do not revert unrelated generated files or prior Atlas work.
3. Confirm whether an equity certification file now exists at the certified data root:
   /Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/equity_profile.csv
   plus equity_profile.csv.prov.json.
4. If the equity CSV+sidecar exists, verify layer readiness through /api/v1/equity/profiles and provenance.
5. If the equity CSV+sidecar does not exist, proceed only with the explicit deployment state:
   equity overlays/source notes are visible, but catchment-level equity values remain REVIEW REQUIRED.
   Do not block W4 solely on this if the owner accepts that state, and do not mark equity READY.
6. If the owner requires READY equity overlays before deployment, stop W4 and run the optional W3.5 prompt first.

Work:
1. Update docs/deployment_options.md and any private deployment example files to include:
   - RLE_ENABLE_ATLAS=1 only on private host
   - RLE_ATLAS_DATA_DIR=/read-only/path/to/replocx_tmy3_wallfix_4scen or mounted app-ready copy
   - RLE_REQUIRE_AUTH=1
   - RLE_PRIVATE_AUTH_TOKEN from secret manager
   - reverse-proxy basic auth config notes for nginx or Caddy
   - read-only real-data mount
   - explicit equity deployment state: READY if sidecar-backed equity_profile.csv verifies, otherwise REVIEW REQUIRED
2. Reconcile or explicitly document branch divergence before publication. Session 16 recorded local branch 25 ahead / 6 behind origin/main.
3. Complete the "Do Not Deploy Real Data Until" checklist before any real deployment.
4. Private-host verification:
   - unauthenticated Atlas frontend route blocked by reverse proxy
   - unauthenticated /api/v1/results/* and /api/v1/equity/* blocked
   - missing bearer token blocked by app where applicable
   - authenticated requests return 200
   - /api/v1/results/provenance returns replocx_tmy3_wallfix_4scen, 720 cells, R9, f2v3_final
   - /api/v1/equity/profiles returns the expected equity state: READY or REVIEW REQUIRED with missing_source_path
5. Public-demo leak test:
   - RLE_ENABLE_ATLAS is off
   - no private Atlas data path mounted
   - /api/v1/results/* and /api/v1/equity/* return 404/disabled
   - image/container/file scan finds no replocx_tmy3_wallfix_4scen private data or f2v3 private assets baked into public layers
6. Release audit:
   - every route/figure/caption/table/download/provenance points to the same certified 4scen tier
   - no f2v2_final or f1v2* links
   - W3 equity state is correctly represented in UI, exports, provenance, and release notes
   - final screenshots/contact sheet
   - docs/SESSION_HANDOFF.md release entry

Required tests:
- Full scripts/verify_all.sh, or documented equivalent if environment limitations prevent a leg.
- Auth smoke tests with explicit 401/403/200 evidence.
- Public-demo leak test with explicit command output summarized in handoff.
- Grep proof for superseded figure links and legacy 540 current-tier language.
- Equity-state smoke:
  - if equity_profile.csv+sidecar exists: show READY layer count and source_csv/provenance_sidecar
  - if not: show REVIEW REQUIRED, missing_source_path, source/vintage notes, and no fake catchment-level values
- Re-run targeted Atlas tests at minimum:
  .venv/bin/python -m unittest tests.test_atlas tests.test_atlas_contract -v
- Re-run frontend Atlas tests and production build, using the repo's Node runtime.

Gate:
- Private deployment is authenticated and serves real results only behind auth.
- Public demo cannot access the Atlas.
- Equity state is explicit and honest: READY only with sidecar-backed values, otherwise REVIEW REQUIRED in UI/provenance/release notes.
- Full release audit passes.
```

---

## One-Shot Continuation Prompt

Use this only if a session is interrupted and a new Codex turn needs to resume.

```text
Resume the current ReplocX Research Atlas session in /Users/cch322/Developer.

First read:
- ATLAS_EXECUTION_PLAN_OPTIMIZED_2026-07-07.md
- ATLAS_CODEX_PROMPT_PACK_2026-07-07.md
- docs/SESSION_HANDOFF.md
- git status

Identify the active W-session from the newest handoff entry and uncommitted changes. Continue from the last incomplete gate. Do not restart from scratch, do not revert unrelated changes, and do not proceed to the next W-session until the current gate is green or a concrete blocker is documented.
```
