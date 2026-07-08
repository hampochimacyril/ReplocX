# W0 Acceptance Criteria

Date: 2026-07-08

These criteria translate the official precedent patterns into gates for the ReplocX Research Atlas migration. They are contract gates, not W1 feature work.

## Precedent Patterns

### OWID Grapher Pattern

- Every chart has an inspectable data payload and machine-readable metadata.
- Downloads carry enough context for a reader to understand variables, units, source, and processing notes.
- The Atlas gate: every results view must resolve to an underlying certified CSV, a display metadata record, and a CSV/ZIP style download plan.

### IPCC Atlas Pattern

- Figures and data products are FAIR: findable, accessible inside the private boundary, interoperable via stable formats, and reusable with provenance.
- Figure generation is reproducible from recorded source data and sidecars.
- The Atlas gate: every f2v3 figure linked by the app must resolve to a registry row with `source_csv`, asset paths, `atlas_route`, and `provenance_sidecar`.

### NREL EULP Pattern

- Multiple access modes are clear: browse, direct file, aggregate download, and citation/source notes.
- Users can tell whether they are seeing aggregate summaries or run-level data.
- The Atlas gate: annual, seasonal, stratum, D-comparison, figure, and provenance endpoints must name their source tier and download scope.

### CDC/ATSDR SVI Pattern

- Percentiles, proxy variables, and vintages are explicit.
- Data-documentation links and caveats are visible where the data is used.
- The Atlas gate: equity payloads must carry proxy badges, source/vintage fields, and join/uncertainty notes; unverified equity layers stay `REVIEW REQUIRED`.

## W0 Gates

- Scenario contract:
  - Scenario order is exactly A, C, B, D.
  - Descriptive labels are primary; scenario codes are provenance details.
  - Any scenario dictionary out of A/C/B/D order fails validation.
  - Any results fixture missing D fails validation.
  - Any results fixture with only A/B/C fails validation.

- Tier contract:
  - Current tier id is `replocx_tmy3_wallfix_4scen`.
  - Current certified cell count is 720.
  - The legacy `data/atlas/replocx_tmy3` scaffold is never silently used as current.
  - Canonical CSVs are read-only inputs; Atlas code must not recompute certified results or figure values.

- Metric contract:
  - Lead with p95, exposure-hour, and degree-hour metrics.
  - Any mean displayed in a view must be paired with its extreme counterpart.
  - Use "Overheating exposure hours" for hours above 28 C.
  - Use "High-humidity exposure hours" for hours above 0.012 kg/kg.
  - Thresholds appear in notes, subtitles, or payload metadata.

- Figure contract:
  - Link only f2v3 final figure registry records and assets.
  - A registry fixture pointing to `f2v2_final` or any `f1v2`/`F1v2` path fails validation.
  - Figure payloads expose `source_csv`, asset paths, `atlas_route`, and `provenance_sidecar`.

- Results API contract:
  - `/api/v1/results/scenario-dictionary` returns A/C/B/D metadata and display labels.
  - `/api/v1/results/scenario-summary` returns annual and seasonal summaries with A/C/B/D rows.
  - `/api/v1/results/by-stratum` returns tier, dimension, grouping column, metric notes, and A/C/B/D rows.
  - `/api/v1/results/d-comparisons` returns D-A, D-C, and D-B comparisons with descriptive interpretations.
  - `/api/v1/results/figures` returns only f2v3 registry rows.
  - `/api/v1/results/provenance` returns canonical roots, endpoint definitions, sidecars, and citation notes.

- Equity API contract:
  - `/api/v1/equity/profiles` returns catchment profiles with proxy badges, source/vintage fields, and uncertainty notes.
  - `/api/v1/equity/scenario-cross` returns a D-centered exposure by vulnerability payload and does not make causal claims.

- Public/private boundary:
  - `RLE_ENABLE_ATLAS` remains off by default.
  - Public demo builds do not mount or serve private results or real equity data.
  - Atlas disabled routes still fail closed as 404 through the existing route gate.

## W0 Evidence Required In Handoff

- Exact canonical data and f2v3 figure roots.
- Read-only smoke test results.
- Schema validation command and result.
- Negative test command and result, proving intended failures are caught.
- Grep proof for the W0 contract layer:
  - no `("A", "B", "C")`
  - no hard-coded 3-scenario count
  - no `f2v2_final`
  - no `f1v2` or `F1v2`

## Stop Rule

Do not proceed to W1 until the W0 contract tests pass or this handoff names one concrete blocker.
