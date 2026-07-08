import { useMemo, useState } from "react";
import { EChart } from "../../components/EChart";
import { LoadingState, ErrorState } from "../../components/states/States";
import {
  useAtlasControls,
  useScenarioSummary,
  useByStratum,
  SCENARIO_COLOR,
  SCENARIOS,
  STRATUM_DIMENSIONS,
  fmt,
} from "./atlas";
import {
  DEFAULT_METRIC,
  DEFAULT_THRESHOLD,
  METRICS,
  THRESHOLDS,
  type AtlasMetricKey,
  type ThresholdKey,
  metricByKey,
  thresholdMetricKey,
  thresholdNote,
  valueOf,
  compactScenarioLabel,
  summaryThresholdMetricKey,
} from "./metrics";
import type { MetricRow, Scenario, StratumDimension } from "../../lib/types";

function groupedOption(
  rows: MetricRow[],
  groupCol: string,
  metricKey: string,
  labels: Record<Scenario, string>,
  unit: string,
) {
  const groups = Array.from(new Set(rows.map((row) => String(row[groupCol]))));
  return {
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 62, right: 12, top: 34, bottom: 66 },
    xAxis: { type: "category", data: groups, axisLabel: { interval: 0, rotate: 22, fontSize: 10 } },
    yAxis: { type: "value", name: unit },
    series: SCENARIOS.map((scenario: Scenario) => ({
      name: compactScenarioLabel(scenario, labels),
      type: "bar",
      itemStyle: { color: SCENARIO_COLOR[scenario] },
      data: groups.map((group) => {
        const row = rows.find((item) => String(item[groupCol]) === group && String(item.hvac_scenario) === scenario);
        return valueOf(row, metricKey);
      }),
    })),
  };
}

function scenarioOverviewOption(rows: MetricRow[], threshold: ThresholdKey, labels: Record<Scenario, string>) {
  const byScenario = new Map(rows.map((row) => [String(row.hvac_scenario), row]));
  const exposureKey = summaryThresholdMetricKey(threshold);
  return {
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 58, right: 12, top: 34, bottom: 58 },
    xAxis: { type: "category", data: SCENARIOS.map((scenario) => compactScenarioLabel(scenario, labels)), axisLabel: { interval: 0, rotate: 18, fontSize: 10 } },
    yAxis: [
      { type: "value", name: "deg C" },
      { type: "value", name: "hours" },
    ],
    series: [
      {
        name: "95th-percentile operative temperature",
        type: "bar",
        yAxisIndex: 0,
        data: SCENARIOS.map((scenario) => ({
          value: valueOf(byScenario.get(scenario), "op_temp_p95_true_c"),
          itemStyle: { color: SCENARIO_COLOR[scenario] },
        })),
      },
      {
        name: "Overheating exposure hours",
        type: "line",
        yAxisIndex: 1,
        data: SCENARIOS.map((scenario) => valueOf(byScenario.get(scenario), exposureKey)),
      },
    ],
  };
}

