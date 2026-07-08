# ReplocX Research Atlas — Post-W4 Review and Next-Session Plan

**Prepared:** 2026-07-08
**Repo:** `/Users/cch322/Developer`
**Current branch:** `feature/research-atlas`
**Reviewed sources:** `ATLAS_CODEX_PROMPT_PACK_2026-07-07.md`,
`docs/SESSION_HANDOFF.md`, W0-W4 deliverables, deployment examples, release
audit, tests, screenshots, Git state, and fresh local verification.

## 1. Executive state

W0-W3 and the follow-on W3.5/W3.5B equity work are implemented. W4 is a
**locally verified release candidate**, not a completed production deployment.

**Owner build choice recorded on 2026-07-08:** `A2 + B1 + C1 + D1`.

That means the next move is to make the current W4 record truthful, isolate a
clean Atlas-only release branch, then add the selected product-depth work before
the first live private deployment. The deployment target remains a private
VM/Compose/Caddy boundary with Basic auth plus app token.

### Current status by workstream

| Workstream | State | Handoff / principal deliverables | Remaining issue |
| --- | --- | --- | --- |
| W0 contract freeze | Complete | Session 13; `docs/atlas/W0_*`, schema, golden/negative fixtures | None blocking |
| W1 results API | Complete | Session 14; canonical read-only A/C/B/D API, D comparisons, R9/f2v3 provenance | None blocking |
| W2 Atlas UI | Complete with two accepted scope gaps | Session 15; story spine, responsive QA, D panel, Fig02 parity | Owner selected A2, so full 20-stratum pivot and parity beyond Fig02 are pre-release work |
| W3 exports/provenance | Complete | Session 16; equity contracts, exports, provenance, figure bundles | Session 16's equity status was superseded |
| W3.5/W3.5B equity | Complete | Newest handoffs; 20 records, 4/4 layers READY, reproducible builder and sidecars | Preserve external canonical artifacts and checksums |
| W4 private release | **Local candidate PASS; production not released** | Caddy/Compose example, public-image allowlist, auth/leak checker, release audit, screenshots | Missing W4 handoff closeout, dirty/mixed Git state, no real container run, no approved live host/sign-off |

## 2. What the W0-W4 execution actually accomplished

### W0 — strong contract-first migration

The migration risk was correctly identified as stale three-scenario assumptions,
not missing greenfield infrastructure. The work froze A/C/B/D order, 720-cell
provenance, endpoint families, and f2v3-only figure resolution. Negative fixtures
prove that missing D, A/B/C-only payloads, wrong order, and superseded figure
paths fail.

Assessment: **green**. The single bundled schema is sufficient for the current
contract tests, even though the original prompt described plural endpoint
schemas.

### W1 — canonical backend migration is complete

The service reads the certified tier read-only, requires sidecars, validates R9,
serves annual/seasonal strata and D-B/D-C/D-A comparisons, and fails loudly
against the legacy scaffold. Both `/api` and `/api/v1` routing are covered.

Assessment: **green**.

### W2 — usable guided Atlas, with two conscious reductions

The UI has the guided story spine, A/C/B/D labels and palette, p95/exposure-hour
framing, threshold notes, D contrasts, site drill-down, f2v3 integration, and
responsive screenshots.

Two original ambitions were narrowed:

1. The landing pivot is climate-region × scenario, not the complete 20
   climate-by-urbanicity strata × scenario view.
2. Formal figure-chart equality is proven for Fig02 only, not every interactive
   twin.

Assessment: **green as executed**, but under the owner-selected A2 path these
two reductions become pre-release product-depth work rather than post-release
enhancements.

### W3 plus W3.5/W3.5B — complete, certified equity

Session 16 honestly stopped at `REVIEW REQUIRED`. Later W3.5 work superseded
that state. The current canonical root contains a sidecar-backed 20-row profile
with all four layers READY:

- CDC/ATSDR SVI — Proxy
- ACS income/poverty — Direct
- DOE LEAD energy burden — Proxy
- heat vulnerability — Modeled

Assessment: **green**. The prompt pack's opening W4 notes are stale because they
predate W3.5/W3.5B.

### W4 — implementation is real, but the handoff overstates closure

Implemented deliverables:

- private Caddy + Docker Compose candidate with Basic auth at the edge;
- independent in-app token gate using `X-RLE-Auth` at the browser and Bearer
  translation upstream;
- read-only data/figure mounts in the Compose candidate;
- public Docker runtime allowlist and explicit `RLE_ENABLE_ATLAS=0`;
- local auth, certified-route, equity, public-disable, and file-leak checker;
- W4 release audit and screenshot/contact-sheet packet.

