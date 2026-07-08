/* TanStack Query hooks for the /api/v1 surfaces used by the foundation. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type CandidateQuery } from "../lib/api";
import type { ScenarioConfig } from "../lib/types";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: api.health, staleTime: 30_000 });
}

export function useDashboard() {
  return useQuery({ queryKey: ["dashboard"], queryFn: api.dashboard, staleTime: 60_000 });
}

export function useProvenance() {
  return useQuery({ queryKey: ["provenance"], queryFn: api.provenance, staleTime: 5 * 60_000 });
}

export function useGeometry() {
  return useQuery({ queryKey: ["geometry"], queryFn: api.geometry, staleTime: 5 * 60_000 });
}

export function useCandidates(q: CandidateQuery) {
  return useQuery({
    queryKey: ["candidates", q],
    queryFn: () => api.candidates(q),
    staleTime: 30_000,
  });
}

export function useAllCandidates() {
  return useQuery({
    queryKey: ["candidates", "all"],
    queryFn: api.allCandidates,
    staleTime: 60_000,
  });
}

/** Evaluate a scenario configuration. Disabled (and idle) when `config` is null,
 * which the map treats as "use the dashboard baseline". The query key is the
 * serialized config so distinct edits are cached independently. */
export function useEvaluate(config: ScenarioConfig | null) {
  return useQuery({
    queryKey: ["evaluate", config ? JSON.stringify(config) : null],
    queryFn: () => api.evaluate(config!),
    enabled: config !== null,
    staleTime: 60_000,
  });
}

export function useScenariosList(limit = 50) {
  return useQuery({
    queryKey: ["scenarios", "list", limit],
    queryFn: () => api.scenarios.list(limit),
    staleTime: 10_000,
  });
}

export function useSavedScenario(id: string | null) {
  return useQuery({
    queryKey: ["scenarios", "get", id],
    queryFn: () => api.scenarios.get(id!),
    enabled: !!id,
  });
}

/** Save a versioned scenario, then refresh the saved-scenario list. */
export function useSaveScenario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (config: Partial<ScenarioConfig> & { parent_id?: string | null }) => api.scenarios.save(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenarios", "list"] });
    },
  });
}
