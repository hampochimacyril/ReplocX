# Case Study — Representative Location Explorer

A research decision-support web application that selects and explains representative
U.S. locations for national building-stock and heat-health simulations.

- **Live demo (synthetic data):** https://representative-location-explorer.onrender.com
- **Source:** https://github.com/hampochimacyril/Location-representation-explorer
- **Role:** Sole designer, developer, and deployer (PhD dissertation research tool)
- **Stack:** Python (FastAPI + zero-dependency `http.server`), vanilla JS/HTML/CSS, Docker, GitHub Actions, Render
- **Status:** Live, CI-green, self-contained demo + private production data mode

> This document is written so it can be lifted directly into a portfolio site, a CV,
> or an interview talk track. Edit the first-person voice and trim sections to taste.

---

## 1. The problem

National building-stock and heat-health studies (e.g. NREL ResStock-style work) cannot
simulate every community in the United States. Researchers must instead choose a small,
defensible set of **representative locations** that stand in for the whole country across
climate and urban-form variation. Doing this badly — or opaquely — undermines every
downstream result.

The selection also has subtle traps that are easy to get wrong:

- A **ZIP code is not a Census geography.** ZIP delivery areas, ZCTAs, counties, CBSAs,
  places, and weather stations are related but **not interchangeable**; conflating them
  silently biases results.
- The correct **simulation filter differs by urban form** — rural tracts must be filtered
  by county; urban/suburban tracts by metro (CBSA). Substituting the wrong field is a
  common, invisible error.
- Selections involve **trade-offs** (national coverage vs. raw score) and occasional
  **research-priority overrides** that must be explicit and auditable, not buried.

**Goal:** build a tool that makes this selection *reproducible, inspectable, and
trustworthy* — so a reviewer can see not just *which* locations were chosen, but *why*,
and what it cost.

## 2. Who it's for

- **Building-energy & climate modelers** — choosing simulation sites with a documented,
  reproducible rationale.
- **Researchers & PhD committees** — auditing methodology and reproducing results.
- **Policy makers & program designers** (energy efficiency, weatherization, heat-health)
  — understanding which places represent which populations, and the coverage trade-offs.
- **Urban planners & public-health analysts** — connecting ZIP-level questions to the
  correct analytical geography without category errors.

## 3. The methodology I implemented

The analytical core selects **one representative "catchment" for every combination of
5 climate regions × 4 urbanicity classes = 20 strata**, and makes each step explicit:

1. **Density screen** — keep candidates at or above a configurable within-stratum
   population-density percentile (baseline 60th).
2. **Composite score** — a transparent weighted sum:
   `score = 0.45·housing-unit-coverage + 0.35·population-density + 0.20·population-coverage`
   (all percentiles; weights configurable and must total 100%).
3. **Distinct-location allocation** — a **minimum-cost flow / assignment** that guarantees
   20 *distinct* catchments while maximizing total score, instead of naively taking each
   stratum's independent top pick. When this substitutes a lower-ranked candidate to
   protect national coverage, the tool reports the exact score difference and reason.
4. **Transparent ZIP resolution** — a ZIP is treated as a *search entry point*, resolved
   through a documented crosswalk to ZCTA / county / CBSA with uncertainty notes; the
   correct simulation boundary (county for rural, CBSA otherwise) is then derived.
5. **Exact ResStock filters** — rural → `in.county`; non-rural →
   `in.metropolitan_and_micropolitan_statistical_area`, with enumeration-verified values
   gated as "review required" until curated.
6. **Representativeness diagnostics** — coverage efficiency (share of unconstrained score
   retained), score distribution, mean station distance, mean unconstrained rank.

Everything is **deterministic**: identical inputs always yield identical outputs, and
every scenario is exportable as versioned JSON + a site-list CSV.

## 4. Architecture & engineering

```
Existing analytical outputs (private CSVs)  ──read-only──┐
Bundled synthetic demo dataset (data/demo) ─────────────┤
                                                          ▼
                       Python ingestion + deterministic scorer / min-cost allocator
                                                          ▼
                       HTTP API  ── stdlib server (zero-install)  |  FastAPI (managed)
                                                          ▼
                       Dependency-free browser UI (maps, charts, tables, exports)
```

Design decisions worth calling out:

- **Two interchangeable backends from one service layer:** a zero-dependency
  `http.server` runner for instant local use, and a FastAPI app (Pydantic validation,
  OpenAPI) for managed deployment — both sharing the same `DataService`/scoring code.
- **Dependency-free front end** (no build step, no framework) so it runs anywhere in a
  controlled research environment and loads instantly.
- **Fault-tolerant, lazy data loading:** a missing data directory no longer crashes the
  process; the service degrades to a clear `503` with remediation guidance, and
  `/api/health` reports readiness, version, counts, and data mode.
- **Privacy-preserving dual data mode:** real analytical outputs locally; an automatic
  fallback to a **bundled synthetic dataset** for public demo, CI, and reviewers — so the
  app is fully self-contained and the private research data is never deployed.
- **Security headers** (strict same-origin CSP + hardening) on both entry points.

## 5. Process I followed (and learned)

This was as much an *engineering-process* exercise as an analytical one:

