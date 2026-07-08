import { useDashboard, useProvenance } from "../state/queries";
import { useScenario } from "../state/scenario";
import { TARGET_STRATA } from "../lib/constants";
import { weightSum } from "../lib/scenario";
import { LoadingState, ErrorState } from "../components/states/States";
import { Tag } from "../components/ui/Tag";

/** Readable document context (§7.6): method, vintage, boundary rules, data
 * lineage, validation status, crosswalk and weather-QC limitations, source
 * citations, and API/export documentation. */
export function Methodology() {
  const { data, isLoading, isError, error, refetch } = useProvenance();
  const dashboard = useDashboard();
  const { applied } = useScenario();

  if (isLoading) return <LoadingState label="Loading methodology…" />;
  if (isError || !data) return <ErrorState message={(error as Error)?.message ?? "Failed to load provenance."} onRetry={refetch} />;

  const kpis = dashboard.data?.kpis;
  const summary = dashboard.data?.scenario.summary;
  const weights = applied?.weights;
  const weightTotal = weights ? weightSum(weights) : 1;

  const checks: Array<{ label: string; pass: boolean; detail: string }> = [
    {
      label: "20 strata resolved",
      pass: (summary?.strata_count ?? 0) === TARGET_STRATA,
      detail: `${summary?.strata_count ?? "—"} of ${TARGET_STRATA} climate × urbanicity strata represented.`,
    },
    {
      label: "Distinct catchments",
      pass: (summary?.distinct_location_count ?? 0) === TARGET_STRATA,
      detail: `${summary?.distinct_location_count ?? "—"} distinct catchments under the uniqueness constraint.`,
    },
    {
      label: "Score weights sum to 1.0",
      pass: Math.abs(weightTotal - 1) <= 1e-6,
      detail: `Active composite weights total ${weightTotal.toFixed(2)}.`,
    },
    {
      label: "ResStock enumeration verified",
      pass: !!kpis && kpis.verified_filter_count === kpis.target_strata,
      detail: `${kpis?.verified_filter_count ?? "—"} of ${kpis?.target_strata ?? TARGET_STRATA} filters verified; the rest are marked REVIEW REQUIRED.`,
    },
    {
      label: "Hourly weather QC complete",
      pass: !!kpis && kpis.weather_qc_complete_count === kpis.target_strata,
      detail: `${kpis?.weather_qc_complete_count ?? "—"} of ${kpis?.target_strata ?? TARGET_STRATA} selected station-years meet the ≥90% completeness threshold.`,
    },
  ];

  return (
    <div className="doc">
      <h1>Methodology &amp; data</h1>
      <p className="muted">{data.analysis_name}</p>

      <h2>Method &amp; vintage</h2>
      <dl className="kv" style={{ gridTemplateColumns: "200px 1fr" }}>
        <dt>Method version</dt>
        <dd>{data.method_version}</dd>
        <dt>Boundary system</dt>
        <dd>{data.boundary_system}</dd>
        <dt>Data mode</dt>
        <dd>{data.data_mode}</dd>
        <dt>Source directory</dt>
        <dd className="muted">{data.source_directory}</dd>
      </dl>

      <h2>Boundary rules</h2>
      <p>
        Exactly 20 strata (5 climate regions × 4 urbanicity categories), one representative each. Rural target catchments use
        counties; non-rural target catchments use CBSAs. Geography identifiers are preserved as strings with leading zeros, and
        scoring and allocation are deterministic.
      </p>

      <h2>Data lineage</h2>
      <p>
        The deterministic pipeline derives every app-ready output in order, caching raw downloads outside the committed results and
        recording source dates and checksums at each step:
      </p>
      <ol className="lineage-steps">
        <li>
          <strong>Census tract inputs</strong> — population, housing units, land area, and internal points are fetched, with tract,
          county, state, and CBSA identifiers preserved as strings.
        </li>
        <li>
          <strong>Classification</strong> — each tract is assigned one of four urbanicity categories and a climate region from the
          project-approved mappings.
        </li>
        <li>
          <strong>Catchment aggregation</strong> — rural tracts roll up to county catchments and non-rural tracts to CBSA
          catchments; join losses and unresolved classifications are reported, not discarded.
        </li>
        <li>
          <strong>Ancillary joins</strong> — HUD-USPS ZIP crosswalk (with allocation ratios and one-to-many records), TIGER/Line
          geometry, NOAA ISD weather completeness, and the NREL ResStock/ComStock enumeration dictionary.
        </li>
        <li>
          <strong>Scoring &amp; validation</strong> — the composite score and minimum-cost allocation run deterministically, then{" "}
          <code>pipeline/validate.py</code> checks every invariant before the API serves the result.
        </li>
      </ol>

      <h2>Validation status</h2>
      <table>
        <thead>
          <tr>
            <th>Invariant</th>
            <th>Status</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody>
          {checks.map((c) => (
            <tr key={c.label}>
              <td>{c.label}</td>
              <td>
                <Tag tone={c.pass ? "ok" : "warn"}>{c.pass ? "PASS" : "REVIEW"}</Tag>
              </td>
              <td className="muted">{c.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted small">
        Status reflects the {data.data_mode} dataset currently served. ResStock and weather values are never silently marked ready;
        unverified enumeration values remain <code>REVIEW REQUIRED</code>.
      </p>

      <h2>ZIP crosswalk limitations</h2>
      <p>
        {data.zip_crosswalk.mode} · {data.zip_crosswalk.record_count} records ·{" "}
        <span className="muted">{data.zip_crosswalk.source_version}</span>
      </p>
      <p className="muted">{data.zip_crosswalk.limitation}</p>

      <h2>Weather QC</h2>
      <p>
        {data.weather_qc.threshold}. Stations scored: {data.weather_qc.stations_scored} ({data.weather_qc.status}).
      </p>

      <h2>Sources</h2>
      <table>
        <thead>
          <tr>
            <th>Source</th>
            <th>Role</th>
            <th>Reference</th>
          </tr>
        </thead>
        <tbody>
          {data.sources.map((s) => (
            <tr key={s.name}>
              <td>{s.name}</td>
              <td className="muted">{s.role}</td>
              <td className="muted">{s.version ?? s.file ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Limitations</h2>
      <ul>
        {data.limitations.map((l) => (
          <li key={l}>{l}</li>
        ))}
      </ul>

      <h2>API &amp; exports</h2>
      <p>
        The interface reads the versioned <code>/api/v1</code> contract; the Python backend owns data, scoring, scenario
        persistence, and exports. Machine-readable schema: <a href="/api/v1/openapi.json">/api/v1/openapi.json</a>.
      </p>
      <table>
        <thead>
          <tr>
            <th>Endpoint</th>
            <th>Purpose</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <code>GET /api/v1/dashboard</code>
            </td>
            <td className="muted">Baseline selection, KPIs, and distributions.</td>
          </tr>
          <tr>
            <td>
              <code>GET /api/v1/candidates</code>
            </td>
            <td className="muted">Filtered, paged candidate ranking.</td>
          </tr>
          <tr>
            <td>
              <code>POST /api/v1/scenarios/evaluate</code>
            </td>
            <td className="muted">Score a scenario configuration without saving it.</td>
          </tr>
          <tr>
            <td>
              <code>GET/POST /api/v1/scenarios</code>
            </td>
            <td className="muted">List or save versioned, shareable scenarios.</td>
          </tr>
          <tr>
            <td>
              <code>GET /api/v1/zip/{"{zip}"}</code>
            </td>
            <td className="muted">Resolve a ZIP to its ZCTA, crosswalk, and representative.</td>
          </tr>
          <tr>
            <td>
              <code>GET /api/v1/geometry</code> · <code>/provenance</code>
            </td>
            <td className="muted">Selected-catchment GeoJSON and source provenance.</td>
          </tr>
        </tbody>
      </table>
      <p>
        Export formats: site-list CSV, ResStock/ComStock sampling CSV, OpenStudio/EnergyPlus manifest JSON (via the Export menu),
        the on-screen ranking CSV (Catchments table), a reusable scenario-config JSON, and a map PNG snapshot.
      </p>
    </div>
  );
}
