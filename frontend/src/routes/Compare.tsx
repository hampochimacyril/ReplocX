import { useMemo } from "react";
import { Link } from "react-router-dom";
import { X, GitCompareArrows } from "lucide-react";
import { useDashboard, useEvaluate } from "../state/queries";
import { useScenario } from "../state/scenario";
import { useCompare } from "../state/compare";
import { useSelection } from "../state/selection";
import { rowKey } from "../lib/selectors";
import { CLIMATE_REGIONS, URBANICITY } from "../lib/constants";
import { formatMiles, formatNumber, formatPercentile, formatScore } from "../lib/format";
import { LoadingState, ErrorState, EmptyState } from "../components/states/States";
import { VerificationTag, WeatherQcTag } from "../components/ui/Tag";
import type { CatchmentRow, ScenarioSummary } from "../lib/types";

function stratumKey(row: { climate_region: string; urbanicity_short: string }): string {
  return `${row.climate_region}|${row.urbanicity_short}`;
}

function DeltaCell({ value, digits = 3, invert = false, suffix = "" }: { value: number; digits?: number; invert?: boolean; suffix?: string }) {
  if (!Number.isFinite(value) || Math.abs(value) < 1e-9) return <span className="muted">±0</span>;
  const positive = value > 0;
  const good = invert ? !positive : positive;
  return (
    <span className="num" style={{ color: good ? "var(--ok)" : "var(--danger)" }}>
      {positive ? "+" : ""}
      {formatNumber(value, digits)}
      {suffix}
    </span>
  );
}

