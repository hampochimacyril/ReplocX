import { EChart } from "../../components/EChart";
import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useAtlasControls, useEquityProfiles, useEquityScenarioCross, SCENARIO_COLOR, fmt } from "./atlas";

/** Equity context: the 20-catchment equity frame + a scenario-exposure cross.
 * Every layer carries its verified READY or REVIEW REQUIRED state, proxy badge,
 * source vintage, and join-uncertainty note. */
export function Equity() {
  const { scenario, scenarioLabels } = useAtlasControls();
  const profiles = useEquityProfiles();
  const cross = useEquityScenarioCross(scenario, "climate");

  if (profiles.isLoading || cross.isLoading) return <LoadingState label="Loading equity context…" />;
  if (profiles.isError || !profiles.data)
    return <ErrorState message={(profiles.error as Error)?.message ?? "Failed."} onRetry={profiles.refetch} />;
  if (cross.isError || !cross.data)
    return <ErrorState message={(cross.error as Error)?.message ?? "Failed."} onRetry={cross.refetch} />;

  const groups = cross.data.rows.map((r) => String(r[cross.data!.group_column]));
  const option = {
    tooltip: { trigger: "axis" },
    grid: { left: 58, right: 12, top: 16, bottom: 56 },
    xAxis: { type: "category", data: groups, axisLabel: { interval: 0, rotate: 20, fontSize: 10 } },
    yAxis: { type: "value", name: "hours" },
    series: [
      {
        type: "bar",
        itemStyle: { color: SCENARIO_COLOR[scenario] },
        data: cross.data.rows.map((r) => Number(r.exposure_hours ?? 0)),
        barWidth: "56%",
      },
    ],
  };
  const layerRecords = profiles.data.layers.records ?? [];
  const readyLayers = layerRecords.filter((layer) => layer.status === "READY");
  const reviewLayers = layerRecords.filter((layer) => layer.status !== "READY");

  return (
    <div className="doc">
      <h1>Equity context</h1>
      <p className="muted">{profiles.data.disclaimer}</p>

      <h2>Overheating exposure under {scenarioLabels[scenario]} ({scenario})</h2>
      <div className="chart-frame">
        <EChart option={option} ariaLabel={`${scenarioLabels[scenario]} overheating exposure hours by climate`} height={240} />
        <p className="chart-note">
          {cross.data.metric_label ?? "Overheating exposure hours"} by climate region. {cross.data.threshold_note}{" "}
          D contrast: {fmt(cross.data.rows[0]?.d_minus_scenario_exposure_hours, 0)} hours for the first shown group.{" "}
          {cross.data.note}
        </p>
      </div>

      <h2>Layer verification</h2>
      <div className="atlas-figure-grid">
        {layerRecords.map((layer) => (
          <article className="atlas-figure-card" key={layer.id}>
            <Tag tone={layer.status === "READY" ? "ok" : "warn"} title={layer.join_uncertainty_note}>
              {layer.status}
            </Tag>
            <strong>{layer.label}</strong>
            <p className="muted small">{layer.value_label}</p>
            <dl className="kv" style={{ gridTemplateColumns: "120px 1fr" }}>
              <dt>Source/vintage</dt>
              <dd>{layer.source_vintage}</dd>
              <dt>Badge</dt>
              <dd>
                <Tag tone={layer.status === "READY" ? "info" : "warn"} title="Direct, proxy, modeled, or review status">
                  {layer.proxy_badge}
                </Tag>
              </dd>
              <dt>Join note</dt>
              <dd>{layer.join_uncertainty_note}</dd>
            </dl>
          </article>
        ))}
      </div>

      <h2>Equity frame — 20 catchments</h2>
      <p className="muted">
        Ready layers: {readyLayers.length ? readyLayers.map((l) => l.label).join(", ") : "none"}. Review required:{" "}
        {reviewLayers.map((l) => l.label).join(", ")}.
      </p>
      {profiles.data.missing_source_path ? (
        <div className="banner" role="note">
          <div>
            <strong>REVIEW REQUIRED.</strong>
            <div className="muted small" style={{ marginTop: 4 }}>
              Missing verified equity profile: <code>{profiles.data.missing_source_path}</code>
            </div>
          </div>
        </div>
      ) : null}

      <div className="tablewrap" style={{ maxHeight: 360 }}>
        <table className="dtable">
          <thead>
            <tr>
              <th>Catchment</th>
              <th>Climate</th>
              <th>Urbanicity</th>
              <th className="num">SVI</th>
              <th className="num">Income</th>
              <th className="num">Poverty</th>
              <th className="num">Energy burden</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {profiles.data.catchments.length ? (
              profiles.data.catchments.map((r, i) => (
                <tr key={i}>
                  <td>
                    <span className="cell-label" title={String(r.catchment_label)}>
                      {String(r.catchment_label)}
                    </span>
                  </td>
                  <td>{String(r.climate_region ?? "—")}</td>
                  <td>{String(r.urbanicity_short ?? r.urbanicity ?? "—")}</td>
                  <td className="num">{fmt(r.svi_percentile, 2)}</td>
                  <td className="num">{fmt(r.acs_median_hh_income, 0)}</td>
                  <td className="num">{fmt(r.acs_poverty_rate, 2)}</td>
                  <td className="num">{fmt(r.doe_lead_energy_burden_pct, 2)}</td>
                  <td>
                    <Tag tone={String(r.equity_layer_status) === "READY" ? "ok" : "warn"} title="Equity layer readiness">
                      {String(r.equity_layer_status ?? "REVIEW REQUIRED")}
                    </Tag>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8}>
                  <span className="muted">No verified catchment-level equity profile is available in this Atlas tree.</span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
