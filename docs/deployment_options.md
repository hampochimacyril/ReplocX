# ReplocX Private Deployment Options

Local review is the safest default:

```bash
python3 -m backend.server
```

The public profile is `docker-compose.yml` / `render.yaml`. It is synthetic,
sets `RLE_ENABLE_ATLAS=0`, and has no real-data mount.

## Research Atlas private profile

The approved W4 boundary is defense in depth:

1. nginx or Caddy terminates TLS and requires HTTP Basic auth for every path,
   including `/atlas`, `/api/v1/results/*`, and `/api/v1/equity/*`.
2. The app remains on a private network and requires its independent token.
3. Certified results and figures are mounted read-only; they are never baked
   into the public image.

Use `docker-compose.atlas-private.example.yml` with
`deploy/atlas-private/Caddyfile` as the executable example. Inject all
credentials from the approved secret manager:

```bash
RLE_ANALYSIS_DATA_DIR=/analysis
RLE_ENABLE_ATLAS=1
RLE_ATLAS_DATA_DIR=/atlas
RLE_ATLAS_FIGURE_DIR=/atlas-figures
RLE_REQUIRE_AUTH=1
RLE_PRIVATE_AUTH_TOKEN=<secret-manager value>
RLE_SCENARIO_DB=/state/scenarios.sqlite3
```

The `/atlas` and `/atlas-figures` host mounts must resolve respectively to the
certified `replocx_tmy3_wallfix_4scen` data root and its `f2v3_final` figure
root, and both mounts must be `:ro`. A staged app-ready copy is acceptable only
when its CSVs/assets and provenance sidecars are byte-for-byte certified.

### Basic auth plus app token

Basic auth and Bearer auth both normally use `Authorization`. The Atlas avoids
that collision without adding an identity system:

- the browser uses `Authorization: Basic …` with the reverse proxy;
- the SPA keeps the app token only in memory and sends `X-RLE-Auth`;
- the proxy replaces the upstream header with
  `Authorization: Bearer <X-RLE-Auth>` and removes `X-RLE-Auth`;
- the existing app gate validates `RLE_PRIVATE_AUTH_TOKEN`.

The Caddy example implements this translation. Equivalent nginx configuration:

```nginx
location / {
    auth_basic "ReplocX Research Atlas";
    auth_basic_user_file /run/secrets/replocx_htpasswd;
    proxy_set_header Authorization "Bearer $http_x_rle_auth";
    proxy_set_header X-RLE-Auth "";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://atlas-app:8787;
}
```

Do not publish the app container port. Only the reverse proxy may reach it.
Generate Basic credentials outside the repository (`caddy hash-password` or
`htpasswd`), store the hash/file in the secret manager, and rotate the Basic and
app credentials independently.

## Managed FastAPI deployment

The app process remains private behind the proxy:

```bash
pip install -r backend/requirements.txt
uvicorn backend.fastapi_app:app --host 127.0.0.1 --port 8787
```

Bind to a non-loopback address only on a private container/network interface.
`/api/v1/health` and `/api/v1/openapi.json` are exempt from the app token for
internal readiness, but the edge proxy still protects them with Basic auth.

`render.private.example.yaml` records the required Atlas variables, but a Render
service is not W4-ready unless an external nginx/Caddy Basic-auth proxy fronts
it and the platform enforces read-only Atlas mounts.

## Equity deployment state (2026-07-08)

`equity_profile.csv` and `equity_profile.csv.prov.json` now verify at the
certified data root. `/api/v1/equity/profiles` reports:

- status `READY`;
- 20 source records;
- 4 ready layers (`cdc_svi`, `acs_income_poverty`,
  `doe_lead_energy_burden`, `heat_vulnerability`);
- the certified `source_csv` and `provenance_sidecar`;
- `missing_source_path: null`.

If either file is absent or any layer fails metadata/value checks, deployment
must present `REVIEW REQUIRED`; it must not substitute the legacy
`data/atlas/equity_profile.csv`.

## Public-demo invariant

Public builds must keep `RLE_ENABLE_ATLAS=0`, set no `RLE_ATLAS_DATA_DIR` or
`RLE_ATLAS_FIGURE_DIR`, and mount no private data. The public-safe Dockerfile
copies only backend code, generated synthetic demo data, the demo ZIP crosswalk,
and built frontend assets. It does not copy `data/atlas`, `pipeline/out`,
canonical sidecars, tests, docs, or f2v3 assets.

## Do Not Deploy Real Data Until

No live real-data deploy is authorized until every item is checked and recorded
in `docs/DEPLOYMENT_RECORD.md`:

- [ ] approved private host and private DNS name
- [ ] named access-control owner
- [x] reverse-proxy Basic-auth configuration prepared
- [x] independent app-token gate configured (`RLE_REQUIRE_AUTH=1`)
- [x] secret values excluded from repository and delegated to a secret manager
- [x] certified Atlas data and figure mounts configured read-only in the
  container example
- [x] equity state verified `READY` from the sidecar-backed canonical profile
- [ ] data-retention and backup rules approved
- [ ] crosswalk refresh cadence and weather-QC owner confirmed
- [ ] exact private GitHub repository URL confirmed
- [ ] branch divergence reconciled or approved for publication
- [ ] full verification, live proxy smoke, and owner sign-off attached

Unchecked owner/infrastructure items block a live deployment. Local W4
verification is not production authorization.
