# Production roadmap — from demo to a fully functional tool

Today the app is **complete as a demo**: real method, real interface, but running on a
bundled **synthetic** dataset and a small ZIP-crosswalk subset. To make it a production
research/decision tool on real national data (e.g. once sponsored), the work below remains.

**Ownership key:**
- 🟢 **Cowork can build now** (no sponsor/private data needed — I can implement and test it today).
- 🟡 **Cowork can build, needs your inputs** (a data file, credential, or decision from you).
- 🔴 **Needs you / a sponsor / domain review** (not something I can do).

## A. Real data & ingestion
1. 🟡 **Swap in the real analytical outputs.** Point `RLE_ANALYSIS_DATA_DIR` at the actual
   `location_selection/data/processed/` CSVs; run `scripts/refresh_data.py` for the
   SHA-256 manifest. *I can add a strict schema validator + clear errors; you provide the files.*
2. 🟢 **National HUD-USPS ZIP crosswalk pipeline.** Replace the demo subset with an
   ingestion script for the full quarterly HUD-USPS ZIP↔ZCTA/county/CBSA crosswalk
   (public data), including the one-to-many allocation ratios and a refresh routine.
3. 🟢 **Schema/contract validation + data-quality checks** on ingest (row counts, ranges,
   leading-zero integrity, required columns) with actionable failures.

## B. Method completeness
4. 🟡 **Hourly weather-QC integration.** Replace the `PENDING` weather status with real
   hourly temperature/humidity completeness (e.g. NOAA ISD / TMY3 / AMY). *I build the
   ingestion + scoring hook; you confirm the QC source and thresholds.*
5. 🔴/🟡 **ResStock enumeration verification.** Curate and verify exact
   `in.county` / `in.metropolitan_and_micropolitan_statistical_area` values against the
   current ResStock data dictionary so new scenarios clear "REVIEW REQUIRED". *I can
   automate the cross-check given the dictionary; final sign-off is yours.*
6. 🟡 **Boundary vintage decision.** Baseline uses 2010 Census tracts; decide on 2020
   vintage and document. *I implement once you decide.*
7. 🔴 **Methodological peer review / sensitivity analyses** for publication defensibility.

## C. Geography & visualization
8. 🟢 **Real polygon maps.** Render tract/county/CBSA polygons from Census TIGER/Line
   (currently centroids), with proper projection and choropleths.
9. 🟢 **Map performance** — simplify/serve geometry efficiently (TopoJSON/vector tiles).

## D. Productionization (engineering)
10. 🟢 **Auth + private deployment** for serving real (potentially sensitive) data —
    login/SSO, role-based access, and a private host config (the public demo stays demo-only).
11. 🟢 **Scenario persistence** — save/share/version scenarios (SQLite/Postgres), optional
    user accounts and a scenario library.
12. 🟢 **Observability** — structured logging, error tracking (e.g. Sentry), metrics,
    uptime monitoring (free pinger already documented).
13. 🟢 **CI hardening** — linting (ruff), formatting (black), type-checking (mypy), test
    coverage gates, dependency pinning + security scanning (pip-audit/Dependabot).
14. 🟢 **API versioning & docs** — formalize `/api/v1`, publish the OpenAPI/Swagger UI
    (FastAPI already generates it), add rate limiting.
15. 🟢 **Performance/scale** — caching, load-test the full national candidate set, paginate
    heavy endpoints (ranking already caps rows).
16. 🟢 **Accessibility audit** (WCAG AA pass) and a small docs site.

## E. Interoperability / integration ("pairing")
17. 🟢 **Export adapters** — one-click export of selected sites as ResStock/ComStock
    sampling inputs and OpenStudio/EnergyPlus-ready manifests.
18. 🟢 **REST integration + client** — a small Python client package so pipelines
    (URBANopt, GeoPandas workflows) can call the selection programmatically.
19. 🟡 **Co-simulation/coupling** (longer-term) — FMI/FMU or URBANopt coupling. *Scope with
    a modeling collaborator.*

## F. Funding / partnerships
20. 🔴 **Sponsor, data-use agreements, licensing, and citation** — secure support and
    clarify data licenses/attribution and how to cite the tool.

---

### Suggested first sponsored sprint (highest value, mostly 🟢/🟡)
1. National HUD-USPS crosswalk pipeline (A2) → real ZIP search.
2. Real-data schema validator + ingest (A1, A3) → run on production CSVs.
3. Real polygon maps (C8) → credible visuals.
4. Auth + private deploy (D10) → safe to share real data.
5. ResStock/OpenStudio export adapters (E17) → immediate utility to modelers.

**I (Cowork) can start any 🟢 item now** — for example, building the HUD-USPS crosswalk
ingestion pipeline, the real-data schema validator, TIGER polygon rendering, scenario
persistence, or the CI hardening — all testable against the existing demo before your real
data arrives. Tell me which to begin with.
