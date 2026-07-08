import { RotateCcw, X } from "lucide-react";
import { useFilters, isDefault } from "../state/filters";
import { CLIMATE_REGIONS, URBANICITY } from "../lib/constants";
import { formatPercentile } from "../lib/format";
import type { ScenarioConfig } from "../lib/types";

/**
 * Persistent filter/scenario panel (§3). Filters on top; a read-only summary of
 * the active scenario below the divider — full scenario editing is the Scenario
 * context (Session 8). All filter state is URL-encoded and shareable.
 */
export function FilterPanel({
  scenario,
  open = false,
  resultCount,
  totalCount,
  onClose,
}: {
  scenario?: ScenarioConfig;
  open?: boolean;
  resultCount?: number;
  totalCount?: number;
  onClose?: () => void;
}) {
  const { filters, setFilters, reset } = useFilters();
  const weights = scenario?.weights;

  return (
    <>
      {open && <button className="panel-scrim" type="button" aria-label="Close filters" onClick={onClose} />}
      <aside className={`panel ${open ? "show" : ""}`} aria-label="Filters and scenario">
        <div className="panel-head">
          <div>
            <div className="grouphead">Filters</div>
            {resultCount !== undefined && totalCount !== undefined && (
              <div className="muted small num" aria-live="polite">
                {resultCount.toLocaleString()} of {totalCount.toLocaleString()} candidates
              </div>
            )}
          </div>
          <button className="btn btn-icon panel-close" type="button" onClick={onClose} aria-label="Close filters">
            <X size={16} aria-hidden />
          </button>
        </div>

        <div className="group">
        <div className="field">
          <label htmlFor="f-climate">Climate region</label>
          <select
            id="f-climate"
            className="select"
            value={filters.climate}
            onChange={(e) => setFilters({ climate: e.target.value })}
          >
            <option value="">All climate regions</option>
            {CLIMATE_REGIONS.map((r) => (
              <option key={r.name} value={r.name}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="f-selected">Selected status</label>
          <select
            id="f-selected"
            className="select"
            value={filters.selectedStatus}
            onChange={(e) => setFilters({ selectedStatus: e.target.value as typeof filters.selectedStatus })}
          >
            <option value="">Representatives and candidates</option>
            <option value="selected">Selected representatives</option>
            <option value="candidate">Non-selected candidates</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="f-urb">Urbanicity</label>
          <select
            id="f-urb"
            className="select"
            value={filters.urbanicity}
            onChange={(e) => setFilters({ urbanicity: e.target.value })}
          >
            <option value="">All urbanicity</option>
            {URBANICITY.map((u) => (
              <option key={u.short} value={u.short}>
                {u.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="f-verif">ResStock verification</label>
          <select
            id="f-verif"
            className="select"
            value={filters.verification}
            onChange={(e) => setFilters({ verification: e.target.value })}
          >
            <option value="">Any status</option>
            <option value="VERIFIED">Verified</option>
            <option value="REVIEW REQUIRED">Review required</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="f-qc">Weather QC</label>
          <select id="f-qc" className="select" value={filters.weatherQc} onChange={(e) => setFilters({ weatherQc: e.target.value })}>
            <option value="">Any completeness</option>
            <option value="COMPLETE">Complete (≥90%)</option>
            <option value="INCOMPLETE">Incomplete</option>
            <option value="PENDING">Pending / not scored</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="f-smin">
            Score range · {formatPercentile(filters.scoreMin)}–{formatPercentile(filters.scoreMax)}
          </label>
          <div className="rangewrap">
            <input
              id="f-smin"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={filters.scoreMin}
              aria-label="Minimum score"
              onChange={(e) => setFilters({ scoreMin: Math.min(Number(e.target.value), filters.scoreMax) })}
            />
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={filters.scoreMax}
              aria-label="Maximum score"
              onChange={(e) => setFilters({ scoreMax: Math.max(Number(e.target.value), filters.scoreMin) })}
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="f-dist">
            Max station distance · {filters.maxStationDistance === null ? "any" : `${filters.maxStationDistance} mi`}
          </label>
          <input
            id="f-dist"
            type="range"
            min={0}
            max={300}
            step={10}
            value={filters.maxStationDistance ?? 300}
            aria-label="Maximum station distance in miles"
            onChange={(e) => setFilters({ maxStationDistance: Number(e.target.value) >= 300 ? null : Number(e.target.value) })}
          />
        </div>

        <button className="btn" type="button" onClick={reset} disabled={isDefault(filters)} style={{ marginTop: "var(--space-3)" }}>
          <RotateCcw size={14} aria-hidden /> Reset filters
        </button>
      </div>

      <div className="group">
        <div className="grouphead">Active scenario</div>
        {weights ? (
          <>
            <div className="weightline">
              <span>Housing-unit coverage</span>
              <span className="num">{formatPercentile(weights.housing_unit_coverage_percentile)}</span>
            </div>
            <div className="weightline">
              <span>Population density</span>
              <span className="num">{formatPercentile(weights.population_density_percentile)}</span>
            </div>
            <div className="weightline">
              <span>Population coverage</span>
              <span className="num">{formatPercentile(weights.population_coverage_percentile)}</span>
            </div>
            <div className="weightline" style={{ borderTop: "1px solid var(--border)", paddingTop: 4, marginTop: 4 }}>
              <span className="muted">Weights Σ</span>
              <span className="num" style={{ color: "var(--ok)", fontWeight: 600 }}>
                {formatPercentile(
                  weights.housing_unit_coverage_percentile +
                    weights.population_density_percentile +
                    weights.population_coverage_percentile,
                )}
              </span>
            </div>
            <div className="checks" style={{ marginTop: "var(--space-3)" }}>
              <span className="check">
                <input type="checkbox" checked={scenario?.unique_location_constraint} readOnly aria-readonly /> Unique locations
              </span>
              <span className="check">
                <input type="checkbox" checked={scenario?.require_weather_qc} readOnly aria-readonly /> Require weather QC
              </span>
            </div>
            <p className="note">Editing weights, density screen, and PA preference opens in the Scenario context.</p>
          </>
        ) : (
          <p className="muted small">Scenario summary loads with the dashboard.</p>
        )}
      </div>
      </aside>
    </>
  );
}