Fresh verification on 2026-07-08:

- `scripts/check_atlas_release.py`: **PASS**.
- Auth evidence: proxy blocks unauthenticated frontend/results/equity; app
  blocks Basic-only API calls; Basic + app token returns 200.
- Certified evidence: 720 cells, A/C/B/D, R9 PASS, f2v3_final, 4/4 equity layers
  READY, 20 records.
- Public evidence: Atlas APIs return 404/disabled and the runtime allowlist scan
  finds no certified tier, sidecar, or f2v3 asset collision.
- `scripts/verify_all.sh`: **all checks passed**; 120 backend tests in each data
  mode, 72% coverage, no known backend dependency vulnerability, 49 frontend
  tests, production build, and 13 Playwright tests passed with one
  mode-appropriate skip.
- Private-enabled Atlas Playwright rerun: **1 passed, 1 disabled-mode skip**.

Why W4 is not yet “released”:

1. `docs/SESSION_HANDOFF.md` has no W4/Session 17 entry.
2. `docs/DEPLOYMENT_RECORD.md` still says the final local gate is pending.
3. No approved private host, DNS name, access owner, secret manager, retention
   owner, or live sign-off is recorded.
4. Docker is not installed in the current environment, so the committed
   Caddy/Compose pair and a built image have not been exercised as containers.
   The current leak test inspects the intended runtime allowlist, not real image
   layers.
5. Git is unsafe to release as-is: 25 commits ahead / 6 behind `origin/main`,
   with 618 status entries, 592 staged entries, and unrelated generated,
   paper-workspace, and automation files mixed into the index.
6. `CHANGELOG.md` still describes the old 540-cell A/B/C Atlas and all equity
   layers as `REVIEW REQUIRED`.
7. The W4 contact sheet shows a global `DEMO` badge while presenting certified
   private Atlas results. That reflects the local selection-data mode, but it is
   visually ambiguous and should not be the final release screenshot.

## 3. Owner decisions now locked

The owner selected the following build path on 2026-07-08:

`A2 product-depth before release` + `B1 approved VM/Compose/Caddy` +
`C1 Basic auth + app token` + `D1 clean Atlas-only release series`.

This supersedes the earlier recommended default of `A1 release-first`. The
reasoning is coherent: the first private reviewer experience should feel
methodologically complete, not merely operationally available. For this project,
that means the full 20-stratum climate-by-urbanicity pivot and full interactive
parity gates should land before any live private deployment.

### Decision A — selected: A2 product-depth before release

Add the full 20-stratum pivot and parity gates for every interactive figure
before any deploy.

Best when: the first reviewer is likely to evaluate methodological completeness,
research credibility, and product polish more heavily than raw deployment speed.

Tradeoff: deployment moves later, and the added surface must be re-audited
before release.

### Decision B — selected: B1 approved VM + Docker Compose + Caddy

Use the already prepared Caddy/Compose boundary on a small private VM or
organization-controlled host.

Why it fits: it directly supports a private app network, edge-only port,
read-only bind mounts, two-layer auth, and real container/image verification.

Tradeoff: someone owns patching, backups, DNS, and uptime.

### Decision C — selected: C1 Basic auth + app token

Keep the currently implemented two-layer gate for the first small reviewer
group. Rotate both secrets independently.

Escalate to SSO or identity-aware access later only if policy requires per-user
revocation, institution-level audit, or a larger reviewer group.

### Decision D — selected: D1 clean Atlas-only release series

Create a clean worktree from updated `origin/main`, then bring over only the
reviewed Atlas, equity-builder, deployment, test, and documentation changes in
logical commits.

Do not ship the current mixed worktree as one large commit. It would mix
hundreds of unrelated generated files and weaken reviewability, reversibility,
and portfolio credibility.

## 4. New session-by-session plan for A2 + B1 + C1 + D1

Do not combine these sessions. Each session must append measured evidence to
`docs/SESSION_HANDOFF.md` and stop at its gate.

The A2 choice changes the order: product-depth work is now mandatory before
live deployment. N1 and N2 still happen first because stale records and a mixed
worktree would make the product-depth sprint harder to trust.

### Session N1 — Close W4 locally and make the records truthful

**Goal:** Convert the locally passing W4 candidate into a fully documented local
release candidate, while recording the owner-selected `A2+B1+C1+D1` path.

**Work:**

1. Add an append-only W4/Session 17 handoff entry with the fresh measured gates
   above.