export function Compare() {
  const dashboard = useDashboard();
  const { active, customized } = useScenario();
  const appliedEval = useEvaluate(active);
  const compare = useCompare();
  const { selectCatchment } = useSelection();

  const baseline = dashboard.data?.scenario;
  const usingActive = active !== null && !!appliedEval.data;
  const applied = usingActive ? appliedEval.data! : baseline;

  const strata = useMemo(() => {
    if (!baseline || !applied) return [];
    const baseMap = new Map(baseline.selected.map((r) => [stratumKey(r), r]));
    const appliedMap = new Map(applied.selected.map((r) => [stratumKey(r), r]));
    const out: Array<{ key: string; climate: string; urb: string; base?: CatchmentRow; next?: CatchmentRow }> = [];
    for (const region of CLIMATE_REGIONS) {
      for (const urb of URBANICITY) {
        const key = `${region.name}|${urb.short}`;
        out.push({ key, climate: region.name, urb: urb.short, base: baseMap.get(key), next: appliedMap.get(key) });
      }
    }
    return out;
  }, [baseline, applied]);

  if (dashboard.isLoading || (active !== null && appliedEval.isLoading)) return <LoadingState label="Loading comparison…" />;
  if (dashboard.isError || !baseline) return <ErrorState message={(dashboard.error as Error)?.message ?? "Failed to load comparison."} onRetry={dashboard.refetch} />;

  const appliedSummary = applied!.summary;
  const baseSummary = baseline.summary;
  const changedStrata = strata.filter((s) => s.base && s.next && s.base.catchment_code !== s.next.catchment_code);

  return (
    <div className="comparepage">
      <header className="doc-head">
        <h1>
          <GitCompareArrows size={20} aria-hidden /> Compare
        </h1>
        <p className="muted">
          Baseline allocation versus the {customized ? "applied custom scenario" : "active scenario"}. Deltas are quantified per
          stratum; substitutions carry their reason.
        </p>
      </header>

      <section className="cmp-section">
        <h2>Allocation summary</h2>
        {!customized && (
          <p className="note">
            No custom scenario is applied, so the applied allocation equals the baseline. Edit and apply a scenario in the{" "}
            <Link to="/scenario">Scenario workbench</Link> to see allocation deltas here.
          </p>
        )}
        <table className="cmp-table">
          <thead>
            <tr>
              <th scope="col">Metric</th>
              <th scope="col" className="num">Baseline</th>
              <th scope="col" className="num">Applied</th>
              <th scope="col" className="num">Δ</th>
            </tr>
          </thead>
          <tbody>
            <SummaryRow label="Distinct catchments" k="distinct_location_count" a={baseSummary} b={appliedSummary} digits={0} />
            <SummaryRow label="Combined score" k="combined_score" a={baseSummary} b={appliedSummary} digits={3} />
            <SummaryRow label="Changed assignments" k="changed_assignment_count" a={baseSummary} b={appliedSummary} digits={0} invert />
            <SummaryRow label="Eligible candidates" k="eligible_candidate_count" a={baseSummary} b={appliedSummary} digits={0} />
            <SummaryRow label="Mean station distance (mi)" k="mean_station_distance_miles" a={baseSummary} b={appliedSummary} digits={1} invert />
            <SummaryRow label="Median scenario score" k="median_scenario_score" a={baseSummary} b={appliedSummary} digits={3} />
          </tbody>
        </table>
      </section>

      <section className="cmp-section">
        <h2>Per-stratum representatives {changedStrata.length > 0 && <span className="tag warn">{changedStrata.length} changed</span>}</h2>
        <div className="tablewrap">
          <table className="dtable">
            <thead>
              <tr>
                <th>Climate</th>
                <th>Urb.</th>
                <th>Baseline representative</th>
                <th>Applied representative</th>
                <th className="num">Base score</th>
                <th className="num">Applied score</th>
                <th className="num">Δ</th>
              </tr>
            </thead>
            <tbody>
              {strata.map((s) => {
                const changed = s.base && s.next && s.base.catchment_code !== s.next.catchment_code;
                const baseScore = s.base ? s.base.scenario_score ?? s.base.location_score : NaN;
                const nextScore = s.next ? s.next.scenario_score ?? s.next.location_score : NaN;
                return (
                  <tr key={s.key} className={changed ? "row-changed" : undefined}>
                    <td>{s.climate}</td>
                    <td>{s.urb}</td>
                    <td>
                      {s.base ? (
                        <button className="linklike" type="button" onClick={() => s.base && selectCatchment(s.base)}>
                          {s.base.catchment_label}
                        </button>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td>
                      {s.next ? (
                        <button className="linklike" type="button" onClick={() => s.next && selectCatchment(s.next)}>
                          {changed ? <strong>{s.next.catchment_label}</strong> : s.next.catchment_label}
                        </button>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td className="num">{Number.isNaN(baseScore) ? "—" : formatScore(baseScore)}</td>
                    <td className="num">{Number.isNaN(nextScore) ? "—" : formatScore(nextScore)}</td>
                    <td className="num">
                      {Number.isNaN(baseScore) || Number.isNaN(nextScore) ? "—" : <DeltaCell value={nextScore - baseScore} />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {applied!.changes.length > 0 && (
        <section className="cmp-section">
          <h2>Override substitutions ({applied!.changes.length})</h2>
          <div className="tablewrap">
            <table className="dtable">
              <thead>
                <tr>
                  <th>Stratum</th>
                  <th>From (unconstrained)</th>
                  <th>To (applied)</th>
                  <th className="num">Score loss</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {applied!.changes.map((c) => (
                  <tr key={`${c.climate_region}-${c.urbanicity_short}`}>
                    <td>
                      {c.climate_region} · {c.urbanicity_short}
                    </td>
                    <td className="muted">{c.from_label}</td>
                    <td>
                      <strong>{c.to_label}</strong>
                    </td>
                    <td className="num" style={{ color: "var(--danger)" }}>
                      −{formatScore(c.score_loss)}
                    </td>
                    <td className="muted small">{c.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="cmp-section">
        <h2>
          Candidate comparison {compare.rows.length > 0 && <span className="muted small">({compare.rows.length} selected)</span>}
        </h2>
        {compare.rows.length === 0 ? (
          <EmptyState
            title="No candidates selected"
            message="Use the compare checkboxes in the Catchments ranking table to pick up to four candidates, then compare them attribute by attribute here."
          />
        ) : (
          <CandidateMatrix rows={compare.rows} onRemove={compare.remove} onClear={compare.clear} onSelect={selectCatchment} />
        )}
      </section>
    </div>
  );
}

function SummaryRow({
  label,
  k,
  a,
  b,
  digits,
  invert,
}: {
  label: string;
  k: keyof ScenarioSummary;
  a: ScenarioSummary;
  b: ScenarioSummary;
  digits: number;
  invert?: boolean;
}) {
  return (
    <tr>
      <th scope="row">{label}</th>
      <td className="num">{formatNumber(a[k], digits)}</td>
      <td className="num">{formatNumber(b[k], digits)}</td>
      <td>
        <DeltaCell value={b[k] - a[k]} digits={digits} invert={invert} />
      </td>
    </tr>
  );
}

function CandidateMatrix({
  rows,
  onRemove,
  onClear,
  onSelect,
}: {
  rows: CatchmentRow[];
  onRemove: (key: string) => void;
  onClear: () => void;
  onSelect: (row: CatchmentRow) => void;
}) {
  const score = (r: CatchmentRow) => r.scenario_score ?? r.location_score;
  const bestIndex = (values: number[], mode: "max" | "min") => {
    let best = 0;
    for (let i = 1; i < values.length; i += 1) {
      if (mode === "max" ? values[i] > values[best] : values[i] < values[best]) best = i;
    }
    return best;
  };
  const numericRow = (label: string, get: (r: CatchmentRow) => number, fmt: (n: number) => string, mode: "max" | "min") => {
    const values = rows.map(get);
    const best = rows.length > 1 ? bestIndex(values, mode) : -1;
    return (
      <tr key={label}>
        <th scope="row">{label}</th>
        {rows.map((r, i) => (
          <td key={rowKey(r)} className="num">
            {i === best ? <strong>{fmt(values[i])}</strong> : fmt(values[i])}
          </td>
        ))}
      </tr>
    );
  };

  return (
    <div className="tablewrap">
      <table className="dtable cmp-candidates">
        <thead>
          <tr>
            <th>
              <button className="btn btn-icon" type="button" onClick={onClear} aria-label="Clear comparison">
                <X size={14} aria-hidden />
              </button>
            </th>
            {rows.map((r) => (
              <th key={rowKey(r)}>
                <button className="linklike" type="button" onClick={() => onSelect(r)}>
                  {r.catchment_label}
                </button>
                <button className="btn btn-icon remove-col" type="button" onClick={() => onRemove(rowKey(r))} aria-label={`Remove ${r.catchment_label}`}>
                  <X size={12} aria-hidden />
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Climate</th>
            {rows.map((r) => (
              <td key={rowKey(r)}>{r.climate_region}</td>
            ))}
          </tr>
          <tr>
            <th scope="row">Urbanicity</th>
            {rows.map((r) => (
              <td key={rowKey(r)}>{r.urbanicity_short}</td>
            ))}
          </tr>
          <tr>
            <th scope="row">Type / code</th>
            {rows.map((r) => (
              <td key={rowKey(r)} className="num">
                {r.catchment_type} {r.catchment_code}
              </td>
            ))}
          </tr>
          {numericRow("Composite score", score, formatScore, "max")}
          {numericRow("Housing-unit coverage", (r) => r.housing_unit_coverage_percentile, formatPercentile, "max")}
          {numericRow("Population density", (r) => r.population_density_percentile, formatPercentile, "max")}
          {numericRow("Population coverage", (r) => r.population_coverage_percentile, formatPercentile, "max")}
          {numericRow("Station distance", (r) => r.station_distance_miles, formatMiles, "min")}
          <tr>
            <th scope="row">Weather QC</th>
            {rows.map((r) => (
              <td key={rowKey(r)}>
                <WeatherQcTag status={r.hourly_weather_qc_status} />
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">ResStock</th>
            {rows.map((r) => (
              <td key={rowKey(r)}>
                <VerificationTag status={r.nrel_verification_status} />
              </td>
            ))}
          </tr>
          <tr>
            <th scope="row">Selected</th>
            {rows.map((r) => (
              <td key={rowKey(r)}>{r.selected || r.scenario_selected || r.baseline_selected ? "Representative" : "candidate"}</td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
