# ReplocX Deployment Record

Authoritative record of the ReplocX deployments: the public demo (live) and the
private production instance (prepared, pending owner-executed deploy + sign-off).

## 1. Public demo — LIVE

| Field | Value |
| --- | --- |
| Service | `replocx` (Render, Docker runtime, `render.yaml`) |
| URL | <https://replocx.onrender.com> |
| Data mode | `demo` (bundled synthetic `data/demo/`, 2,959 candidates) |
| Auth | none (open; serves no private data) |
| Plan | free (spins down after 15 min idle; first request cold-starts ~30 s) |
| Verified | June 8, 2026 (Session 10) — see `docs/SESSION_HANDOFF.md` |

The demo never serves the national dataset. This record's remaining sections are
about the **private** instance only.

## 2. Private production — selected infrastructure decisions

The owner selected `B1 + C1` on July 8, 2026: an approved
VM/Docker Compose/Caddy host with HTTP Basic auth plus the app token. The older
Session 11 Render blueprint remains a historical alternative, not the selected
Atlas release path. `TO CONFIRM` items are completed before live deployment.

| Decision | Value |
| --- | --- |
| Host / platform | Approved organization-controlled VM running `docker-compose.atlas-private.example.yml` with Caddy as the only edge; exact host **TO CONFIRM** |
| Instance plan | Small always-on VM sized for the app, Caddy, and reviewer traffic — **TO CONFIRM** provider and size |
| Region | **TO CONFIRM** based on organization policy and reviewer location |
| Access-control owner | **TO CONFIRM** (named individual responsible for the token + IP allowlist) |
| Authentication | Reverse-proxy HTTP Basic auth plus app token (`RLE_PRIVATE_AUTH_TOKEN`), translated to Bearer upstream |
| Network restriction | `atlas-app` is internal-only; Caddy publishes 443; org egress / VPN ranges — **TO CONFIRM** |
| Persistent storage | Compose `atlas-state` volume with SQLite at `/state/scenarios.sqlite3`; host snapshot/backup policy **TO CONFIRM** |
| National/Atlas data delivery | Out-of-band read-only mounts; the public-safe image does not bake `pipeline/out`, `data/atlas`, or f2v3 assets |
| Data-retention rules | Certified inputs are immutable/reproducible. Scenario database retention and purge policy — **TO CONFIRM** |
| Backup owner | **TO CONFIRM** (owns VM snapshots and SQLite backup/restore drills) |
| Budget | **TO CONFIRM** (VM, storage/snapshots, DNS, and monitoring) |
| Secret manager | **TO CONFIRM** source of truth for Basic credentials and `RLE_PRIVATE_AUTH_TOKEN`; never commit secrets or plaintext hashes |
| Error tracking | Optional Sentry via `RLE_SENTRY_DSN` — **TO CONFIRM** whether enabled |
| TLS | Caddy-managed TLS for the approved private DNS name |
| Exact private repository | **TO CONFIRM** before publication |

### Research Atlas W4 addendum (July 8, 2026)

- Certified Atlas root: `replocx_tmy3_wallfix_4scen` (720 cells, A/C/B/D,
  R9 PASS); figure root: `f2v3_final`.
- Sidecar-backed equity profile is READY: 20 records and 4/4 verified layers.
- The executable private candidate is
  `docker-compose.atlas-private.example.yml` plus
  `deploy/atlas-private/Caddyfile`; real mounts are `:ro`.
- The public Docker runtime now uses an allowlist and explicitly keeps
  `RLE_ENABLE_ATLAS=0`.
- N5 exercised the committed boundary as real containers on July 9, 2026:
  actual image/layer leak scan PASS; Caddy 401 / app-token 401 / authorized
  200 matrix PASS; app host port absent; all analytical bind mounts read-only;
  certified route, equity, and export audit PASS. Evidence:
  `docs/atlas/N5_CONTAINER_BOUNDARY_AUDIT_2026-07-09.md`.
- Live deploy remains blocked on the `TO CONFIRM` owner/infrastructure fields.
  N5 is local container verification, not a live deployment or owner sign-off.

### Historical Render alternative confirmed June 8, 2026

These facts explain the older `render.private.example.yaml` option. They do not
override the selected B1 VM/Compose/Caddy release path.

