import { CLIMATE_REGIONS, URBANICITY } from "../lib/constants";
import { matchesFilters } from "../lib/selectors";
import { formatPercentile } from "../lib/format";
import { useFilters } from "../state/filters";
import { useSelection } from "../state/selection";
import type { CatchmentRow } from "../lib/types";

/**
 * Compact 5×4 stratum coverage matrix (§3, §7.1). One representative per stratum;
 * cells are colored by climate region and labeled with the score (never color
 * alone). Clicking a cell selects that stratum's representative. Cells that fall
 * outside the active filters are dimmed but still legible.
 */
export function CoverageMatrix({ rows }: { rows: CatchmentRow[] }) {
  const { filters } = useFilters();
  const { selectCatchment, selection } = useSelection();

  const byKey = new Map<string, CatchmentRow>();
  for (const row of rows) byKey.set(`${row.climate_region}|${row.urbanicity_short}`, row);

  const selectedCode = selection?.kind === "catchment" ? selection.row.catchment_code : null;

  return (
    <table className="matrix" aria-label="Stratum coverage matrix: 5 climate regions by 4 urbanicity categories">
      <thead>
        <tr>
          <th scope="col" aria-label="Climate region" />
          {URBANICITY.map((u) => (
            <th key={u.short} scope="col" title={u.label}>
              {u.short}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {CLIMATE_REGIONS.map((region) => (
          <tr key={region.name}>
            <th scope="row" style={{ textAlign: "left", whiteSpace: "nowrap" }} title={region.name}>
              <span
                aria-hidden
                style={{
                  display: "inline-block",
                  width: 9,
                  height: 9,
                  borderRadius: 2,
                  background: `var(${region.cssVar})`,
                  marginRight: 5,
                }}
              />
              {region.name.replace(" & ", " & ").replace("Hot-Dry & Mixed Dry", "Hot-Dry")}
            </th>
            {URBANICITY.map((u) => {
              const row = byKey.get(`${region.name}|${u.short}`);
              if (!row) {
                return (
                  <td key={u.short}>
                    <span className="cell empty" aria-label={`${region.name} ${u.label}: no representative`}>
                      –
                    </span>
                  </td>
                );
              }
              const dim = !matchesFilters(row, filters);
              const isSel = row.catchment_code === selectedCode;
              const score = row.scenario_score ?? row.location_score;
              return (
                <td key={u.short}>
                  <button
                    type="button"
                    className="cell"
                    onClick={() => selectCatchment(row)}
                    title={`${row.catchment_label} · score ${formatPercentile(score)}`}
                    aria-label={`${region.name} ${u.label}: ${row.catchment_label}, score ${formatPercentile(score)}`}
                    style={{
                      background: `var(${region.cssVar})`,
                      opacity: dim ? 0.28 : 1,
                      boxShadow: isSel ? "inset 0 0 0 2px var(--text)" : undefined,
                    }}
                  >
                    {formatPercentile(score)}
                  </button>
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
