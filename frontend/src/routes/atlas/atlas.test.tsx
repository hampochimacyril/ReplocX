import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SelectionProvider } from "../../state/selection";
import { AtlasShell } from "./AtlasShell";
import { Equity } from "./Equity";
import { Exports } from "./Exports";
import { Introduction } from "./Introduction";
import { Provenance } from "./Provenance";
import { SealedPassive } from "./SealedPassive";
import { buildF02SummaryOption, f02ParityValues } from "./metrics";
import { SCENARIOS } from "./atlas";
import type { MetricRow } from "../../lib/types";

const health = vi.fn();
const overview = vi.fn();
const scenarioDictionary = vi.fn();
const byStratum = vi.fn();
const figureSource = vi.fn();
const dComparisons = vi.fn();
const scenarioSummary = vi.fn();
const atlasExports = vi.fn();
const atlasProvenance = vi.fn();
const equityProfiles = vi.fn();
const equityScenarioCross = vi.fn();
const dashboard = vi.fn();
const geometry = vi.fn();

vi.mock("../../components/MapCanvas", () => ({
  MapCanvas: () => <div role="img" aria-label="Atlas MapLibre drill map" />,
}));

vi.mock("../../components/EChart", () => ({
  EChart: ({ ariaLabel }: { ariaLabel: string }) => <div role="img" aria-label={ariaLabel} />,
}));

vi.mock("../../lib/api", () => ({
  API_BASE: "/api/v1",
  ApiError: class extends Error {},
  api: {
    health: () => health(),
    dashboard: () => dashboard(),
    geometry: () => geometry(),
    atlas: {
      overview: () => overview(),
      scenarioDictionary: () => scenarioDictionary(),
      byStratum: (tier: string, dimension: string) => byStratum(tier, dimension),
      figureSource: (figureId: string) => figureSource(figureId),
      dComparisons: (tier: string) => dComparisons(tier),
      scenarioSummary: (tier: string) => scenarioSummary(tier),
      exports: () => atlasExports(),
      provenance: () => atlasProvenance(),
      equityProfiles: () => equityProfiles(),
      equityScenarioCross: (scenario: string, dimension: string) => equityScenarioCross(scenario, dimension),
    },
  },
}));

const scenarioLabels = {
  A: "AC all day",
  C: "AC 2-8pm + NV other hours",
  B: "NV only",
  D: "No AC or NV",
};

const F02_ROWS: MetricRow[] = [
  { hvac_scenario: "A", scope: "annual", op_temp_mean_c: 21, op_temp_p95_true_c: 24, scenario_display_label: scenarioLabels.A },
  { hvac_scenario: "C", scope: "annual", op_temp_mean_c: 22, op_temp_p95_true_c: 27, scenario_display_label: scenarioLabels.C },
  { hvac_scenario: "B", scope: "annual", op_temp_mean_c: 23, op_temp_p95_true_c: 29, scenario_display_label: scenarioLabels.B },
  { hvac_scenario: "D", scope: "annual", op_temp_mean_c: 24, op_temp_p95_true_c: 33, scenario_display_label: scenarioLabels.D },
];

