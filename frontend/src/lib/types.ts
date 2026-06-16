/*
 * TypeScript shapes for the ReplocX /api/v1 contract.
 * These mirror the live demo responses captured from the Python backend
 * (backend/data_service.py). The backend owns data, scoring, persistence, and
 * exports; the frontend never recomputes selection.
 */

export type DataMode = "demo" | "production";

export interface AuthStatus {
  required: boolean;
  configured: boolean;
  token_env: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  version: string;
  api_version: string;
  data_ready: boolean;
  auth: AuthStatus;
  scenario_store: { database_env: string; default_path: string };
  detail?: string;
  data_mode?: DataMode;
  analysis_directory?: string;
  candidate_count?: number;
  selected_count?: number;
  method_version?: string | null;
}

/** A single catchment row — shared by candidates, dashboard.selected, etc. */
export interface CatchmentRow {
  climate_region: string;
  urbanicity: string;
  urbanicity_short: string;
  catchment_type: "CBSA" | "County" | string;
  catchment_code: string;
  catchment_label: string;
  population_2010: number;
  housing_units_2010: number;
  population_density_sqmi: number;
  housing_unit_density_sqmi: number;
  housing_unit_coverage_percentile: number;
  population_density_percentile: number;
  population_coverage_percentile: number;
  location_score: number;
  selection_rank: number;
  selected: boolean;
  station_distance_miles: number;
  selected_station_name: string;
  selected_station_number: number;
  selected_station_lat: number;
  selected_station_lon: number;
  centroid_lat: number;
  centroid_lon: number;
  hourly_weather_qc_status: "COMPLETE" | "INCOMPLETE" | string;
  location_uniqueness_key: string;
  // scenario-evaluated fields (present in dashboard.scenario.selected)
  scenario_score?: number;
  scenario_selected?: boolean;
  scenario_rank?: number;
  scenario_note?: string;
  scenario_eligible?: boolean;
  // ResStock / ComStock enumeration mapping
  nrel_filter_field?: string;
  nrel_filter_value?: number | string;
  nrel_value_verified?: boolean;
  nrel_verification_status?: "VERIFIED" | "REVIEW REQUIRED" | string;
  filter_scope_note?: string;
  // candidate-only baseline flag
  baseline_selected?: boolean;
}

export interface ScenarioWeights {
  housing_unit_coverage_percentile: number;
  population_density_percentile: number;
  population_coverage_percentile: number;
}

export interface ScenarioOverride {
  climate_region: string;
  urbanicity: string;
  catchment_type: string;
  catchment_code: string;
  rationale?: string;
}

export interface ScenarioConfig {
  version: string;
  name: string;
  density_screen_percentile: number;
  weights: ScenarioWeights;
  unique_location_constraint: boolean;
  max_station_distance_miles: number;
  station_distance_penalty: number;
  require_weather_qc: boolean;
  overrides?: ScenarioOverride[];
}

export interface ScenarioChange {
  climate_region: string;
  urbanicity: string;
  urbanicity_short: string;
  from_key: string;
  from_label: string;
  to_key: string;
  to_label: string;
  score_loss: number;
  reason: string;
}

export interface ScenarioSummary {
  strata_count: number;
  represented_location_count: number;
  independent_location_count: number;
  distinct_location_count: number;
  combined_score: number;
  independent_combined_score: number;
  score_difference: number;
  changed_assignment_count: number;
  eligible_candidate_count: number;
  coverage_efficiency: number;
  min_scenario_score: number;
  median_scenario_score: number;
  mean_station_distance_miles: number;
  max_station_distance_miles: number;
  mean_unconstrained_rank: number;
}

export interface ScenarioResult {
  config: ScenarioConfig;
  independent: CatchmentRow[];
  distinct: CatchmentRow[];
  selected: CatchmentRow[];
  changes: ScenarioChange[];
  summary: ScenarioSummary;
}

export interface DashboardKpis {
  target_strata: number;
  distinct_locations: number;
  candidate_count: number;
  verified_filter_count: number;
  weather_qc_complete_count: number;
}

export interface ScoreBin {
  label: string;
  count: number;
}

export interface DashboardResponse {
  scenario: ScenarioResult;
  kpis: DashboardKpis;
  climate_distribution: Record<string, number>;
  urbanicity_distribution: Record<string, number>;
  score_distribution: ScoreBin[];
  provenance: ProvenanceResponse;
}

export interface ProvenanceSource {
  name: string;
  role: string;
  file?: string;
  version?: string;
}

export interface ProvenanceResponse {
  analysis_name: string;
  method_version: string;
  boundary_system: string;
  data_mode: DataMode;
  source_directory: string;
  sources: ProvenanceSource[];
  limitations: string[];
  zip_crosswalk: {
    mode: string;
    record_count: number;
    source_version: string;
    limitation: string;
  };
  weather_qc: { threshold: string; stations_scored: number; status: string };
}

export interface GeometryFeatureProps {
  catchment_type: string;
  catchment_code: string;
  catchment_label: string;
  climate_region: string;
  urbanicity_short: string;
  geometry_kind: string;
}

export interface GeometryFeature {
  type: "Feature";
  properties: GeometryFeatureProps;
  geometry: {
    type: "Polygon" | "MultiPolygon";
    coordinates: number[][][] | number[][][][];
  };
}

export interface GeometryResponse {
  type: "FeatureCollection";
  metadata: Record<string, unknown>;
  features: GeometryFeature[];
}

export interface CandidatesPage {
  rows: CatchmentRow[];
  total: number;
  returned: number;
  limit: number;
  offset: number;
  has_more: boolean;
  next_offset: number;
}

export interface ZipResolution {
  zip_code: string;
  zcta: string;
  county_geoid: string;
  county_label: string;
  cbsa_code: string;
  cbsa_label: string;
  state: string;
  climate_region: string;
  urbanicity: string;
  urbanicity_short: string;
  allocation_ratio: number;
  match_type: string;
  uncertainty_note: string;
  source_version: string;
  latitude: number;
  longitude: number;
}

/** Metadata returned when a scenario is saved or listed (backend/scenario_store.py). */
export interface SavedScenarioMeta {
  id: string;
  parent_id: string | null;
  root_id?: string;
  version: number;
  name: string;
  created_at: string;
  share_path: string;
  summary: ScenarioSummary;
}

/** A full saved scenario (list/save also include config on save and get). */
export interface SavedScenario extends SavedScenarioMeta {
  config: ScenarioConfig;
}

export interface ScenarioListResponse {
  scenarios: SavedScenarioMeta[];
  returned: number;
  limit: number;
}

export interface ZipLookupResponse {
  zip_code: string;
  resolved: ZipResolution;
  crosswalk_matches: ZipResolution[];
  candidate: CatchmentRow | null;
  selected_representative: CatchmentRow | null;
  nearby_weather_stations: Array<{
    station_name: string;
    station_number: number | string;
    distance_from_zip_miles: number | null;
    latitude: number;
    longitude: number;
    weather_qc_status: string;
  }>;
  simulation_filter_geography: Record<string, unknown>;
}
