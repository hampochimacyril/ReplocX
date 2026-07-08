import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useAtlasProvenance, fmt } from "./atlas";

/** Provenance: manifest SHA, engine, certification chain, and per-file
 * checksums for the bundled canonical dataset. */
export function Provenance() {
  const { data, isLoading, isError, error, refetch } = useAtlasProvenance();
  if (isLoading) return <LoadingState label="Loading provenance…" />;
  if (isError || !data) return <ErrorState message={(error as Error)?.message ?? "Failed."} onRetry={refetch} />;

  const files = Object.entries(data.file_checksums);
  return (
    <div className="doc">
      <h1>Provenance</h1>
      <p className="muted">{data.dataset}</p>

      <dl className="kv" style={{ gridTemplateColumns: "220px 1fr" }}>
        <dt>Tier</dt>
        <dd>{data.tier}</dd>
        <dt>Certified tier id</dt>
        <dd>{data.tier_id}</dd>
        <dt>Certification</dt>
        <dd>{data.certification}</dd>
        <dt>R9 gate report</dt>
        <dd>
          <code>{data.r9_gate_report?.source_csv ?? data.manifest}</code>
        </dd>
        <dt>f2v3 gate report</dt>
        <dd>
          <Tag tone={data.f2v3_gate_report?.status === "PASS" ? "ok" : "warn"} title="f2v3 registry/figure gate status">
            {data.f2v3_gate_report?.status ?? "UNKNOWN"}
          </Tag>{" "}
          <code>{data.f2v3_gate_report?.source_csv}</code>
        </dd>
        <dt>Scenario ordering</dt>
        <dd>{data.scenario_ordering}</dd>
        <dt>Frozen manifest</dt>
        <dd>
          <code>{data.manifest}</code>
        </dd>
        <dt>Canonical source root</dt>
        <dd>
          <code>{data.source_canonical_root}</code>
        </dd>
        <dt>Figure registry</dt>
        <dd>
          <code>{data.f2v3_registry?.registry_csv}</code>
        </dd>
        <dt>Figure captions</dt>
        <dd>
          <code>{data.f2v3_registry?.captions_source ?? "not supplied"}</code>
        </dd>
        <dt>Equity join</dt>
        <dd>{data.equity_verification?.catchment_join_method}</dd>
        <dt>Copied at</dt>
        <dd>{data.copied_at}</dd>
      </dl>

      <div className="banner" role="note">
        <div>
          <strong>Tier wall.</strong>
          <div className="muted small" style={{ marginTop: 4 }}>
            {data.tier_wall}
          </div>
        </div>
      </div>

      <h2>Equity source/vintage notes</h2>
      <div className="tablewrap" style={{ maxHeight: 320 }}>
        <table className="dtable">
          <thead>
            <tr>
              <th>Layer</th>
              <th>Status</th>
              <th>Source/vintage</th>
              <th>Badge</th>
              <th>Join uncertainty</th>
            </tr>
          </thead>
          <tbody>
            {(data.equity_source_notes ?? []).map((layer) => (
              <tr key={layer.id}>
                <td>{layer.label}</td>
                <td>
                  <Tag tone={layer.status === "READY" ? "ok" : "warn"} title={layer.missing_reason ?? undefined}>
                    {layer.status}
                  </Tag>
                </td>
                <td>{layer.source_vintage}</td>
                <td>{layer.proxy_badge}</td>
                <td>{layer.join_uncertainty_note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Bundled dataset checksums ({files.length} files)</h2>
      <div className="tablewrap" style={{ maxHeight: 360 }}>
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
                  <span className="cell-label" title={path} style={{ maxWidth: 360 }}>
                    {path}
                  </span>
                </td>
                <td className="num">{fmt(meta.bytes, 0)}</td>
                <td>
                  <code title={meta.sha256}>{meta.sha256.slice(0, 16)}…</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
