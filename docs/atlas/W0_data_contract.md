# W0 Data Contract

Date: 2026-07-08

This freezes the Research Atlas payload shapes before W1 implementation. The contract is based on the certified read-only tier at:

`/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen`

and f2v3 registry root:

`/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final`

The app may stage app-ready copies later, but the certified CSVs remain read-only sources of truth.

## Common Fields

- `schema_version`: string, currently `atlas.w0/1.0`.
- `tier_id`: `replocx_tmy3_wallfix_4scen`.
- `scenario_order`: exactly `["A", "C", "B", "D"]`.
- `scenario_display_label`: one of `AC all day`, `AC 2-8pm + NV other hours`, `NV only`, `No AC or NV`.
- `metric_notes`: object keyed by metric name. Must include threshold notes for exposure-hour metrics.
- `provenance`: object with source CSV, sidecar, canonical root, and read-only status.

## `/api/v1/results/scenario-dictionary`

Purpose: canonical scenario semantics for selectors, legends, downloads, and provenance.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "scenario_order": ["A", "C", "B", "D"],
  "scenarios": [
    {
      "code": "A",
      "scenario_display_label": "AC all day",
      "scenario_order": 1,
      "scenario_color": "#0072B2",
      "cooling": "23.88889 C all day",
      "heating": "21.11111 C all day",
      "natural_ventilation": "none"
    }
  ],
  "source_csv": "04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/metadata/replocxTMY3wf4_metadata_scenario_dictionary_4scen_2026-07-07.csv"
}
```

Rules:

- Array order is semantic and must not be sorted alphabetically.
- Display labels are primary in UI text; codes appear as details.

## `/api/v1/results/scenario-summary`

Purpose: annual and seasonal scenario-level metrics.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "scenario_order": ["A", "C", "B", "D"],
  "tiers": [
    {
      "tier": "annual",
      "source_csv": "04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/annual/replocxTMY3wf4_annual_annual_scenario_summary_2026-07-07.csv",
      "rows": [
        {
          "hvac_scenario": "A",
          "scenario_display_label": "AC all day",
          "scenario_order": 1,
          "n_runs": 180,
          "op_temp_mean_c": 21.735795699946067,
          "op_temp_p95_true_c": 24.65200223575926,
          "hours_gt_28c": 3.411111111111111,
          "degree_hours_28c": 0.9163531874772487
        }
      ]
    }
  ],
  "metric_notes": {
    "hours_gt_28c": "Overheating exposure hours; threshold: operative temperature above 28 C.",
    "degree_hours_28c": "Overheating degree-hours; threshold: operative temperature above 28 C."
  }
}
```

Rules:

- Both `annual` and `seasonal` tiers are present.
- Each tier has exactly A/C/B/D rows.
- Mean operative temperature is never the only temperature signal; p95 is paired in the same row.

## `/api/v1/results/by-stratum`

Purpose: certified summaries by climate, urbanicity, the complete 20-cell
climate × urbanicity lattice, building type, or vintage.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "tier": "annual",
  "dimension": "climate",
  "group_column": "climate_region",
  "scenario_order": ["A", "C", "B", "D"],
  "source_csv": "04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/annual/replocxTMY3wf4_annual_annual_by_climate_region_scenario_2026-07-07.csv",
  "rows": [
    {
      "climate_region": "Hot-Humid",
      "hvac_scenario": "C",
      "scenario_display_label": "AC 2-8pm + NV other hours",
      "op_temp_p95_true_c_mean": 30.199240637285406,
      "op_temp_hours_gt_28c_mean": 1038.4444444444443,
      "humidity_hours_gt_0p012kgkg_mean": 3736.972222222222
    }
  ],
  "metric_notes": {
    "op_temp_hours_gt_28c_mean": "Overheating exposure hours; threshold: operative temperature above 28 C.",
    "humidity_hours_gt_0p012kgkg_mean": "High-humidity exposure hours; threshold: humidity ratio above 0.012 kg/kg."
  }
}
```

Rules:

- `dimension` is one of `climate`, `urbanicity`, `building`, or `vintage`.
- `group_column` must name the grouping column in each row.
- N3 adds `dimension=stratum` under contract `atlas.strata/1.0`. It returns
  exactly 20 `strata` records and 80 metric rows (20 strata × A/C/B/D), with
  `group_columns: ["climate_region", "urbanicity"]`.
- The combined-stratum values are arithmetic means computed server-side from
  the certified annual or seasonal `run_level_metrics` CSV. The response names
  that CSV and its provenance sidecar; the browser may filter returned rows but
  must not derive analytical aggregates.
- Every combined-stratum scenario group is ordered `A`, `C`, `B`, `D` and
  carries `certified_provenance` with R9 `PASS`, `f2v3_final`, and read-only
  source status.

## `/api/v1/results/d-comparisons`

Purpose: certified D-centered comparisons for the sealed-passive story panel.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "tier": "annual",
  "base_scenario": "D",
  "base_scenario_display_label": "No AC or NV",
  "scenario_order": ["A", "C", "B", "D"],
  "comparisons": [
    {
      "comparison_scenario": "A",
      "comparison_scenario_display_label": "AC all day",
      "comparison_interpretation": "Full active-cooling protection relative to sealed passive",
      "comparison_key": "D-A",
      "metrics": {
        "op_temp_p95_true_c_reduction_from_D": 2.0669049517366496,
        "op_temp_hours_gt_28c_reduction_from_D": 102,
        "degree_hours_28c_reduction_from_D": 51.73405076855306
      }
    }
  ],
  "source_csv": "04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/annual/replocxTMY3wf4_annual_annual_d_specific_comparisons_2026-07-07.csv"
}
```

