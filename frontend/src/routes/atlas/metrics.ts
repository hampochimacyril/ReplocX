import type { EChartsCoreOption } from "echarts/core";
import type { MetricRow, Scenario } from "../../lib/types";
import { SCENARIO_COLOR, SCENARIOS } from "./atlas";

export type ThresholdKey = "28c" | "30c" | "32c";
export type AtlasMetricKey =
  | "op_temp_p95_true_c_mean"
  | "op_temp_hours_gt_28c_mean"
  | "op_temp_hours_gt_30c_mean"
  | "op_temp_hours_gt_32c_mean"
  | "humidity_hours_gt_0p012kgkg_mean"
  | "degree_hours_28c_mean"
  | "op_temp_mean_c_mean"
  | "humidity_ratio_mean_kgkg_mean";

export interface AtlasMetric {
  key: AtlasMetricKey;
  summaryKey: string;
  label: string;
  unit: string;
  digits: number;
  pairedKey?: AtlasMetricKey;
  subtitle: string;
}

export const THRESHOLDS: Array<{ key: ThresholdKey; label: string; note: string }> = [
  { key: "28c", label: ">28 C", note: "Threshold: operative temperature above 28 C." },
  { key: "30c", label: ">30 C", note: "Threshold: operative temperature above 30 C." },
  { key: "32c", label: ">32 C", note: "Threshold: operative temperature above 32 C." },
];

export const METRICS: AtlasMetric[] = [
  {
    key: "op_temp_p95_true_c_mean",
    summaryKey: "op_temp_p95_true_c",
    label: "95th-percentile operative temperature",
    unit: "deg C",
    digits: 1,
    subtitle: "Tail metric; paired with overheating exposure hours for threshold context.",
  },
  {
    key: "op_temp_hours_gt_28c_mean",
    summaryKey: "hours_gt_28c",
    label: "Overheating exposure hours",
    unit: "hours",
    digits: 0,
    subtitle: "Exposure-hour metric; threshold is echoed in the chart subtitle and export metadata.",
  },
  {
    key: "humidity_hours_gt_0p012kgkg_mean",
    summaryKey: "humidity_hours",
    label: "High-humidity exposure hours",
    unit: "hours",
    digits: 0,
    subtitle: "High-humidity exposure-hour metric; threshold: humidity ratio above 0.012 kg/kg.",
  },
  {
    key: "degree_hours_28c_mean",
    summaryKey: "degree_hours_28c",
    label: "Overheating degree-hours",
    unit: "C-hours",
    digits: 0,
    subtitle: "Intensity-weighted overheating exposure above 28 C.",
  },
  {
    key: "op_temp_mean_c_mean",
    summaryKey: "op_temp_mean_c",
    label: "Mean operative temperature",
    unit: "deg C",
    digits: 1,
    pairedKey: "op_temp_p95_true_c_mean",
    subtitle: "Mean view; the paired 95th-percentile operative temperature is shown beside it.",
  },
  {
    key: "humidity_ratio_mean_kgkg_mean",
    summaryKey: "humidity_ratio_mean_kgkg",
    label: "Mean humidity ratio",
    unit: "kg/kg",
    digits: 4,
    pairedKey: "humidity_hours_gt_0p012kgkg_mean",
    subtitle: "Mean view; the paired high-humidity exposure hours are shown beside it.",
  },
];

export const DEFAULT_METRIC: AtlasMetricKey = "op_temp_p95_true_c_mean";
export const DEFAULT_THRESHOLD: ThresholdKey = "28c";

export function metricByKey(key: AtlasMetricKey): AtlasMetric {
  return METRICS.find((metric) => metric.key === key) ?? METRICS[0];
}

export function thresholdMetricKey(threshold: ThresholdKey): AtlasMetricKey {
  return `op_temp_hours_gt_${threshold}_mean` as AtlasMetricKey;
}

export function summaryThresholdMetricKey(threshold: ThresholdKey): string {
  return `hours_gt_${threshold}`;
}

export function thresholdNote(threshold: ThresholdKey): string {
  return THRESHOLDS.find((item) => item.key === threshold)?.note ?? THRESHOLDS[0].note;
}

export function valueOf(row: MetricRow | undefined, key: string): number {
  const raw = row?.[key];
  const value = typeof raw === "number" ? raw : Number(raw);
  return Number.isFinite(value) ? value : 0;
}

export function rowScenario(row: MetricRow): Scenario {
  return String(row.hvac_scenario) as Scenario;
}

export function scenarioLabel(scenario: Scenario, labels: Partial<Record<Scenario, string>> = {}): string {
  return labels[scenario] ?? scenario;
}

export function compactScenarioLabel(scenario: Scenario, labels: Partial<Record<Scenario, string>> = {}): string {
  return `${scenario} · ${scenarioLabel(scenario, labels)}`;
}

export function axisLabels(labels: Partial<Record<Scenario, string>> = {}): string[] {
  return SCENARIOS.map((scenario) => compactScenarioLabel(scenario, labels));
}

export function buildF02SummaryOption(
  rows: MetricRow[],
  scope: "annual" | "seasonal",
  labels: Partial<Record<Scenario, string>>,
): EChartsCoreOption {
  const scoped = rows.filter((row) => String(row.scope ?? scope) === scope);
  const byScenario = new Map(scoped.map((row) => [rowScenario(row), row]));
  return {
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 54, right: 12, top: 34, bottom: 58 },
    xAxis: {
      type: "category",
      data: axisLabels(labels),
      axisLabel: { interval: 0, rotate: 18, fontSize: 10 },
    },
    yAxis: { type: "value", name: "deg C" },
    series: [
      {
        name: "Mean operative temperature",
        type: "bar",
        data: SCENARIOS.map((scenario) => ({
          value: valueOf(byScenario.get(scenario), "op_temp_mean_c"),
          itemStyle: { color: `${SCENARIO_COLOR[scenario]}99` },
        })),
      },
      {
        name: "95th-percentile operative temperature",
        type: "bar",
        data: SCENARIOS.map((scenario) => ({
          value: valueOf(byScenario.get(scenario), "op_temp_p95_true_c"),
          itemStyle: { color: SCENARIO_COLOR[scenario] },
        })),
      },
    ],
  };
}

export function f02ParityValues(rows: MetricRow[], scope: "annual" | "seasonal") {
  const scoped = rows.filter((row) => String(row.scope ?? scope) === scope);
  const byScenario = new Map(scoped.map((row) => [rowScenario(row), row]));
  return SCENARIOS.flatMap((scenario) => [
    valueOf(byScenario.get(scenario), "op_temp_mean_c"),
    valueOf(byScenario.get(scenario), "op_temp_p95_true_c"),
  ]);
}
