import { useState } from "react";
import { EChart } from "../../components/EChart";
import { LoadingState, ErrorState } from "../../components/states/States";
import { useAtlasControls, useByStratum, SCENARIO_COLOR, SCENARIOS, fmt } from "./atlas";
import type { Scenario, StratumDimension } from "../../lib/types";

/** Building-archetype vulnerability: exposure by building type and by
 * construction-era vintage, crossed with scenario. */
export function Archetypes() {
  const { tier } = useAtlasControls();
  const [dimension, setDimension] = useState<StratumDimension>("building");
  const { data, isLoading, isError, error, refetch } = useByStratum(tier, dimension);
  if (isLoading) return <LoadingState label="Loading archetype vulnerability…" />;
  if (isError || !data) return <ErrorState message={(error as Error)?.message ?? "Failed."} onRetry={refetch} />;

  const groupCol = data.group_column;
  const groups = Array.from(new Set(data.rows.map((r) => String(r[groupCol]))));
  const option = {
    tooltip: { trigger: "axis" },
    legend: {},
    grid: { left: 52, right: 12, top: 28, bottom: 56 },
    xAxis: { type: "category", data: groups, axisLabel: { interval: 0, rotate: 18, fontSize: 10 } },
    yAxis: { type: "value", name: "hours" },
    series: SCENARIOS.map((s: Scenario) => ({
      name: `Scenario ${s}`,
      type: "bar",
      itemStyle: { color: SCENARIO_COLOR[s] },
      data: groups.map((g) => {
        const row = data.rows.find((r) => String(r[groupCol]) === g && String(r.hvac_scenario) === s);
        return Number(row?.op_temp_hours_gt_28c_mean ?? 0);
      }),
    })),
  };

  return (
    <div className="doc">
      <h1>Archetype vulnerability</h1>
      <p className="muted">
        ReplocX TMY3 · {tier} tier. Older vintages and lighter constructions can carry more Overheating exposure
        hours under no-AC operation, the building-stock dimension of heat vulnerability.
      </p>

      <div className="atlas-inline-controls">
        <label>
          Dimension{" "}
          <select value={dimension} onChange={(e) => setDimension(e.target.value as StratumDimension)}>
            <option value="building">Building type</option>
            <option value="vintage">Vintage group</option>
          </select>
        </label>
      </div>

      <div className="chart-frame">
        <EChart option={option} ariaLabel={`Overheating exposure hours by ${dimension} and scenario`} height={260} />
        <p className="chart-note">
          Overheating exposure hours by {dimension} × scenario. Threshold: operative temperature above 28 C.
        </p>
      </div>

      <div className="tablewrap" style={{ maxHeight: 300 }}>
        <table className="dtable">
          <thead>
            <tr>
              <th>{groupCol}</th>
              <th>Scenario</th>
              <th className="num">Overheating exposure hours (&gt;28 C)</th>
              <th className="num">Overheating exposure hours (&gt;30 C)</th>
              <th className="num">Overheating degree-hours (&gt;28 C)</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r, i) => (
              <tr key={i}>
                <td>{String(r[groupCol])}</td>
                <td>
                  <span style={{ color: SCENARIO_COLOR[String(r.hvac_scenario) as Scenario] }}>
                    {String(r.hvac_scenario)}
                  </span>
                </td>
                <td className="num">{fmt(r.op_temp_hours_gt_28c_mean, 0)}</td>
                <td className="num">{fmt(r.op_temp_hours_gt_30c_mean, 0)}</td>
                <td className="num">{fmt(r.degree_hours_28c_mean, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
