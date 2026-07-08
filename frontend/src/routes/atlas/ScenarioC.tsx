import { EChart } from "../../components/EChart";
import { LoadingState, ErrorState } from "../../components/states/States";
import { useAtlasControls, useScenarioC, SCENARIO_COLOR, fmt } from "./atlas";

/** The signature figure: Scenario C partial-protection decomposition —
 * hours avoided (B→C) vs residual hours that remain (C−A). */
export function ScenarioC() {
  const { tier, scenarioLabels } = useAtlasControls();
  const { data, isLoading, isError, error, refetch } = useScenarioC(tier);
  if (isLoading) return <LoadingState label="Loading Scenario C decomposition…" />;
  if (isError || !data) return <ErrorState message={(error as Error)?.message ?? "Failed."} onRetry={refetch} />;

  const climates = data.by_climate.map((c) => c.climate_region);
  const option = {
    tooltip: { trigger: "axis" },
    legend: {},
    grid: { left: 48, right: 12, top: 28, bottom: 56 },
    xAxis: { type: "category", data: climates, axisLabel: { interval: 0, rotate: 20, fontSize: 10 } },
    yAxis: { type: "value", name: "hours" },
    series: [
      {
        name: "Avoided (B→C)",
        type: "bar",
        stack: "c",
        itemStyle: { color: SCENARIO_COLOR.C },
        data: data.by_climate.map((c) => Number(c.avoided_gt_28c_mean ?? 0)),
      },
      {
        name: "Residual (C−A)",
        type: "bar",
        stack: "c",
        itemStyle: { color: SCENARIO_COLOR.B },
        data: data.by_climate.map((c) => Number(c.residual_gt_28c_mean ?? 0)),
      },
    ],
  };

  const o = data.overall;
  return (
    <div className="doc">
      <h1>{scenarioLabels.C} (C)</h1>
      <p className="muted">
        ReplocX TMY3 · {tier} tier · AC 2-8pm + NV other hours. Decomposition over {o.n_cells} cells.
      </p>

      <p>
        Scenario C sits between full AC and natural ventilation only. Its protection splits into Overheating
        exposure hours it <strong>avoids</strong> relative to B, and the <strong>residual</strong> exposure
        that remains relative to A, largely off-window and overnight.
      </p>

      <dl className="kv" style={{ gridTemplateColumns: "260px 1fr" }}>
        <dt>Mean avoided Overheating exposure hours (B to C)</dt>
        <dd>{fmt(o.avoided_gt_28c_mean, 0)}</dd>
        <dt>Mean residual Overheating exposure hours (C to A)</dt>
        <dd>{fmt(o.residual_gt_28c_mean, 0)}</dd>
        <dt>Mean benefit fraction</dt>
        <dd>{fmt(typeof o.benefit_fraction_gt_28c_mean === "number" ? o.benefit_fraction_gt_28c_mean * 100 : null, 1)}%</dd>
        <dt>Mean off-window residual Overheating exposure hours</dt>
        <dd>{fmt(o.off_window_hours_gt_28c_mean, 0)}</dd>
        <dt>Mean overnight residual Overheating exposure hours</dt>
        <dd>{fmt(o.overnight_residual_hours_gt_28c_mean, 0)}</dd>
      </dl>

      <div className="chart-frame">
        <EChart option={option} ariaLabel="Scenario C avoided vs residual hours by climate" height={260} />
        <p className="chart-note">
          Avoided (green) vs residual (orange) Overheating exposure hours by climate region. Threshold:
          operative temperature above 28 C.
        </p>
      </div>
    </div>
  );
}