- Persistent disks require a **paid** instance; the default filesystem is
  ephemeral, so a free instance would lose all saved scenarios on every
  deploy/restart. ([Render Docs — Persistent Disks](https://render.com/docs/disks))
- Disks are encrypted at rest with **automatic daily snapshots retained ≥ 7
  days**, restorable from the dashboard. ([Render Docs — Persistent Disks](https://render.com/docs/disks))
- A disk binds to one instance, is unavailable during build/one-off jobs, and
  **disables zero-downtime deploys** (brief downtime on each deploy).
- **Free** web services spin down after 15 min idle; **paid** instances do not.
  ([Render Docs — FAQ](https://render.com/docs/faq))
- Inbound IP rules and managed TLS are available for the service.

## 3. Pre-deploy verification — LOCAL evidence (June 8, 2026)

Run against the committed national outputs in `pipeline/out/` on the prepared
toolchain. Sandbox Python is 3.10, so `datetime.UTC` (3.11+) was provided via a
`sitecustomize` shim — behavior identical to the CI 3.11/3.12 runtime.

**Dataset invariants** — `python -m pipeline.validate --dir pipeline/out`:
`OK — schema and invariants hold`.

| Check | Result |
| --- | --- |
| Strata | 20, all `RESOLVED` (5 climate regions × 4 urbanicity) |
| Distinct catchments | 20 / 20 |
| County/CBSA rule | 4 rural → County, 16 non-rural → CBSA |
| Geometry | 20 / 20 valid (19 Polygon + 1 MultiPolygon), 0 null |
| Weather QC | 19 `COMPLETE`, 1 `INCOMPLETE` (NY Port Authority, 85.6%) — honestly flagged, no `PENDING` |
| ZIP crosswalk | 54,242 rows, 39,299 distinct ZIPs (HUD-USPS Q1 2025), one-to-many retained |
| ResStock enumeration | 20 / 20 enumeration-verified against the real NREL dictionary |
| Score weights | sum to 1.0 (enforced by validate) |
| Source metadata | `method_version: 3.0-national-tract`, 2020 tract boundaries, ACS 2019–2023, Jul-2023 CBSA delineation, NOAA ISD 2023 |

**Production-mode application** — `RLE_ANALYSIS_DATA_DIR=pipeline/out`,
`RLE_REQUIRE_AUTH=1`, `RLE_PRIVATE_AUTH_TOKEN` set:

| Check | Result |
| --- | --- |
| `/api/v1/health` | `data_mode: production`, `data_ready: true`, `candidate_count: 4019`, `selected_count: 20`, `auth.required/configured: true` |
| Protected route, no token | `GET /api/v1/dashboard` → **401** JSON |
| Protected route, valid token | `GET /api/v1/dashboard` → **200**; `/api/v1/candidates` total **4019** |
| Scenario persistence | `POST /api/v1/scenarios` → **201**; read back at version 1; row written to SQLite |
| Exports (auth required) | `site-list.csv` (20), `openstudio-manifest.json` (`rle.openstudio_manifest/1.0`, 20 sites), `resstock-sampling.csv` (20) — all 200 with token, **401** without |
| Structured logs | one-line JSON `http_request` events with status + duration |

## 4. Ready-to-execute deploy plan

Prerequisites: approved VM, private DNS name, firewall/VPN policy, secret-manager
credentials, Docker Engine, and the certified read-only host paths from §2.

1. **Prepare the VM.** Patch the OS, install Docker Engine with Compose support,
   configure the private DNS record, and make the certified analysis/Atlas/
   f2v3 host paths available read-only to the deployment account.
2. **Inject secrets.** Supply `RLE_BASIC_AUTH_USER`,
   `RLE_BASIC_AUTH_HASH`, `RLE_PRIVATE_AUTH_TOKEN`, `RLE_PRIVATE_HOST`, and
   optionally `RLE_SENTRY_DSN` from the approved secret manager. Do not use a
   committed production `.env` file.
3. **Restrict the network.** Keep the app port private; expose only the
   Basic-auth proxy, add confirmed org/VPN ranges, and confirm TLS is active.
4. **Deploy the stack.** Validate the resolved Compose configuration, build the
   public-safe app image, start Caddy and the app, and inspect the real image
   layers before accepting the deployment.
5. **Verify** with the post-deploy smoke checklist
   (`docs/OPERATIONS_RUNBOOK.md` §6): production data mode, 401-without /
   200-with auth, 4019 candidates, exports, scenario persistence over HTTPS, and
   confirm no private rows or token appear in logs.
6. **Take the first scenario backup** and confirm the VM/volume snapshot policy
   plus a restore drill owner.
7. **Record results** in §5 below and tag the production release (§6).

## 5. Deploy log

| Date | Actor | Action | Result |
| --- | --- | --- | --- |
| 2026-06-08 | Session 11 | Prepared private blueprint, runbook, and local verification | Local production verification PASS; live deploy pending owner |
| 2026-07-08 | Session 17 / W4 | Prepared Atlas Basic+app-token boundary, read-only mounts, public-image allowlist, and clarified selection-demo vs certified-Atlas UI state | Local W4 verification PASS; live deploy and owner sign-off pending |
| _TBD_ | _owner_ | Executed private deploy + post-deploy smoke | _record URL, smoke results_ |

## 6. Owner sign-off and production release tag

Tag the production release **only after** owner sign-off and a passing live smoke.

- [ ] Owner sign-off recorded (name + date): ______________________
- [ ] Live post-deploy smoke PASS (attach output)
- [ ] No private data or token in logs
- [ ] First scenario backup taken; VM/volume snapshot and restore owner confirmed

```bash
# after sign-off, on the release commit:
git tag -a v1.2.0-production -m "ReplocX private production deployment (national dataset)"
git push origin v1.2.0-production
```

Record the tag, commit hash, and live (private) URL here once complete.
