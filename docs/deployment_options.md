# Private Deployment Options

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

## Do Not Deploy Yet

Do not execute a deployment until the team confirms:

- approved private hosting environment
- access-control owner
- data-retention rules
- crosswalk refresh cadence
- weather-QC ownership
- exact private GitHub repository URL

