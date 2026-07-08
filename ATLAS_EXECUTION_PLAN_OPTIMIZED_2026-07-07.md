# ReplocX Research Atlas — Optimized Execution Plan (migration-aware, four-scenario)

**Prepared:** 2026-07-07 · **Optimizes:** `ATLAS_BUILD_BRIEF_2026-07-07.md` +
`ATLAS_COMPLETION_PLAN_4SCEN_2026-07-07.md`.
**For:** implementation by **Codex GPT 5.5** in `/Users/cch322/Developer`, branch
`feature/research-atlas`.
**Companion:** `ATLAS_CODEX_PROMPT_PACK_2026-07-07.md` (paste-ready per-session prompts).
**Completion pass:** 2026-07-08.

This is a planning artifact. It resolves the §9 open questions, corrects the plan's
assumptions against the **actual repo state**, and rewrites W0–W4 as a *migration +
completion of an existing scaffold* rather than a greenfield build. No code is written here.

External precedent checks were grounded in the official OWID Grapher Chart API documentation,
the IPCC-WG1 Atlas reproducibility repository, NREL's End-Use Load Profiles access page, and
CDC/ATSDR SVI data/documentation pages. Repo checks were grounded in the current
`backend/atlas_service.py`, `backend/atlas_routes.py`, `backend/fastapi_app.py`,
`frontend/src/routes/atlas/atlas.ts`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`,
`tests/test_atlas.py`, `data/atlas/atlas_metadata.json`, `docs/SESSION_HANDOFF.md`, and
`docs/deployment_options.md`.

---

## 0. The single most important correction

The uploaded plan reads as a **greenfield W0→W4 build**. The repo is not greenfield.
A working Atlas scaffold **already exists** on `feature/research-atlas`, but it was built
against the **previous generation** of the results tier. The real work is a **migration**.

| Dimension | Uploaded plan assumes | Repo actually has (2026-07-07) | Consequence |
|---|---|---|---|
| Scaffold | To be built (W1–W2) | `backend/atlas_routes.py`, `backend/atlas_service.py`, `backend/exports.py`, `frontend/src/routes/atlas/{AtlasShell.tsx,atlas.ts,atlas.test.tsx}`, `data/atlas/` | Chassis exists → faster, but embedded legacy assumptions must be hunted down |
| Scenarios | Four: **A/C/B/D** | Three: **A, B, C** (`SCENARIOS = ("A","B","C")`) | **D (sealed-passive) is entirely missing**; ordering is A,B,C not A,C,B,D |
| Tier | 720-cell `replocx_tmy3_wallfix_4scen` | 540-cell `replocx_tmy3` (local `data/atlas/replocx_tmy3/`) | Data domain must be re-pointed + re-shaped |
| Labels | Descriptive, canonical | `"Full AC"`, `"No AC / natural ventilation (hottest)"`, `"Intermittent AC 14:00-20:00"` | Non-canonical; must map to the frozen dictionary |
| Scenario C | Symmetric member of A/C/B/D | Special-cased: dedicated `scenario_c` folder + `/api/results/scenario-c` route + bespoke `avoided/residual` math | C must become a first-class scenario; keep the C intervention panel but re-source it |
| Terminology | "Overheating / High-humidity exposure hours" | "heat hours" style / `gt_28c` / `gt_30c` fields | Must enforce canonical terminology + thresholds in notes |
| Figures | Link **only** `f2v3_final` | Not yet wired to a figure registry | Add figure-registry resolution; forbid superseded folders |
| Routes | `/api/v1/results/*`, `/api/v1/equity/*` | Dispatched as `/api/results/*`, `/api/equity/*` via `server.py` + `fastapi_app.py` mapping `/api/v1/…`→`/api/…` | Verify the v1 mapping holds; don't regress it |
| Auth boundary | To be built (W4) | **Already present**: Atlas gated off by `RLE_ENABLE_ATLAS`; data dir via `RLE_ATLAS_DATA_DIR`; in-memory **bearer-token prompt already in the React UI** (commit `5cb1be6`) | W4 shrinks to reverse-proxy basic auth + verification, not from-scratch auth |
| Equity | To be built (W3) | `data/atlas/equity_profile.csv` + `atlas.equity_profiles()` + `equity_scenario_cross()` exist (3-scenario) | Migrate + verify against real CDC-SVI/ACS/DOE-LEAD source; extend to D |

**Net effect on effort:** W1 and W2 shrink (chassis + routes + charts exist); **W0 grows**
(it must become a rigorous *audit + migration-design* session); a new risk dominates —
**silent three-scenario assumptions surviving the migration.** The plan below is re-weighted
accordingly.

### Branch hygiene note
`docs/SESSION_HANDOFF.md` tail describes "Session 9/10/11" on
`feature/location-representation-explorer` — that is the **selection product's** deploy
lineage, not the Atlas. Atlas work lives on `feature/research-atlas`. W0 must confirm
`feature/research-atlas` is current with `main` (rebase/merge if stale) and that the atlas
scaffold commits are the intended baseline. Also delete the noted audit scratch files
(`__t1`, `.git/__t2`, stale `.git/index.lock`) before starting.

### Concrete repo evidence from this completion pass

- `backend/atlas_service.py` still declares `SCENARIOS = ("A", "B", "C")`, documents the
  private tier as "TMY3 (Session 7, 540-cell factorial)", calculates overview `n_cells` by
  multiplying the A count by 3, and reads `data/atlas/replocx_tmy3/...`.
- `tests/test_atlas.py` still asserts exactly `{"A", "B", "C"}`, checks for `"540"` in
  provenance, and validates the old A < C < B ordering instead of the four-scenario contract.
- `frontend/src/lib/types.ts` defines `Scenario = "A" | "B" | "C"`; `frontend/src/routes/atlas/atlas.ts`
  exports `SCENARIOS = ["A", "B", "C"]` and a three-color palette.
- `backend/fastapi_app.py` and `backend/server.py` already route `/api/v1/results/*` and
  `/api/v1/equity/*` through `atlas_routes.py`; this dispatch should be preserved while the
  payload contract is migrated.
- `frontend/src/lib/api.ts` already has the in-memory bearer-token retry prompt, so W4 should
  add the reverse-proxy/basic-auth boundary and leak tests rather than inventing a new identity
  system.

---

## 1. Resolved §9 design questions (recommendations Codex should treat as decisions)

These convert the brief's open questions into concrete, buildable positions. Items marked
**[OWNER-CONFIRMED]** were locked in this session; **[RECOMMEND]** is a default Codex should
follow unless the owner overrides.

1. **Story architecture — [RECOMMEND] guided-first, free-explore always one click away.**
   A single scroll spine (Intro → How locations were selected → Results A/C/B/D → the
   sealed-passive **D** panel → Equity), where each section is a self-contained "scrollytelling"
   card with a default framing but a persistent **"Explore this yourself"** affordance that
   drops the reader into the interactive map/pivot pre-filtered to that section's state.
   **D leads without overwhelming** by being introduced *as a contrast, not a fourth column*:
   the D panel opens on the three precomputed story contrasts (D−B natural-ventilation effect,
   D−C peak-window effect, D−A full-AC protection) rather than raw D levels. Raw D sits behind
   the same "explore" affordance.

2. **Map vs pivot — [RECOMMEND] land on the pivot, offer the map as the drill path.**
   The reader lands on a **national stratum × scenario pivot** (the "overview first" that OWID/
   IPCC Atlas use), because the headline finding is cross-stratum, not per-site. The MapLibre
   map is the **drill-down**: clicking a site opens a drawer → deep link `/atlas/sites/<id>`.
   Deep-link scheme: `/atlas/sites/<site_id>?scenario=<A|C|B|D>&tier=<annual|seasonal>&metric=<endpoint>`;
   national pivot state is also URL-encoded so any view is shareable. (This inverts the scaffold
   if it currently defaults to the map — verify in W0.)

3. **Metric framing — [RECOMMEND] p95/exposure-hours is the default; mean is opt-in and always paired.**
   Default metric selector value = `op_temp_p95_true_c` (and the exposure-hour family), never the
   mean. Any view that shows a mean **must** render its extreme counterpart beside it (enforced in
   a shared chart wrapper, not per-view). Threshold selector: a small segmented control
   (e.g. >28 °C / >30 °C for overheating; the canonical humidity threshold for high-humidity),
   with the active threshold echoed in every subtitle and export. This operationalizes the
   R3/R5 "signal is in the extremes, not the mean" finding.

4. **Equity transparency — [RECOMMEND] borrow CDC-SVI badging conventions.**
   Every equity layer carries a **proxy badge** (`Modeled` / `Proxy` / `Direct`) + a source-and-vintage
   chip (e.g. "CDC SVI 2022, tract→catchment area-weighted"). Uncertainty shown as a muted band or
   an explicit "join uncertainty" note where the crosswalk is one-to-many. Surface the **D-related**
   equity contrast that matters most: sealed-passive (**D**) overheating-exposure hours vs
   catchment SVI/energy-burden percentile — i.e. "who bears the most exposure when there is no
   cooling and no ventilation." Keep it descriptive; no causal claims.

5. **Auth + private boundary — [OWNER-CONFIRMED] reverse-proxy basic auth + existing bearer token.**
   Front the private host with HTTP basic auth (nginx/Caddy) **and** keep the app's bearer-token
   gate on `/api/results/*` + `/api/equity/*` + Atlas frontend routes (defense-in-depth). No new
   identity system. The public synthetic selection demo keeps `RLE_ENABLE_ATLAS` **off** and never
   mounts the private tier — this is the leak-prevention invariant, tested in W4.

6. **Figure–chart parity — [RECOMMEND] one derived-table source of truth.**
   ECharts must read the **same derived CSVs** that produced the `f2v3_final` figures (the
   registry's `source_csv` column), not a parallel query path. Add a **parity gate**: for each
   figure with an interactive twin, assert the chart's plotted values equal the figure's
   `source_csv` values within a tiny tolerance (max|diff| ≈ 0). This is the single best defense
   against "the site says X, the paper figure says Y."

7. **Acceptance criteria — [RECOMMEND] precedent patterns become per-session gates.**
   OWID/NREL EULP/IPCC Atlas/CDC-SVI converge on four testable properties, folded into the gates
   below: (a) **download** — every view exports its underlying data + citation; (b) **provenance** —
   every table/figure resolves to a certified tier id + sidecar; (c) **selector legibility** — scenario/
   metric/threshold selectors are labeled with descriptive terms and never assume a fixed count;
   (d) **caveat visibility** — proxy/uncertainty/threshold notes are on-screen, not hidden.

---

## 2. Optimized session plan (W0–W4)

Format per session: **Goal → Preconditions → Work → Gate (measured) → Handoff.**
Every session appends a dated entry to `docs/SESSION_HANDOFF.md` with **measured** gate values
and never edits prior entries. Every session ends on a green `scripts/verify_all.sh` (or the
documented reason a specific matrix leg is deferred).

Dependency graph: **W0 → W1 → W2 → {W3 ∥ export-half of W2} → W4.** W0 is the long pole.

---

### W0 — Audit, reconcile, and freeze the four-scenario contract *(the critical session)*

**Goal.** Turn the legacy 3-scenario scaffold into a *known quantity*, re-point it at the
certified 720-cell four-scenario tier and `f2v3` registry, and **freeze** the results + equity
API schema so W1–W3 can't reintroduce a three-scenario assumption.

**Preconditions.**
- `feature/research-atlas` current with `main`; scratch/lock files removed.
- The PhD Framework canonical sources are **reachable read-only** from the Mac. The OneDrive mount
  is cloud-synced and can stall on first access — **materialize (download) the exact `_CANONICAL/`
  subtrees the Atlas consumes before coding**, or stage a read-only copy under a path pointed to
  by `RLE_ATLAS_DATA_DIR`. Record the resolved absolute path in the handoff. *(This was not
  verifiable from the planning sandbox and is the #1 thing to confirm first.)*

**Work.**
1. **Scaffold audit (write it down).** Enumerate every place the current code assumes three
   scenarios or the 540-cell tier: `SCENARIOS`, `SCENARIO_LABELS`, the `scenario_c` special-case,
   `data/atlas/replocx_tmy3/*`, `atlas_metadata.json`, `equity_profile.csv`, the `atlas_routes.py`
   table, `AtlasShell.tsx`, `atlas.ts`, and tests. Produce a short `docs/atlas/W0_scaffold_audit.md`.
2. **Canonical mapping.** For each certified CSV/dictionary in the 4scen tier
   (`replocx_tmy3_wallfix_4scen/{annual,seasonal}/…`, `metadata/…scenario_dictionary…`,
   `…endpoint_definitions…`, `d_specific_comparisons`, `by_{climate,urbanicity,building,vintage}_scenario`),
   define the exact endpoint that will serve it and the field-name translation to descriptive labels.
3. **Precedent → acceptance criteria.** Convert OWID / NREL EULP / IPCC Atlas / CDC-SVI
   download+provenance+selector+caveat patterns into the concrete per-session gates already listed
   in §1.7; record in `docs/atlas/W0_acceptance_criteria.md`.
4. **Freeze the schema.** Author JSON Schemas for every results + equity payload and **golden
   fixtures** derived from the real tier (small, checked-in, clearly labeled). Schemas encode:
   `scenario` ∈ {A,C,B,D} with `scenario_order` and `scenario_display_label`; both `annual` and
   `seasonal` tiers; the D−B/D−C/D−A comparison fields; figure resolution via `atlas_route`,
   `figure_class`, `source_csv`, `provenance_sidecar`; descriptive-label-primary payloads.
5. **Re-point + rename (no new features).** Update `atlas_service.py` constants/paths to the 4scen
   tier and canonical labels; keep endpoints returning *shaped* data even if some fields are stubbed
   pending W1. Do **not** yet build the D story panels — just make the contract four-scenario-true.

**Gate (measured).**
- Resolved canonical data path recorded; a fixtures-load smoke test passes.
- `grep` proof: **zero** remaining `("A","B","C")` / hard-coded-3 / `f2v2`/`f1v2` references on any
  served path (paste the grep command + empty result into the handoff).
- JSON Schemas + golden fixtures committed; a schema-validation test passes and **fails** if D or any
  primary endpoint family is omitted (add a deliberately-broken fixture to prove the negative).
- `scripts/verify_all.sh` green (or documented deferral).

**Handoff.** `docs/atlas/W0_*` files + schema/fixtures committed; migration risks logged.

---

### W1 — Results API over the 720-cell four-scenario tier (backend)

**Goal.** Serve A/C/B/D annual + seasonal results and the D-specific comparisons through the
existing dispatch, with contract tests that make a three-scenario regression impossible.

**Work.**
- Implement/upgrade `/api/results/*` (mapped from `/api/v1/results/*`): `overview`,
  `scenario-summary`, `by-stratum` (climate/urbanicity/building/vintage), `differential`
  (D−B / D−C / D−A), `cooling-seasons`, `sensitivity`, `provenance`, plus a **scenario-dictionary**
  endpoint returning A/C/B/D display label + order + color + cooling/heating/NV semantics.
- Reconcile the legacy `scenario-c` route: keep a **Scenario-C intervention** endpoint (it powers a
  real story panel) but re-source it from the 4scen tier and stop treating C as special in the core
  scenario loop.
- Contract tests: every default results payload returns all four scenarios; a payload missing D or
  any primary endpoint family (`op_temp_mean_c`, `op_temp_p95_true_c`, `humidity_ratio_mean_kgkg`,
  `humidity_ratio_p95_true_kgkg`) **fails** the suite. Provenance points to the 720-cell tier.

**Gate (measured).** API tests green; contract tests enumerate 4 scenarios and reject 3; provenance
metadata = 720-cell 4scen tier id; coverage ≥ repo floor (≥50%); `ruff`/`black`/`mypy` clean;
old 540 tier not served as current (grep proof).

---

### W2 — Atlas UI + story spine (frontend)

**Goal.** Build the guided story spine and the two entry points on the existing shell, with the
sealed-passive **D** panel and figure–chart parity.

**Work.**
- Scenario/metric/threshold selectors use descriptive labels + the colorblind palette
  (`#0072B2 / #009E73 / #E69F00 / #D55E00`); Scenario C reads "AC 2–8pm + NV other hours".
  Default metric = p95/exposure-hours; mean always paired (shared chart wrapper, per §1.3).
- Story spine with progressive disclosure (§1.1); pivot-first landing (§1.2); map drill-down →
  `/atlas/sites/<id>` deep links with URL-encoded state.
- **D panel** opens on the three story contrasts (D−B/D−C/D−A); raw D behind "explore".
- Embed `f2v3_final` figures resolved from the registry `atlas_route`; **F19 under
  Supplementary/Methods**, never the main grid. Charts read the registry `source_csv`.
- **Parity gate** (§1.6): interactive chart values == figure `source_csv` values (max|diff| ≈ 0).
- Responsive QA desktop/tablet/mobile.

**Gate (measured).** Playwright e2e green; no chart/label overlap at any breakpoint (screenshot
evidence); D present in every relevant selector/view; terminology enforced ("Overheating exposure
hours" / "High-humidity exposure hours" with thresholds in notes); figures link **only** to
`f2v3_final` (grep proof); parity gate passes with reported max|diff|.

---

### W3 — Equity overlays + exports + provenance

**Goal.** Join real equity proxies to the 20 catchments, extend everything to D, and ship
downloads + a provenance page.

**Work.**
- **Verify equity source first** (open risk): locate + confirm CDC SVI / ACS median-income+poverty /
  DOE LEAD energy-burden source data and its catchment join and vintage **before** building overlays.
  If `data/atlas/equity_profile.csv` is synthetic/legacy, replace with the verified join; if the real
  source isn't yet reachable, ship the endpoints against verified data only and mark unverified layers
  `REVIEW REQUIRED` (never silently "ready").
- `/api/equity/*`: `profiles` (per-catchment SVI percentile, income, poverty, energy burden with proxy
  badges + uncertainty) and `scenario-cross` extended to **all four scenarios**, including the
  D-related exposure×vulnerability contrast (§1.4).
- Exports: per-figure/table CSV + citation text + PDF/PNG/SVG links (all `f2v3_final`); provenance page
  reflecting the R9 tier + `f2v3` gate report. Reuse `backend/exports.py`.

**Gate (measured).** Equity endpoints + exports include D; every proxy badged + uncertainty visible;
exported figures/tables carry certified four-scenario provenance; any unverified equity layer is
explicitly `REVIEW REQUIRED`, not "ready"; tests green.

---

### W4 — Private authenticated deploy + release audit

**Goal.** Deploy the real 720-cell results to an approved private host behind auth; prove the public
demo can't leak it.

**Work.**
- Auth (§1.5): reverse-proxy basic auth in front of the private host **+** the existing bearer-token
  gate on `/api/results/*`, `/api/equity/*`, and Atlas frontend routes. Secrets via env/secret store.
- Deploy per `docs/deployment_options.md` (private container or managed FastAPI bound to a private
  network); real outputs mounted **read-only**; `RLE_ENABLE_ATLAS=1` only on the private host.
- Complete the `deployment_options.md` "Do Not Deploy Real Data Until" checklist (approved host, auth
  in front, read-only mount, secrets handling, exact private repo URL) **before** go.
- **Leak test**: build the public demo image and assert `RLE_ENABLE_ATLAS` off, no private tier mounted,
  `/api/results/*` + `/api/equity/*` return 404/disabled, and no private data in the image layers.
- Figure-registry linkage resolves entirely to `f2v3_final`; release-audit note + screenshot/contact-sheet
  packet.

**Gate (measured).** Private auth enforced on all results/equity routes (unauth → 401/403 evidence);
public demo leak test passes (evidence); every route/figure/caption/table/download/provenance points to
the same certified four-scenario tier; **no default path links `f2v2_final` or any `f1v2*`** (grep proof);
full `verify_all.sh` matrix green.

---

## 3. Risk register

| # | Risk | Likelihood | Impact | Mitigation (which session) |
|---|---|---|---|---|
| R1 | **Silent 3-scenario assumption** survives migration (loop, default, test fixture, or UI selector still A/B/C) | High | High | W0 grep-proof gate + a negative test that fails when D is absent; W1 contract tests enumerate 4 |
| R2 | **Canonical data not reachable** / OneDrive cloud-only stalls; app silently reads legacy `data/atlas/replocx_tmy3` | High | High | W0 precondition: materialize `_CANONICAL/` subtree, record absolute path, fixtures-load smoke test; fail loudly if path missing |
| R3 | **Stale local data masquerades as real** (`data/atlas/*` is the 540 tier) | Med | High | W0 re-point + provenance assertion that served tier id == 720-cell 4scen; delete/quarantine legacy local copy |
| R4 | **Figure–chart divergence** (site numbers ≠ paper figures) | Med | High | §1.6 parity gate in W2; charts read registry `source_csv` only |
| R5 | **Equity source unverified** (join/vintage unknown) | Med | Med | W3 verify-first; `REVIEW REQUIRED` marking; never silently "ready" |
| R6 | **Superseded figures linked** (`f2v2`, `f1v2*`) | Low | High | grep-proof gate in W0 + W4; registry is the only figure source |
| R7 | **Private data leaks into public demo** | Low | Critical | §1.5 boundary + W4 leak test on the built public image |
| R8 | **v1 route mapping regressed** (`/api/v1/*`→`/api/*`) during migration | Med | Med | W1 keep dispatch table intact; add a route-contract test hitting `/api/v1/results/*` |
| R9 | **Branch drift** (atlas branch stale vs main; selection-lineage handoff confusion) | Med | Med | W0 rebase/confirm; separate Atlas handoff entries from selection Session 9–11 lineage |
| R10 | **Scope creep from richer legacy routes** (cooling-seasons/sensitivity beyond brief) | Low | Med | Keep existing useful routes, but gate each on 4-scenario correctness; don't add net-new analytics |

---

## 4. Guardrails Codex must not violate (unchanged, restated for the migration)

- Four scenarios (A/C/B/D) on **every** path; no three-scenario assumption survives.
- Link **only** `f2v3_final`; never `f2v2_final` or any `f1v2*`.
- Descriptive labels primary; codes in provenance/detail only; enforce "Overheating exposure hours" /
  "High-humidity exposure hours" with thresholds in notes.
- Real 720-cell results + equity are **private, behind auth**; public demo stays synthetic + selection-only
  with `RLE_ENABLE_ATLAS` off.
- Read-only over canonical CSVs; **recompute nothing**; every served table/figure carries provenance to
  the certified tier.
- Vintage/equity contrasts lead on p95 + exposure/degree-hours, not the mean; pair any mean with its extreme.
- Never weaken a quality gate (`ruff`/`black`/`mypy`/coverage≥50/`pip-audit`) to get green.

---

## 5. What changed vs the uploaded plan (summary for the owner)

1. **Reframed W0** from "study precedent + freeze schema" to a full **scaffold audit + 3→4 scenario
   migration + schema freeze** — because the scaffold already exists and is a generation behind.
2. **Shrank W1/W2** (chassis, routes, charts, bearer-auth prompt already exist) and **shrank W4 auth**
   to reverse-proxy basic + existing bearer.
3. **Resolved all seven §9 questions** into build-ready decisions (pivot-first landing, guided-first story,
   p95 default with paired mean, CDC-SVI-style proxy badging, defense-in-depth auth, single derived-table
   parity source, precedent-as-gates).
4. **Added a figure–chart parity gate** and a **public-demo leak test** as first-class gates.
5. **Added a 10-item risk register** dominated by migration risks (silent A/B/C survival, stale/unreachable
   data) absent from the greenfield framing.
