# Render Private Atlas Deployment

Use this path when deploying the private Research Atlas from GitHub to Render.

## Source

- GitHub repository: `https://github.com/hampochimacyril/ReplocX`
- Branch: `codex/atlas-release-candidate`
- Render Blueprint: `render.yaml`

## What Render Provides

- Docker build from the repository Dockerfile.
- HTTPS/TLS at the Render edge.
- A paid web service that does not spin down.
- A persistent disk mounted at `/var/data`.
- Daily disk snapshots retained by Render.

## What You Still Provide

- `RLE_PRIVATE_AUTH_TOKEN` in the Render Dashboard.
- Certified analysis/Atlas/figure data uploaded out of band to `/var/data`.
- Optional inbound IP restrictions or an external Basic-auth proxy if policy
  requires the original two-layer C1 boundary.
- Custom domain, if desired.

## Dashboard Steps

1. Open:
   `https://dashboard.render.com/blueprint/new?repo=https://github.com/hampochimacyril/ReplocX`
2. Select branch `codex/atlas-release-candidate`.
3. Review the detected `render.yaml`.
4. Set the required secret value:
   - `RLE_PRIVATE_AUTH_TOKEN`
5. Apply the Blueprint. The first deploy can come up with degraded data until
   `/var/data` is populated.

## Prepare the Private Data Bundle

Run this locally. The bundle is not committed to Git.

```bash
export RLE_ANALYSIS_SOURCE=/path/to/selection-analysis-root
export RLE_ATLAS_SOURCE=/path/to/replocx_tmy3_wallfix_4scen
export RLE_ATLAS_FIGURE_SOURCE=/path/to/f2v3_final

scripts/package_render_private_data.sh /private/tmp/replocx-render-private-data.tar.gz
```

The archive expands into the Render disk layout expected by `render.yaml`:

```text
/var/data/analysis
/var/data/atlas/replocx_tmy3_wallfix_4scen
/var/data/atlas-figures/f2v3_final
```

## Upload the Bundle

Use the exact SSH/SCP hostname shown in the Render service dashboard. The shape
is typically:

```bash
scp -s /private/tmp/replocx-render-private-data.tar.gz \
  replocx-private-atlas@ssh.oregon.render.com:/var/data/replocx-render-private-data.tar.gz

ssh replocx-private-atlas@ssh.oregon.render.com
cd /var/data
tar -xzf replocx-render-private-data.tar.gz
mkdir -p /var/data/replocx
```

Then trigger a manual redeploy or restart from the Render Dashboard.

## Smoke Test

Set:

```bash
export U=https://YOUR_RENDER_SERVICE.onrender.com
export T=YOUR_RLE_PRIVATE_AUTH_TOKEN
```

Run:

```bash
curl -s "$U/api/v1/health" | python3 -m json.tool
curl -s -o /dev/null -w '%{http_code}\n' "$U/api/v1/results/provenance"
curl -s -H "X-RLE-Auth: $T" "$U/api/v1/results/provenance" | python3 -m json.tool
curl -s -H "X-RLE-Auth: $T" "$U/api/v1/equity/profiles" | python3 -m json.tool
```

Expected:

- Health reports `data_mode: production`, `data_ready: true`, and
  `auth.required/configured: true`.
- Unauthenticated protected Atlas API returns `401`.
- Authorized provenance reports 720 cells, A/C/B/D, R9 PASS, and `f2v3_final`.
- Authorized equity reports READY, 20 records, and 4/4 layers.

Record the live URL, commit, image digest, data bundle checksum, smoke output,
and owner sign-off in `docs/DEPLOYMENT_RECORD.md`.
