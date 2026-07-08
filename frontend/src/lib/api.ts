/*
 * Typed client for the versioned /api/v1 contract. Same-origin only (the backend
 * sets a strict CSP), so every request is a relative path. The Python backend
 * remains responsible for data, scoring, persistence, and exports.
 */
import { authHeaders, promptForToken } from "./auth";
import type {
  AtlasOverviewResponse,
  AtlasProvenanceResponse,
  AtlasTier,
  ByStratumResponse,
  CatchmentRow,
  CandidatesPage,
  CoolingSeasonsResponse,
  DashboardResponse,
  ExportCatalogResponse,
  ExportViewResponse,
  EquityProfilesResponse,
  EquityScenarioCrossResponse,
  FigureBundleResponse,
  GeometryResponse,
  HealthResponse,
  ProvenanceResponse,
  SavedScenario,
  Scenario,
  ScenarioCResponse,
  ScenarioConfig,
  ScenarioDictionaryResponse,
  ScenarioListResponse,
  ScenarioResult,
  ScenarioSummaryResponse,
  SensitivityResponse,
  StratumDimension,
  ZipLookupResponse,
  DComparisonsResponse,
  FigureSourceResponse,
  FigureRegistryResponse,
} from "./types";

export const API_BASE = "/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // Loop so that a 401 on a private deployment can prompt for an access token
  // and retry once the user supplies it. The public demo never 401s, so the
  // loop runs exactly once there.
  for (;;) {
    let res: Response;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        headers: {
          Accept: "application/json",
          ...(init?.body ? { "Content-Type": "application/json" } : {}),
          ...authHeaders(),
        },
        ...init,
      });
    } catch (cause) {
      throw new ApiError(0, `Network error contacting the API: ${(cause as Error).message}`);
    }
    const text = await res.text();
    const data = text ? safeJson(text) : null;
    if (res.status === 401) {
      const token = await promptForToken();
      if (token) continue; // retry with the freshly entered bearer token
    }
    if (!res.ok) {
      const detail =
        (data && typeof data === "object" && ("error" in data ? (data as { error?: string }).error : (data as { detail?: string }).detail)) ||
        `Request failed (${res.status})`;
      throw new ApiError(res.status, String(detail));
    }
    return data as T;
  }
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function query(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export interface CandidateQuery {
  search?: string;
  climate?: string;
  urbanicity?: string;
  selected_only?: boolean;
  limit?: number;
  offset?: number;
}

async function allCandidates(): Promise<CatchmentRow[]> {
  const rows: CatchmentRow[] = [];
  let offset = 0;

  for (;;) {
    const page = await request<CandidatesPage>(`/candidates${query({ limit: 3000, offset })}`);
    rows.push(...page.rows);
    if (!page.has_more || page.next_offset === null || page.next_offset === undefined) break;
    offset = page.next_offset;
  }

  return rows;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  dashboard: () => request<DashboardResponse>("/dashboard"),
  provenance: () => request<ProvenanceResponse>("/provenance"),
  geometry: () => request<GeometryResponse>("/geometry"),
  candidates: (q: CandidateQuery = {}) => request<CandidatesPage>(`/candidates${query({ ...q })}`),
  allCandidates,
  zip: (zip: string) => request<ZipLookupResponse>(`/zip/${encodeURIComponent(zip)}`),
  evaluate: (config: Partial<ScenarioConfig>) =>
    request<ScenarioResult>("/scenarios/evaluate", { method: "POST", body: JSON.stringify(config) }),
  scenarios: {
    list: (limit = 50) => request<ScenarioListResponse>(`/scenarios${query({ limit })}`),
    get: (id: string) => request<SavedScenario>(`/scenarios/${encodeURIComponent(id)}`),
    /** Save a versioned scenario. Passing `parent_id` records a new version in a lineage. */
    save: (config: Partial<ScenarioConfig> & { parent_id?: string | null }) =>
      request<SavedScenario>("/scenarios", { method: "POST", body: JSON.stringify(config) }),
  },
  /**
   * Research Atlas (private ReplocX TMY3 results tier). These endpoints only
   * respond when the backend is started with RLE_ENABLE_ATLAS=1; otherwise they
   * return 404 (surfaced as an ApiError the Atlas shell renders as "not enabled
   * on this deployment"), so the public demo never exposes the private results.
   */
  atlas: {
    overview: () => request<AtlasOverviewResponse>("/results/overview"),
    scenarioDictionary: () => request<ScenarioDictionaryResponse>("/results/scenario-dictionary"),
    scenarioSummary: (tier: AtlasTier = "annual") =>
      request<ScenarioSummaryResponse>(`/results/scenario-summary${query({ tier })}`),
    byStratum: (tier: AtlasTier, dimension: StratumDimension) =>
      request<ByStratumResponse>(`/results/by-stratum${query({ tier, dimension })}`),
    scenarioC: (tier: AtlasTier = "annual") =>
      request<ScenarioCResponse>(`/results/scenario-c${query({ tier })}`),
    dComparisons: (tier: AtlasTier = "annual") =>
      request<DComparisonsResponse>(`/results/d-comparisons${query({ tier })}`),
    figures: () => request<FigureRegistryResponse>("/results/figures"),
    figureSource: (figure_id: string) =>
      request<FigureSourceResponse>(`/results/figure-source${query({ figure_id })}`),
    figureBundle: (figure_id: string) =>
      request<FigureBundleResponse>(`/results/figure-bundle${query({ figure_id })}`),
    exports: () => request<ExportCatalogResponse>("/results/exports"),
    exportView: (
      view: string,
      tier: AtlasTier = "annual",
      dimension: StratumDimension = "climate",
      scenario: Scenario = "D",
    ) => request<ExportViewResponse>(`/results/export-view${query({ view, tier, dimension, scenario })}`),
    coolingSeasons: () => request<CoolingSeasonsResponse>("/results/cooling-seasons"),
    sensitivity: () => request<SensitivityResponse>("/results/sensitivity"),
    provenance: () => request<AtlasProvenanceResponse>("/results/provenance"),
    equityProfiles: () => request<EquityProfilesResponse>("/equity/profiles"),
    equityScenarioCross: (scenario: Scenario = "D", dimension: StratumDimension = "climate") =>
      request<EquityScenarioCrossResponse>(`/equity/scenario-cross${query({ scenario, dimension })}`),
  },
};