/** Guided A/C/B/D results with p95 and exposure-hour metrics first. */
export function SimulationResults() {
  const { tier, scenarioLabels } = useAtlasControls();
  const summary = useScenarioSummary(tier);
  const [dimension, setDimension] = useState<StratumDimension>("climate");
  const [metric, setMetric] = useState<AtlasMetricKey>(DEFAULT_METRIC);
  const [threshold, setThreshold] = useState<ThresholdKey>(DEFAULT_THRESHOLD);
  const stratum = useByStratum(tier, dimension);

  const selectedMetric = metric === "op_temp_hours_gt_28c_mean" ? metricByKey(thresholdMetricKey(threshold)) : metricByKey(metric);
  const pairedMetric = selectedMetric.pairedKey ? metricByKey(selectedMetric.pairedKey) : null;
  const exposureCompanion = metric === "op_temp_p95_true_c_mean" ? metricByKey(thresholdMetricKey(threshold)) : null;

  const overviewOption = useMemo(
    () => (summary.data ? scenarioOverviewOption(summary.data.rows, threshold, scenarioLabels) : undefined),
    [scenarioLabels, summary.data, threshold],
  );
  const primaryOption = useMemo(
    () =>
      stratum.data
        ? groupedOption(stratum.data.rows, stratum.data.group_column, selectedMetric.key, scenarioLabels, selectedMetric.unit)
        : undefined,
    [scenarioLabels, selectedMetric.key, selectedMetric.unit, stratum.data],
  );
  const pairedOption = useMemo(
    () =>
      pairedMetric && stratum.data
        ? groupedOption(stratum.data.rows, stratum.data.group_column, pairedMetric.key, scenarioLabels, pairedMetric.unit)
        : undefined,
    [pairedMetric, scenarioLabels, stratum.data],
  );
  const exposureOption = useMemo(
    () =>
      exposureCompanion && stratum.data
        ? groupedOption(stratum.data.rows, stratum.data.group_column, exposureCompanion.key, scenarioLabels, exposureCompanion.unit)
        : undefined,
    [exposureCompanion, scenarioLabels, stratum.data],
  );

  if (summary.isLoading || stratum.isLoading) return <LoadingState label="Loading A/C/B/D results…" />;
  if (summary.isError || !summary.data)
    return <ErrorState message={(summary.error as Error)?.message ?? "Failed."} onRetry={summary.refetch} />;
  if (stratum.isError || !stratum.data || !overviewOption || !primaryOption)
    return <ErrorState message={(stratum.error as Error)?.message ?? "Failed."} onRetry={stratum.refetch} />;

  const groupCol = stratum.data.group_column;

  return (
    <div className="doc atlas-story">
      <section className="atlas-story-section">
        <p className="atlas-kicker">Certified results</p>
        <h1>Results A/C/B/D</h1>
        <p className="muted">
          ReplocX TMY3 wallfix · {tier === "annual" ? "annual" : "seasonal"} tier · p95 and exposure-hour
          metrics lead the story.
        </p>
      </section>

      <section className="atlas-story-section">
        <div className="atlas-section-head">
          <div>
            <h2>Scenario overview</h2>
            <p className="muted">
              95th-percentile operative temperature paired with Overheating exposure hours. {thresholdNote(threshold)}
            </p>
          </div>
          <div className="atlas-thresholds" role="group" aria-label="Overheating exposure threshold">
            {THRESHOLDS.map((item) => (
              <button
                key={item.key}
                type="button"
                className={threshold === item.key ? "active" : ""}
                aria-pressed={threshold === item.key}
                onClick={() => setThreshold(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <EChart option={overviewOption} ariaLabel="Scenario p95 and overheating exposure-hour overview" height={260} />
        <p className="chart-note">{thresholdNote(threshold)} Source CSV: <code>{summary.data.source_csv}</code>.</p>
      </section>

      <section className="atlas-story-section">
        <div className="atlas-inline-controls">
          <label>
            Dimension{" "}
            <select value={dimension} onChange={(e) => setDimension(e.target.value as StratumDimension)}>
              {STRATUM_DIMENSIONS.map((d) => (
                <option key={d.key} value={d.key}>
                  {d.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Metric{" "}
            <select value={metric} onChange={(e) => setMetric(e.target.value as AtlasMetricKey)}>
              {METRICS.map((m) => (
                <option key={m.key} value={m.key}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <h2>{selectedMetric.label}</h2>
        <EChart option={primaryOption} ariaLabel={`${selectedMetric.label} by ${dimension} and scenario`} height={280} />
        <p className="chart-note">
          {selectedMetric.subtitle} {selectedMetric.key.includes("hours_gt") ? thresholdNote(threshold) : ""}
          {" "}Source CSV: <code>{stratum.data.source_csv}</code>.
        </p>

        {pairedMetric && pairedOption && (
          <>
            <h2>Paired extreme metric</h2>
            <EChart option={pairedOption} ariaLabel={`${pairedMetric.label} paired with mean view`} height={260} />
            <p className="chart-note">{pairedMetric.label} is shown because the selected mean metric cannot stand alone.</p>
          </>
        )}

        {exposureCompanion && exposureOption && (
          <>
            <h2>Paired exposure metric</h2>
            <EChart option={exposureOption} ariaLabel="Overheating exposure hours paired with p95 view" height={260} />
            <p className="chart-note">{thresholdNote(threshold)}</p>
          </>
        )}
      </section>

      <section className="atlas-story-section">
        <h2>Export metadata</h2>
        <dl className="kv" style={{ gridTemplateColumns: "220px 1fr" }}>
          <dt>Metric</dt>
          <dd>{selectedMetric.label}</dd>
          <dt>Threshold</dt>
          <dd>{selectedMetric.key.includes("hours_gt") || exposureCompanion ? thresholdNote(threshold) : "Not thresholded"}</dd>
          <dt>Tier</dt>
          <dd>{tier}</dd>
          <dt>Source CSV</dt>
          <dd><code>{stratum.data.source_csv}</code></dd>
        </dl>

        <div className="tablewrap" style={{ maxHeight: 320 }}>
          <table className="dtable">
            <thead>
              <tr>
                <th>{groupCol}</th>
                <th>Scenario label</th>
                <th className="num">{selectedMetric.label}</th>
                {pairedMetric && <th className="num">{pairedMetric.label}</th>}
                {exposureCompanion && <th className="num">{exposureCompanion.label}</th>}
              </tr>
            </thead>
            <tbody>
              {stratum.data.rows.map((row, i) => {
                const scenario = String(row.hvac_scenario) as Scenario;
                return (
                  <tr key={i}>
                    <td>{String(row[groupCol])}</td>
                    <td style={{ color: SCENARIO_COLOR[scenario] }}>{compactScenarioLabel(scenario, scenarioLabels)}</td>
                    <td className="num">{fmt(row[selectedMetric.key], selectedMetric.digits)}</td>
                    {pairedMetric && <td className="num">{fmt(row[pairedMetric.key], pairedMetric.digits)}</td>}
                    {exposureCompanion && <td className="num">{fmt(row[exposureCompanion.key], exposureCompanion.digits)}</td>}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
