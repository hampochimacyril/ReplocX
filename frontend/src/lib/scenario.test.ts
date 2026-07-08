import { describe, it, expect } from "vitest";
import {
  DEFAULT_WEIGHTS,
  cloneConfig,
  configsEqual,
  normalizeWeights,
  weightSum,
  weightsValid,
} from "./scenario";
import type { ScenarioConfig, ScenarioWeights } from "./types";

function baseConfig(): ScenarioConfig {
  return {
    version: "1.0",
    name: "Test",
    density_screen_percentile: 0.6,
    weights: { ...DEFAULT_WEIGHTS },
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
        rationale: "x",
      },
    ],
  };
}

describe("weightSum / weightsValid", () => {
  it("the default weights sum to 1.0 and are valid", () => {
    expect(weightSum(DEFAULT_WEIGHTS)).toBeCloseTo(1, 9);
    expect(weightsValid(DEFAULT_WEIGHTS)).toBe(true);
  });

  it("rejects weights that do not sum to 1.0", () => {
    const w: ScenarioWeights = {
      housing_unit_coverage_percentile: 0.5,
      population_density_percentile: 0.5,
      population_coverage_percentile: 0.5,
    };
    expect(weightsValid(w)).toBe(false);
  });

  it("rejects negative weights", () => {
    const w: ScenarioWeights = {
      housing_unit_coverage_percentile: 1.2,
      population_density_percentile: -0.2,
      population_coverage_percentile: 0,
    };
    expect(weightsValid(w)).toBe(false);
  });
});

describe("normalizeWeights", () => {
  it("rescales to exactly 1.0 while preserving relative balance", () => {
    const w: ScenarioWeights = {
      housing_unit_coverage_percentile: 0.6,
      population_density_percentile: 0.3,
      population_coverage_percentile: 0.3,
    };
    const n = normalizeWeights(w);
    expect(weightSum(n)).toBeCloseTo(1, 9);
    expect(weightsValid(n)).toBe(true);
    // largest input stays the largest output
    expect(n.housing_unit_coverage_percentile).toBeGreaterThan(n.population_density_percentile);
  });

  it("falls back to the default split when all weights are zero", () => {
    const n = normalizeWeights({
      housing_unit_coverage_percentile: 0,
      population_density_percentile: 0,
      population_coverage_percentile: 0,
    });
    expect(n).toEqual(DEFAULT_WEIGHTS);
  });
});

describe("configsEqual / cloneConfig", () => {
  it("treats identical configs as equal regardless of override ordering", () => {
    const a = baseConfig();
    const b = baseConfig();
    expect(configsEqual(a, b)).toBe(true);
  });

  it("detects a changed weight", () => {
    const a = baseConfig();
    const b = baseConfig();
    b.weights.population_density_percentile = 0.3;
    b.weights.population_coverage_percentile = 0.25;
    expect(configsEqual(a, b)).toBe(false);
  });

  it("detects a changed override set", () => {
    const a = baseConfig();
    const b = baseConfig();
    b.overrides = [];
    expect(configsEqual(a, b)).toBe(false);
  });

  it("cloneConfig produces an independent copy", () => {
    const a = baseConfig();
    const c = cloneConfig(a);
    c.weights.population_density_percentile = 0.1;
    c.overrides!.pop();
    expect(a.weights.population_density_percentile).toBe(0.35);
    expect(a.overrides).toHaveLength(1);
  });
});
