import { useEffect, useMemo, useRef } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { EChart } from "../../components/EChart";
import { MapCanvas } from "../../components/MapCanvas";
import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useDashboard, useGeometry } from "../../state/queries";
import { useSelection } from "../../state/selection";
import { rowKey } from "../../lib/selectors";
import {
  atlasStratumId,
  GUIDED_STRATUM_DIMENSIONS,
  useAtlasControls,
  useAtlasOverview,
  useByStratum,
  useFigureSource,
  SCENARIOS,
  SCENARIO_COLOR,
  fmt,
} from "./atlas";
import {
  DEFAULT_METRIC,
  buildF02SummaryOption,
  compactScenarioLabel,
  metricByKey,
  valueOf,
} from "./metrics";
import type { AtlasTier, CatchmentRow, MetricRow, Scenario, StratumDimension } from "../../lib/types";

function PivotTable({
  rows,
  groupColumn,
  labels,
  dimension,
  sites,
  searchParams,
  tier,
  scenario,
}: {
  rows: MetricRow[];
  groupColumn: string;
  labels: Record<Scenario, string>;
  dimension: StratumDimension;
  sites: CatchmentRow[];
  searchParams: URLSearchParams;
  tier: AtlasTier;
  scenario: Scenario;
}) {
  const groups = Array.from(new Set(rows.map((row) => String(row[groupColumn]))));
  return (
    <div className="tablewrap atlas-pivot-table">
      <table className="dtable">
        <caption>{groups.length} {dimension === "stratum" ? "climate × urbanicity strata" : `${dimension} groups`}</caption>
        <thead>
          <tr>
            <th>{dimension === "stratum" ? "Climate × urbanicity stratum" : "National group"}</th>
            {SCENARIOS.map((scenario) => (
              <th key={scenario} className="num" title={`${labels[scenario]} — scenario ${scenario}`}>
                {compactScenarioLabel(scenario, labels)}
              </th>
            ))}
            {dimension === "stratum" && <th>Site drill-down</th>}
          </tr>
        </thead>
        <tbody>
          {groups.map((group) => {
            const first = rows.find((item) => String(item[groupColumn]) === group);
            const label = dimension === "stratum" ? String(first?.stratum_label ?? group) : group;
            const site =
              dimension === "stratum"
                ? sites.find(
                    (item) =>
                      item.climate_region === first?.climate_region &&
                      item.urbanicity_short === first?.urbanicity,
                  )
                : undefined;
            const siteParams = new URLSearchParams(searchParams);
            if (first) {
              siteParams.set("dimension", "stratum");
              siteParams.set("climate", String(first.climate_region));
              siteParams.set("urbanicity", String(first.urbanicity));
              siteParams.set("stratum", String(first.stratum_id));
              siteParams.set("metric", DEFAULT_METRIC);
              siteParams.set("tier", tier);
              siteParams.set("scenario", scenario);
            }
            return (
              <tr key={group} data-stratum-id={dimension === "stratum" ? group : undefined}>
                <td title={dimension === "stratum" ? `Certified stratum ID: ${group}` : undefined}>{label}</td>
                {SCENARIOS.map((scenario) => {
                  const row = rows.find(
                    (item) => String(item[groupColumn]) === group && item.hvac_scenario === scenario,
                  );
                  return (
                    <td
                      key={scenario}
                      className="num"
                      style={{ color: SCENARIO_COLOR[scenario] }}
                      title={`${labels[scenario]} (${scenario}) · ${label}`}
                    >
                      {fmt(valueOf(row, "op_temp_p95_true_c_mean"), 1)}
                    </td>
                  );
                })}
                {dimension === "stratum" && (
                  <td>
                    {site ? (
                      <Link to={`/atlas/sites/${encodeURIComponent(rowKey(site))}?${siteParams.toString()}`}>
                        {site.catchment_label}
                      </Link>
                    ) : (
                      <span className="muted">Site metadata unavailable</span>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
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
    const params = new URLSearchParams({
      scenario,
      tier,
      metric: DEFAULT_METRIC,
      dimension: "stratum",
      climate: selection.row.climate_region,
      urbanicity: selection.row.urbanicity_short,
      stratum: atlasStratumId(selection.row.climate_region, selection.row.urbanicity_short),
    });
    navigate(`/atlas/sites/${encodeURIComponent(siteId)}?${params.toString()}`, { replace: false });
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
  const { tier, scenario, scenarioLabels } = useAtlasControls();
  const [searchParams, setSearchParams] = useSearchParams();
  const dimensionParam = searchParams.get("dimension");
  const dimension: StratumDimension =
    dimensionParam === "climate" || dimensionParam === "urbanicity" || dimensionParam === "stratum"
      ? dimensionParam
      : "stratum";
  const climateFilter = searchParams.get("climate") ?? "";
  const urbanicityFilter = searchParams.get("urbanicity") ?? "";
  const setPivotParam = (key: "dimension" | "climate" | "urbanicity", value: string) => {
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value) next.set(key, value);
        else next.delete(key);
        if (key === "dimension" && value !== "stratum") {
          next.delete("climate");
          next.delete("urbanicity");
          next.delete("stratum");
        }
        return next;
      },
      { replace: true },
    );
  };
  const overview = useAtlasOverview();
  const pivot = useByStratum(tier, dimension);
  const f02 = useFigureSource("Fig02");
  const dashboard = useDashboard();

  const chartOption = useMemo(
    () => (f02.data ? buildF02SummaryOption(f02.data.rows, tier, scenarioLabels) : undefined),
    [f02.data, scenarioLabels, tier],
  );

  if (overview.isLoading || pivot.isLoading || f02.isLoading || dashboard.isLoading) {
    return <LoadingState label="Loading Atlas overview…" />;
  }
  if (overview.isError || !overview.data) {
    return <ErrorState message={(overview.error as Error)?.message ?? "Failed to load."} onRetry={overview.refetch} />;
  }
  if (pivot.isError || !pivot.data) {
    return <ErrorState message={(pivot.error as Error)?.message ?? "Failed to load pivot."} onRetry={pivot.refetch} />;
  }
  if (dashboard.isError || !dashboard.data) {
    return <ErrorState message={(dashboard.error as Error)?.message ?? "Failed to load site links."} onRetry={dashboard.refetch} />;
  }
  if (f02.isError || !f02.data || !chartOption) {
    return <ErrorState message={(f02.error as Error)?.message ?? "Failed to load f2v3 figure source."} onRetry={f02.refetch} />;
  }

  const metric = metricByKey(DEFAULT_METRIC);
  const strata = pivot.data.strata ?? [];
  const climates = Array.from(new Set(strata.map((item) => item.climate_region)));
  const urbanicities = Array.from(new Set(strata.map((item) => item.urbanicity)));
  const filteredRows = pivot.data.rows.filter(
    (row) =>
      (dimension !== "stratum" || !climateFilter || row.climate_region === climateFilter) &&
      (dimension !== "stratum" || !urbanicityFilter || row.urbanicity === urbanicityFilter),
  );

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
            <h2 id="atlas-pivot-title">20-stratum reviewer path</h2>
            <p className="muted">
              Move from climate to urbanicity to the complete climate × urbanicity lattice, then open its
              representative site. Metric: {metric.label}; scenario order: A/C/B/D.
            </p>
          </div>
          <Tag tone="info">{pivot.data.stratum_count ?? "—"} groups</Tag>
        </div>
        <div className="atlas-pivot-steps" role="group" aria-label="Reviewer pivot level">
          {GUIDED_STRATUM_DIMENSIONS.map((item, index) => (
            <button
              key={item.key}
              type="button"
              className={dimension === item.key ? "active" : ""}
              aria-pressed={dimension === item.key}
              title={
                item.key === "stratum"
                  ? "Show every certified climate-region × urbanicity combination."
                  : `Show certified ${item.label.toLowerCase()} aggregates.`
              }
              onClick={() => setPivotParam("dimension", item.key)}
            >
              <span>{index + 1}</span>
              {item.label}
            </button>
          ))}
          <span className="atlas-pivot-site-step"><b>4</b> Representative site</span>
        </div>
        {dimension === "stratum" && (
          <div className="atlas-inline-controls" aria-label="20-stratum filters">
            <label>
              Climate{" "}
              <select value={climateFilter} onChange={(event) => setPivotParam("climate", event.target.value)}>
                <option value="">All 5 climate regions</option>
                {climates.map((climate) => <option key={climate}>{climate}</option>)}
              </select>
            </label>
            <label>
              Urbanicity{" "}
              <select value={urbanicityFilter} onChange={(event) => setPivotParam("urbanicity", event.target.value)}>
                <option value="">All 4 urbanicity groups</option>
                {urbanicities.map((urbanicity) => <option key={urbanicity}>{urbanicity}</option>)}
              </select>
            </label>
          </div>
        )}
        <PivotTable
          rows={filteredRows}
          groupColumn={pivot.data.group_column}
          labels={scenarioLabels}
          dimension={dimension}
          sites={dashboard.data.scenario.selected}
          searchParams={searchParams}
          tier={tier}
          scenario={scenario}
        />
        <p className="chart-note">
          Values are read from <code>{pivot.data.source_csv}</code>. The combined view is aggregated on the server
          from the certified run-level output; the browser only filters returned rows. R9{" "}
          {pivot.data.certified_provenance?.r9_status ?? "PASS"} ·{" "}
          {pivot.data.certified_provenance?.figure_registry_tier ?? "f2v3_final"}.
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
