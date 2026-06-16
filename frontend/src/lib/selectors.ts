/* Pure client-side filtering used to keep the map, matrix, table, and charts in
 * sync against one filter object. Selection itself is computed server-side; this
 * only narrows which already-scored rows are shown. */
import type { Filters } from "../state/filters";
import type { CatchmentRow } from "./types";

export function rowKey(row: CatchmentRow): string {
  return row.location_uniqueness_key || `${row.catchment_type}:${row.catchment_code}`;
}

export function isRepresentative(row: CatchmentRow): boolean {
  return row.scenario_selected ?? row.baseline_selected ?? row.selected;
}

export function mergeScenarioSelection(candidates: CatchmentRow[], selected: CatchmentRow[]): CatchmentRow[] {
  const selectedByKey = new Map(selected.map((row) => [rowKey(row), row]));
  return candidates.map((row) => {
    const active = selectedByKey.get(rowKey(row));
    return active
      ? { ...row, ...active, baseline_selected: row.baseline_selected, scenario_selected: true }
      : { ...row, scenario_selected: false };
  });
}

export function matchesFilters(row: CatchmentRow, f: Filters): boolean {
  if (f.climate && row.climate_region !== f.climate) return false;
  if (f.urbanicity && row.urbanicity_short !== f.urbanicity) return false;
  const selected = isRepresentative(row);
  if (f.selectedStatus === "selected" && !selected) return false;
  if (f.selectedStatus === "candidate" && selected) return false;
  if (f.verification && (row.nrel_verification_status ?? "") !== f.verification) return false;
  if (f.weatherQc && row.hourly_weather_qc_status !== f.weatherQc) return false;
  const score = row.scenario_score ?? row.location_score;
  if (score < f.scoreMin || score > f.scoreMax) return false;
  if (f.maxStationDistance !== null && row.station_distance_miles > f.maxStationDistance) return false;
  if (f.search) {
    const needle = f.search.toLowerCase();
    const haystack = `${row.catchment_label} ${row.catchment_code} ${row.selected_station_name}`.toLowerCase();
    if (!haystack.includes(needle)) return false;
  }
  return true;
}
