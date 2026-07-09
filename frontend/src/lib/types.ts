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
  atlas_enabled?: boolean;
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

/* ---------------------------------------------------------------------------
 * Research Atlas (private ReplocX TMY3 results tier). All rows are loosely
 * typed maps because the certified CSVs carry many metric columns; the UI
 * reads the ones it charts and passes the rest through.
 * ------------------------------------------------------------------------- */

export type AtlasTier = "annual" | "seasonal";
export type Scenario = "A" | "C" | "B" | "D";
export type StratumDimension = "climate" | "urbanicity" | "stratum" | "building" | "vintage";

export type MetricRow = Record<string, number | string | boolean | null>;

export interface ScenarioSummaryResponse {
  schema_version?: string;
  tier_id?: string;
  tier: AtlasTier;
  scenario_semantics: Record<Scenario, string>;
  scenario_ordering: string;
  scenario_order?: Scenario[];
  rows: MetricRow[];
  metric_notes?: Record<string, string>;
  endpoint_definitions?: AtlasEndpointDefinitions;
  source_csv?: string;
  provenance_sidecar?: string;
}

export interface ScenarioDictionaryEntry {
  code: Scenario;
  scenario_display_label: string;
  scenario_order: number;
  scenario_color: string;
  cooling?: string;
  heating?: string;
  natural_ventilation?: string;
}

export interface ScenarioDictionaryResponse {
  schema_version?: string;
  tier_id: string;
  scenario_order: Scenario[];
  scenarios: ScenarioDictionaryEntry[];
  source_csv?: string;
  provenance_sidecar?: string;
}

export interface ByStratumResponse {
  schema_version?: string;
  contract_version?: "atlas.strata/1.0";
  tier_id?: string;
  tier: AtlasTier;
  dimension: StratumDimension;
  group_column: string;
  group_columns?: string[];
  stratum_count?: number;
  scenario_ordering?: string;
  scenario_order?: Scenario[];
  strata?: AtlasStratum[];
  rows: MetricRow[];
  aggregation?: {
    location: "server";
    source_level: string;
    method: string;
    metric_columns: string[];
  };
  certified_provenance?: {
    tier_id: string;
    r9_status: "PASS" | string;
    figure_registry_tier: "f2v3_final";
    read_only: boolean;
  };
  metric_notes?: Record<string, string>;
  endpoint_definitions?: AtlasEndpointDefinitions;
  source_csv?: string;
  provenance_sidecar?: string;
}

export interface AtlasStratum {
  stratum_id: string;
  stratum_label: string;
  climate_region: string;
  urbanicity: string;
  location_label: string;
  scenario_cell_counts: Record<Scenario, number>;
}

export interface ScenarioCSummary {
  n_cells: number;
  avoided_gt_28c_mean: number | null;
  residual_gt_28c_mean: number | null;
  benefit_fraction_gt_28c_mean: number | null;
  avoided_gt_30c_mean: number | null;
  residual_gt_30c_mean: number | null;
  off_window_hours_gt_28c_mean: number | null;
  overnight_residual_hours_gt_28c_mean: number | null;
}

export interface ScenarioCResponse {
  schema_version?: string;
  tier_id?: string;
  tier: AtlasTier;
  scenario_semantics: Record<Scenario, string>;
  overall: ScenarioCSummary;
  by_climate: Array<{ climate_region: string } & ScenarioCSummary>;
  metric_notes?: Record<string, string>;
  source_csv?: string;
  provenance_sidecar?: string;
}

export interface CoolingSeasonsResponse {
  schema_version?: string;
  tier_id?: string;
  available?: boolean;
  sites: MetricRow[];
  long_term?: MetricRow[];
  long_term_note: string;
  reason?: string;
}

export interface AtlasOverviewResponse {
  schema_version?: string;
  tier_id?: string;
  dataset: string;
  tier: string;
  scenario_semantics: Record<Scenario, string>;
  scenario_ordering: string;
  scenario_order?: Scenario[];
  tier_wall: string;
  n_cells: number;
  scenario_summary: ScenarioSummaryResponse;
  metric_notes?: Record<string, string>;
}

export interface AtlasEndpointDefinitions {
  primary_endpoint_families: string[];
  rows?: MetricRow[];
  source_csv?: string;
  provenance_sidecar?: string;
}

export interface AtlasProvenanceResponse {
  schema_version?: string;
  dataset: string;
  tier: string;
  tier_id?: string;
  certified_cell_count?: number;
  certification: string;
  r9_status?: string;
  r9_certification?: Record<string, unknown>;
  scenario_semantics: Record<Scenario, string>;
  scenario_ordering: string;
  scenario_order?: Scenario[];
  manifest: string;
  canonical_data_root?: string;
  figure_registry_root?: string;
  source_canonical_root: string;
  read_only_sources?: boolean;
  figure_registry_tier?: "f2v3_final";
  r9_gate_report?: CsvExportDescriptor;
  f2v3_gate_report?: CsvExportDescriptor & { status?: string; report?: Record<string, unknown> };
  f2v3_registry?: {
    registry_csv: string;
    registry_sidecar: string;
    figure_count: number;
    captions_source?: string | null;
    captions_sidecar?: string | null;
  };
  equity_source_notes?: EquityLayerRecord[];
  equity_verification?: {
    status: "READY" | "REVIEW REQUIRED" | string;
    verified_layer_count: number;
    source_record_count: number;
    catchment_join_method: string;
    source_csv?: CsvExportDescriptor | null;
    missing_source_path?: string | null;
  };
  export_views?: ExportViewRecord[];
  endpoint_definitions?: AtlasEndpointDefinitions;
  tier_wall: string;
  copied_at: string;
  file_checksums: Record<string, { sha256: string; bytes: number; file?: string; sidecar?: string }>;
  data_directory: string;
}