2. Record the owner decision: A2 product-depth before release, B1 VM/Compose/Caddy,
   C1 Basic+app token, D1 clean release series.
3. Update `docs/DEPLOYMENT_RECORD.md` from “local verification pending” to local
   PASS while leaving live deployment/sign-off pending.
4. Update `CHANGELOG.md` to the 720-cell A/C/B/D, f2v3, and 4/4 READY equity
   state.
5. Refresh the prompt pack's W4 readiness note so W3.5B and the A2 path are
   authoritative.
6. Resolve the screenshot's ambiguous `DEMO` badge:
   - preferred: capture against approved production selection data plus the
     certified Atlas tier; or
   - change the UI badge to distinguish “selection data mode” from “Atlas
     certified tier,” then recapture.
7. Re-run `scripts/check_atlas_release.py`, `scripts/verify_all.sh`, and both
   enabled/disabled Atlas Playwright modes.

**Gate:**

- W4 handoff exists and all documentation agrees on local PASS / live pending.
- The selected `A2+B1+C1+D1` build path is recorded in handoff/planning docs.
- No current release note describes 540 cells, A/B/C-only, or all-equity
  `REVIEW REQUIRED`.
- Final screenshots do not misleadingly label the certified Atlas itself as
  demo.
- All local gates pass.

**Stop:** no commit, rebase, push, infrastructure creation, or live deploy.

### Session N2 — Build a clean, reviewable Atlas release branch

**Goal:** Separate the Atlas release from the current mixed index and reconcile
the six `origin/main` commits without losing user work.

**Work:**

1. Inventory current staged, unstaged, and untracked files by product area.
2. Preserve the current worktree exactly; do not reset or mass-unstage it.
3. Fetch `origin`, create a new clean worktree/branch from updated
   `origin/main`, using the `codex/` branch prefix unless the owner specifies a
   release branch name.
4. Transfer only the Atlas release files in logical groups:
   - W0 contract and fixtures;
   - W1 backend and API tests;
   - W2 frontend and browser tests;
   - W3/W3.5 equity builder, exports, and provenance;
   - W4 auth/container boundary and release docs.
5. Keep canonical private data outside Git. Keep legacy scaffold/demo artifacts
   only where tests explicitly need them.
6. Run the full verification matrix in the clean worktree.
7. Produce a file manifest and proposed commit series for owner review.

**Gate:**

- Clean branch is based on current `origin/main`.
- No unrelated `replocx_paper_workspace`, font cache, or
  `x_growth_automation` file is in the Atlas release diff.
- Private canonical CSVs, f2v3 assets, and secrets are absent from Git history
  and the build context.
- Full verification passes.

**Stop:** do not push or open a PR until the owner approves the manifest.

### Session N3 — A2 product-depth: full 20-stratum pivot

**Goal:** Make the Atlas landing and comparison flow support the complete
climate-region × urbanicity stratification, not only climate-region pivoting.

**Work:**

1. Inspect the certified backend result structure and existing W2 UI pivot.
2. Define a stable backend response contract for the 20 strata and scenario
   order `A`, `C`, `B`, `D`.
3. Add or extend backend tests so every climate-by-urbanicity stratum is covered
   and provenance remains R9/f2v3.
4. Update the frontend pivot, state model, labels, tooltips, and URL/share state
   so reviewers can move cleanly between climate, urbanicity, stratum, and site
   drill-down.
5. Keep aggregation server-side or from certified prepared outputs; do not
   invent ad hoc browser-side analytical summaries.
6. Update screenshots and docs to show the 20-stratum reviewer path.
7. Run targeted backend tests, frontend unit tests, Atlas Playwright, and the
   full verification matrix if the surface area changed broadly.

**Gate:**

- All 20 strata are visible or reachable through the guided Atlas experience.
- Scenario ordering and D comparison semantics remain unchanged.
- Disabled public-demo mode still blocks Atlas private APIs.
- Screenshots prove the 20-stratum flow.
- Tests pass with measured evidence in the handoff.

**Stop:** no deploy and no infrastructure changes.

### Session N4 — A2 product-depth: full interactive parity gates

**Goal:** Prove every interactive f2v3 twin agrees with its static certified
figure or explicitly document that no interactive twin exists.

**Work:**

1. Enumerate the f2v3 static figure registry and current interactive Atlas
   charts.
2. Create a parity manifest mapping static figures to interactive twins,
   including “not applicable” entries where the Atlas intentionally does not
   duplicate a static figure.
3. Add automated parity checks that report max absolute difference, tolerances,
   fixture/provenance hashes, and failure context.