function seedApi(enabled = true) {
  health.mockResolvedValue({ status: "ok", atlas_enabled: enabled });
  scenarioDictionary.mockResolvedValue({
    tier_id: "replocx_tmy3_wallfix_4scen",
    scenario_order: SCENARIOS,
    scenarios: SCENARIOS.map((code, index) => ({
      code,
      scenario_display_label: scenarioLabels[code],
      scenario_order: index + 1,
      scenario_color: { A: "#0072B2", C: "#009E73", B: "#E69F00", D: "#D55E00" }[code],
    })),
  });
  overview.mockResolvedValue({
    dataset: "ReplocX TMY3 wallfix four-scenario tier",
    tier: "replocx_tmy3_wallfix_4scen",
    scenario_semantics: scenarioLabels,
    scenario_ordering: "A, C, B, D",
    tier_wall: "Certified f2v3 and R9 aggregate CSVs only.",
    n_cells: 720,
    scenario_summary: {
      tier: "annual",
      scenario_semantics: scenarioLabels,
      scenario_ordering: "A, C, B, D",
      rows: F02_ROWS,
    },
  });
  byStratum.mockResolvedValue({
    tier: "annual",
    dimension: "climate",
    group_column: "climate_region",
    source_csv: "04_Analysis/_CANONICAL/10_DATA/replocx_tmy3_wallfix_4scen/annual/by_climate.csv",
    rows: SCENARIOS.map((scenario, index) => ({
      climate_region: "Hot-Humid",
      hvac_scenario: scenario,
      scenario_display_label: scenarioLabels[scenario],
      op_temp_p95_true_c_mean: [26, 30, 32, 36][index],
    })),
  });
  figureSource.mockImplementation((figureId: string) =>
    Promise.resolve({
      tier_id: "replocx_tmy3_wallfix_4scen",
      registry_tier: "f2v3_final",
      figure_id: figureId,
      figure: { figure_id: figureId, stem: "F02_summary", figure_class: "results" },
      source_csv: `04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/tables/${figureId}.csv`,
      provenance_sidecar: "sidecar",
      rows:
        figureId === "Fig02"
          ? F02_ROWS
          : [
              { climate_short: "Hot-Humid", climate_region: "Hot-Humid", op_temp_hours_gt_28c_reduction: 10 },
              { climate_short: "Cold", climate_region: "Cold & Very Cold", op_temp_hours_gt_28c_reduction: 4 },
            ],
    }),
  );
  dComparisons.mockResolvedValue({
    tier: "annual",
    base_scenario: "D",
    base_scenario_display_label: scenarioLabels.D,
    story_comparison_order: ["D-B", "D-C", "D-A"],
    comparisons: [
      { comparison_key: "D-B", comparison_interpretation: "Natural ventilation effect without AC", row_count: 180 },
      { comparison_key: "D-C", comparison_interpretation: "Peak-window AC plus outside-window NV effect", row_count: 180 },
      { comparison_key: "D-A", comparison_interpretation: "Full active-cooling protection", row_count: 180 },
    ],
    rows: [],
  });
  scenarioSummary.mockResolvedValue({
    tier: "annual",
    scenario_semantics: scenarioLabels,
    scenario_ordering: "A, C, B, D",
    source_csv: "summary.csv",
    rows: [
      { hvac_scenario: "A", op_temp_p95_true_c: 24, hours_gt_28c: 1, humidity_hours: 2, degree_hours_28c: 1 },
      { hvac_scenario: "C", op_temp_p95_true_c: 27, hours_gt_28c: 10, humidity_hours: 20, degree_hours_28c: 20 },
      { hvac_scenario: "B", op_temp_p95_true_c: 29, hours_gt_28c: 20, humidity_hours: 30, degree_hours_28c: 40 },
      { hvac_scenario: "D", op_temp_p95_true_c: 33, hours_gt_28c: 40, humidity_hours: 50, degree_hours_28c: 80 },
    ],
  });
  const equityLayers = {
    populated: ["CDC/ATSDR SVI percentile"],
    ready: ["cdc_svi"],
    review_required: ["doe_lead_energy_burden"],
    pending_review_required: ["DOE LEAD energy burden"],
    proxy_badges_required: true,
    unverified_status: "REVIEW REQUIRED",
    verified_layer_count: 1,
    source_record_count: 1,
    catchment_join_method: "Tract-to-catchment area-weighted crosswalk over the selected 20 representative locations",
    note: "Fixture equity layer note",
    records: [
      {
        id: "cdc_svi",
        label: "CDC/ATSDR SVI percentile",
        value_fields: ["svi_percentile"],
        value_label: "Overall SVI percentile",
        status: "READY",
        source_vintage: "CDC/ATSDR SVI 2022 tract RPL_THEMES",
        proxy_badge: "Proxy",
        join_uncertainty_note: "Area-weighted proxy join",
        geography_level: "Census tract",
        source_url: "https://www.atsdr.cdc.gov/place-health/php/svi/index.html",
        verified: true,
      },
      {
        id: "doe_lead_energy_burden",
        label: "DOE LEAD energy burden",
        value_fields: ["doe_lead_energy_burden_pct"],
        value_label: "Energy burden percent",
        status: "REVIEW REQUIRED",
        source_vintage: "DOE LEAD source not verified",
        proxy_badge: "REVIEW REQUIRED",
        join_uncertainty_note: "No verified DOE LEAD join",
        geography_level: "LEAD geography",
        verified: false,
        missing_reason: "Missing verified source.",
      },
    ],
  };
  equityProfiles.mockResolvedValue({
    catchment_profile_status: "READY",
    disclaimer: "Real equity layers carry badges, source vintage, and join uncertainty.",
    layers: equityLayers,
    catchments: [
      {
        catchment_label: "Hot-Humid HDU",
        climate_region: "Hot-Humid",
        urbanicity_short: "HDU",
        svi_percentile: 0.82,
        acs_median_hh_income: 42000,
        acs_poverty_rate: 0.19,
        equity_layer_status: "PARTIAL",
      },
    ],
  });
  equityScenarioCross.mockResolvedValue({
    scenario: "D",
    scenario_label: scenarioLabels.D,
    scenario_display_label: scenarioLabels.D,
    dimension: "climate",
    group_column: "climate_region",
    metric_label: "Overheating exposure hours",
    threshold_note: "Threshold: operative temperature above 28 C.",
    rows: [
      {
        climate_region: "Hot-Humid",
        exposure_hours: 40,
        d_exposure_hours: 40,
        d_minus_scenario_exposure_hours: 0,
      },
    ],
    exposure: [],
    equity_layers: equityLayers,
    d_related_contrast: {
      base_scenario: "D",
      base_scenario_display_label: scenarioLabels.D,
      comparison_scenario: "D",
      comparison_scenario_display_label: scenarioLabels.D,
      metric: "op_temp_hours_gt_28c",
      metric_label: "Overheating exposure hours",
      threshold_note: "Threshold: operative temperature above 28 C.",
      vulnerability_layer_status: "READY",
    },
    note: "Descriptive exposure x vulnerability contrast only; no causal claim.",
  });
  atlasExports.mockResolvedValue({
    tier_id: "replocx_tmy3_wallfix_4scen",
    scenario_order: SCENARIOS,
    note: "Export paths resolve to f2v3_final.",
    citation_text: "ReplocX Research Atlas citation.",
    views: [
      {
        view: "scenario-summary",
        label: "Annual scenario summary",
        api_path: "/api/v1/results/scenario-summary",
        csv_export: { status: "READY", source_csv: "f2v3_final/tables/F02.csv" },
        citation_text: "Scenario summary citation.",
      },
      {
        view: "equity-profiles",
        label: "Equity profiles",
        api_path: "/api/v1/equity/profiles",
        csv_export: { status: "REVIEW REQUIRED", reason: "No verified equity profile CSV." },
        citation_text: "Equity citation.",
      },
    ],
    figure_bundles: [
      {
        figure_id: "Fig02",
        stem: "F02_summary",
        figure_class: "results",
        source_csv: "f2v3_final/tables/F02.csv",
        asset_png: "f2v3_final/F02.png",
        asset_pdf: "f2v3_final/F02.pdf",
        asset_svg: "f2v3_final/F02.svg",
        provenance_sidecar: "f2v3_final/F02.png.prov.json",
        api_path: "/api/v1/results/figure-bundle?figure_id=Fig02",
        citation_text: "Figure citation.",
      },
      {
        figure_id: "Fig19",
        stem: "F19_gate",
        figure_class: "supplementary",
        source_csv: "f2v3_final/tables/F19.csv",
        asset_png: "f2v3_final/F19.png",
        asset_pdf: "f2v3_final/F19.pdf",
        asset_svg: "f2v3_final/F19.svg",
        provenance_sidecar: "f2v3_final/F19.png.prov.json",
        api_path: "/api/v1/results/figure-bundle?figure_id=Fig19",
        citation_text: "Figure 19 citation.",
      },
    ],
  });
  atlasProvenance.mockResolvedValue({
    dataset: "ReplocX Research Atlas certified TMY3 wallfix four-scenario tier",
    tier: "replocx_tmy3_wallfix_4scen",
    tier_id: "replocx_tmy3_wallfix_4scen",
    certification: "R9 gate PASS",
    scenario_semantics: scenarioLabels,
    scenario_ordering: "A, C, B, D",
    manifest: "r9_reproduction_gate_report.json",
    source_canonical_root: "/canonical/replocx_tmy3_wallfix_4scen",
    copied_at: "read-only canonical source",
    tier_wall: "Only certified files.",
    file_checksums: { "figures.registry": { sha256: "abcdef1234567890", bytes: 42 } },
    data_directory: "/canonical/replocx_tmy3_wallfix_4scen",
    r9_gate_report: { source_csv: "audit/r9_reproduction_gate_report.json" },
    f2v3_gate_report: { status: "PASS", source_csv: "f2v3_final/gate_report.json" },
    f2v3_registry: {
      registry_csv: "f2v3_final/figure_registry.csv",
      registry_sidecar: "f2v3_final/figure_registry.csv.prov.json",
      figure_count: 19,
      captions_source: "f2v3_final/captions.md",
    },
    equity_verification: {
      status: "READY",
      verified_layer_count: 1,
      source_record_count: 1,
      catchment_join_method: "Tract-to-catchment area-weighted crosswalk over the selected 20 representative locations",
    },
    equity_source_notes: equityLayers.records,
    export_views: [],
  });
  dashboard.mockResolvedValue({
    scenario: { selected: [] },
    climate_distribution: {},
    urbanicity_distribution: {},
    kpis: {},
  });
  geometry.mockResolvedValue({ type: "FeatureCollection", metadata: {}, features: [] });
}