export interface DComparisonsResponse {
  schema_version?: string;
  tier_id?: string;
  tier: AtlasTier;
  base_scenario: "D";
  base_scenario_display_label?: string;
  comparison_order?: string[];
  story_comparison_order?: string[];
  comparisons?: MetricRow[];
  metric_notes?: Record<string, string>;
  rows: MetricRow[];
  source_csv?: string;
  provenance_sidecar?: string;
}

export interface FigureRegistryResponse {
  schema_version?: string;
  tier_id: string;
  registry_tier: "f2v3_final";
  registry_csv?: string;
  figures?: FigureRegistryRow[];
  rows: FigureRegistryRow[];
  source_csv?: string;
  provenance_sidecar?: string;
}

export interface FigureRegistryRow extends MetricRow {
  figure_id: string;
  stem: string;
  figure_class: "results" | "supplementary" | string;
  tier_id: string;
  source_csv: string;
  asset_png: string;
  asset_pdf: string;
  asset_svg: string;
  caption: string;
  alt_text: string;
  atlas_route: string;
  provenance_sidecar: string;
}

export interface FigureSourceResponse {
  schema_version?: string;
  tier_id: string;
  registry_tier: "f2v3_final";
  figure: FigureRegistryRow;
  figure_id: string;
  source_csv: string;
  provenance_sidecar: string;
  rows: MetricRow[];
}

export interface FigureBundleResponse {
  schema_version?: string;
  tier_id: string;
  registry_tier: "f2v3_final";
  figure: FigureRegistryRow;
  figure_id: string;
  source_csv: string;
  source_csv_sidecar: string;
  assets: Record<"png" | "pdf" | "svg", string>;
  asset_sidecars: Record<"png" | "pdf" | "svg", string>;
  caption?: string;
  alt_text?: string;
  atlas_route?: string;
  citation_text: string;
}

export interface CsvExportDescriptor {
  status?: "READY" | "REVIEW REQUIRED" | string;
  label?: string;
  source_csv?: string | null;
  provenance_sidecar?: string | null;
  read_only?: boolean;
  reason?: string;
}

export interface ExportViewRecord {
  view: string;
  label: string;
  api_path: string;
  csv_export: CsvExportDescriptor;
  citation_text: string;
}

export interface ExportCatalogResponse {
  schema_version?: string;
  tier_id: string;
  scenario_order: Scenario[];
  views: ExportViewRecord[];
  figure_bundles: Array<{
    figure_id: string;
    stem: string;
    figure_class: string;
    source_csv: string;
    asset_png: string;
    asset_pdf: string;
    asset_svg: string;
    provenance_sidecar: string;
    api_path: string;
    citation_text: string;
  }>;
  citation_text: string;
  f2v3_gate_report?: CsvExportDescriptor & { status?: string };
  note: string;
}

export interface ExportViewResponse {
  schema_version?: string;
  tier_id: string;
  scenario_order: Scenario[];
  view: string;
  label: string;
  api_path: string;
  csv_export: CsvExportDescriptor;
  source_csv?: string | null;
  provenance_sidecar?: string | null;
  row_count: number;
  rows: MetricRow[];
  citation_text: string;
  payload: Record<string, unknown>;
}

export interface EquityLayerRecord {
  id: string;
  label: string;
  value_fields: string[];
  value_label: string;
  status: "READY" | "REVIEW REQUIRED" | string;
  source_vintage: string;
  proxy_badge: "Direct" | "Proxy" | "Modeled" | "REVIEW REQUIRED" | string;
  join_uncertainty_note: string;
  geography_level: string;
  source_url?: string;
  verified: boolean;
  missing_reason?: string | null;
}

export interface EquityLayers {
  populated: string[];
  ready: string[];
  review_required: string[];
  pending_review_required: string[];
  records: EquityLayerRecord[];
  proxy_badges_required: boolean;
  unverified_status: "REVIEW REQUIRED" | string;
  verified_layer_count: number;
  source_record_count: number;
  catchment_join_method: string;
  note: string;
}

export interface EquityProfilesResponse {
  schema_version?: string;
  tier_id?: string;
  profiles?: MetricRow[];
  catchments: MetricRow[];
  layers: EquityLayers;
  source_csv?: string | null;
  provenance_sidecar?: string | null;
  missing_source_path?: string | null;
  catchment_profile_status?: "READY" | "REVIEW REQUIRED" | string;
  disclaimer: string;
}

export interface EquityScenarioCrossResponse {
  schema_version?: string;
  tier_id?: string;
  scenario: Scenario;
  scenario_label: string;
  scenario_display_label?: string;
  dimension: StratumDimension;
  group_column: string;
  metric?: string;
  metric_label?: string;
  threshold_note?: string;
  rows: MetricRow[];
  exposure: MetricRow[];
  equity_layers: EquityLayers;
  vulnerability_layer?: EquityLayerRecord;
  d_related_contrast?: {
    base_scenario: "D";
    base_scenario_display_label: string;
    comparison_scenario: Scenario;
    comparison_scenario_display_label: string;
    metric: string;
    metric_label: string;
    threshold_note: string;
    vulnerability_layer_status: string;
  };
  note: string;
}

export interface SensitivityResponse {
  schema_version?: string;
  tier_id?: string;
  available?: boolean;
  leave_one_location_out: MetricRow[];
  degreeday_year_deltas: MetricRow[];
  repro_check: MetricRow[];
  reason?: string;
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
