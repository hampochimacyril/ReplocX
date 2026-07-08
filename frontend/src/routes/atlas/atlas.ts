/*
 * Research Atlas shared state: TanStack Query hooks over the private
 * /api/v1/results/* + /api/v1/equity/* surfaces, plus the scenario/tier control
 * context shared across Atlas contexts, and the house-style scenario palette.
 */
import { createContext, useContext } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { AtlasTier, Scenario, StratumDimension } from "../../lib/types";

/** Four-scenario colorblind palette from the certified wallfix dictionary. */
export const SCENARIO_COLOR: Record<Scenario, string> = {
  A: "#0072B2",
  C: "#009E73",
  B: "#E69F00",
  D: "#D55E00",
};

export const SCENARIO_SHORT: Record<Scenario, string> = {
  A: "AC all day",
  C: "AC 2-8pm + NV other hours",
  B: "NV only",
  D: "No AC or NV",
};

export const SCENARIOS: Scenario[] = ["A", "C", "B", "D"];

export const STRATUM_DIMENSIONS: Array<{ key: StratumDimension; label: string }> = [
  { key: "climate", label: "Climate region" },
  { key: "urbanicity", label: "Urbanicity" },
  { key: "building", label: "Building type" },
  { key: "vintage", label: "Vintage group" },
];

/** Controls shared by the shell's top bar and every context. */
export interface AtlasControls {
  tier: AtlasTier;
  scenario: Scenario;
  scenarioLabels: Record<Scenario, string>;
  setTier: (t: AtlasTier) => void;
  setScenario: (s: Scenario) => void;
}

export const AtlasControlsContext = createContext<AtlasControls | null>(null);

export function useAtlasControls(): AtlasControls {
  const ctx = useContext(AtlasControlsContext);
  if (!ctx) throw new Error("useAtlasControls must be used within the Atlas shell");
  return ctx;
}

const STALE = 5 * 60_000;

export function useScenarioDictionary(enabled = true) {
  return useQuery({
    queryKey: ["atlas", "scenario-dictionary"],
    queryFn: api.atlas.scenarioDictionary,
    staleTime: STALE,
    enabled,
  });
}

export function useAtlasOverview() {
  return useQuery({ queryKey: ["atlas", "overview"], queryFn: api.atlas.overview, staleTime: STALE });
}

export function useScenarioSummary(tier: AtlasTier) {
  return useQuery({
    queryKey: ["atlas", "scenario-summary", tier],
    queryFn: () => api.atlas.scenarioSummary(tier),
    staleTime: STALE,
  });
}

export function useByStratum(tier: AtlasTier, dimension: StratumDimension) {
  return useQuery({
    queryKey: ["atlas", "by-stratum", tier, dimension],
    queryFn: () => api.atlas.byStratum(tier, dimension),
    staleTime: STALE,
  });
}

export function useScenarioC(tier: AtlasTier) {
  return useQuery({
    queryKey: ["atlas", "scenario-c", tier],
    queryFn: () => api.atlas.scenarioC(tier),
    staleTime: STALE,
  });
}

export function useDComparisons(tier: AtlasTier) {
  return useQuery({
    queryKey: ["atlas", "d-comparisons", tier],
    queryFn: () => api.atlas.dComparisons(tier),
    staleTime: STALE,
  });
}

export function useFigureRegistry() {
  return useQuery({
    queryKey: ["atlas", "figures"],
    queryFn: api.atlas.figures,
    staleTime: STALE,
  });
}

export function useFigureSource(figureId: string) {
  return useQuery({
    queryKey: ["atlas", "figure-source", figureId],
    queryFn: () => api.atlas.figureSource(figureId),
    staleTime: STALE,
  });
}

export function useFigureBundle(figureId: string) {
  return useQuery({
    queryKey: ["atlas", "figure-bundle", figureId],
    queryFn: () => api.atlas.figureBundle(figureId),
    staleTime: STALE,
  });
}

export function useAtlasExports() {
  return useQuery({
    queryKey: ["atlas", "exports"],
    queryFn: api.atlas.exports,
    staleTime: STALE,
  });
}

export function useExportView(view: string, tier: AtlasTier, dimension: StratumDimension, scenario: Scenario) {
  return useQuery({
    queryKey: ["atlas", "export-view", view, tier, dimension, scenario],
    queryFn: () => api.atlas.exportView(view, tier, dimension, scenario),
    staleTime: STALE,
  });
}

export function useCoolingSeasons() {
  return useQuery({
    queryKey: ["atlas", "cooling-seasons"],
    queryFn: api.atlas.coolingSeasons,
    staleTime: STALE,
  });
}

export function useAtlasProvenance() {
  return useQuery({ queryKey: ["atlas", "provenance"], queryFn: api.atlas.provenance, staleTime: STALE });
}

export function useEquityProfiles() {
  return useQuery({ queryKey: ["atlas", "equity"], queryFn: api.atlas.equityProfiles, staleTime: STALE });
}

export function useEquityScenarioCross(scenario: Scenario, dimension: StratumDimension) {
  return useQuery({
    queryKey: ["atlas", "equity-cross", scenario, dimension],
    queryFn: () => api.atlas.equityScenarioCross(scenario, dimension),
    staleTime: STALE,
  });
}

/** Round a metric to a readable number of digits (hours vs °C). */
export function fmt(value: number | string | boolean | null | undefined, digits = 0): string {
  if (value === null || value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}
