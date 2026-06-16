# `replocx-client` — Python client for ReplocX

A **standard-library-only** client so building-stock pipelines (URBANopt,
GeoPandas, ResStock/ComStock, OpenStudio/EnergyPlus) can call the explorer's
selection over its REST API without pulling in any dependencies. GeoPandas is the
single optional extra, used only by `to_geodataframe()`.

## Install

```bash
pip install ./clients/python              # core (no dependencies)
pip install "./clients/python[geo]"       # + geopandas for to_geodataframe()
```

Or just copy the `rle_client/` folder next to your pipeline — it is pure stdlib.

## Quick start

Start an explorer locally (`python3 -m backend.server`), then:

```python
from rle_client import ReplocXClient

replocx = ReplocXClient("http://127.0.0.1:8787")
# Private deployment:
# replocx = ReplocXClient("https://private.example", auth_token="...")

replocx.health()["data_mode"]              # 'demo' or 'production'
sites = replocx.selected_locations()       # baseline 20-site selection (list of dicts)

# One-click interoperability exports (Phase 3 adapters)
open("sampling.csv", "w").write(replocx.resstock_sampling_csv())   # ResStock/ComStock downselect
manifest = replocx.openstudio_manifest()                           # OpenStudio/EnergyPlus manifest

# Custom scenario (same schema the Scenario builder POSTs)
result = replocx.evaluate({"density_screen_percentile": 0.75, "require_weather_qc": True})
saved = replocx.save_scenario({"name": "Weather-QC priority", "require_weather_qc": True})

# Optional: selected catchment polygons as a GeoDataFrame (needs geopandas)
gdf = replocx.to_geodataframe()
```

## Methods

| Method | REST endpoint |
|---|---|
| `health()` | `GET /api/v1/health` |
| `dashboard()` | `GET /api/v1/dashboard` |
| `provenance()` | `GET /api/v1/provenance` |
| `geometry()` | `GET /api/v1/geometry` (GeoJSON) |
| `candidates(...)` | `GET /api/v1/candidates` |
| `zip_lookup(zip)` | `GET /api/v1/zip/{zip}` |
| `evaluate(scenario)` / `selected_locations(scenario)` | `POST /api/v1/scenarios/evaluate` |
| `save_scenario(scenario)` | `POST /api/v1/scenarios` |
| `scenarios(limit)` | `GET /api/v1/scenarios` |
| `scenario(id)` | `GET /api/v1/scenarios/{id}` |
| `site_list_csv(scenario)` | `POST /api/v1/exports/site-list.csv` |
| `resstock_sampling_csv(scenario)` | `POST /api/v1/exports/resstock-sampling.csv` |
| `openstudio_manifest(scenario)` | `POST /api/v1/exports/openstudio-manifest.json` |
| `to_geodataframe()` | `GET /api/v1/geometry` → GeoDataFrame (needs `geopandas`) |

`scenario` defaults to `None`/`{}` everywhere, which returns the baseline
selection. Errors raise `ReplocXClientError` (an alias of the compatibility
`RLEClientError`, with a `.status` for HTTP errors).
