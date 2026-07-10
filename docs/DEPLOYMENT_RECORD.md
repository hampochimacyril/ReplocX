# ReplocX Deployment Record

Authoritative record of the ReplocX deployments: the public demo (live) and the
private production instance (live on Render, pending formal owner sign-off/tag).

## 1. Public demo — LIVE

| Field | Value |
| --- | --- |
| Service | `replocx` (Render, Docker runtime, public-demo `render.yaml` on the demo branch) |
| URL | <https://replocx.onrender.com> |
| Data mode | `demo` (bundled synthetic `data/demo/`, 2,959 candidates) |
| Auth | none (open; serves no private data) |
| Plan | free (spins down after 15 min idle; first request cold-starts ~30 s) |
| Verified | June 8, 2026 (Session 10) — see `docs/SESSION_HANDOFF.md` |

The demo never serves the national dataset. This record's remaining sections are
about the **private** instance only.

## 2. Private production — selected infrastructure decisions

The owner selected `B1 + C1` on July 8, 2026: an approved
VM/Docker Compose/Caddy host with HTTP Basic auth plus the app token. On July 9,
2026, the owner changed the immediate execution path to a GitHub-backed Render
deployment for speed. This Render path keeps private data out of Git and uses
the app token as the required reviewer gate; add Render inbound IP rules or an
external Basic-auth proxy if the original two-layer C1 boundary is required
before sign-off. `TO CONFIRM` items are completed before live deployment.

| Decision | Value |
| --- | --- |
| Host / platform | Render web service `srv-d983c558nd3s73bknkg0` from `hampochimacyril/ReplocX`, branch `codex/atlas-release-candidate`; <https://replocx-private-atlas.onrender.com> |
| Instance plan | Render paid `starter` Docker web service with persistent disk |
| Region | Render `oregon` unless owner changes it in the Dashboard |
| Access-control owner | Owner/operator for the Render workspace; named reviewer/access owner still **TO CONFIRM** for long-term operation |
| Authentication | Required app token (`RLE_PRIVATE_AUTH_TOKEN`) configured in Render service environment; optional Render inbound IP restriction or external Basic-auth proxy for two-layer access |
| Network restriction | Render public HTTPS endpoint plus app token; allowed IP/VPN ranges **TO CONFIRM** if using Render inbound IP rules |
| Persistent storage | Render disk `replocx-private-data` mounted at `/var/data`; SQLite at `/var/data/replocx/scenarios.sqlite3` |
| National/Atlas data delivery | Out-of-band upload to the Render disk; the public-safe image does not bake `pipeline/out`, `data/atlas`, or f2v3 assets |
| Data-retention rules | Certified inputs are immutable/reproducible. Scenario database retention and purge policy — **TO CONFIRM** |
| Backup owner | **TO CONFIRM** (owns VM snapshots and SQLite backup/restore drills) |
| Budget | Command/download/upload approval granted July 9, 2026; Render starter service and disk active; long-term spend owner **TO CONFIRM** |
| Secret manager | `RLE_PRIVATE_AUTH_TOKEN` currently stored as a Render service environment secret; longer-term source of truth for credential rotation **TO CONFIRM** |
| Error tracking | Optional Sentry via `RLE_SENTRY_DSN` — **TO CONFIRM** whether enabled |
| TLS | Render-managed TLS for the `.onrender.com` service domain; custom private DNS **TO CONFIRM** |
| Exact private repository | Owner-confirmed repository `https://github.com/hampochimacyril/ReplocX.git`, branch `codex/atlas-release-candidate` |

### Research Atlas W4 addendum (July 8, 2026)

- Certified Atlas root: `replocx_tmy3_wallfix_4scen` (720 cells, A/C/B/D,
  R9 PASS); figure root: `f2v3_final`.
- Sidecar-backed equity profile is READY: 20 records and 4/4 verified layers.
- The executable private candidate is
  `docker-compose.atlas-private.example.yml` plus
  `deploy/atlas-private/Caddyfile`; real mounts are `:ro`.
- The public Docker runtime now uses an allowlist and explicitly keeps
  `RLE_ENABLE_ATLAS=0`.
- The private Render release branch now uses `render.yaml` as a paid Docker web
  service Blueprint with a `/var/data` persistent disk and private Atlas env
  paths. Deployment instructions: `docs/RENDER_PRIVATE_DEPLOYMENT.md`.
