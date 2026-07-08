# W0 Scaffold Audit

Date: 2026-07-08

Scope: legacy Research Atlas scaffold on `feature/research-atlas`, before W1 feature work.

## Branch And Data State

- Current branch: `feature/research-atlas`.
- No upstream is configured for this branch.
- `origin/main` exists at `c0fb5cb`, but `git merge-base --is-ancestor origin/main HEAD` returned nonzero. The branch is not proven current with main in this working tree.
- The worktree was already dirty before W0, including Atlas scaffold files, docs, generated presentation/media/cache files, and unrelated `x_growth_automation` additions. W0 did not revert any pre-existing changes.
- Certified data root was reachable read-only at:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen`
- Certified figure root was reachable read-only at:
  `/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final`
- Smoke test evidence:
  - Annual scenario summary: 5 lines, header plus A/C/B/D rows.
  - Seasonal scenario summary: 5 lines, header plus A/C/B/D rows.
  - f2v3 registry: 20 lines, header plus 19 figure rows.
  - Captions/alt text markdown: readable.

## Certified Tier Observations

- Scenario dictionary file: `metadata/replocxTMY3wf4_metadata_scenario_dictionary_4scen_2026-07-07.csv`.
- Scenario order is A, C, B, D.
- Display labels are primary:
  - A: AC all day
  - C: AC 2-8pm + NV other hours
  - B: NV only
  - D: No AC or NV
- Endpoint dictionary file: `metadata/replocxTMY3wf4_metadata_endpoint_definitions_4scen_2026-07-07.csv`.
- Primary endpoint families recorded there:
  - `op_temp_mean_c`
  - `op_temp_p95_true_c`
  - `humidity_ratio_mean_kgkg`
  - `humidity_ratio_p95_true_kgkg`
- Exposure-hour labels to surface:
  - Overheating exposure hours: `op_temp_hours_gt_28c`, hours above 28 C.
  - High-humidity exposure hours: `humidity_hours_gt_0p012kgkg`, hours above 0.012 kg/kg.
- D-specific comparison source files exist for both annual and seasonal tiers as `*_d_specific_comparisons_2026-07-07.csv`, with D as the base scenario and A/C/B as comparison scenarios.
- Figure registry source is only the f2v3 final registry: `f2v3_final/replocxTMY3wf4_figure_registry_f2v3_2026-07-07.csv`.

## Legacy Assumptions Found

### Backend

- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:3) documents the tier as "TMY3 (Session 7, 540-cell factorial)".
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:14) encodes A < C < B as the scenario ordering.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:44) defines `SCENARIOS = ("A", "B", "C")`.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:45) defines old labels: Full AC, No AC / natural ventilation, Intermittent AC.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:56) says Atlas exposes unpublished 540-cell results.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:108) expects bundled `replocx_tmy3/` CSVs.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:131) reads `replocx_tmy3/{tier}/{tier}_scenario_summary.csv`.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:149) special-cases Scenario C via `scenario_c`.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:158) reads the old `replocx_tmy3/scenario_c` folder.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:188) reads old `differential_summary` instead of the certified D-specific comparisons.
- [backend/atlas_service.py](/Users/cch322/Developer/backend/atlas_service.py:263) multiplies A-count by 3 to report `n_cells`.
- [backend/atlas_routes.py](/Users/cch322/Developer/backend/atlas_routes.py:39) exposes `/api/results/scenario-c` as a core route, reinforcing C as special.
- [backend/atlas_routes.py](/Users/cch322/Developer/backend/atlas_routes.py:45) defaults equity scenario-cross to B instead of the D-related contract.
- [backend/fastapi_app.py](/Users/cch322/Developer/backend/fastapi_app.py:256) documents the unpublished tier as 540-cell.
- [backend/fastapi_app.py](/Users/cch322/Developer/backend/fastapi_app.py:278) only exposes the legacy Scenario C route, not scenario dictionary, figures, or D comparisons.

### Frontend

- [frontend/src/lib/types.ts](/Users/cch322/Developer/frontend/src/lib/types.ts:230) defines `Scenario = "A" | "B" | "C"`.
- [frontend/src/routes/atlas/atlas.ts](/Users/cch322/Developer/frontend/src/routes/atlas/atlas.ts:13) exports a three-color palette.
- [frontend/src/routes/atlas/atlas.ts](/Users/cch322/Developer/frontend/src/routes/atlas/atlas.ts:19) exports old short labels.
- [frontend/src/routes/atlas/atlas.ts](/Users/cch322/Developer/frontend/src/routes/atlas/atlas.ts:24) exports `SCENARIOS = ["A", "B", "C"]`.
- [frontend/src/routes/atlas/AtlasShell.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/AtlasShell.tsx:25) keeps a primary "Scenario C - partial protection" nav item.
- [frontend/src/routes/atlas/AtlasShell.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/AtlasShell.tsx:72) documents the shell as a 540-cell surface.
- [frontend/src/routes/atlas/AtlasShell.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/AtlasShell.tsx:139) tells disabled deployments that the Atlas is 540-cell.
- [frontend/src/routes/atlas/DataMethods.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/DataMethods.tsx:4) documents 540-cell methods.
- [frontend/src/routes/atlas/DataMethods.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/DataMethods.tsx:16) uses "The 540-cell factorial".
- [frontend/src/routes/atlas/DataMethods.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/DataMethods.tsx:19) says three HVAC scenarios yield 540 EnergyPlus cells.
- [frontend/src/routes/atlas/Introduction.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/Introduction.tsx:8) describes the headline as A < C < B.
- [frontend/src/routes/atlas/Introduction.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/Introduction.tsx:40) describes a 540-cell, three-scenario tier.
- [frontend/src/routes/atlas/Introduction.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/Introduction.tsx:45) uses "The three HVAC scenarios".
- [frontend/src/routes/atlas/SimulationResults.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/SimulationResults.tsx:23) says A < C < B is front and centre.
- [frontend/src/routes/atlas/SimulationResults.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/SimulationResults.tsx:81) hard-codes "180 runs per scenario (540 cells)".
- [frontend/src/routes/atlas/HeatHealth.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/HeatHealth.tsx:16) uses generic "Hours > 30 C" terminology instead of canonical exposure-hour wording.
- [frontend/src/routes/atlas/atlas.test.tsx](/Users/cch322/Developer/frontend/src/routes/atlas/atlas.test.tsx:46) mocks the old 540-cell dataset and A/B/C semantics.

### Tests

- [tests/test_atlas.py](/Users/cch322/Developer/tests/test_atlas.py:3) documents the old 540-cell tier.
- [tests/test_atlas.py](/Users/cch322/Developer/tests/test_atlas.py:58) asserts exactly three scenarios.
- [tests/test_atlas.py](/Users/cch322/Developer/tests/test_atlas.py:64) asserts A < C < B.
- [tests/test_atlas.py](/Users/cch322/Developer/tests/test_atlas.py:87) treats Scenario C decomposition as a core shape test.
- [tests/test_atlas.py](/Users/cch322/Developer/tests/test_atlas.py:99) asserts provenance contains "540".
- [tests/test_atlas.py](/Users/cch322/Developer/tests/test_atlas.py:119) defaults equity scenario-cross to B.

### Data Metadata And Bundled Legacy Data

- [data/atlas/atlas_metadata.json](/Users/cch322/Developer/data/atlas/atlas_metadata.json:2) describes "Session 7, 540-cell factorial".
- [data/atlas/atlas_metadata.json](/Users/cch322/Developer/data/atlas/atlas_metadata.json:10) records "A < C < B" ordering.
- [data/atlas/atlas_metadata.json](/Users/cch322/Developer/data/atlas/atlas_metadata.json:11) points to `replocx_successful_run_manifest_540.csv`.
- [data/atlas/atlas_metadata.json](/Users/cch322/Developer/data/atlas/atlas_metadata.json:12) points to `_CANONICAL/10_DATA/replocx_tmy3`.
- [data/atlas/atlas_metadata.json](/Users/cch322/Developer/data/atlas/atlas_metadata.json:35) records old bundled `replocx_tmy3/...` file checksums.
- `data/atlas/replocx_tmy3/**` is the legacy app-ready 540-cell tier and must not be silently treated as current.

### Docs

- [docs/SESSION_HANDOFF.md](/Users/cch322/Developer/docs/SESSION_HANDOFF.md:9) records Session 12 as a 540-cell Atlas scaffold.
- [docs/SESSION_HANDOFF.md](/Users/cch322/Developer/docs/SESSION_HANDOFF.md:15) says data was copied from `_CANONICAL/10_DATA/replocx_tmy3`.
- [docs/SESSION_HANDOFF.md](/Users/cch322/Developer/docs/SESSION_HANDOFF.md:22) records the existing `/api/v1/results/*` and `/api/v1/equity/*` wiring.
- [docs/deployment_options.md](/Users/cch322/Developer/docs/deployment_options.md:1) documents private deployment controls but does not yet mention the Atlas-specific `RLE_ENABLE_ATLAS` off-by-default boundary or the 720-cell/f2v3 guardrails.

## W0 Resolution

- W0 freezes a four-scenario schema and tiny real-derived fixtures without copying the private canonical tier into the public/demo `data/atlas` bundle.
- The service must fail loudly if pointed only at the legacy `data/atlas/replocx_tmy3` scaffold.
- W1 should implement the actual reader over a staged read-only copy or direct canonical root, using the contract in `docs/atlas/W0_data_contract.md` and the schemas in `docs/atlas/schemas/`.
