import { useEffect } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { LoadingState, ErrorState } from "../../components/states/States";
import { useDashboard } from "../../state/queries";
import { useSelection } from "../../state/selection";
import { rowKey } from "../../lib/selectors";
import { fmt } from "./atlas";

/** Deep-link target for Atlas map drill-downs. The drawer owns the detailed UI. */
export function AtlasSiteDetail() {
  const { siteId = "" } = useParams();
  const [params] = useSearchParams();
  const dashboard = useDashboard();
  const { selectCatchment } = useSelection();

  const decoded = decodeURIComponent(siteId);
  const row = dashboard.data?.scenario.selected.find((item) => rowKey(item) === decoded);

  useEffect(() => {
    if (row) selectCatchment(row);
  }, [row, selectCatchment]);

  if (dashboard.isLoading) return <LoadingState label="Loading Atlas site detail…" />;
  if (dashboard.isError || !dashboard.data) {
    return <ErrorState message={(dashboard.error as Error)?.message ?? "Failed."} onRetry={dashboard.refetch} />;
  }

  if (!row) {
    return (
      <div className="doc">
        <h1>Site not found</h1>
        <p className="muted">No selected catchment matched <code>{decoded}</code>.</p>
        <Link className="btn" to="/atlas">Back to Atlas overview</Link>
      </div>
    );
  }

  return (
    <div className="doc atlas-story">
      <section className="atlas-story-section">
        <p className="atlas-kicker">Site drill-down</p>
        <h1>{row.catchment_label}</h1>
        <p className="muted">
          {row.climate_region} · {row.urbanicity} · {row.catchment_type} {row.catchment_code}
        </p>
        <dl className="kv" style={{ gridTemplateColumns: "220px 1fr" }}>
          <dt>Scenario</dt>
          <dd>{params.get("scenario") ?? "D"}</dd>
          <dt>Tier</dt>
          <dd>{params.get("tier") ?? "annual"}</dd>
          <dt>Metric</dt>
          <dd>{params.get("metric") ?? "op_temp_p95_true_c_mean"}</dd>
          <dt>Weather station</dt>
          <dd>{row.selected_station_name}</dd>
          <dt>Station distance</dt>
          <dd>{fmt(row.station_distance_miles, 1)} mi</dd>
        </dl>
        <p className="chart-note">
          The details drawer is open with geography, weather, ResStock, score, data-quality, and provenance sections.
        </p>
        <Link className="btn" to="/atlas">Back to Atlas overview</Link>
      </section>
    </div>
  );
}
