# ReplocX Production Roadmap

This document tracks the path from the current baseline to a verified public demo
and an approved private production deployment. The authoritative, session-by-session
execution plan lives in [`NEXT_SESSION_PROMPT.md`](../NEXT_SESSION_PROMPT.md); the
running status of each session is recorded in
[`docs/SESSION_HANDOFF.md`](SESSION_HANDOFF.md).

## Phases

| Session | Scope | Status |
| --- | --- | --- |
| 0 | Bootstrap a reproducible local toolchain and align it with CI | Complete |
| 1 | Reconcile the Phase 2-4 working tree into a clean v1.2 baseline; green CI | Complete |
| 2 | Build the real tract-level pipeline for pilot states (incl. Pennsylvania) | Complete |
| 3 | Complete real ancillary data integration (HUD crosswalk, geometry, NOAA, ResStock) | Complete (live) |
| 4 | Run and audit the national production dataset | Complete (live) |
| 5 | Benchmark leading interfaces and approve the redesign specification | Complete |
| 6 | Build the new React/TypeScript/Vite frontend foundation | Planned |
| 7 | Implement the map-first analysis workspace | Planned |
| 8 | Complete scenarios, ranking, comparison, and provenance workflows | Planned |
| 9 | Full quality, security, performance, and release audit | Planned |
| 10 | Deploy and verify the public demo | Planned |
| 11 | Deploy the private production instance and close the project | Planned |

## Guardrails

Carried through every phase (see `CLAUDE.md` and the "Non-Negotiable Product
Rules" in `NEXT_SESSION_PROMPT.md`):

- Preserve exactly 20 climate-region × urbanicity strata; rural→county,
  non-rural→CBSA; leading-zero identifiers as strings; deterministic scoring;
  weights summing to 1.0.
- Keep the public deployment demo-only. Real analytical data belongs only on an
  approved private deployment.
- Fixture outputs stay reproducible and labeled synthetic. Real outputs carry
  source versions, timestamps, limitations, and verification status.
- Never silently mark ResStock values or weather files as ready.

## Current Baseline (v1.2 + national dataset)

- Deterministic fixture pipeline and demo dataset; full Python suite passes in
  both data modes.
- Versioned `/api/v1` surface with OpenAPI, optional bearer auth, SQLite scenario
  persistence, structured logs, and a health/degradation contract.
- Per-station weather QC computed (`COMPLETE`/`INCOMPLETE`, 90% threshold).
- The real `--source api` tract-level method is implemented and has been run for
  the full nation (Session 4, committed `4d097b3`): 84,080 tracts classified;
  rural tracts → County and non-rural tracts → CBSA; 20 distinct strata selected;
  `data_mode: production`; provenance, limitations, and verification status
  recorded. Outputs live in `pipeline/out/` and pass `pipeline/validate.py`.
- The national run is intentionally distinct from the dissertation's
  boundary-consistent 2010 tract basis; differences are explained by data vintage,
  boundary definitions, classification, and scoring in `docs/methodology.md`
  rather than forced to agree.

## Remaining Work

Session 5 (redesign specification + benchmark + prototype) is complete; see
`docs/UI_BENCHMARK.md`, `docs/UI_REDESIGN_SPEC.md`, and
`prototype/redesign_prototype.html`. Sessions 6–11 remain: the new React
frontend, the map-first analysis workspace, the remaining product workflows, the
release audit, and the public-demo / private-production deployments.