Rules:

- Must include D-A, D-C, and D-B comparisons.
- Reductions are read from certified fields; do not recompute.

## `/api/v1/results/figures`

Purpose: f2v3 final registry records for static figures and interactive parity.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "registry_csv": "04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/replocxTMY3wf4_figure_registry_f2v3_2026-07-07.csv",
  "figures": [
    {
      "figure_id": "Fig02",
      "figure_class": "results",
      "source_csv": "04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/tables/replocxTMY3wf4_final_data_F02_summary_2026-07-07.csv",
      "asset_png": "04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/replocxTMY3wf4_final_fig_F02_summary_2026-07-07.png",
      "asset_pdf": "04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/replocxTMY3wf4_final_fig_F02_summary_2026-07-07.pdf",
      "asset_svg": "04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/replocxTMY3wf4_final_fig_F02_summary_2026-07-07.svg",
      "atlas_route": "/results/replocx_tmy3_wallfix_4scen/figures/F02_summary",
      "provenance_sidecar": "04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/replocxTMY3wf4_final_fig_F02_summary_2026-07-07.png.prov.json"
    }
  ]
}
```

Rules:

- Any `f2v2_final`, `f1v2`, or `F1v2` path is invalid.
- F19 is supplementary/methods, not a main results-grid figure.

## `/api/v1/results/provenance`

Purpose: source, citation, reproducibility, and caveat envelope.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "certified_cell_count": 720,
  "scenario_order": ["A", "C", "B", "D"],
  "canonical_data_root": "04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen",
  "figure_registry_root": "04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final",
  "read_only_sources": true,
  "endpoint_definitions": {
    "primary_endpoint_families": [
      "op_temp_mean_c",
      "op_temp_p95_true_c",
      "humidity_ratio_mean_kgkg",
      "humidity_ratio_p95_true_kgkg"
    ]
  }
}
```

Rules:

- Provenance must distinguish data root from figure root.
- Include source/citation notes for downloads.

## `/api/v1/equity/profiles`

Purpose: equity and vulnerability profile metadata per catchment.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "profiles": [
    {
      "catchment_id": "HotHumid_Suburban_BatonRouge_LA",
      "catchment_label": "HotHumid_Suburban_BatonRouge_LA",
      "proxy_badge": "REVIEW REQUIRED",
      "source_vintage": "pending verified CDC SVI / ACS / DOE LEAD join",
      "join_uncertainty_note": "Do not present as certified until the equity join is verified."
    }
  ],
  "layers": {
    "proxy_badges_required": true,
    "unverified_status": "REVIEW REQUIRED"
  }
}
```

Rules:

- Real equity data is private.
- Unverified layers must not be silently labeled ready.

## `/api/v1/equity/scenario-cross`

Purpose: exposure by vulnerability for the D-centered equity story.

Payload:

```json
{
  "schema_version": "atlas.w0/1.0",
  "tier_id": "replocx_tmy3_wallfix_4scen",
  "scenario": "D",
  "scenario_display_label": "No AC or NV",
  "scenario_order": ["A", "C", "B", "D"],
  "metric": "op_temp_hours_gt_28c",
  "metric_label": "Overheating exposure hours",
  "threshold_note": "Threshold: operative temperature above 28 C.",
  "rows": [
    {
      "catchment_id": "HotHumid_Suburban_BatonRouge_LA",
      "exposure_hours": 1403,
      "equity_percentile": null,
      "proxy_badge": "REVIEW REQUIRED",
      "interpretation_note": "Descriptive exposure by vulnerability only; no causal claim."
    }
  ]
}
```

Rules:

- Default scenario is D.
- Payloads must state threshold and proxy status.
- No causal claims.

## Schema And Fixtures

- JSON Schema: `docs/atlas/schemas/w0_contract_bundle.schema.json`.
- Golden fixture: `tests/fixtures/atlas/w0/w0_contract_bundle.golden.json`.
- Negative cases are generated from the golden fixture in `tests/test_atlas_contract.py` so the intended mutation is visible in each test.
