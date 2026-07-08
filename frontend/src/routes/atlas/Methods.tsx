import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useAtlasProvenance, useCoolingSeasons, useFigureRegistry, SCENARIOS, useAtlasControls, fmt } from "./atlas";

/** Methods story section for certified inputs, caveats, and supplementary figures. */
export function Methods() {
  const provenance = useAtlasProvenance();
  const cooling = useCoolingSeasons();
  const figures = useFigureRegistry();
  const { scenarioLabels } = useAtlasControls();

  if (provenance.isLoading || cooling.isLoading || figures.isLoading) return <LoadingState label="Loading Atlas methods…" />;
  if (provenance.isError || !provenance.data)
    return <ErrorState message={(provenance.error as Error)?.message ?? "Failed."} onRetry={provenance.refetch} />;
  if (cooling.isError || !cooling.data)
    return <ErrorState message={(cooling.error as Error)?.message ?? "Failed."} onRetry={cooling.refetch} />;
  if (figures.isError || !figures.data)
    return <ErrorState message={(figures.error as Error)?.message ?? "Failed."} onRetry={figures.refetch} />;

  const f19 = figures.data.rows.find((row) => row.figure_id === "Fig19");

  return (
    <div className="doc atlas-story">
      <section className="atlas-story-section">
        <p className="atlas-kicker">Methods</p>
        <h1>Methods</h1>
        <p className="muted">{provenance.data.dataset}</p>
        <p>
          Results are read-only certified aggregates from the R9 reproduction gate. The Atlas does not rerun
          EnergyPlus and does not recompute certified figure values.
        </p>
      </section>

      <section className="atlas-story-section">
        <h2>Four-scenario contract</h2>
        <ul>
          {SCENARIOS.map((scenario) => (
            <li key={scenario}>
              {scenarioLabels[scenario]} ({scenario})
            </li>
          ))}
        </ul>
      </section>

      <section className="atlas-story-section">
        <h2>Cooling-season and sensitivity status</h2>
        <div className="banner" role="note">
          <div>
            <strong>{cooling.data.available ? "Certified cooling-season files available" : "Certified cooling-season files unavailable"}</strong>
            <div className="muted small" style={{ marginTop: 4 }}>
              {cooling.data.long_term_note || cooling.data.reason}
            </div>
          </div>
        </div>
      </section>

      <section className="atlas-story-section">
        <h2>Supplementary/Methods figure</h2>
        {f19 ? (
          <div className="atlas-figure-card">
            <Tag tone="info">Supplementary/Methods</Tag>
            <strong>{f19.figure_id} · {f19.stem}</strong>
            <p>{f19.caption}</p>
            <dl className="kv" style={{ gridTemplateColumns: "160px 1fr" }}>
              <dt>Source CSV</dt>
              <dd><code>{f19.source_csv}</code></dd>
              <dt>Registry route</dt>
              <dd><code>{f19.atlas_route}</code></dd>
            </dl>
          </div>
        ) : (
          <p className="muted">No Fig19 supplementary registry row was served.</p>
        )}
      </section>

      <section className="atlas-story-section">
        <h2>Gate values</h2>
        <dl className="kv" style={{ gridTemplateColumns: "220px 1fr" }}>
          <dt>Tier</dt>
          <dd>{provenance.data.tier_id ?? provenance.data.tier}</dd>
          <dt>Certified cell count</dt>
          <dd>{fmt(provenance.data.certified_cell_count, 0)}</dd>
          <dt>R9 status</dt>
          <dd>{provenance.data.r9_status}</dd>
          <dt>Figure registry tier</dt>
          <dd>{provenance.data.figure_registry_tier}</dd>
          <dt>Canonical data root</dt>
          <dd><code>{provenance.data.canonical_data_root}</code></dd>
        </dl>
      </section>
    </div>
  );
}
