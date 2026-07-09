# N5 real-container boundary audit

Date: 2026-07-09  
Branch/worktree: `codex/atlas-release-candidate`,
`/private/tmp/Developer-atlas-release`  
Result: **PASS**

## Runtime and images

- Host runtime: Docker Desktop 4.81.0 (232925), Docker Engine 29.6.1,
  Linux/arm64.
- Docker Desktop source: Docker's official Apple-silicon distribution.
  macOS verification passed: valid on disk, designated requirement satisfied,
  and Gatekeeper accepted it as `Notarized Developer ID` from Docker Inc
  (`9BNSXJN65R`).
- Public app image:
  `sha256:f821629698b257642a6fa5fc3380f7e5c243725bbe322ca59661bf0de42d0c7a`,
  59,253,207 bytes.
- Compose app image:
  `sha256:9b8482a6cffd84a2923f0c5307280f6ac0e2f81d146a012a2c1941d4035ccb41`,
  59,253,336 bytes.
- The public and Compose app images had the same 13 root filesystem layer
  diff IDs.
- Caddy image:
  `caddy@sha256:4c6e91c6ed0e2fa03efd5b44747b625fec79bc9cd06ac5235a779726618e530d`.

## Defects found and fixed by the real build

The first real build did not pass unchanged:

1. Root-only `node_modules/` and `dist/` ignore rules allowed 463 MB of host
   frontend dependencies and stale compiled bundles into the build context.
   Nested ignore rules reduced the effective context to approximately 8 KB and
   left exactly the five current production assets in the final image.
2. `backend/atlas_service.py` embedded the owner's absolute canonical OneDrive
   paths. Container-safe defaults are now `/atlas` and `/atlas-figures`;
   development and deployment overrides remain environment-driven.
3. Nested host `backend/__pycache__` files entered the image and retained the
   removed host path in stale bytecode. Nested bytecode/cache ignore rules now
   exclude them.

Regression assertions cover the container-safe defaults, nested ignore rules,
and absence of `/Users/` paths from the runtime Atlas service source.

## Actual image and layer scan

The corrected public image was exported both as a merged root filesystem and
as a saved OCI image. Every saved compressed layer was scanned.

| Check | Measured result |
| --- | --- |
| App files in merged rootfs | 30 |
| Current frontend assets | 5 |
| Host Python bytecode files | 0 |
| Provenance/checksum sidecars | 0 |
| Canonical f2v3 asset basename collisions | 0 |
| Owner host-path or disposable-secret content hits | 0 |
| Saved layers scanned | 13 |
| Layers with owner host-path or disposable-secret hits | 0 |
| Saved OCI image SHA-256 | `8701ac748331aca2e2ba81be792e70ca7ad3614351966954c52d76b7b7461b24` |
| Exported rootfs SHA-256 | `5dc6e07751c5d302a522a3a21a922212f7473fe43f9b71dda5750599e6c6495f` |

The certified tier ID and f2v3 tier label remain intentional validation
constants in application code. No canonical data row, figure asset, sidecar,
secret, or owner-specific host path is present.

## Actual Compose/Caddy boundary

The committed `docker-compose.atlas-private.example.yml` and
`deploy/atlas-private/Caddyfile` were started with disposable credentials,
the real selection analysis root, and the certified Atlas data/figure roots.
All analytical mounts were read-only.

| Request | Result |
| --- | --- |
| `/atlas`, no Basic auth | 401 at Caddy |
| certified API, no Basic auth | 401 at Caddy |
| certified API, Basic auth only | 401 at app token gate |
| certified API, Basic auth + app token | 200 |
| `/atlas`, Basic auth | 200 |

Only Caddy published a host port (`443:443`). The app exposed `8787` solely on
the internal Compose network and had an empty host `PortBindings` map.

Effective mount flags:

| Container destination | Type | Writable |
| --- | --- | --- |
| `/analysis` | bind | no |
| `/atlas` | bind | no |
| `/atlas-figures` | bind | no |
| `/state` | named volume | yes |

Explicit `touch` probes against all three analytical mounts failed with
`Read-only file system`.

## Certified proxy audit

- Overview: 720 cells, scenario order A/C/B/D, schema `atlas.w1/1.0`.
- Full N3 stratum route: 20 metadata records, 80 scenario rows, nine certified
  cells per stratum/scenario, R9 `PASS`, `f2v3_final`.
- Provenance: 720 certified cells, R9 `PASS`, `f2v3_final`,
  `read_only_sources: true`.
- Equity: 20 profiles, 4/4 layers READY, zero `REVIEW REQUIRED`.
- Exports: four export views, 19 figure bundles, and an annual
  scenario-summary export with four A/C/B/D rows and read-only source metadata.
- Logs: 20 app lines and 29 proxy lines scanned; zero secret, owner-path,
  canonical asset-name, or certified-row hits.

## Volumes and shutdown

Before shutdown, the Atlas state volume was empty. Caddy volumes contained
only the locally generated test CA/certificate material and Caddy
configuration. They contained no canonical data, figures, sidecars, or app
token.

The stack was stopped with `docker compose down -v`. All N5 containers,
networks, named volumes, and the host port binding were removed. The verified
image remains local for review. No public DNS or production credential was
created.

