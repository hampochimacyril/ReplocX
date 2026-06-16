/* Shared API fixtures + a provider harness for route-level integration tests.
 * Mirrors the demo /api/v1 response shapes so route components exercise their
 * real data paths (state/rows, scenario, compare) without a network. */
import { makeRow } from "./fixtures";
import type {
  CatchmentRow,
  DashboardResponse,
  ProvenanceResponse,
  ScenarioConfig,
  ScenarioResult,
  ScenarioSummary,
} from "../lib/types";

export const DEMO_CONFIG: ScenarioConfig = {
  version: "1.0",
  name: "User-defined scenario",
  density_screen_percentile: 0.6,
  weights: {
    housing_unit_coverage_percentile: 0.45,
    population_density_percentile: 0.35,
    population_coverage_percentile: 0.2,
  },
  unique_location_constraint: true,
  max_station_distance_miles: 250,
  station_distance_penalty: 0,
  require_weather_qc: false,
  overrides: [
    {
      climate_region: "Mixed-Humid",
      urbanicity: "higher density urban",
      catchment_type: "CBSA",
      catchment_code: "37980",
      rationale: "Research-priority override.",
    },
  ],
};

export function makeSelected(): CatchmentRow[] {
  return [
    makeRow({
      catchment_code: "10000",
      catchment_label: "Cold HDU rep (demo)",
      location_uniqueness_key: "CBSA:10000",
      location_score: 0.92,
      scenario_score: 0.92,
      scenario_rank: 1,
      station_distance_miles: 20,
    }),
    makeRow({
      climate_region: "Marine",
      urbanicity: "rural",
      urbanicity_short: "Rural",
      catchment_type: "County",
      catchment_code: "41005",
      catchment_label: "Marine rural rep (demo)",
      location_uniqueness_key: "County:41005",
      location_score: 0.71,
      scenario_score: 0.71,
      scenario_rank: 1,
      station_distance_miles: 88,
      hourly_weather_qc_status: "COMPLETE",
      nrel_verification_status: "REVIEW REQUIRED",
      nrel_value_verified: false,
    }),
  ];
}

export function makeCandidates(): CatchmentRow[] {
  const selected = makeSelected().map((r) => ({ ...r, baseline_selected: true }));
  const extras = [
    makeRow({
      catchment_code: "20000",
      catchment_label: "Cold HDU candidate B (demo)",
      location_uniqueness_key: "CBSA:20000",
      selected: false,
      scenario_selected: false,
      location_score: 0.61,
      scenario_score: undefined,
      selection_rank: 2,
      station_distance_miles: 140,
      baseline_selected: false,
    }),
    makeRow({
      climate_region: "Hot-Humid",
      urbanicity_short: "LDU",
      urbanicity: "lower density urban",
      catchment_code: "30000",
      catchment_label: "Hot-Humid LDU candidate (demo)",
      location_uniqueness_key: "CBSA:30000",
      selected: false,
      scenario_selected: false,
      location_score: 0.44,
      scenario_score: undefined,
      selection_rank: 3,
      station_distance_miles: 200,
      baseline_selected: false,
    }),
  ];
  return [...selected, ...extras];
}

export function makeSummary(partial: Partial<ScenarioSummary> = {}): ScenarioSummary {
  return {
    strata_count: 20,
    represented_location_count: 20,
    independent_location_count: 20,
    distinct_location_count: 20,
    combined_score: 18.0,
    independent_combined_score: 18.05,
    score_difference: -0.05,
    changed_assignment_count: 1,
    eligible_candidate_count: 2959,
    coverage_efficiency: 0.997,
    min_scenario_score: 0.71,
    median_scenario_score: 0.9,
    mean_station_distance_miles: 54,
    max_station_distance_miles: 110,
    mean_unconstrained_rank: 1.05,
    ...partial,
  };
}

export function makeScenarioResult(config: ScenarioConfig = DEMO_CONFIG): ScenarioResult {
  const selected = makeSelected();
  return {
    config,
    independent: selected,
    distinct: selected,
    selected,
    changes: [
      {
        climate_region: "Mixed-Humid",
        urbanicity: "higher density urban",
        urbanicity_short: "HDU",
        from_key: "CBSA:47900",
        from_label: "Washington (demo)",
        to_key: "CBSA:37980",
        to_label: "Philadelphia (demo)",
        score_loss: 0.051,
        reason: "Research-priority override. Unconstrained rank: 2.",
      },
    ],
    summary: makeSummary(),
  };
}

export const PROVENANCE: ProvenanceResponse = {
  analysis_name: "ReplocX demo",
  method_version: "demo-1.2",
  boundary_system: "2020 TIGER/Line",
  data_mode: "demo",
  source_directory: "data/demo",
  sources: [{ name: "Census", role: "population", version: "2020" }],
  limitations: ["Synthetic demo dataset."],
  zip_crosswalk: { mode: "HUD-USPS", record_count: 10, source_version: "2024Q1", limitation: "demo only" },
  weather_qc: { threshold: "≥90% hourly", stations_scored: 20, status: "scored" },
};

export function makeDashboard(): DashboardResponse {
  return {
    scenario: makeScenarioResult(),
    kpis: {
      target_strata: 20,
      distinct_locations: 20,
      candidate_count: 2959,
      verified_filter_count: 19,
      weather_qc_complete_count: 14,
    },
    climate_distribution: {},
    urbanicity_distribution: {},
    score_distribution: [],
    provenance: PROVENANCE,
  };
}