- N5 exercised the committed boundary as real containers on July 9, 2026:
  actual image/layer leak scan PASS; Caddy 401 / app-token 401 / authorized
  200 matrix PASS; app host port absent; all analytical bind mounts read-only;
  certified route, equity, and export audit PASS. Evidence:
  `docs/atlas/N5_CONTAINER_BOUNDARY_AUDIT_2026-07-09.md`.
- Live Render deploy completed after N5; remaining `TO CONFIRM` fields are
  governance/operations items, not blockers for the running service. N5 remains
  local container verification, not owner sign-off.

### Render facts confirmed June 8-July 9, 2026

These facts apply to the selected Render execution path.

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

## 4. Ready-to-execute Render deploy plan

Prerequisites: owner access to Render, GitHub repo access, a secret value for
`RLE_PRIVATE_AUTH_TOKEN`, and the certified analysis/Atlas/f2v3 roots available
locally for out-of-band upload.

1. **Create the Render Blueprint** from
   `https://github.com/hampochimacyril/ReplocX`, branch
   `codex/atlas-release-candidate`. Render reads `render.yaml`.
2. **Set the secret** `RLE_PRIVATE_AUTH_TOKEN` in the Render Dashboard.
3. **Apply the Blueprint.** The first deploy may show degraded data until
   `/var/data` is populated.
4. **Package and upload private data** using
   `scripts/package_render_private_data.sh`; expand it on the Render disk so
   `/var/data/analysis`, `/var/data/atlas/replocx_tmy3_wallfix_4scen`, and
   `/var/data/atlas-figures/f2v3_final` exist.
5. **Redeploy/restart the service**, then verify production data mode, protected
   API 401 without token, authorized 200 with `X-RLE-Auth`, 720 cells,
   A/C/B/D, R9 PASS, `f2v3_final`, equity READY, and clean logs.
6. **Optionally add access restrictions**: Render inbound IP rules, custom
   domain, or an external Basic-auth proxy if policy requires C1 two-layer auth.
7. **Record results** in §5 below and tag the production release (§6) only after
   owner sign-off.

## 5. Deploy log

| Date | Actor | Action | Result |
| --- | --- | --- | --- |
| 2026-06-08 | Session 11 | Prepared private blueprint, runbook, and local verification | Local production verification PASS; live deploy pending owner |
| 2026-07-08 | Session 17 / W4 | Prepared Atlas Basic+app-token boundary, read-only mounts, public-image allowlist, and clarified selection-demo vs certified-Atlas UI state | Local W4 verification PASS; live deploy and owner sign-off pending |
| 2026-07-09 | Session N6 preflight | Owner granted command/download approval; release commit `a13157d` prepared; branch `codex/atlas-release-candidate` published to `hampochimacyril/ReplocX`; certified smoke PASS; no host/DNS/secret-manager/network target found | Correct release branch published; live deploy remains blocked on concrete infrastructure values |
| 2026-07-09 | Session N6 Render pivot | Owner selected Render from GitHub; root `render.yaml`, data-packaging helper, and Render deploy guide prepared for the release branch | Ready for owner Dashboard deploy; live URL, data upload, smoke, and sign-off pending |
| 2026-07-10 UTC / 2026-07-09 EDT | Session N6 Render execution | Render service `srv-d983c558nd3s73bknkg0` deployed live from commit `333d59ca76e016dcfd6e711549719fa902a88629`; private data archive uploaded to `/var/data`, checksum `20b16221e3198acfeca352f4ddaf02886e73f4902ab604c9b14495e8cba39329`; macOS `._*` sidecars removed from the disk after extraction | PASS: <https://replocx-private-atlas.onrender.com>; health `status: ok`, `data_mode: production`, `auth.required/configured: true`, `candidate_count: 4019`, `selected_count: 20`; unauthenticated Atlas API `401`; authorized provenance `200`, 720 cells, A/C/B/D, R9 PASS, `f2v3_final`; authorized equity `200`, READY, 20 profiles, 4/4 verified layers |

## 6. Owner sign-off and production release tag

Tag the production release **only after** owner sign-off and a passing live smoke.

- [ ] Owner sign-off recorded (name + date): ______________________
- [x] Live post-deploy smoke PASS (outputs saved locally under `/private/tmp/replocx_*_final*.json`)
- [ ] No private data or token in logs
- [ ] First scenario backup taken; VM/volume snapshot and restore owner confirmed

```bash
# after sign-off, on the release commit:
git tag -a v1.2.0-production -m "ReplocX private production deployment (national dataset)"
git push origin v1.2.0-production
```

Record the tag, commit hash, and live (private) URL here once complete.