4. Fix any chart transform, label, ordering, or filtering drift uncovered by the
   parity checks.
5. Update release audit and handoff records with the parity manifest and test
   results.
6. Re-run full verification after parity changes.

**Gate:**

- Every intended interactive f2v3 twin has a passing parity result.
- Every omitted twin is explicitly documented with rationale.
- The release audit no longer says parity is proven only for Fig02.
- Full verification passes.

**Stop:** no deploy and no infrastructure changes.

### Session N5 — B1/C1 real container boundary

**Goal:** Prove the candidate works as the committed Caddy + app containers and
inspect the actual public image.

**Precondition:** Docker/Podman is available on an approved machine.

**Work:**

1. Build the public app image with no private mounts.
2. Inspect image contents and saved layers for private tier identifiers,
   canonical asset basenames, sidecars, and secrets.
3. Start `docker-compose.atlas-private.example.yml` with temporary secrets and
   read-only canonical mounts.
4. Confirm the app container has no published host port and cannot write to
   analytical mounts.
5. Run proxy-level 401/200 smoke against the actual Caddy service.
6. Run the certified route/export/equity audit through the proxy.
7. Stop containers and verify no private data was copied into image layers or
   named volumes.

**Gate:**

- Actual image-layer leak scan passes.
- Actual Caddy + app stack passes unauthenticated, Basic-only, and
  Basic+app-token cases.
- Read-only writes fail.
- Evidence is attached to the handoff and release audit.

**Stop:** no public DNS or production credentials.

### Session N6 — B1 owner-assisted private deployment

**Goal:** Deploy the verified A2 candidate to the selected private host.

**Owner inputs required:**

- host/platform and private DNS name;
- access-control owner and reviewer list;
- Basic-auth and app-token secret source;
- retention/backup owner and policy;
- allowed networks or VPN ranges;
- exact private repository and release branch;
- budget approval.

**Work:**

1. Provision the approved host and private network.
2. Deliver canonical data and figures out of band; verify checksums before
   mounting read-only.
3. Configure TLS, Basic auth, app token, firewall/VPN restrictions, logging,
   backups, and health checks.
4. Deploy the release commit.
5. Run live frontend/API auth smoke, certified provenance/equity/export smoke,
   public-demo leak regression, and log inspection.
6. Record URL, commit, image digest, checksums, actors, results, and owner
   sign-off in `docs/DEPLOYMENT_RECORD.md`.

**Gate:**

- Live unauthenticated access is blocked.
- Authorized reviewers can use the Atlas.
- Certified provenance and equity match the local candidate.
- No private value or secret appears in public services, image layers, or logs.
- Owner signs off.

### Session N7 — Portfolio/network leverage package

**Goal:** Turn the deployed private Atlas into opportunity-generating proof
without exposing private data.

**Work options:**

- Create a sanitized public walkthrough using synthetic or demo-only data.
- Prepare a reviewer packet for advisors, collaborators, fellowships, funders,
  or hiring conversations.
- Write a concise case-study page that highlights the engineering/research
  boundary: certified data, provenance, private deployment, parity, and equity
  readiness.

**Gate:** the artifact demonstrates skill and credibility without leaking
private canonical results, paths, secrets, or reviewer-only URLs.

## 5. Paste-ready prompt for the next session

```text
Continue the ReplocX Research Atlas in /Users/cch322/Developer.

Read first:
- ATLAS_POST_W4_SESSION_PLAN_2026-07-08.md
- docs/SESSION_HANDOFF.md
- docs/DEPLOYMENT_RECORD.md
- docs/atlas/W4_RELEASE_AUDIT.md
- docs/deployment_options.md
- git status

Owner decision is locked as A2+B1+C1+D1:
- A2 product-depth before release;
- B1 approved VM + Docker Compose + Caddy;
- C1 Basic auth + app token;
- D1 clean Atlas-only release series.

Execute Session N1 only: close W4 locally and make the records truthful while
recording the A2+B1+C1+D1 path.

Treat W3.5B as the current equity source of truth: 20 records and all four
layers READY. Preserve the dirty worktree and existing staged state; do not
reset, commit, rebase, push, deploy, or modify external infrastructure.

Append a W4/Session 17 entry to docs/SESSION_HANDOFF.md with measured results.
Update stale W4 deployment records, the changelog, and any prompt-pack language
that still implies A1 release-first or pre-W3.5B equity status. Resolve the
ambiguous DEMO badge in the final private-Atlas screenshots. Re-run the local
W4 boundary, full verification, and both Atlas Playwright modes. Stop after
reporting the N1 gate and the exact starting point for N2.
```
