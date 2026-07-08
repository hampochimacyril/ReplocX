import { useMemo, useState } from "react";
import { EChart } from "../../components/EChart";
import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useAtlasControls, useDComparisons, useFigureSource, useScenarioSummary, fmt, SCENARIO_COLOR } from "./atlas";
import { thresholdNote, valueOf } from "./metrics";
import type { MetricRow } from "../../lib/types";

type StoryKey = "D-B" | "D-C" | "D-A";

const STORY: Record<StoryKey, { figure: string; label: string; short: string }> = {
  "D-B": { figure: "Fig05", label: "Natural ventilation effect without AC", short: "D-B" },
  "D-C": { figure: "Fig06", label: "Peak-window AC plus outside-window NV effect", short: "D-C" },
  "D-A": { figure: "Fig07", label: "Full active-cooling protection", short: "D-A" },
};

const METRIC = {
  key: "op_temp_hours_gt_28c_reduction",
  label: "Overheating exposure hours reduced",
};

function comparisonChart(rows: MetricRow[], story: StoryKey) {
  return {
    tooltip: { trigger: "axis" },
    grid: { left: 58, right: 12, top: 18, bottom: 58 },
    xAxis: { type: "category", data: rows.map((row) => String(row.climate_short ?? row.climate_region)), axisLabel: { interval: 0, rotate: 18, fontSize: 10 } },
    yAxis: { type: "value", name: "hours" },
    series: [
      {
        name: STORY[story].label,
        type: "bar",
        itemStyle: { color: SCENARIO_COLOR.D },
        data: rows.map((row) => valueOf(row, METRIC.key)),
        barWidth: "56%",
      },
    ],
  };
}

/** D story panel: sealed-passive contrasts first, raw D values behind explore. */
export function SealedPassive() {
  const { tier, scenarioLabels } = useAtlasControls();
  const [story, setStory] = useState<StoryKey>("D-B");
  const comparisons = useDComparisons(tier);
  const summary = useScenarioSummary(tier);
  const f05 = useFigureSource("Fig05");
  const f06 = useFigureSource("Fig06");
  const f07 = useFigureSource("Fig07");

  const source = story === "D-B" ? f05 : story === "D-C" ? f06 : f07;
  const option = useMemo(() => (source.data ? comparisonChart(source.data.rows, story) : undefined), [source.data, story]);

  if (comparisons.isLoading || summary.isLoading || f05.isLoading || f06.isLoading || f07.isLoading) {
    return <LoadingState label="Loading sealed-passive contrasts…" />;
  }
  if (comparisons.isError || !comparisons.data) {
    return <ErrorState message={(comparisons.error as Error)?.message ?? "Failed."} onRetry={comparisons.refetch} />;
  }
  if (summary.isError || !summary.data) {
    return <ErrorState message={(summary.error as Error)?.message ?? "Failed."} onRetry={summary.refetch} />;
  }
  if (source.isError || !source.data || !option) {
    return <ErrorState message={(source.error as Error)?.message ?? "Failed to load f2v3 source."} onRetry={source.refetch} />;
  }

  const rawD = summary.data.rows.find((row) => row.hvac_scenario === "D");
  const storyRows = comparisons.data.comparisons ?? [];

  return (
    <div className="doc atlas-story">
      <section className="atlas-story-section">
        <p className="atlas-kicker">Sealed-passive story panel</p>
        <h1>Sealed-passive D contrasts</h1>
        <p className="muted">
          Opens on contrasts from {scenarioLabels.D} (D), not raw D levels. Raw sealed-passive values stay behind
          the explore affordance below.
        </p>
        <div className="atlas-comparison-tabs" role="tablist" aria-label="D contrast">
          {(comparisons.data.story_comparison_order ?? ["D-B", "D-C", "D-A"]).map((key) => {
            const storyKey = key as StoryKey;
            return (
              <button
                key={storyKey}
                type="button"
                role="tab"
                aria-selected={story === storyKey}
                className={story === storyKey ? "active" : ""}
                onClick={() => setStory(storyKey)}
              >
                <span>{STORY[storyKey].short}</span>
                {STORY[storyKey].label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="atlas-story-section">
        <div className="atlas-section-head">
          <div>
            <h2>{STORY[story].label}</h2>
            <p className="muted">
              {METRIC.label} from {scenarioLabels.D} ({story}); {thresholdNote("28c")}
            </p>
          </div>
          <Tag tone="info">f2v3_final</Tag>
        </div>
        <EChart option={option} ariaLabel={`${story} overheating exposure-hour reduction by climate`} height={270} />
        <p className="chart-note">
          Source CSV: <code>{source.data.source_csv}</code>. {METRIC.label}; {thresholdNote("28c")}
        </p>
      </section>

      <section className="atlas-story-section">
        <h2>Contrast provenance</h2>
        <div className="tablewrap" style={{ maxHeight: 260 }}>
          <table className="dtable">
            <thead>
              <tr>
                <th>Contrast</th>
                <th>Interpretation</th>
                <th className="num">Rows</th>
              </tr>
            </thead>
            <tbody>
              {storyRows.map((row) => (
                <tr key={String(row.comparison_key)}>
                  <td>{String(row.comparison_key)}</td>
                  <td>{String(row.comparison_interpretation)}</td>
                  <td className="num">{fmt(row.row_count, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="atlas-story-section">
        <details className="atlas-explore">
          <summary>Explore raw D values</summary>
          <dl className="kv" style={{ gridTemplateColumns: "280px 1fr" }}>
            <dt>95th-percentile operative temperature</dt>
            <dd>{fmt(rawD?.op_temp_p95_true_c, 1)} deg C</dd>
            <dt>Overheating exposure hours</dt>
            <dd>{fmt(rawD?.hours_gt_28c, 0)} hours; {thresholdNote("28c")}</dd>
            <dt>High-humidity exposure hours</dt>
            <dd>{fmt(rawD?.humidity_hours, 0)} hours; threshold: humidity ratio above 0.012 kg/kg.</dd>
            <dt>Overheating degree-hours</dt>
            <dd>{fmt(rawD?.degree_hours_28c, 0)} C-hours; {thresholdNote("28c")}</dd>
          </dl>
        </details>
      </section>
    </div>
  );
}
