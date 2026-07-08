import { useEffect, useRef, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { X, MapPin, Building2, Thermometer, Boxes, Gauge, ShieldCheck, FileText } from "lucide-react";
import { useSelection } from "../state/selection";
import { useDashboard, useProvenance } from "../state/queries";
import { isRepresentative, rowKey } from "../lib/selectors";
import { VerificationTag, WeatherQcTag } from "./ui/Tag";
import { formatInt, formatMiles, formatNumber, formatPercentile, formatScore } from "../lib/format";
import type { CatchmentRow, ScenarioWeights, ZipLookupResponse, ZipResolution } from "../lib/types";

function Section({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <section className="sect">
      <div className="st">
        {icon}
        {title}
      </div>
      {children}
    </section>
  );
}

function KV({ items }: { items: Array<[string, ReactNode]> }) {
  return (
    <dl className="kv">
      {items.map(([k, v]) => (
        <div key={k} style={{ display: "contents" }}>
          <dt>{k}</dt>
          <dd className="num">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function ScoreComponent({ label, value, weight }: { label: string; value: number; weight?: number }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--fs-body-sm)" }}>
        <span className="muted">{label}{weight === undefined ? "" : ` (${formatPercentile(weight)})`}</span>
        <span className="num">{formatPercentile(value)}</span>
      </div>
      <div className="scorebar">
        <span style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
      </div>
    </div>
  );
}

function CatchmentSections({
  row,
  weights,
  selectedRepresentative,
  nearbyStations,
}: {
  row: CatchmentRow;
  weights?: ScenarioWeights;
  selectedRepresentative?: CatchmentRow | null;
  nearbyStations?: ZipLookupResponse["nearby_weather_stations"];
}) {
  const composite = row.scenario_score ?? row.location_score;
  const representativeDiffers =
    selectedRepresentative && rowKey(selectedRepresentative) !== rowKey(row);
  return (
    <>
      <Section icon={<Building2 size={14} aria-hidden />} title="Catchment">
        <KV
          items={[
            ["Label", <span className="muted">{row.catchment_label}</span>],
            ["Type", row.catchment_type],
            ["Code", row.catchment_code],
            ["Climate", <span className="muted">{row.climate_region}</span>],
            ["Urbanicity", <span className="muted">{row.urbanicity}</span>],
            ["Population (2010)", formatInt(row.population_2010)],
            ["Housing units", formatInt(row.housing_units_2010)],
            ["Pop. density", `${formatInt(row.population_density_sqmi)}/sq mi`],
            [
              "Stratum representative",
              representativeDiffers
                ? <span className="muted">{selectedRepresentative.catchment_label}</span>
                : isRepresentative(row) ? "This catchment" : "Not selected",
            ],
          ]}
        />
      </Section>

      <Section icon={<Thermometer size={14} aria-hidden />} title="Weather station">
        <KV
          items={[
            ["Station", <span className="muted">{row.selected_station_name}</span>],
            ["USAF/ID", row.selected_station_number],
            ["Distance", formatMiles(row.station_distance_miles)],
            ["Hourly QC", <WeatherQcTag status={row.hourly_weather_qc_status} />],
          ]}
        />
        {nearbyStations && nearbyStations.length > 0 && (
          <div className="nearby-stations">
            <div className="muted small">Nearest stations to the ZIP point</div>
            {nearbyStations.map((station) => (
              <div className="nearby-station" key={String(station.station_number)}>
                <span>{station.station_name}</span>
                <span className="num muted">
                  {station.distance_from_zip_miles === null ? "distance unavailable" : formatMiles(station.distance_from_zip_miles)}
                  {" · "}
                  {station.weather_qc_status}
                </span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section icon={<Boxes size={14} aria-hidden />} title="ResStock filter">
        <KV
          items={[
            ["Filter field", <code className="muted">{row.nrel_filter_field ?? "—"}</code>],
            ["Filter value", String(row.nrel_filter_value ?? "—")],
            ["Verification", <VerificationTag status={row.nrel_verification_status} />],
          ]}
        />
        {row.filter_scope_note && <p className="note">{row.filter_scope_note}</p>}
      </Section>

      <Section icon={<Gauge size={14} aria-hidden />} title="Score components">
        <ScoreComponent
          label="Housing-unit coverage"
          value={row.housing_unit_coverage_percentile}
          weight={weights?.housing_unit_coverage_percentile}
        />
        <ScoreComponent
          label="Population density"
          value={row.population_density_percentile}
          weight={weights?.population_density_percentile}
        />
        <ScoreComponent
          label="Population coverage"
          value={row.population_coverage_percentile}
          weight={weights?.population_coverage_percentile}
        />
        <KV
          items={[
            ["Composite score", <strong>{formatScore(composite)}</strong>],
            ["Selection rank", row.scenario_rank ?? row.selection_rank],
            ["Selected", isRepresentative(row) ? "Yes" : "No"],
          ]}
        />
        {row.scenario_note && <p className="note">{row.scenario_note}</p>}
      </Section>

      <Section icon={<ShieldCheck size={14} aria-hidden />} title="Data quality">
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <WeatherQcTag status={row.hourly_weather_qc_status} />
          <VerificationTag status={row.nrel_verification_status} />
        </div>
        {row.hourly_weather_qc_status !== "COMPLETE" && (
          <p className="note">
            Hourly weather completeness is below the 90% temperature + humidity threshold for this station-year.
          </p>
        )}
      </Section>
    </>
  );
}

function ZipSection({ resolved, matchCount }: { resolved: ZipResolution; matchCount: number }) {
  return (
    <Section icon={<MapPin size={14} aria-hidden />} title="ZIP / ZCTA">
      <KV
        items={[
          ["ZIP", resolved.zip_code],
          ["ZCTA", resolved.zcta || <span className="muted">no ZCTA mapping</span>],
          ["County", <span className="muted">{`${resolved.county_label} (${resolved.county_geoid})`}</span>],
          ["CBSA", <span className="muted">{`${resolved.cbsa_label} (${resolved.cbsa_code})`}</span>],
          ["State", resolved.state],
          ["Climate", <span className="muted">{resolved.climate_region}</span>],
          ["Urbanicity", <span className="muted">{resolved.urbanicity}</span>],
          ["Allocation ratio", formatNumber(resolved.allocation_ratio, 2)],
          ["Match type", <span className="muted">{resolved.match_type}</span>],
        ]}
      />
      {matchCount > 1 && (
        <p className="note">This ZIP has {matchCount} crosswalk records (one-to-many); the primary allocation is shown.</p>
      )}
      {resolved.uncertainty_note && <p className="note">{resolved.uncertainty_note}</p>}
    </Section>
  );
}

export function DetailsDrawer() {
  const { selection, clear } = useSelection();
  const dashboard = useDashboard();
  const provenance = useProvenance();
  const closeRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLElement>(null);
  const lastFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (selection) {
      lastFocus.current = document.activeElement as HTMLElement;
      closeRef.current?.focus();
    } else {
      lastFocus.current?.focus?.();
    }
  }, [selection]);

  useEffect(() => {
    if (!selection) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") clear();
      if (e.key !== "Tab" || !drawerRef.current) return;
      const focusable = Array.from(
        drawerRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [selection, clear]);

  if (!selection) return null;

  const title =
    selection.kind === "zip"
      ? `ZIP ${selection.result.zip_code}`
      : selection.row.catchment_label;
  const subtitle =
    selection.kind === "zip"
      ? selection.result.resolved.cbsa_label
      : `${selection.row.climate_region} · ${selection.row.urbanicity}`;
  const displayRow =
    selection.kind === "zip"
      ? selection.result.candidate ?? selection.result.selected_representative
      : selection.row;
  const selectedRepresentative =
    selection.kind === "zip" ? selection.result.selected_representative : selection.row;
  const weights = dashboard.data?.scenario.config.weights;

  return (
    <>
      <div className="scrim" onClick={clear} aria-hidden />
      <aside
        ref={drawerRef}
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="details-title"
      >
        <div className="dh">
          <div className="title">
            <div id="details-title" style={{ fontWeight: 600 }}>{title}</div>
            <div className="muted small">{subtitle}</div>
          </div>
          <button ref={closeRef} className="btn btn-icon" type="button" onClick={clear} aria-label="Close details">
            <X size={16} aria-hidden />
          </button>
        </div>
        <div className="db">
          {selection.kind === "zip" ? (
            <>
              <ZipSection resolved={selection.result.resolved} matchCount={selection.result.crosswalk_matches.length} />
              {displayRow ? (
                <CatchmentSections
                  row={displayRow}
                  weights={weights}
                  selectedRepresentative={selectedRepresentative}
                  nearbyStations={selection.result.nearby_weather_stations}
                />
              ) : (
                <Section icon={<Building2 size={14} aria-hidden />} title="Catchment">
                  <p className="muted small">No representative resolved for this ZIP in the current dataset.</p>
                </Section>
              )}
            </>
          ) : (
            <>
              <Section icon={<MapPin size={14} aria-hidden />} title="ZIP / ZCTA">
                <p className="muted small">Search a ZIP code to inspect its ZCTA, crosswalk, and caveats here.</p>
              </Section>
              <CatchmentSections row={selection.row} weights={weights} />
            </>
          )}

          <Section icon={<FileText size={14} aria-hidden />} title="Provenance">
            <p className="muted small">
              {provenance.data
                ? `${provenance.data.method_version} · ${provenance.data.boundary_system} · ${provenance.data.data_mode.toUpperCase()} data`
                : "Loading method version and boundary provenance…"}
            </p>
            {provenance.data?.limitations[0] && <p className="note">{provenance.data.limitations[0]}</p>}
            <Link className="btn" to="/methodology" onClick={clear} style={{ marginTop: 6 }}>
              Methodology &amp; data sources
            </Link>
          </Section>
        </div>
      </aside>
    </>
  );
}
