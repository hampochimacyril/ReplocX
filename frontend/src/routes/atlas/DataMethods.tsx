import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useDashboard, useProvenance } from "../../state/queries";
import { SCENARIOS, SCENARIO_COLOR, useAtlasControls, fmt } from "./atlas";

/** Story section: how the 20 ReplocX locations were selected before simulation. */
export function DataMethods() {
  const dashboard = useDashboard();
  const provenance = useProvenance();
  const { scenarioLabels } = useAtlasControls();

  if (dashboard.isLoading || provenance.isLoading) return <LoadingState label="Loading location-selection context…" />;
  if (dashboard.isError || !dashboard.data)
    return <ErrorState message={(dashboard.error as Error)?.message ?? "Failed."} onRetry={dashboard.refetch} />;
  if (provenance.isError || !provenance.data)
    return <ErrorState message={(provenance.error as Error)?.message ?? "Failed."} onRetry={provenance.refetch} />;

  const rows = dashboard.data.scenario.selected;
  const climateCounts = Object.entries(dashboard.data.climate_distribution);
  const urbanCounts = Object.entries(dashboard.data.urbanicity_distribution);

  return (
    <div className="doc atlas-story">
      <section className="atlas-story-section">
        <p className="atlas-kicker">Location frame</p>
        <h1>How locations were selected</h1>
        <p className="muted">
          The Atlas inherits the existing ReplocX 20-stratum location scaffold; it does not reselect locations
          during Atlas rendering.
        </p>
        <p>
          One representative catchment is selected for each climate-region × urbanicity stratum. Rural targets use
          counties; non-rural targets use CBSAs. ZIP, ZCTA, county, CBSA, station, and tract identifiers remain
          distinct throughout the workflow.
        </p>
      </section>

      <section className="atlas-story-section">
        <div className="atlas-section-head">
          <div>
            <h2>Coverage</h2>
            <p className="muted">Selected catchments are the drill-down frame for the Atlas map.</p>
          </div>
          <Tag tone="info">{fmt(rows.length, 0)} selected</Tag>
        </div>
        <div className="atlas-stat-grid">
          {climateCounts.map(([label, count]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{fmt(count, 0)}</strong>
            </div>
          ))}
          {urbanCounts.map(([label, count]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{fmt(count, 0)}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="atlas-story-section">
        <h2>Scenario dictionary</h2>
        <div className="atlas-scenario-strip" aria-label="Canonical scenario dictionary">
          {SCENARIOS.map((scenario) => (
            <span key={scenario} style={{ borderColor: SCENARIO_COLOR[scenario] }}>
              <i style={{ background: SCENARIO_COLOR[scenario] }} />
              {scenarioLabels[scenario]} ({scenario})
            </span>
          ))}
        </div>
      </section>

      <section className="atlas-story-section">
        <h2>Selection provenance</h2>
        <dl className="kv" style={{ gridTemplateColumns: "220px 1fr" }}>
          <dt>Method version</dt>
          <dd>{provenance.data.method_version}</dd>
          <dt>Boundary system</dt>
          <dd>{provenance.data.boundary_system}</dd>
          <dt>ZIP crosswalk</dt>
          <dd>{provenance.data.zip_crosswalk.source_version}</dd>
          <dt>Weather QC</dt>
          <dd>{provenance.data.weather_qc.status}</dd>
        </dl>
      </section>
    </div>
  );
}