function renderAtlas(initial = "/atlas") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initial]}>
        <SelectionProvider>
          <Routes>
            <Route path="/atlas" element={<AtlasShell />}>
            <Route index element={<Introduction />} />
            <Route path="sealed-passive" element={<SealedPassive />} />
            <Route path="equity" element={<Equity />} />
            <Route path="exports" element={<Exports />} />
            <Route path="provenance" element={<Provenance />} />
          </Route>
          </Routes>
        </SelectionProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Research Atlas", () => {
  it("shows a disabled-mode panel when the backend has Atlas disabled", async () => {
    seedApi(false);
    renderAtlas();
    await waitFor(() => expect(screen.getByText(/not enabled here/i)).toBeInTheDocument());
    expect(screen.getByText(/RLE_ENABLE_ATLAS=1/)).toBeInTheDocument();
  });

  it("renders the pivot-first landing with dictionary labels and MapLibre drill path", async () => {
    seedApi(true);
    renderAtlas();
    await waitFor(() => expect(screen.getByRole("heading", { name: "National pivot" })).toBeInTheDocument());
    expect(screen.getAllByText("AC 2-8pm + NV other hours (C)").length).toBeGreaterThan(0);
    expect(screen.getAllByText("No AC or NV (D)").length).toBeGreaterThan(0);
    expect(screen.getByRole("img", { name: "Atlas MapLibre drill map" })).toBeInTheDocument();
  });

  it("renders the D story route on the D-B, D-C, and D-A contrasts", async () => {
    seedApi(true);
    renderAtlas("/atlas/sealed-passive");
    await waitFor(() => expect(screen.getByRole("heading", { name: "Sealed-passive D contrasts" })).toBeInTheDocument());
    expect(screen.getByRole("tab", { name: /D-B/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /D-C/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /D-A/ })).toBeInTheDocument();
  });

  it("reports max absolute F02 chart parity difference as zero", () => {
    const option = buildF02SummaryOption(F02_ROWS, "annual", scenarioLabels);
    const series = option.series as Array<{ data: Array<number | { value: number }> }>;
    const plotted = SCENARIOS.flatMap((_, index) =>
      series.map((item) => {
        const point = item.data[index];
        return typeof point === "number" ? point : point.value;
      }),
    );
    const source = f02ParityValues(F02_ROWS, "annual");
    const maxDiff = Math.max(...source.map((value, index) => Math.abs(value - plotted[index])));
    expect(maxDiff).toBe(0);
  });

  it("renders equity source badges and review-required layers", async () => {
    seedApi(true);
    renderAtlas("/atlas/equity");
    await waitFor(() => expect(screen.getByRole("heading", { name: "Layer verification" })).toBeInTheDocument());
    expect(screen.getByText("CDC/ATSDR SVI percentile")).toBeInTheDocument();
    expect(screen.getByText("CDC/ATSDR SVI 2022 tract RPL_THEMES")).toBeInTheDocument();
    expect(screen.getAllByText("REVIEW REQUIRED").length).toBeGreaterThan(0);
  });

  it("renders export CSV and f2v3 asset links", async () => {
    seedApi(true);
    renderAtlas("/atlas/exports");
    await waitFor(() => expect(screen.getByRole("heading", { name: "View CSV exports" })).toBeInTheDocument());
    expect(screen.getByText("Annual scenario summary")).toBeInTheDocument();
    expect(screen.getByText("f2v3_final/F02.png")).toBeInTheDocument();
    expect(screen.getByText("f2v3_final/F02.pdf")).toBeInTheDocument();
    expect(screen.getByText("f2v3_final/F02.svg")).toBeInTheDocument();
    expect(screen.getByText("Figure citation.")).toBeInTheDocument();
  });

  it("renders provenance gate, registry, captions, and equity source fields", async () => {
    seedApi(true);
    renderAtlas("/atlas/provenance");
    await waitFor(() => expect(screen.getAllByText("replocx_tmy3_wallfix_4scen").length).toBeGreaterThan(0));
    expect(screen.getByText("f2v3_final/gate_report.json")).toBeInTheDocument();
    expect(screen.getByText("f2v3_final/figure_registry.csv")).toBeInTheDocument();
    expect(screen.getByText("f2v3_final/captions.md")).toBeInTheDocument();
    expect(screen.getByText("CDC/ATSDR SVI 2022 tract RPL_THEMES")).toBeInTheDocument();
  });
});
