import { useMemo } from "react";
import { useDashboard, useGeometry } from "../state/queries";
import { useActiveRows } from "../state/rows";
import { useScenario } from "../state/scenario";
import { useFilters } from "../state/filters";
import { useHealth } from "../state/queries";
import { matchesFilters } from "../lib/selectors";
import { FilterPanel } from "../components/FilterPanel";
import { MapCanvas } from "../components/MapCanvas";
import { CoverageMatrix } from "../components/CoverageMatrix";
import { KpiBar } from "../components/KpiBar";
import { ScoreDistribution, StationDistanceDistribution } from "../components/Distributions";
import { LoadingState, ErrorState, DegradedBanner } from "../components/states/States";

export function MapWorkspace({ filtersOpen, onCloseFilters }: { filtersOpen: boolean; onCloseFilters: () => void }) {
  const dashboard = useDashboard();
  const geometry = useGeometry();
  const health = useHealth();
  const { applied } = useScenario();
  const { rows, selectedRows, isLoading, isError, error, refetch } = useActiveRows();
  const { filters } = useFilters();

  const filteredRows = useMemo(() => rows.filter((r) => matchesFilters(r, filters)), [rows, filters]);

  if (health.data?.status === "degraded") return <DegradedBanner detail={health.data.detail} />;
  if (isLoading || geometry.isLoading) return <LoadingState label="Loading analysis workspace…" />;
  if (isError || geometry.isError) {
    const message = error?.message ?? (geometry.error as Error)?.message ?? "Failed to load data.";
    return (
      <ErrorState
        message={message}
        onRetry={() => {
          refetch();
          geometry.refetch();
        }}
      />
    );
  }

  const kpis = dashboard.data!.kpis;
  return (
    <div className="ws">
      <FilterPanel
        scenario={applied ?? undefined}
        open={filtersOpen}
        resultCount={filteredRows.length}
        totalCount={rows.length}
        onClose={onCloseFilters}
      />
      <div className="stage">
        <KpiBar kpis={kpis} />
        {geometry.data && <MapCanvas geometry={geometry.data} rows={rows} />}
        <div className="strip">
          <section aria-label="Stratum coverage matrix">
            <h4>Coverage · 5 climate × 4 urbanicity</h4>
            <CoverageMatrix rows={selectedRows} />
          </section>
          <section aria-label="Score distribution">
            <h4>Candidate score distribution ({filteredRows.length})</h4>
            <ScoreDistribution rows={filteredRows} />
            <div className="chart-note">Composite score across candidates matching every active filter.</div>
          </section>
          <section aria-label="Station-distance distribution">
            <h4>Candidate station distance (mi)</h4>
            <StationDistanceDistribution rows={filteredRows} />
            <div className="chart-note">Catchment-centroid distance to each candidate’s assigned ISD station.</div>
          </section>
        </div>
      </div>
    </div>
  );
}
