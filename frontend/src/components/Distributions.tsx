import { useMemo } from "react";
import { EChart } from "./EChart";
import { readVar } from "../lib/css";
import type { CatchmentRow } from "../lib/types";
import type { EChartsCoreOption } from "echarts/core";

const SCORE_BINS = [
  { label: "0.0–0.2", min: 0, max: 0.2 },
  { label: "0.2–0.4", min: 0.2, max: 0.4 },
  { label: "0.4–0.6", min: 0.4, max: 0.6 },
  { label: "0.6–0.8", min: 0.6, max: 0.8 },
  { label: "0.8–1.0", min: 0.8, max: 1.0001 },
];

const DIST_BINS = [
  { label: "0–50", min: 0, max: 50 },
  { label: "50–100", min: 50, max: 100 },
  { label: "100–150", min: 100, max: 150 },
  { label: "150–200", min: 150, max: 200 },
  { label: "200–250", min: 200, max: 250 },
  { label: "250+", min: 250, max: Infinity },
];

function barOption(labels: string[], counts: number[], color: string, axis: string): EChartsCoreOption {
  return {
    grid: { left: 6, right: 8, top: 8, bottom: 18, containLabel: true },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { color: axis, fontSize: 10 },
      axisLine: { lineStyle: { color: axis } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      minInterval: 1,
      axisLabel: { color: axis, fontSize: 10 },
      splitLine: { lineStyle: { color: readVar("--border", "#d7dce2") } },
    },
    series: [{ type: "bar", data: counts, itemStyle: { color, borderRadius: [2, 2, 0, 0] }, barWidth: "62%" }],
  };
}

function bin<T>(rows: T[], bins: { min: number; max: number }[], value: (r: T) => number): number[] {
  const counts = new Array(bins.length).fill(0);
  for (const row of rows) {
    const v = value(row);
    const idx = bins.findIndex((b) => v >= b.min && v < b.max);
    if (idx >= 0) counts[idx] += 1;
  }
  return counts;
}

export function ScoreDistribution({ rows }: { rows: CatchmentRow[] }) {
  const option = useMemo(() => {
    const counts = bin(rows, SCORE_BINS, (r) => r.scenario_score ?? r.location_score);
    return barOption(
      SCORE_BINS.map((b) => b.label),
      counts,
      readVar("--accent", "#1f6feb"),
      readVar("--text-muted", "#5b6470"),
    );
  }, [rows]);
  return <EChart option={option} ariaLabel={`Distribution of scores across ${rows.length} filtered candidates`} />;
}

export function StationDistanceDistribution({ rows }: { rows: CatchmentRow[] }) {
  const option = useMemo(() => {
    const counts = bin(rows, DIST_BINS, (r) => r.station_distance_miles);
    return barOption(
      DIST_BINS.map((b) => b.label),
      counts,
      readVar("--info", "#2563a8"),
      readVar("--text-muted", "#5b6470"),
    );
  }, [rows]);
  return <EChart option={option} ariaLabel={`Distribution of weather-station distances across ${rows.length} filtered candidates`} />;
}
