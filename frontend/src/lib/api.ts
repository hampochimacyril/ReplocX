/*
 * Typed client for the versioned /api/v1 contract. Same-origin only (the backend
 * sets a strict CSP), so every request is a relative path. The Python backend
 * remains responsible for data, scoring, persistence, and exports.
 */
import { authHeaders, promptForToken } from "./auth";
import type {
  CatchmentRow,
  CandidatesPage,
  DashboardResponse,
  GeometryResponse,
  HealthResponse,
  ProvenanceResponse,
  SavedScenario,
  ScenarioConfig,
  ScenarioListResponse,
  ScenarioResult,
  ZipLookupResponse,
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
};
