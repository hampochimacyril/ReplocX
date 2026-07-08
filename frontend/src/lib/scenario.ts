/*
 * Pure, unit-testable helpers for scenario-config editing. The backend
 * (backend/models.py) is the source of truth for validation; these mirror its
 * rules client-side so the workbench can give immediate feedback before an
 * evaluate round-trip. Score weights must sum to 1.0 (a non-negotiable invariant).
 */
import type { ScenarioConfig, ScenarioWeights } from "./types";

export const WEIGHT_KEYS: Array<keyof ScenarioWeights> = [
  "housing_unit_coverage_percentile",
  "population_density_percentile",
  "population_coverage_percentile",
];

export const WEIGHT_LABELS: Record<keyof ScenarioWeights, string> = {
  housing_unit_coverage_percentile: "Housing-unit coverage",
  population_density_percentile: "Population density",
  population_coverage_percentile: "Population coverage",
};

export const DEFAULT_WEIGHTS: ScenarioWeights = {
  housing_unit_coverage_percentile: 0.45,
  population_density_percentile: 0.35,
  population_coverage_percentile: 0.2,
};

export function weightSum(weights: ScenarioWeights): number {
  return WEIGHT_KEYS.reduce((total, key) => total + (Number(weights[key]) || 0), 0);
}

/** Weights are valid when they sum to 1.0 (within tolerance) and are all ≥ 0. */
export function weightsValid(weights: ScenarioWeights): boolean {
  if (WEIGHT_KEYS.some((key) => !Number.isFinite(weights[key]) || weights[key] < 0)) return false;
  return Math.abs(weightSum(weights) - 1) <= 1e-6;
}

/**
 * Proportionally rescale weights so they sum to 1.0, preserving their relative
 * balance. If every weight is zero, fall back to the canonical default split.
 */
export function normalizeWeights(weights: ScenarioWeights): ScenarioWeights {
  const total = weightSum(weights);
  if (total <= 0) return { ...DEFAULT_WEIGHTS };
  const scaled = WEIGHT_KEYS.map((key) => Math.max(0, weights[key]) / total);
  // Round to 3 dp and push any residual onto the largest weight so the sum is exactly 1.
  const rounded = scaled.map((value) => Math.round(value * 1000) / 1000);
  const residual = Math.round((1 - rounded.reduce((a, b) => a + b, 0)) * 1000) / 1000;
  let maxIndex = 0;
  for (let i = 1; i < rounded.length; i += 1) if (rounded[i] > rounded[maxIndex]) maxIndex = i;
  rounded[maxIndex] = Math.round((rounded[maxIndex] + residual) * 1000) / 1000;
  return {
    housing_unit_coverage_percentile: rounded[0],
    population_density_percentile: rounded[1],
    population_coverage_percentile: rounded[2],
  };
}

/** Stable deep-equality for two scenario configs (used for dirty tracking). */
export function configsEqual(a: ScenarioConfig, b: ScenarioConfig): boolean {
  return canonical(a) === canonical(b);
}

function canonical(config: ScenarioConfig): string {
  return JSON.stringify({
    density_screen_percentile: round(config.density_screen_percentile),
    weights: WEIGHT_KEYS.map((key) => round(config.weights[key])),
    unique_location_constraint: config.unique_location_constraint,
    max_station_distance_miles: round(config.max_station_distance_miles),
    station_distance_penalty: round(config.station_distance_penalty),
    require_weather_qc: config.require_weather_qc,
    overrides: (config.overrides ?? [])
      .map((o) => `${o.climate_region}|${o.urbanicity}|${o.catchment_type}|${o.catchment_code}`)
      .sort(),
  });
}

function round(value: number): number {
  return Math.round((Number(value) || 0) * 1e6) / 1e6;
}

export function cloneConfig(config: ScenarioConfig): ScenarioConfig {
  return {
    ...config,
    weights: { ...config.weights },
    overrides: (config.overrides ?? []).map((o) => ({ ...o })),
  };
}
