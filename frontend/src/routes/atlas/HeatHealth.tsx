import { EChart } from "../../components/EChart";
import { LoadingState, ErrorState } from "../../components/states/States";
import { useAtlasControls, useScenarioSummary, SCENARIO_COLOR, SCENARIOS, fmt } from "./atlas";
import type { Scenario } from "../../lib/types";

/** Heat / health indicators: overheating exposure, humidity exposure, and
 * degree-hours — the health-relevant tail of the exposure distribution. */
export function HeatHealth() {
  const { tier } = useAtlasControls();
  const { data, isLoading, isError, error, refetch } = useScenarioSummary(tier);
  if (isLoading) return <LoadingState label="Loading heat/health indicators…" />;
  if (isError || !data) return <ErrorState message={(error as Error)?.message ?? "Failed."} onRetry={refetch} />;

  const byScenario = Object.fromEntries(data.rows.map((r) => [String(r.hvac_scenario), r]));
  const INDICATORS = [
    { key: "hours_gt_30c", label: "Overheating exposure hours (>30 C)" },
    { key: "hours_gt_32c", label: "Overheating exposure hours (>32 C)" },
    { key: "humidity_hours", label: "High-humidity exposure hours" },
    { key: "joint_hours_28c", label: "Joint hot-humid exposure hours (>28 C)" },
  ];

  const option = {
    tooltip: { trigger: "axis" },
    legend: {},
    grid: { left: 52, right: 12, top: 28, bottom: 40 },
    xAxis: { type: "category", data: INDICATORS.map((i) => i.label), axisLabel: { fontSize: 10 } },
    yAxis: { type: "value", name: "hours" },
    series: SCENARIOS.map((s: Scenario) => ({
      name: `Scenario ${s}`,
      type: "bar",
      itemStyle: { color: SCENARIO_COLOR[s] },
      data: INDICATORS.map((ind) => Number(byScenario[s]?.[ind.key] ?? 0)),
    })),
  };

  return (
    <div className="doc">
      <h1>Heat / health indicators</h1>
      <p className="muted">
        ReplocX TMY3 · {tier} tier. Health-relevant exposure emphasises the hot tail and combined heat-humidity
        load, where overnight recovery failure and dangerous apparent temperatures concentrate.
      </p>

      <div className="chart-frame">
        <EChart option={option} ariaLabel="Heat and humidity exposure indicators by scenario" height={260} />
        <p className="chart-note">
          Overheating exposure hours, High-humidity exposure hours, and joint hot-humid exposure hours by
          scenario. Overheating thresholds are shown in the labels; the high-humidity threshold is 0.012 kg/kg.
        </p>
      </div>

      <div className="tablewrap" style={{ maxHeight: 260 }}>
        <table className="dtable">
          <thead>
            <tr>
              <th>Scenario</th>
              {INDICATORS.map((i) => (
                <th key={i.key} className="num">
                  {i.label}
                </th>
              ))}
              <th className="num">Overheating degree-hours (&gt;28 C)</th>
            </tr>
          </thead>
          <tbody>
            {SCENARIOS.map((s) => (
              <tr key={s}>
                <td>
                  <span style={{ color: SCENARIO_COLOR[s] }}>{s}</span>
                </td>
                {INDICATORS.map((i) => (
                  <td key={i.key} className="num">
                    {fmt(byScenario[s]?.[i.key], 0)}
                  </td>
                ))}
                <td className="num">{fmt(byScenario[s]?.degree_hours_28c, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
