import { describe, it, expect } from "vitest";
import { isRepresentative, matchesFilters, mergeScenarioSelection } from "./selectors";
import { DEFAULT_FILTERS } from "../state/filters";
import { makeRow } from "../test/fixtures";

describe("matchesFilters", () => {
  it("passes everything with default filters", () => {
    expect(matchesFilters(makeRow(), DEFAULT_FILTERS)).toBe(true);
  });

  it("filters by climate region and urbanicity", () => {
    const row = makeRow();
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, climate: "Marine" })).toBe(false);
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, climate: "Cold & Very Cold" })).toBe(true);
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, urbanicity: "Rural" })).toBe(false);
  });

  it("filters representatives and non-selected candidates", () => {
    const representative = makeRow({ scenario_selected: true });
    const candidate = makeRow({ scenario_selected: false, selected: false });
    expect(matchesFilters(representative, { ...DEFAULT_FILTERS, selectedStatus: "selected" })).toBe(true);
    expect(matchesFilters(candidate, { ...DEFAULT_FILTERS, selectedStatus: "selected" })).toBe(false);
    expect(matchesFilters(candidate, { ...DEFAULT_FILTERS, selectedStatus: "candidate" })).toBe(true);
  });

  it("filters by verification, weather QC, score range, and station distance", () => {
    const row = makeRow({ nrel_verification_status: "REVIEW REQUIRED", station_distance_miles: 120 });
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, verification: "VERIFIED" })).toBe(false);
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, weatherQc: "COMPLETE" })).toBe(false);
    expect(matchesFilters(makeRow({ scenario_score: 0.5 }), { ...DEFAULT_FILTERS, scoreMin: 0.6 })).toBe(false);
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, maxStationDistance: 100 })).toBe(false);
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, maxStationDistance: 200 })).toBe(true);
  });

  it("searches across label, code, and station name", () => {
    const row = makeRow();
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, search: "philadelphia" })).toBe(false);
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, search: "10000" })).toBe(true);
    expect(matchesFilters(row, { ...DEFAULT_FILTERS, search: "Climate Station" })).toBe(true);
  });

  it("merges the active scenario selection onto the candidate population", () => {
    const candidates = [
      makeRow({ catchment_code: "10000", location_uniqueness_key: "CBSA:10000", baseline_selected: true }),
      makeRow({
        catchment_code: "10001",
        location_uniqueness_key: "CBSA:10001",
        selected: false,
        baseline_selected: false,
      }),
    ];
    const selected = [
      makeRow({ catchment_code: "10001", location_uniqueness_key: "CBSA:10001", scenario_score: 0.77 }),
    ];
    const merged = mergeScenarioSelection(candidates, selected);
    expect(isRepresentative(merged[0])).toBe(false);
    expect(isRepresentative(merged[1])).toBe(true);
    expect(merged[1].scenario_score).toBe(0.77);
  });
});
