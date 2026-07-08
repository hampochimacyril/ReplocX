import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useAtlasExports, useAtlasProvenance, fmt } from "./atlas";

/** Exports/provenance: certified data files and f2v3 registry records. */
export function Exports() {
  const provenance = useAtlasProvenance();
  const exportsCatalog = useAtlasExports();

  if (provenance.isLoading || exportsCatalog.isLoading) return <LoadingState label="Loading exports and provenance…" />;
  if (provenance.isError || !provenance.data)
    return <ErrorState message={(provenance.error as Error)?.message ?? "Failed."} onRetry={provenance.refetch} />;
  if (exportsCatalog.isError || !exportsCatalog.data)
    return <ErrorState message={(exportsCatalog.error as Error)?.message ?? "Failed."} onRetry={exportsCatalog.refetch} />;

  const files = Object.entries(provenance.data.file_checksums).sort(([a], [b]) => a.localeCompare(b));
  const resultFigures = exportsCatalog.data.figure_bundles.filter(
    (row) => row.figure_class !== "supplementary" && row.figure_id !== "Fig19",
  );
  const supplementary = exportsCatalog.data.figure_bundles.filter(
    (row) => row.figure_class === "supplementary" || row.figure_id === "Fig19",
  );

  return (
    <div className="doc atlas-story">
      <section className="atlas-story-section">
        <p className="atlas-kicker">Exports/provenance</p>
        <h1>Exports/provenance</h1>
        <p className="muted">
          Every table and figure listed here resolves to the certified four-scenario tier and the f2v3_final
          registry. Superseded figure families are not served.
        </p>
      </section>

      <section className="atlas-story-section">
        <h2>View CSV exports</h2>
        <div className="tablewrap">
          <table className="dtable">
            <thead>
              <tr>
                <th>View</th>
                <th>Status</th>
                <th>Source CSV</th>
                <th>Citation</th>
              </tr>
            </thead>
            <tbody>
              {exportsCatalog.data.views.map((view) => (
                <tr key={view.view}>
                  <td>{view.label}</td>
                  <td>
                    <Tag tone={view.csv_export.status === "READY" ? "ok" : "warn"} title={view.csv_export.reason}>
                      {view.csv_export.status}
                    </Tag>
                  </td>
                  <td>
                    <code>{view.csv_export.source_csv ?? view.csv_export.reason}</code>
                  </td>
                  <td>{view.citation_text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="atlas-story-section">
        <h2>Results figure registry</h2>
        <div className="atlas-figure-grid">
          {resultFigures.map((figure) => (
            <article className="atlas-figure-card" key={figure.figure_id}>
              <Tag tone="info">f2v3_final</Tag>
              <strong>{figure.figure_id} · {figure.stem}</strong>
              <dl className="kv" style={{ gridTemplateColumns: "140px 1fr" }}>
                <dt>Source CSV</dt>
                <dd><code>{figure.source_csv}</code></dd>
                <dt>PNG/PDF/SVG</dt>
                <dd>
                  <code>{figure.asset_png}</code><br />
                  <code>{figure.asset_pdf}</code><br />
                  <code>{figure.asset_svg}</code>
                </dd>
                <dt>Provenance</dt>
                <dd><code>{figure.provenance_sidecar}</code></dd>
                <dt>Citation</dt>
                <dd>{figure.citation_text}</dd>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="atlas-story-section">
        <h2>Supplementary/Methods</h2>
        {supplementary.map((figure) => (
          <article className="atlas-figure-card" key={figure.figure_id}>
            <Tag tone="warn">Not main results grid</Tag>
            <strong>{figure.figure_id} · {figure.stem}</strong>
            <code>{figure.source_csv}</code>
          </article>
        ))}
      </section>

      <section className="atlas-story-section">
        <h2>Certified data domain ({files.length} files)</h2>
        <div className="tablewrap" style={{ maxHeight: 420 }}>
          <table className="dtable">
            <thead>
              <tr>
                <th>File</th>
                <th className="num">Bytes</th>
                <th>SHA-256</th>
              </tr>
            </thead>
            <tbody>
              {files.map(([path, meta]) => (
                <tr key={path}>
                  <td>
                    <span className="cell-label" title={meta.file ?? path} style={{ maxWidth: 420 }}>
                      {path}
                    </span>
                  </td>
                  <td className="num">{fmt(meta.bytes, 0)}</td>
                  <td>
                    <code title={meta.sha256}>{meta.sha256.slice(0, 16)}...</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
