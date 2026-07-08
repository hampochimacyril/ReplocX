import { useEffect, useMemo, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EChart } from "../../components/EChart";
import { MapCanvas } from "../../components/MapCanvas";
import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useDashboard, useGeometry } from "../../state/queries";
import { useSelection } from "../../state/selection";
import { rowKey } from "../../lib/selectors";
import { useAtlasControls, useAtlasOverview, useByStratum, useFigureSource, SCENARIOS, SCENARIO_COLOR, fmt } from "./atlas";
import {
  DEFAULT_METRIC,
  buildF02SummaryOption,
  compactScenarioLabel,
  metricByKey,
  valueOf,
} from "./metrics";
import type { MetricRow, Scenario } from "../../lib/types";

function PivotTable({
  rows,
  groupColumn,
  labels,
}: {
  rows: MetricRow[];
  groupColumn: string;
  labels: Record<Scenario, string>;
}) {
  const groups = Array.from(new Set(rows.map((row) => String(row[groupColumn]))));
  return (
    <div className="tablewrap atlas-pivot-table">
      <table className="dtable">
        <thead>
          <tr>
            <th>National stratum</th>
            {SCENARIOS.map((scenario) => (
              <th key={scenario} className="num">
                {compactScenarioLabel(scenario, labels)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => (
            <tr key={group}>
              <td>{group}</td>
              {SCENARIOS.map((scenario) => {
                const row = rows.find((item) => String(item[groupColumn]) === group && item.hvac_scenario === scenario);
                return (
                  <td key={scenario} className="num" style={{ color: SCENARIO_COLOR[scenario] }}>
                    {fmt(valueOf(row, "op_temp_p95_true_c_mean"), 1)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AtlasSiteMap() {
  const dashboard = useDashboard();
  const geometry = useGeometry();
  const navigate = useNavigate();
  const { selection } = useSelection();
  const { scenario, tier } = useAtlasControls();
  const lastSite = useRef<string | null>(null);

  useEffect(() => {
    if (selection?.kind !== "catchment") return;
    const siteId = rowKey(selection.row);
    if (lastSite.current === siteId) return;
    lastSite.current = siteId;
    navigate(
      `/atlas/sites/${encodeURIComponent(siteId)}?scenario=${scenario}&tier=${tier}&metric=${DEFAULT_METRIC}`,
      { replace: false },
    );
  }, [navigate, scenario, selection, tier]);

  if (dashboard.isLoading || geometry.isLoading) return <LoadingState label="Loading site map…" />;
  if (dashboard.isError || geometry.isError || !dashboard.data || !geometry.data) {
    const message = (dashboard.error as Error)?.message ?? (geometry.error as Error)?.message ?? "Failed to load site map.";
    return <ErrorState message={message} onRetry={() => { dashboard.refetch(); geometry.refetch(); }} />;
  }

  return (
    <div className="atlas-map-panel">
      <MapCanvas geometry={geometry.data} rows={dashboard.data.scenario.selected} />
    </div>
  );
}

/** Atlas landing: pivot first, figure parity chart, and MapLibre site drill path. */
export function Introduction() {
  const { tier, scenarioLabels } = useAtlasControls();
  const overview = useAtlasOverview();
  const climatePivot = useByStratum(tier, "climate");
  const f02 = useFigureSource("Fig02");

  const chartOption = useMemo(
    () => (f02.data ? buildF02SummaryOption(f02.data.rows, tier, scenarioLabels) : undefined),
    [f02.data, scenarioLabels, tier],
  );

  if (overview.isLoading || climatePivot.isLoading || f02.isLoading) {
    return <LoadingState label="Loading Atlas overview…" />;
  }
  if (overview.isError || !overview.data) {
    return <ErrorState message={(overview.error as Error)?.message ?? "Failed to load."} onRetry={overview.refetch} />;
  }
  if (climatePivot.isError || !climatePivot.data) {
    return <ErrorState message={(climatePivot.error as Error)?.message ?? "Failed to load pivot."} onRetry={climatePivot.refetch} />;
  }
  if (f02.isError || !f02.data || !chartOption) {
    return <ErrorState message={(f02.error as Error)?.message ?? "Failed to load f2v3 figure source."} onRetry={f02.refetch} />;
  }

  const metric = metricByKey(DEFAULT_METRIC);

  return (
    <div className="doc atlas-story">
      <section className="atlas-story-section">
        <p className="atlas-kicker">Private Research Atlas</p>
        <h1>ReplocX Research Atlas</h1>
        <p className="muted">{overview.data.dataset}</p>
        <p>
          The Atlas reads the certified 720-cell <strong>replocx_tmy3_wallfix_4scen</strong> tier and
          f2v3 registry records. Scenario labels come from the canonical dictionary; codes are shown only
          as provenance detail.
        </p>
        <div className="atlas-scenario-strip" aria-label="Scenario legend">
          {SCENARIOS.map((scenario) => (
            <span key={scenario} style={{ borderColor: SCENARIO_COLOR[scenario] }}>
              <i style={{ background: SCENARIO_COLOR[scenario] }} />
              {scenarioLabels[scenario]} ({scenario})
            </span>
          ))}
        </div>
      </section>

      <section className="atlas-story-section" aria-labelledby="atlas-pivot-title">
        <div className="atlas-section-head">
          <div>
            <h2 id="atlas-pivot-title">National pivot</h2>
            <p className="muted">
              Default overview: {metric.label}, by climate-region stratum and scenario, in A/C/B/D order.
            </p>
          </div>
          <Tag tone="info">Pivot first</Tag>
        </div>
        <PivotTable rows={climatePivot.data.rows} groupColumn={climatePivot.data.group_column} labels={scenarioLabels} />
        <p className="chart-note">
          Values are read from <code>{climatePivot.data.source_csv}</code>. The drill path below opens site detail
          links without recomputing certified results.
        </p>
      </section>

      <section className="atlas-story-section" aria-labelledby="atlas-f02-title">
        <div className="atlas-section-head">
          <div>
            <h2 id="atlas-f02-title">Figure-chart parity</h2>
            <p className="muted">Interactive twin of Fig02, sourced from the f2v3 registry source_csv.</p>
          </div>
          <Tag tone="info">f2v3_final</Tag>
        </div>
        <EChart option={chartOption} ariaLabel="Fig02 source values for mean and 95th-percentile operative temperature" height={260} />
        <p className="chart-note">
          Chart source: <code>{f02.data.source_csv}</code>. Mean operative temperature is shown only beside its
          extreme counterpart, the 95th-percentile operative temperature.
        </p>
      </section>

      <section className="atlas-story-section" aria-labelledby="atlas-map-title">
        <div className="atlas-section-head">
          <div>
            <h2 id="atlas-map-title">Site drill-down map</h2>
            <p className="muted">
              Click a selected site to open the drawer and route to <code>/atlas/sites/&lt;site_id&gt;</code> with
              scenario, tier, and metric in the URL.
            </p>
          </div>
          <Link className="btn" to="/atlas/results">
            Results A/C/B/D
          </Link>
        </div>
        <AtlasSiteMap />
      </section>

      <section className="atlas-story-section">
        <div className="banner" role="note">
          <div>
            <strong>Tier wall.</strong>
            <div className="muted small" style={{ marginTop: 4 }}>
              {overview.data.tier_wall}
            </div>
          </div>
        </div>
        <p style={{ marginTop: "var(--space-3)" }}>
          <Tag tone="info">Private tier</Tag> Real results and equity data stay behind <code>RLE_ENABLE_ATLAS=1</code>
          on an approved private deployment. Public demo builds leave the Atlas disabled.
        </p>
      </section>
    </div>
  );
}
