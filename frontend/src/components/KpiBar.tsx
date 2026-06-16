import { formatInt } from "../lib/format";
import { TARGET_STRATA } from "../lib/constants";
import type { DashboardKpis } from "../lib/types";

/** Compact KPI strip — inline figures with labels, not ornamental cards (§6). */
export function KpiBar({ kpis }: { kpis: DashboardKpis }) {
  const items: Array<{ label: string; value: string; tone?: "ok" | "warn" }> = [
    { label: "Strata covered", value: `${kpis.distinct_locations} / ${TARGET_STRATA}`, tone: kpis.distinct_locations === TARGET_STRATA ? "ok" : "warn" },
    { label: "Distinct catchments", value: formatInt(kpis.distinct_locations) },
    { label: "Candidates scored", value: formatInt(kpis.candidate_count) },
    { label: "ResStock verified", value: `${kpis.verified_filter_count} / ${kpis.target_strata}`, tone: kpis.verified_filter_count === kpis.target_strata ? "ok" : "warn" },
    { label: "Weather QC complete", value: `${kpis.weather_qc_complete_count} / ${kpis.target_strata}`, tone: kpis.weather_qc_complete_count === kpis.target_strata ? "ok" : "warn" },
  ];
  return (
    <div className="kpibar" aria-label="Selection summary">
      {items.map((item) => (
        <div className="kpi" key={item.label}>
          <span className="v num" style={item.tone ? { color: `var(--${item.tone})` } : undefined}>
            {item.value}
          </span>
          <span className="l">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
