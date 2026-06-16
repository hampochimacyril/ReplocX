# ReplocX Operations Runbook — Private Production Instance

Day-2 operations for the **private, authenticated, real-data** ReplocX instance
on Render. This is the operational companion to:

- `docs/deployment_options.md` — private-mode environment variables and controls.
- `docs/LIVE_DATA_RUNBOOK.md` — how the national dataset in `pipeline/out/` is
  produced and validated (Sessions 3–4).
- `render.private.example.yaml` — the private Render blueprint template.
- `docs/DEPLOYMENT_RECORD.md` — the infrastructure decisions and deploy log.

> The public demo (`render.yaml`, <https://replocx.onrender.com>) is a separate
> service and must **never** serve the national dataset. Nothing in this runbook
> applies to the public demo.

## 1. Service profile

| Property | Value |
| --- | --- |
| Service | `replocx-private` (Render web service, Docker runtime) |
| Plan | Paid (`starter` or higher) — required for the persistent disk and to avoid idle spin-down |
| Data mode | `production` (`RLE_ANALYSIS_DATA_DIR=/app/pipeline/out`) |
| Auth | Required (`RLE_REQUIRE_AUTH=1` + `RLE_PRIVATE_AUTH_TOKEN`) |
| Scenario store | SQLite on the persistent disk (`/var/data/replocx/scenarios.sqlite3`) |
| Health check | `GET /api/v1/health` |
| TLS | Render-managed certificate on the service domain |
| Network | Inbound IP allowlist (dashboard → Settings → Inbound IP rules) |

### Environment variables

```bash
RLE_ANALYSIS_DATA_DIR=/app/pipeline/out          # forces data_mode: production
RLE_REQUIRE_AUTH=1
RLE_PRIVATE_AUTH_TOKEN=<from secret manager>     # bearer token; never committed
RLE_SCENARIO_DB=/var/data/replocx/scenarios.sqlite3
RLE_LOG_LEVEL=INFO
RLE_SENTRY_DSN=<optional Sentry DSN>             # enables error tracking if set
```

`/api/v1/health` and `/api/v1/openapi.json` are intentionally public (readiness +
schema). Every other `/api` route requires `Authorization: Bearer <token>` (or
`X-RLE-Auth: <token>`). The token is compared with `hmac.compare_digest`
(`backend/auth.py`).

## 2. Health monitoring

The readiness probe is `GET /api/v1/health` (unauthenticated). A healthy
production instance returns:

```json
{ "status": "ok", "data_mode": "production", "data_ready": true,
  "candidate_count": 4019, "selected_count": 20,
  "auth": { "required": true, "configured": true } }
```

Alert if any of: HTTP != 200, `status` != `ok`, `data_mode` != `production`,
`data_ready` != `true`, `selected_count` != `20`, or `auth.required` != `true`
(an unauthenticated production instance is a P1 — see §7).

Configure monitoring in the Render dashboard (Notifications → email/Slack on
deploy + health failure) and, for external uptime, an approved monitor hitting
`/api/v1/health` every 1–5 min from an allowlisted source. Because the instance
is paid it does not spin down, so a cold-start grace period is not required (the
public demo is the only service that spins down).

## 3. Persistent storage, backups, and recovery

The only mutable runtime state is the scenario SQLite database on the persistent
disk. The national dataset is immutable (baked into the image, reproducible from
`docs/LIVE_DATA_RUNBOOK.md`), so disaster recovery is scenarios-only.

**Automatic backups.** Render snapshots the disk every 24 h, encrypted at rest,
retained ≥ 7 days. Restore from the dashboard (service → Disks → Restore
snapshot). Restoring reverts the whole disk to the snapshot — any scenarios saved
after it are lost.

**Manual backup (recommended weekly and before every deploy).** SQLite supports
hot online backup; copy the file off the disk via SSH/SCP:

```bash
# from an allowlisted machine, after `render` SSH is set up for the service
scp -s replocx-private@ssh.<region>.render.com:/var/data/replocx/scenarios.sqlite3 \
    ./backups/scenarios-$(date +%F).sqlite3
```

Verify a backup is readable before trusting it:

```bash
sqlite3 backups/scenarios-YYYY-MM-DD.sqlite3 \
  'PRAGMA integrity_check; SELECT count(*) FROM scenarios;'
```

**Restore a manual backup.** SSH to the service shell, stop writes (put the
service in maintenance mode), copy the file back to
`/var/data/replocx/scenarios.sqlite3`, then redeploy.

> Disk caveat: a disk binds to a single instance, cannot be used during build or
> one-off jobs, and disables zero-downtime deploys (a few seconds of downtime per
> deploy while instances swap). Deploy during a low-use window.

## 4. Logs and error tracking

Structured one-line JSON request logs go to stdout (captured by Render logging):

```json
{"event":"http_request","method":"GET","path":"/api/v1/dashboard",
 "status":200,"duration_ms":161.4,"service":"replocx","timestamp":"...Z"}
```

`RLE_LOG_LEVEL` controls verbosity. View live logs in the dashboard (Logs) or
stream them to an approved syslog/HTTPS endpoint (Render log streams). When
`RLE_SENTRY_DSN` is set and `sentry-sdk` is installed, unhandled errors are
captured to Sentry (`backend/observability.py`). Logs must not contain the auth
token or raw analytical rows — confirm during the first live verification.

## 5. Deploy / promote a new version

1. Confirm CI is green on the release commit.
2. Take a manual scenario backup (§3).
3. In the dashboard, trigger a manual deploy of `replocx-private` (autoDeploy is
   off by design). Expect a few seconds of downtime (disk attached).
4. Post-deploy smoke (§6). If it fails, roll back: dashboard → service → Rollback
   to the previous deploy.

## 6. Post-deploy smoke checklist

Run from an allowlisted host (`$T` = the bearer token, `$U` = the service URL):

```bash
curl -s $U/api/v1/health | python3 -m json.tool   # data_mode: production, selected_count 20, auth.required true
curl -s -o /dev/null -w '%{http_code}\n' $U/api/v1/dashboard                       # expect 401
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $T" $U/api/v1/dashboard  # 200
curl -s -H "Authorization: Bearer $T" "$U/api/v1/candidates?page=1&page_size=1" | grep -o '"total":[0-9]*'  # 4019
curl -s -X POST -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d '{}' \
     $U/api/v1/exports/site-list.csv | wc -l        # 21 (header + 20 sites)
curl -s -o /dev/null -w '%{http_code}\n' $U/api/v1/openapi.json                    # 200 (public)
```

Also load the UI over HTTPS, confirm the production (not demo) indicator, and
verify a scenario save persists across a page reload.

## 7. Incident response

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `/api/v1/health` 200 but `auth.required:false` | token env unset | **P1.** Set `RLE_PRIVATE_AUTH_TOKEN`, redeploy, rotate the token, review access logs. |
| Health `degraded` / API 503 | data dir not resolving | Check `RLE_ANALYSIS_DATA_DIR` points at the image's `/app/pipeline/out`; redeploy. |
| `data_mode: demo` on the private host | data dir unset/wrong | Set `RLE_ANALYSIS_DATA_DIR`; the service must never serve demo data as production. |
| Scenarios disappear after deploy | disk missing / wrong DB path | Confirm the disk is attached and `RLE_SCENARIO_DB` is under the mount path. |
| 5xx spike | app error | Check logs + Sentry; roll back to the last good deploy. |
| Suspected token leak | — | Rotate `RLE_PRIVATE_AUTH_TOKEN`, redeploy, audit logs, tighten the inbound IP allowlist. |

Escalate per the access-control owner in `docs/DEPLOYMENT_RECORD.md`.

## 8. Token rotation

1. Generate a new token (`python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`).
2. Store it in the secret manager; update `RLE_PRIVATE_AUTH_TOKEN` in the dashboard.
3. Redeploy; run the §6 smoke. Distribute the new token to authorized users out of band.

## 9. Refreshing the national dataset

When the analytical outputs are regenerated (`docs/LIVE_DATA_RUNBOOK.md`):
re-run `pipeline.validate --dir pipeline/out`, commit the new `pipeline/out/`,
tag a new production release, then deploy (§5). The data ships with the image, so
a data refresh is a normal deploy — no separate transfer step.

## 10. Decommission

Remove the service in the dashboard (this deletes the disk and its snapshots —
take a final backup first), revoke the token, remove inbound IP rules, and record
the decommission date in `docs/DEPLOYMENT_RECORD.md`.
