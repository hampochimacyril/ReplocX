# ReplocX Private Deployment Options

Local review is the default and safest operating mode:

```bash
python3 -m backend.server
```

## Private Container Deployment

For a private network environment:

```bash
docker compose up --build
```

The compose file mounts processed analytical outputs read-only. Add authentication,
TLS termination, access logs, and organization-approved secret management before
hosting beyond localhost.

## Managed FastAPI Deployment

Install managed dependencies and launch:

```bash
pip install -r backend/requirements.txt
uvicorn backend.fastapi_app:app --host 127.0.0.1 --port 8787
```

Bind to a non-loopback interface only within an approved private network.

## Phase 4 Private-Mode Controls

Set these environment variables for a private deployment that serves real data:

```bash
RLE_ANALYSIS_DATA_DIR=/read-only/path/to/processed
RLE_REQUIRE_AUTH=1
RLE_PRIVATE_AUTH_TOKEN=<secret token from your secret manager>
RLE_SCENARIO_DB=/persistent/private/scenarios.sqlite3
RLE_LOG_LEVEL=INFO
RLE_SENTRY_DSN=<optional free-tier Sentry DSN>
```

`/api/v1/health` and `/api/v1/openapi.json` remain public for readiness and
schema inspection. All other API routes require `Authorization: Bearer <token>`
when `RLE_PRIVATE_AUTH_TOKEN` is set. The public demo blueprint remains
`render.yaml`; use `render.private.example.yaml` only as a template for a private
profile and do not commit real secrets.

## Do Not Deploy Real Data Until

Do not execute a real-data deployment until the team confirms:

- approved private hosting environment
- access-control owner
- data-retention rules
- crosswalk refresh cadence
- weather-QC ownership
- exact private GitHub repository URL