1. **Specify & preserve method** — encoded the selection rules as deterministic code with
   a regression suite asserting the invariants (20 strata, distinct catchments, correct
   per-urbanicity filters, override behavior, leading-zero geography IDs).
2. **Harden for production** — lazy loading, graceful failure, health probe, security
   headers, input validation, accessible and responsive UI.
3. **Make it self-contained** — wrote a deterministic synthetic-data generator so the app
   and tests run on any clone with zero external inputs (reproducibility for reviewers).
4. **Automate quality** — GitHub Actions CI (Python 3.11/3.12 unit tests, a
   graceful-degradation smoke test, front-end syntax check, Playwright end-to-end flows).
5. **Ship it** — containerized (`Dockerfile`/Compose), wrote a Render blueprint
   (`render.yaml`) binding `$PORT`, and deployed a public demo-data instance.
6. **Communicate it** — produced marketing collateral (animated promo + narration script)
   and this case study.
7. **Verify in production** — exercised the live `/api/health`, `/api/dashboard`, and ZIP
   endpoints and confirmed they matched local results exactly.

## 6. Challenges & how I solved them

| Challenge | Resolution |
|---|---|
| App couldn't run/test without private data | Built a deterministic synthetic demo dataset + auto-fallback, keeping production behavior unchanged |
| Public deploy vs. data privacy | "Demo mode" serves only synthetic data; real outputs are never published; mode surfaced in `/api/health` and the UI |
| Process crashed when inputs were absent | Lazy service accessor → clear `503` + readiness probe instead of an import-time crash |
| Brittle, dataset-specific tests | Reframed assertions around structural invariants that hold for both real and demo data |
| Repo lived in a cloud-synced folder (file locks, `.git` conflicts) | Diagnosed the sync/permission issue and migrated to a local working copy; documented the pitfall |
| Free-tier hosting cold starts | Documented a free uptime-pinger pattern to keep the service warm |
| `git push` HTTP 400 on a large pack | Diagnosed buffer/transport cause; resolved with `http.postBuffer` / retry |

## 7. Outcomes

- **Live, reproducible web app** with a public demo and a private production data path.
- **Green CI** across Python 3.11/3.12 with unit, smoke, and end-to-end tests.
- **Self-contained**: a fresh clone runs the full suite and the app with no external data.
- **Auditable method**: deterministic selection, explicit overrides, exact simulation
  filters, and versioned JSON/CSV exports.
- **Verified in production** (health, dashboard, and ZIP endpoints match local results;
  coverage efficiency 99.7% on the demo scenario).

## 8. Skills demonstrated

**Software engineering** — Python; API design (FastAPI + Pydantic, and a stdlib server);
deterministic algorithms (weighted scoring, **min-cost flow / assignment**); error
handling, logging, and health checks; clean front-end (vanilla JS, SVG data-viz,
accessibility/WCAG, responsive design).

**Data & methodology** — geospatial/Census geography (ZIP/ZCTA/county/CBSA), crosswalks
and uncertainty, percentile scoring, sensitivity analysis, reproducibility, data
provenance and SHA-256 fingerprinting.

**DevOps & delivery** — Docker & Compose; GitHub Actions CI; Playwright e2e; cloud
deployment (Render blueprint, `$PORT`, health checks); Git workflow and troubleshooting.

**Security & privacy** — CSP and hardening headers; designing a public demo that never
exposes private research data.

**Communication** — technical documentation, a methodology appendix, developer handoff,
and marketing collateral (promo video + script).

## 9. CV bullet options (pick/trim per role)

**Research software engineer / scientific software**
- Designed and shipped a reproducible decision-support web app that selects representative
  U.S. locations for national building-stock simulations, encoding a transparent
  density-screen + weighted-score + **minimum-cost distinct-location allocation** with a
  regression suite enforcing methodological invariants.
- Built dual backends (FastAPI and a zero-dependency stdlib server) over a shared service
  layer, with fault-tolerant lazy loading, a health/readiness probe, and CSP/security
  hardening.

**Data scientist / computational researcher**
- Implemented a deterministic, auditable location-selection method (climate × urbanicity
  strata, percentile scoring, coverage-efficiency diagnostics) with versioned JSON/CSV
  exports and transparent ZIP→ZCTA/county/CBSA resolution that avoids geography-category
  errors.
- Authored a synthetic-data generator and CI (Python 3.11/3.12, unit + e2e) so results
  reproduce on any clone with no private data.

**Full-stack / DevOps**
- Containerized and deployed a public, demo-data web service (Docker, Render blueprint,
  GitHub Actions CI, Playwright e2e), with a privacy-preserving dual data mode keeping
  real research data off the public host.

## 10. Keywords (for ATS / profile)

Python · FastAPI · Pydantic · REST API · vanilla JavaScript · SVG data visualization ·
accessibility (WCAG) · deterministic algorithms · minimum-cost flow / assignment ·
geospatial · Census geography (ZIP/ZCTA/CBSA) · reproducible research · data provenance ·
unit testing · Playwright · CI/CD · GitHub Actions · Docker · Render · cloud deployment ·
Content-Security-Policy · technical writing.
