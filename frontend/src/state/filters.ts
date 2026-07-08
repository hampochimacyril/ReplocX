/*
 * Filter/scenario state is URL-encoded so any view is shareable and reproducible
 * (docs/UI_REDESIGN_SPEC.md §3). The map, coverage matrix, table, and charts all
 * read the same parsed filter object.
 */
import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export interface Filters {
  climate: string;
  urbanicity: string;
  selectedStatus: "" | "selected" | "candidate";
  verification: string;
  weatherQc: string;
  scoreMin: number;
  scoreMax: number;
  maxStationDistance: number | null;
  search: string;
}

export const DEFAULT_FILTERS: Filters = {
  climate: "",
  urbanicity: "",
  selectedStatus: "",
  verification: "",
  weatherQc: "",
  scoreMin: 0,
  scoreMax: 1,
  maxStationDistance: null,
  search: "",
};

export function parseFilters(params: URLSearchParams): Filters {
  const num = (key: string, fallback: number) => {
    const raw = params.get(key);
    if (raw === null) return fallback;
    const value = Number(raw);
    return Number.isFinite(value) ? value : fallback;
  };
  const selected = params.get("selected");
  return {
    climate: params.get("climate") ?? "",
    urbanicity: params.get("urbanicity") ?? "",
    selectedStatus: selected === "1" || selected === "selected" ? "selected" : selected === "candidate" ? "candidate" : "",
    verification: params.get("verification") ?? "",
    weatherQc: params.get("qc") ?? "",
    scoreMin: num("smin", 0),
    scoreMax: num("smax", 1),
    maxStationDistance: params.has("dist") ? num("dist", 0) : null,
    search: params.get("q") ?? "",
  };
}

export function filtersToParams(filters: Filters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.climate) params.set("climate", filters.climate);
  if (filters.urbanicity) params.set("urbanicity", filters.urbanicity);
  if (filters.selectedStatus) params.set("selected", filters.selectedStatus);
  if (filters.verification) params.set("verification", filters.verification);
  if (filters.weatherQc) params.set("qc", filters.weatherQc);
  if (filters.scoreMin > 0) params.set("smin", String(filters.scoreMin));
  if (filters.scoreMax < 1) params.set("smax", String(filters.scoreMax));
  if (filters.maxStationDistance !== null) params.set("dist", String(filters.maxStationDistance));
  if (filters.search) params.set("q", filters.search);
  return params;
}

export function isDefault(filters: Filters): boolean {
  return filtersToParams(filters).toString() === "";
}

/** Hook bound to the router so filter state lives in the address bar. */
export function useFilters() {
  const [params, setParams] = useSearchParams();
  const filters = useMemo(() => parseFilters(params), [params]);

  const setFilters = useCallback(
    (next: Partial<Filters>) => {
      setParams(filtersToParams({ ...filters, ...next }), { replace: true });
    },
    [filters, setParams],
  );

  const reset = useCallback(() => setParams(new URLSearchParams(), { replace: true }), [setParams]);

  return { filters, setFilters, reset };
}
